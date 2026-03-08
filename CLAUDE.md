# Lumi — Confidence-Aware AI Scientist with Human-in-the-Loop Routing

## Vision

Lumi is an agentic virtual lab for drug discovery that orchestrates specialist AI agents across biology, chemistry, and clinical domains. Unlike single-model copilots, Lumi runs multi-agent debate to produce **confidence-scored findings** and routes low-confidence results to human domain experts before they enter reports.

## How It Works

1. User submits a research question (e.g., "Validate PCSK9 as a cardiovascular target")
2. Division leads delegate to specialist agents (target biology, safety, clinical, modality)
3. Agents query literature, databases, and computational tools via MCP servers
4. Multi-agent debate produces consensus findings with confidence scores
5. Low-confidence findings route to human experts for review
6. Final visual report combines figures, confidence data, and provenance trails

## Use Cases

- **Target validation** — evidence dossiers with pathway diagrams and confidence scores
- **Assay troubleshooting** — root-cause analysis with annotated cell diagrams
- **Biomarker curation** — panel candidates with expression heatmaps
- **Regulatory submissions** — toxicology literature reviews with MoA illustrations

## Competitive Differentiation

- Confidence scoring via structured multi-agent debate (not just LLM logprobs)
- Human-in-the-loop routing for findings below confidence threshold
- Visual context reports with BioRender-style figures alongside text
- Full provenance chain from source data to final recommendation

## Stack

- **Language**: Python 3.11+
- **LLM**: Anthropic Claude (via `anthropic` SDK)
- **Agent framework**: Custom agents + FastMCP v3 for tool servers
- **Key deps**: BioPython, scanpy, RDKit, ESM, PyTorch, Pydantic
- **Async**: asyncio + uvloop

## Project Structure

```
src/
  agents/       # Specialist agents (target_biologist, antibody_engineer, etc.)
  divisions/    # Division leads that coordinate agent groups
  utils/        # Confidence scoring, LLM helpers, cost tracking, provenance
  factory.py    # System factory — wires agents, divisions, MCP bridge
  mcp_bridge.py # Connects agents to external tool servers
demos/          # Example usage scripts
tests/          # Test suite
```

## Dev Conventions

- Concise conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- Ruff for linting (line-length 120, target py311)
- pytest + pytest-asyncio for tests
- Keep agents stateless; state flows through message context
