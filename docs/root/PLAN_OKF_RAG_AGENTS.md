# Plan: Enhancing aldo-f.github.io for AI Agent Usage (OKF/RAG) and Auto-Updates

## Overview
This plan outlines enhancements to make the aldo-f.github.io documentation site:
1. **Easily usable by AI agents** - Implementing OKF (Open Knowledge Format) principles and RAG (Retrieval-Augmented Generation) capabilities
2. **Automatically updated** - Ensuring documentation from all active apps is always current

## Phase 1: AI Agent Enhancements (OKF/RAG)

### 1.1 Structured Data & Metadata
- Add JSON-LD structured data to all documentation pages
- Implement schema.org markup for:
  - Tutorials (HowTo)
  - Reference documentation (TechnicalArticle)
  - FAQ sections
  - API documentation
- Create agent-readable metadata files alongside markdown

### 1.2 Enhanced Search Capabilities (RAG Foundation)
- Upgrade from basic search to semantic search using:
  - Vector embeddings for documentation chunks
  - Integration with Mem0 or similar vector store
  - Custom search API endpoint for agents
- Implement chunking strategy:
  - Split documentation into semantic chunks (sections, code examples, explanations)
  - Generate embeddings for each chunk
  - Store with metadata (source, topic, difficulty level, etc.)

### 1.3 Agent-Friendly APIs & Endpoints
- Create `/api/docs/search` endpoint for semantic queries
- Create `/api/docs/sections` endpoint for structured navigation
- Create `/api/docs/summary` endpoint for TL;DR versions
- Add OpenAPI/Swagger documentation for all endpoints
- Implement rate limiting and caching for agent requests

### 1.4 Knowledge Format Standards
- Adopt OKF-inspired principles:
  - Machine-readable metadata with each document
  - Clear licensing and attribution information
  - Versioned documentation snapshots
  - Change logs and diff feeds
- Create `/api/changes` endpoint for documentation updates
- Implement webhook system for notifying agents of updates

### 1.5 LLM Optimization
- Add `llms.txt` file (LLM-standard for documentation)
- Create agent-specific documentation views:
  - Simplified navigation for agents
  - Code-example extraction endpoints
  - Parameter/API reference in machine-readable formats
- Implement prompt-optimized content variants

## Phase 2: Automatic Documentation Updates

### 2.1 Monitoring System
- Create documentation watcher service:
  - Polls source repositories for changes to documentation folders
  - Uses GitHub webhooks for real-time updates (where possible)
  - Falls back to periodic polling (every 15-30 minutes)
- Track:
  - Documentation file changes (additions, modifications, deletions)
  - Structural changes in source repos
  - New repositories that should be included

### 2.2 Automatic Integration Workflow
When documentation changes are detected:
1. Fetch latest documentation from source repository
2. Validate documentation format and links
3. Update local copy in appropriate language folder
4. Trigger MkDocs rebuild if significant changes
5. Update search index/vector store
6. Notify via webhooks/API of updates
7. Generate changelog entry

### 2.2 Repository Discovery & Onboarding
- Implement intelligent repository discovery:
  - Scan `~/dev/06-apps-*` for new applications
  - Automatically detect documentation folders (`docs/`, `website/docs/`, etc.)
  - Suggest new repositories for inclusion in multirepo config
- Create approval workflow for auto-adding new doc sources
- Maintain blacklist/whitelist for repositories to include/exclude

### 2.3 Documentation Generation & Enhancement
- Create documentation generators for apps lacking docs:
  - Extract docstrings/comments from source code
  - Generate API references from OpenAPI/Swagger specs
  - Create usage guides from example files/test cases
  - Extract CLI documentation from argument parsers
- Implement documentation quality scoring:
  - Check for completeness (installation, usage, examples)
  - Validate code examples
  - Assess readability and structure
  - Suggest improvements

### 2.4 Build & Deployment Automation
- Enhance GitHub Actions workflow:
  - Trigger rebuilds on documentation changes in source repos
  - Parallel builds for multiple language versions
  - Automated testing of documentation links and code examples
  - Deployment only when builds succeed and pass validation
- Create local development scripts for testing changes
- Implement rollback mechanism for problematic updates

## Phase 3: Implementation Details

### 3.1 Technical Stack
- **Vector Store**: Use existing Mem0 configuration or add local vector DB (FAISS/Chroma)
- **Embedding Model**: Use same LLM provider as Mem0 for consistency
- **API Framework**: FastAPI or Python Flask for lightweight endpoints
- **Scheduler**: APScheduler or cron-based for polling tasks
- **Webhook Receiver**: Lightweight HTTP endpoint for GitHub notifications

### 3.2 File Structure Additions
```
06-apps-aldo-f-github-io/
├── agent_api/                 # New: Agent-facing API endpoints
│   ├── __init__.py
│   ├── search.py              # Semantic search endpoint
│   ├── sections.py            # Structured navigation
│   ├── changes.py             # Update feed/webhooks
│   └── models.py              # Data models
├── documentation_watcher/     # New: Auto-update system
│   ├── __init__.py
│   ├── repo_scanner.py        # Discovers new doc sources
│   ├── change_detector.py     # Watches for documentation changes
│   ├── fetcher.py             # Fetches updates from source repos
│   ├── validator.py           # Validates fetched documentation
│   └── integrator.py          # Integrates changes into site
├── generators/                # New: Documentation generators
│   ├── __init__.py
│   ├── code_extractor.py      # Extracts docs from source
│   ├── api_reference.py       # Generates API docs from specs
│   └── cli_helper.py          # Generates CLI documentation
├── scripts/
│   ├── update_docs.py         # Manual trigger for updates
│   ├── generate_vectors.py    # (Re)generate search vectors
│   └── validate_docs.py       # Validate documentation quality
├── agent_config.json          # Configuration for agent features
└── docs/agent_guide.md        # Guide for agents using this documentation
```

### 3.3 Configuration
Add to `mkdocs.base.yml` or create `mkdocs.agent.yml`:
```yaml
# Agent-specific configuration
agent_features:
  enabled: true
  semantic_search: true
  vector_store_path: "./agent_data/vectors"
  embedding_model: "same-as-mem0"
  update_poll_interval: 15  # minutes
  webhook_endpoint: "/agent/webhook"
  api_rate_limit: "100/hour"
  
# Automatic documentation sources
auto_doc_sources:
  - path: "~/dev/06-apps-*"
    doc_patterns: 
      - "docs/**/*.md"
      - "website/docs/**/*.md"
      - "*.md"  # root level README, etc.
    exclude:
      - "*/node_modules/**"
      - "*/.git/**"
      - "*legacy*"
```

## Phase 4: Validation & Testing

### 4.1 Agent Usability Testing
- Create test scenarios for common agent tasks:
  - "Find installation instructions for thuis"
  - "Get API reference for radio-community streaming"
  - "Show me CLI usage examples for clock"
  - "What are the system requirements for passive-income?"
- Measure success rate and time to answer
- Compare against baseline (current site)

### 4.2 Automatic Update Validation
- Test with controlled changes in source repositories
- Verify:
  - Changes detected within expected timeframe
  - Documentation correctly integrated
  - Links remain functional
  - Search index updated appropriately
  - No breaking changes to site structure

### 4.3 Performance Benchmarks
- API response times (<2s for search, <1s for section lookup)
- Vector search quality (relevance of results)
- Update latency (time from source commit to site availability)
- Resource usage (memory, CPU during updates)

## Phase 5: Deployment & Rollout

### 5.1 Pilot Implementation
- Start with one or two representative repositories (thuis, clock)
- Implement agent features and auto-updates for these
- Gather feedback and refine
- Expand to all repositories

### 5.2 Monitoring & Maintenance
- Create dashboards for:
  - Documentation freshness (time since last update)
  - Agent API usage statistics
  - Search effectiveness metrics
  - Update success/failure rates
- Set up alerts for:
  - Failed documentation updates
  - Degraded search performance
  - API error rates

### 5.3 Documentation for Agents
- Create `docs/agent_guide.md` explaining:
  - How to use the agent API endpoints
  - Best practices for querying the documentation
  - Rate limits and authentication (if implemented)
  - Examples of common agent workflows
  - How to contribute to improving agent accessibility

## Success Metrics

### For Agent Usability:
- 80%+ success rate on common agent documentation tasks
- Average time to find information <15 seconds
- Positive feedback from agent users on usability
- Reduction in "I couldn't find..." type queries

### For Automatic Updates:
- 95%+ of documentation changes reflected within 30 minutes
- 0% broken links from auto-updated documentation
- 100% of active apps with documentation included in site
- Successful automatic integration of 90%+ of updates without manual intervention

## Implementation Roadmap

### Week 1-2: Foundation
- Set up vector store and embedding pipeline
- Create basic semantic search prototype
- Implement documentation change detection for one repo

### Week 3-4: Agent API
- Build core agent API endpoints
- Create llms.txt and agent guide
- Add structured data to existing documentation

### Week 5-6: Automation
- Complete automatic update system
- Implement repository discovery
- Add documentation generators
- Enhance GitHub Actions workflow

### Week 7-8: Integration & Testing
- Expand to all repositories
- Run validation tests
- Fix issues and optimize performance
- Deploy to production

### Week 9+: Refinement
- Add advanced features (personalization, recommendations)
- Improve based on user/agent feedback
- Document lessons learned and create maintenance procedures