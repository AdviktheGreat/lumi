# Lumi

Multi-agent virtual lab for drug discovery. Specialist AI agents debate across biology, chemistry, and clinical domains to produce confidence-scored findings with human-in-the-loop routing.

## How it works

1. Submit a research question to a **sublab** (target validation, lead optimization, etc.)
2. The sublab's agent team queries literature, databases, and computational tools
3. Multi-agent debate produces consensus findings with confidence scores
4. Low-confidence findings route to human experts for review
5. Final report combines figures, confidence data, and provenance trails

## Sublabs

| Sublab | Purpose |
|--------|---------|
| Target Validation | Evidence dossiers with pathway diagrams |
| Assay Troubleshooting | Root-cause analysis of unexpected results |
| Biomarker Curation | Panel candidates with expression heatmaps |
| Regulatory Submissions | Tox literature reviews with MoA illustrations |
| Lead Optimization | Multi-parameter drug candidate optimization |
| Clinical Translation | Go/no-go packages for IND-enabling studies |

## Setup

```bash
pip install -e .                  # core
pip install -e ".[bio,ml,chem]"   # all optional deps
pip install -e ".[dev]"           # dev tools
```

## Project structure

```
src/
  agents/       # Specialist agents
  sublabs/      # Sublab definitions (agents, tools, debate protocol)
  divisions/    # Division leads coordinating agent groups
  utils/        # Confidence scoring, LLM helpers, provenance
  factory.py    # System factory
  mcp_bridge.py # MCP tool server bridge
```

## Stack

Python 3.11+ · Claude (anthropic SDK) · FastMCP v3 · Streamlit

## Dev

```bash
ruff check src/
pytest
```
