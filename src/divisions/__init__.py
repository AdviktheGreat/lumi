"""
Division Lead factory functions — Lumi Virtual Lab

Each factory creates a configured :class:`DivisionLead` instance for one
of the eight organisational divisions in the swarm hierarchy.
"""

from src.divisions.base_lead import DivisionLead
from src.divisions.biosecurity import create_biosecurity_lead
from src.divisions.clinical import create_clinical_lead
from src.divisions.compbio import create_compbio_lead
from src.divisions.experimental import create_experimental_lead
from src.divisions.modality import create_modality_lead
from src.divisions.molecular_design import create_molecular_design_lead
from src.divisions.target_id import create_target_id_lead
from src.divisions.target_safety import create_target_safety_lead

__all__ = [
    # Base class
    "DivisionLead",
    # Factory functions (alphabetical)
    "create_biosecurity_lead",
    "create_clinical_lead",
    "create_compbio_lead",
    "create_experimental_lead",
    "create_modality_lead",
    "create_molecular_design_lead",
    "create_target_id_lead",
    "create_target_safety_lead",
]
