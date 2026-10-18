# Kinase Agentic AI — Dovitinib

Phase 1: provenance-aware acquisition from PubChem, ChEMBL, Europe PMC, and RCSB PDB.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
```

## Run
```bash
kinase-acquire --compound dovitinib --db data/evidence.sqlite
pytest -q
```

## Inspect
```bash
python - <<'PY'
import sqlite3
con = sqlite3.connect('data/evidence.sqlite')
for row in con.execute('SELECT source,record_type,COUNT(*) FROM evidence GROUP BY 1,2'):
    print(row)
PY
```

## Scope and limitations
- This is deterministic API-based acquisition, not yet autonomous LLM reasoning.
- ChEMBL activity retrieval uses compound-name/synonym matches; review molecule identity and salt/tautomer forms before treating results as a verified dovitinib set.
- Raw activity records preserve units, assay identifiers, target identifiers, relationships, and publication IDs when provided. No averaging or conversion is performed.
- RCSB full-text hits are **candidates**, not confirmed ligand-bound dovitinib structures. Validate each ligand identity and binding site before use.
- Europe PMC returns the first page of publication metadata; full-text and supplements are not yet parsed.
- Public APIs require internet access; transient errors are logged and partial successful sources are retained.
- Missing or failed source retrieval is not evidence of biological absence.

## Next milestones
1. Resolve molecular identities with InChIKey, salts, and ChEMBL cross-references.
2. Normalize bioactivity measurements into queryable tables without losing raw evidence.
3. Retrieve verified PDB ligand/target associations and extract binding sites.
4. Add BindingDB, full-text/supplement extraction, and citation-level provenance.
5. Add LLM-driven tool planning and evidence reconciliation with human review.
