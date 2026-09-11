#!/usr/bin/env python3
"""
Minimal RAG pipeline for querying the OKF Home-Lab Infrastructure bundle
"""

import os
import re
import json
import yaml
import numpy as np
from sentence_transformers import SentenceTransformer

# Attempt to import FAISS; if unavailable, fallback to numpy similarity
try:
    import faiss
except Exception:
    faiss = None

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_helper import get_memory_provider
from typing import List, Dict, Tuple, Optional


class OKFRAGPipeline:
    def __init__(self, bundle_path: str):
        """
        Initialize the RAG pipeline

        Args:
            bundle_path: Path to the OKF bundle root directory
        """
        self.bundle_path = Path(bundle_path)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.documents = []  # List of (content, metadata) tuples
        self.index = None
        self._load_documents()
        self._build_index()

    def _extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Extract YAML frontmatter from markdown content

        Returns:
            Tuple of (frontmatter_dict, body_content)
        """
        import yaml  # local import: module-level yaml may not exist yet

        frontmatter = {}
        body = content

        # Check for frontmatter delimiter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                except Exception:
                    pass  # If parsing fails, treat as no frontmatter

        return frontmatter, body

    def _load_documents(self):
        """Load all markdown documents from the bundle"""
        import yaml  # Import here to avoid issues if not installed

        # Scan projects/, docs/, specs/ for concept folders (01-, 05-, 06-)
        # Concept docs live under these subdirectories, not at the bundle root.
        CONCEPT_PREFIXES = ("01-", "05-", "06-")
        md_files_set = set()
        for subdir in ("projects", "docs", "specs"):
            dir_path = self.bundle_path / subdir
            if dir_path.is_dir():
                for f in dir_path.rglob("*.md"):
                    try:
                        rel = f.relative_to(dir_path)
                        if rel.parts and rel.parts[0].startswith(CONCEPT_PREFIXES):
                            md_files_set.add(f)
                    except ValueError:
                        pass
        md_files_set.update(self.bundle_path.glob("index.md"))
        md_files_set.update(self.bundle_path.glob("log.md"))
        md_files = sorted(md_files_set)

        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract frontmatter and body
                frontmatter, body = self._extract_frontmatter(content)

                # Clean up body text
                body = re.sub(r"\s+", " ", body).strip()

                if body:  # Only add if there's content
                    # Create metadata
                    metadata = {
                        "path": str(md_file.relative_to(self.bundle_path)),
                        "title": frontmatter.get("title", "Untitled"),
                        "type": frontmatter.get("type", "Unknown"),
                        "tags": frontmatter.get("tags", []),
                        "sources": frontmatter.get("sources", []),
                    }

                    self.documents.append((body, metadata))

            except Exception as e:
                print(f"Warning: Could not process {md_file}: {e}")

    def _build_index(self):
        """Build vector store (Mem0 when configured, else FAISS)"""
        if not self.documents:
            print("No documents loaded")
            return

        # Extract text content for embedding
        texts = [doc[0] for doc in self.documents]

        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.model.encode(texts)

        if get_memory_provider() == "mem0":
            from mem0_store import Mem0VectorStore

            self.vector_store = Mem0VectorStore(collection="okf_rag")
        else:
            # existing FAISS logic
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings.astype("float32"))

        if self._uses_mem0():
            # Index documents into Mem0, but only when the bundle changed.
            # Each add() triggers Mem0's LLM fact-extraction (~1-2 s per doc),
            # so re-indexing 223 docs on every cold start costs minutes.
            # A content-hash marker makes this a no-op for unchanged bundles.
            import hashlib

            marker = self.bundle_path / ".mem0_index_hash"
            digest = hashlib.sha256(
                "\n".join(t for t, _ in self.documents).encode()
            ).hexdigest()
            if marker.exists() and marker.read_text().strip() == digest:
                print("Mem0 index up to date (bundle unchanged)")
                return
            metadatas = [
                {**meta, "doc_index": i}
                for i, (text, meta) in enumerate(self.documents)
            ]
            print("Indexing documents into Mem0...")
            self.vector_store.add(texts, metadatas)
            marker.write_text(digest + "\n")
            return

        store = getattr(self, "vector_store", None)
        if store is not None:
            print("Built Mem0 vector store (collection=okf_rag)")
        else:
            print(f"Built index with {self.index.ntotal} vectors")

    def _uses_mem0(self) -> bool:
        return getattr(self, "vector_store", None) is not None

    def query(self, question: str, k: int = 3) -> List[Dict]:
        """
        Query the knowledge base

        Args:
            question: The question to ask
            k: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        if not self._uses_mem0() and self.index is None:
            return [{"error": "Index not built"}]

        # Encode the question
        question_embedding = self.model.encode([question])

        if self._uses_mem0():
            # Mem0 vector store search
            hits = self.vector_store.search(query=question, limit=k)
            results = []
            # Build a path -> (content, metadata) lookup so hits resolve by
            # their stored source path, not by a positional doc_index that can
            # go stale when the document list changes between index rebuilds.
            path_lookup = {meta["path"]: (text, meta) for text, meta in self.documents}
            for i, hit in enumerate(hits):
                hit_meta = hit.get("metadata", {})
                resolved = path_lookup.get(hit_meta.get("path", ""))
                if resolved is not None:
                    content, metadata = resolved
                else:
                    content, metadata = hit.get("memory", hit.get("text", "")), {
                        "path": hit_meta.get("path", "unknown"),
                        "title": hit_meta.get("title", "Untitled"),
                        "type": hit_meta.get("type", "Unknown"),
                        "tags": [],
                        "sources": [],
                    }
                score = float(hit.get("score", 0.0))
                results.append(
                    {
                        "rank": i + 1,
                        # Keep the full body; the answer builder picks the best
                        # window around the query terms instead of a fixed prefix.
                        "content": content,
                        "metadata": metadata,
                        "distance": 1.0 - score,
                        "relevance_score": score,
                    }
                )
            return results

        # Search the FAISS index
        distances, indices = self.index.search(question_embedding.astype("float32"), k)

        # Prepare results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):
                content, metadata = self.documents[idx]
                results.append(
                    {
                        "rank": i + 1,
                        "content": (
                            content[:500] + "..." if len(content) > 500 else content
                        ),
                        "metadata": metadata,
                        "distance": float(distance),
                        "relevance_score": 1.0
                        / (1.0 + float(distance)),  # Convert distance to similarity
                    }
                )

        return results

    def query_with_answer(self, question: str, k: int = 3) -> Dict:
        """
        Query and generate a grounded answer (simplified version)

        Args:
            question: The question to ask
            k: Number of context documents to use

        Returns:
            Dictionary with answer and sources
        """
        # Gatekeeper: classify query before RAG retrieval
        from rag.query_classifier import QueryClassifier
        classifier = QueryClassifier()
        classification = classifier.classify(question)

        if classification.type == "greeting":
            return {
                "answer": classification.response,
                "sources": [],
                "confidence": 1.0,
                "query": question,
                "classified_as": "greeting",
            }

        if classification.type == "off_topic":
            return {
                "answer": classification.response,
                "sources": [],
                "confidence": 0.0,
                "query": question,
                "classified_as": "off_topic",
            }

        # Get relevant documents
        results = self.query(question, k)

        if not results or "error" in results[0]:
            return {
                "answer": "Unable to retrieve relevant information",
                "sources": [],
                "confidence": 0.0,
            }

        # Extract context from top results
        context_parts = []
        sources = []

        for result in results:
            context_parts.append(result["content"])
            sources.append(
                {
                    "title": result["metadata"]["title"],
                    "type": result["metadata"]["type"],
                    "path": result["metadata"]["path"],
                    "relevance": result["relevance_score"],
                }
            )

        context = "\n\n---\n\n".join(context_parts)

        # Simple answer generation (no LLM): pick the best window around the
        # query terms in the top-ranked document so key lines (e.g. commands)
        # are included even when they sit deep in the page.
        best_result = results[0]
        content = best_result["content"]
        WINDOW = 700

        # Score candidate windows by query-term overlap
        terms = [t.lower() for t in re.split(r"\W+", question) if len(t) > 2]
        lower = content.lower()
        best_start, best_score = 0, -1
        step = 200
        if len(content) > WINDOW:
            for start in range(0, len(content) - WINDOW + 1, step):
                window = lower[start : start + WINDOW]
                score = sum(window.count(t) for t in terms)
                if score > best_score:
                    best_score, best_start = score, start
            snippet = content[best_start : best_start + WINDOW].strip()
        else:
            snippet = content.strip()

        # Off-topic guard: don't fabricate from irrelevant sources
        max_relevance = max((r.get("relevance_score", r.get("relevance", 0)) for r in sources), default=1.0)
        if max_relevance < 0.32:
            return {
                "answer": "No relevant documentation found for that question.",
                "sources": sources,
                "confidence": float(best_result.get("relevance_score", 0.0)),
                "query": question,
            }

        from rag.llm_answer import _generate_answer
        return {
            "answer": _generate_answer(snippet, question),
            "sources": sources,
            "confidence": float(max_relevance),
            "query": question,
        }


def main():
    """Example usage of the RAG pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="Query the OKF Home-Lab bundle")
    parser.add_argument(
        "question",
        nargs="?",
        default="What is the Jellyfin health-check command?",
        help="Question to ask about the home-lab infrastructure",
    )
    parser.add_argument(
        "--bundle", default=".", help="Path to the OKF bundle root directory"
    )
    parser.add_argument("--k", type=int, default=3, help="Number of results to return")

    args = parser.parse_args()

    # Initialize pipeline
    print(f"Loading OKF bundle from {args.bundle}...")
    pipeline = OKFRAGPipeline(args.bundle)

    # Query
    print(f"\nQuery: {args.question}")
    print("-" * 50)

    result = pipeline.query_with_answer(args.question, args.k)

    print(f"Answer:\n{result['answer']}")
    print(f"\nConfidence: {result['confidence']:.2f}")
    print(f"\nSources:")
    for i, source in enumerate(result["sources"], 1):
        print(f"  {i}. {source['title']} ({source['type']})")
        print(f"     Path: {source['path']}")
        print(f"     Relevance: {source['relevance']:.2f}")


if __name__ == "__main__":
    main()
