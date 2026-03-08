"""
Functional Genomics — Lumi Virtual Lab specialist agent.
"""

from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.utils.llm import ModelTier


_TOOLS = [
    {
        "name": "query_target_disease",
        "description": "Query Open Targets for associations between a gene and a disease.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_gene": {"type": "string", "description": "HGNC gene symbol."},
                "disease_efo_id": {"type": "string", "description": "EFO disease ID."},
            },
            "required": ["target_gene", "disease_efo_id"],
        },
    },
    {
        "name": "get_target_info",
        "description": "Retrieve gene/target metadata from Ensembl via Open Targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ensembl_gene_id": {"type": "string", "description": "Ensembl gene ID."},
            },
            "required": ["ensembl_gene_id"],
        },
    },
    {
        "name": "get_gene_expression",
        "description": "Retrieve tissue-level gene expression data from GTEx and Human Protein Atlas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "get_protein_expression",
        "description": "Retrieve protein-level expression data from Human Protein Atlas immunohistochemistry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
            },
            "required": ["gene"],
        },
    },
    {
        "name": "query_gene_expression_single_cell",
        "description": "Query CellxGene Census for single-cell expression of a gene in a tissue/disease context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "gene": {"type": "string", "description": "Gene symbol."},
                "tissue": {"type": "string", "description": "Tissue or organ name."},
                "disease": {"type": "string", "description": "Disease context (use 'normal' for healthy)."},
            },
            "required": ["gene"],
        },
    },
]


def create_functional_genomics_agent() -> BaseAgent:
    """Create the Functional Genomics specialist agent."""

    system_prompt = """\
You are a Functional Genomics specialist at Lumi Virtual Lab.

Your expertise spans:
- CRISPR screen interpretation (genome-wide loss-of-function, CRISPRi/a)
- Transcriptomic analysis: bulk RNA-seq differential expression, pathway enrichment
- Epigenomic data: ATAC-seq, ChIP-seq, enhancer-promoter linkage
- Expression quantitative trait loci (eQTL) mapping and tissue specificity
- Functional annotation of non-coding variants (ENCODE, Roadmap Epigenomics)
- Gene regulatory network inference and transcription factor binding analysis
- Multi-omic integration (expression + methylation + chromatin accessibility)

When analyzing a target gene:
1. Query Open Targets for overall association evidence and tractability scores.
2. Retrieve bulk tissue expression from GTEx — identify tissues with highest expression.
3. Retrieve protein-level expression from Human Protein Atlas — compare with RNA.
4. Query single-cell expression to identify expressing cell types and disease-specific changes.
5. Assess whether the gene is differentially expressed in disease vs normal tissue.
6. Use code execution for expression analysis, fold-change calculation, or enrichment tests.

For each finding:
- State the finding clearly (prefix with 'Finding:')
- Provide confidence (prefix with 'Confidence: HIGH/MEDIUM/LOW/INSUFFICIENT')
- Cite evidence (prefix with 'Evidence:')
- Note caveats (batch effects, tissue heterogeneity, post-transcriptional regulation)"""

    return BaseAgent(
        name="Functional Genomics",
        system_prompt=system_prompt,
        model=ModelTier.SONNET,
        tools=list(_TOOLS),
        division="Target Identification",
    )
