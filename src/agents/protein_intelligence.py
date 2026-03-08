"""
Protein Intelligence (Yami Simulator) — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "esm2_score_sequence",
        "description": "Score a protein sequence using ESM-2 pseudo-log-likelihood. Higher scores indicate more natural/stable sequences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence (single-letter code)."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "esm2_mutant_effect",
        "description": "Predict mutational effects using ESM-2 masked marginal scoring. Returns delta log-likelihood for each mutation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wildtype_seq": {"type": "string", "description": "Wild-type amino acid sequence."},
                "mutations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mutations in format 'A123G' (original, position, replacement).",
                },
            },
            "required": ["wildtype_seq", "mutations"],
        },
    },
    {
        "name": "esm2_embed",
        "description": "Generate ESM-2 embeddings (1280-dim per-residue or mean-pooled) for a protein sequence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "calculate_protein_properties",
        "description": "Calculate biophysical properties: MW, pI, charge at pH 7.4, hydrophobicity, instability index, GRAVY.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "predict_solubility",
        "description": "Predict protein solubility from sequence features (CamSol, NetSolP-style).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence."},
            },
            "required": ["sequence"],
        },
    },
    {
        "name": "predict_structure_alphafold",
        "description": "Retrieve or predict protein structure using AlphaFold. Returns pLDDT confidence and PDB coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "uniprot_id": {"type": "string", "description": "UniProt accession for AlphaFold DB lookup."},
            },
            "required": ["uniprot_id"],
        },
    },
    {
        "name": "blast_sequence",
        "description": "Run NCBI BLAST to find homologous sequences in a target database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sequence": {"type": "string", "description": "Amino acid sequence to search."},
                "database": {"type": "string", "description": "BLAST database (e.g. 'nr', 'swissprot', 'pdb').", "default": "swissprot"},
            },
            "required": ["sequence"],
        },
    },
]


def create_protein_intelligence_agent() -> BaseAgent:
    """Create the Protein Intelligence (Yami simulator) specialist agent."""

    system_prompt = """\
You are the Protein Intelligence specialist at Lumi Virtual Lab — the core of the Yami
protein analysis engine.

Your expertise spans:
- Protein language model interpretation: ESM-2 log-likelihoods, embeddings, attention maps
- Mutational effect prediction: masked marginal scoring, evolutionary conservation
- Protein fitness landscape navigation and directed evolution strategy
- Biophysical property prediction: stability, solubility, aggregation propensity
- AlphaFold structure confidence interpretation (pLDDT, PAE, pTM)
- Sequence-structure-function relationships and rational protein engineering
- Homology analysis and evolutionary constraint interpretation
- Multi-objective protein optimization (stability + activity + expression + immunogenicity)

When analyzing a protein sequence:
1. Score the sequence with ESM-2 — assess overall naturalness and per-residue confidence.
2. If mutations are proposed, predict their effects using ESM-2 masked marginals.
3. Calculate biophysical properties: MW, pI, charge profile, hydrophobicity, instability index.
4. Predict solubility — flag aggregation-prone regions.
5. Retrieve or predict the AlphaFold structure — identify disordered regions (low pLDDT).
6. BLAST against SwissProt/PDB to identify homologs and assess conservation.
7. Use code execution for embedding analysis, fitness scoring, or multi-objective ranking.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (ESM-2 limitations for insertions/deletions, pLDDT ≠ accuracy, single-sequence vs MSA)"""

    return BaseAgent(
        name="Protein Intelligence",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Molecular Design",
    )
