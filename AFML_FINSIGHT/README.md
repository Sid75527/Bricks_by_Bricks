# FinSight Implementation

This folder contains a ground-up implementation of the **FinSight** architecture described in the paper *“FinSight: Towards Real-World Financial Deep Research.”* The system mirrors the Code Agent with Variable Memory (CAVM) design and covers the complete pipeline: multi-source data collection, deep search, code-first analysis, iterative visualization refinement, and two-stage report writing with citations.

## Folder Structure

```
AFML_FINSIGHT/
├── analysis/              # Chain-of-analysis structures and REPL executor
├── agents/                # Data collection and deep search agents
├── config/                # Environment configuration loader (.env based)
├── evaluation/            # Placeholder automated metric functions
├── interfaces/            # Base classes for agents/tools
├── pipeline/              # High-level FinSightPipeline orchestrator
├── runtime/               # CAVM runtime: variable space, orchestrator, code executor
├── tests/                 # Smoke tests covering runtime and data collection
├── tools/                 # Gemini wrapper, market/SEC collectors, search helper
├── visualization/         # Iterative visualization refinement loop
├── writing/               # Two-stage writing (chain compiler + report writer)
└── README.md              # This document
```

## Environment Setup

1. Create/activate a virtual environment (e.g., `.venv_hybrid`).
2. Install dependencies (reuse the hybrid project requirements or prepare a dedicated list).
3. Copy `.env.example` (you can reuse the one in `AFML_PROJECT_HYBRID` if desired) and set the required keys:
   ```env
   GOOGLE_API_KEY="..."
   FRED_API_KEY="..."
   SEC_USER_AGENT="your_email@example.com"
   ```
4. Ensure the FinSight folder is on the Python path when running scripts (working from the repo root works).

## Quick Smoke Tests

```
pytest AFML_FINSIGHT/tests/test_runtime_smoke.py
pytest AFML_FINSIGHT/tests/test_data_collection_agent.py
```

## Running the Full Pipeline

```python
from AFML_FINSIGHT.pipeline.orchestrator import FinSightPipeline

pipeline = FinSightPipeline()
artifacts = pipeline.run(
    company_name="NVIDIA",
    ticker="NVDA",
    analysis_goal="Assess NVIDIA's financial strength and growth outlook.",
    fred_series_ids={"gdp": "GDP"},
    visualization_spec={"type": "line", "y": ["Close"], "title": "NVDA Price Performance"},
    visualization_goal="Create an executive-ready chart summarizing NVDA stock trend.",
)

print(artifacts["memo_uid"])          # UID of the final memo stored in variable space
snapshot = pipeline.orchestrator.variable_space.snapshot()
```

The returned dictionary contains UIDs for:
- Stock history, macro series, and SEC filing artifacts.
- Deep search log and snippets.
- Chain-of-analysis perspectives.
- Iterative chart refinement history.
- Final Markdown memo with inline `[Ref: UID]` citations.

Use `pipeline.orchestrator.variable_space.snapshot()` to inspect all stored artifacts. Each UID is referenced in the memo’s footnotes to ensure traceable evidence.

## Evaluation Hooks

The `evaluation/metrics.py` module provides placeholder scoring functions inspired by the paper (textual faithfulness, structural logic, chart expressiveness). Extend these to match your course deliverables or benchmark dataset.

## Next Extensions

- Add a Streamlit/CLI interface for easier interaction.
- Expand evaluation metrics with real benchmarks.
- Introduce caching or persistence layers for the variable space.
- Customize analysis goals, visualization specs, and report outlines per assignment requirements.

This implementation completes the FinSight architecture end-to-end using only the Gemini API alongside free-data sources and open-source Python libraries.
