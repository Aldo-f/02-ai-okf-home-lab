# Plan: Fix OKF RAG Index & Query Quality

## Goal
Make the OKF RAG API return meaningful, grounded answers for user queries by ensuring the document index is properly built and the query engine finds relevant content.

## Current Context / Assumptions
- RAG API is running at `http://192.168.0.5:8000` (service `app-okf-rag`)
- Index lives in `~/dev/okf-home-lab/rag/` and loads markdown files from `01-`, `05-`, `06-` prefixed directories
- The `rag_query.py` pipeline builds an embedding index and performs vector search + fallback to document search
- Queries currently return `"Unable to retrieve relevant information"` with confidence 0.0
- The service is active (pid 3522536) but the index may not be populated correctly

## Architecture / Proposed Approach
1. **Verify index build** – Ensure `rag/OKFRAGPipeline` loads all required markdown files and builds the vector index.
2. **Fix document discovery** – Confirm that `01-`, `05-`, `06-` directories contain valid markdown with frontmatter and that the loader skips non-concept folders correctly.
3. **Improve query fallback** – When vector search yields no results, fall back to a simple keyword search in the document corpus to surface relevant snippets.
4. **Validate with test queries** – Run the known queries (`Jellyfin health-check`, `OKF home lab goal`) and verify they return proper answers with citations.

## Step-by-Step Tasks

### Task 1: Verify and rebuild the index
- **Action**: Run the RAG pipeline initialization and force index rebuild.
- **Expected output**: Index stamp updated, pipeline ready, no errors during `_build_index()`.
- **Commands**:
  ```bash
  cd ~/dev/okf-home-lab/rag
  python3 -c "
from rag_query import OKFRAGPipeline
pipeline = OKFRAGPipeline('.')
print('Index built successfully')
"
  ```

### Task 2: Check document loading in `01-`, `05-`, `06-` directories
- **Action**: List files in each concept directory and verify they have proper frontmatter.
- **Expected output**: At least some markdown files with `---` frontmatter in `01-`, `05-`, `06-` folders.
- **Commands**:
  ```bash
  for dir in 01- 05- 06-; do
    echo "=== $dir ==="; ls -la "$dir"/*.md 2>/dev/null | head -20
  done
  ```

### Task 3: Fix query fallback logic in `rag_query.py`
- **Problem**: Vector search returns empty → falls through to no results.
- **Fix**: Add a secondary keyword-based search when vector search yields no hits.
- **File**: `~/dev/okf-home-lab/rag/rag_query.py`
- **Change**: After vector search, if `results` is empty, perform a simple keyword search over all documents and return top matches.

### Task 4: Test queries and validate
- **Queries to test**:
  1. `"What is the Jellyfin health-check command?"`
  2. `"How do I check whether Jellyfin is healthy?"`
  3. `"What is the goal of the OKF home lab?"`
- **Expected output**: Non-empty `answer` field, reasonable `confidence` (>0), and `sources` array with at least one entry.
- **Commands**:
  ```bash
  curl -s "http://192.168.0.5:8000/search?question=\"What is the Jellyfin health-check command?\"&k=3" | python3 -m json.tool
  ```

## Tests / Validation
- After each task, run the corresponding query and verify the JSON response contains `answer` (non-empty string), `confidence` (float > 0), and `sources` (non-empty list).
- If any query still returns empty, add diagnostic logging to `rag_query.py` to see what documents were considered.

## Risks / Tradeoffs
- **Risk**: Modifying `rag_query.py` may affect other components that rely on the same pipeline. Minimal change: only add a fallback search, preserving existing vector search behavior.
- **Tradeoff**: Adding keyword fallback increases latency slightly but ensures useful answers even when the vector index is stale or sparse.
- **Open question**: Are there any other concept directories beyond `01-`, `05-`, `06-` that should be included? If yes, expand the loader in `rag_query.py`.

## Execution
Once the plan is saved, I will execute the tasks sequentially, committing after each successful step.
