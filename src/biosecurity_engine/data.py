"""
Hardcoded reference data for biosecurity screening.

Sources:
- CDC/APHIS Federal Select Agent Program
- Biological Weapons Convention (BWC) Annex
- Australia Group Common Control List
- Pfam/InterPro toxin domain families
"""

# ---------------------------------------------------------------------------
# CDC/APHIS Select Agents and Toxins (representative subset)
# https://www.selectagents.gov/sat/list.htm
# ---------------------------------------------------------------------------

SELECT_AGENTS: list[str] = [
    "Bacillus anthracis",                   # Anthrax
    "Yersinia pestis",                      # Plague
    "Francisella tularensis",               # Tularemia
    "Burkholderia mallei",                  # Glanders
    "Burkholderia pseudomallei",            # Melioidosis
    "Brucella abortus",                     # Brucellosis
    "Brucella melitensis",
    "Brucella suis",
    "Clostridium botulinum",               # Botulism (toxin-producing)
    "Coxiella burnetii",                    # Q fever
    "Rickettsia prowazekii",                # Epidemic typhus
    "Variola major",                        # Smallpox
    "Variola minor",
    "Ebola virus",                          # Ebola
    "Marburg virus",                        # Marburg
    "Nipah virus",
    "Hendra virus",
    "SARS-associated coronavirus",
    "Reconstructed 1918 Influenza virus",
    "Botulinum neurotoxin",                 # Toxin
    "Clostridium perfringens epsilon toxin",
    "Staphylococcal enterotoxin",
    "Ricin",
    "Abrin",
    "Saxitoxin",
    "Tetrodotoxin",
]

# ---------------------------------------------------------------------------
# Known toxin Pfam / InterPro domain families
# ---------------------------------------------------------------------------

TOXIN_PFAM_DOMAINS: list[dict[str, str]] = [
    {"id": "PF00087", "name": "Snake toxin", "risk": "high"},
    {"id": "PF00024", "name": "PAN domain", "risk": "medium"},
    {"id": "PF01549", "name": "ShET2 enterotoxin", "risk": "high"},
    {"id": "PF03318", "name": "Clostridial binary toxin B", "risk": "high"},
    {"id": "PF01375", "name": "Heat-stable enterotoxin", "risk": "high"},
    {"id": "PF03496", "name": "ADP-ribosyltransferase toxin", "risk": "high"},
    {"id": "PF03495", "name": "Pertussis toxin S1 subunit", "risk": "high"},
    {"id": "PF07951", "name": "Diphtheria toxin C domain", "risk": "high"},
    {"id": "PF02876", "name": "Staphylococcal/streptococcal toxin", "risk": "high"},
    {"id": "PF07953", "name": "Anthrax toxin LF", "risk": "high"},
    {"id": "PF01742", "name": "Clostridium neurotoxin zinc protease", "risk": "high"},
    {"id": "PF00161", "name": "Ribosome-inactivating protein", "risk": "high"},
    {"id": "PF00652", "name": "Ricin B lectin", "risk": "high"},
    {"id": "PF03989", "name": "Shiga toxin A subunit", "risk": "high"},
    {"id": "PF05431", "name": "Cholera toxin", "risk": "high"},
]

# Flat set for quick lookup
TOXIN_PFAM_IDS: set[str] = {d["id"] for d in TOXIN_PFAM_DOMAINS}

# ---------------------------------------------------------------------------
# Biological Weapons Convention (BWC) — Annex biological agents
# ---------------------------------------------------------------------------

BWC_AGENTS: list[str] = [
    "Bacillus anthracis",
    "Clostridium botulinum",
    "Yersinia pestis",
    "Variola major",
    "Francisella tularensis",
    "Brucella species",
    "Coxiella burnetii",
    "Burkholderia mallei",
    "Burkholderia pseudomallei",
    "Rickettsia prowazekii",
    "Chlamydophila psittaci",
]

# ---------------------------------------------------------------------------
# Australia Group Common Control List — biological agents
# https://www.dfat.gov.au/publications/minisite/theaustraliagroupnet/
# ---------------------------------------------------------------------------

AUSTRALIA_GROUP_AGENTS: list[str] = [
    "Bacillus anthracis",
    "Brucella abortus",
    "Brucella melitensis",
    "Brucella suis",
    "Burkholderia mallei",
    "Burkholderia pseudomallei",
    "Chlamydophila psittaci",
    "Clostridium botulinum",
    "Francisella tularensis",
    "Coxiella burnetii",
    "Rickettsia prowazekii",
    "Yersinia pestis",
]

# Combined set of all controlled organism names (lowercased for matching)
ALL_CONTROLLED_ORGANISMS: set[str] = {
    name.lower()
    for name in (SELECT_AGENTS + BWC_AGENTS + AUSTRALIA_GROUP_AGENTS)
}
