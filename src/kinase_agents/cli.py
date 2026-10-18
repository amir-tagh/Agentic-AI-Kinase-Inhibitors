"""Run: kinase-acquire --compound dovitinib --db data/evidence.sqlite"""
import argparse
import logging
from pathlib import Path
from .clients import APIClient, PubChemAgent, ChEMBLAgent, LiteratureAgent, StructuralAgent
from .storage import EvidenceStore

log = logging.getLogger(__name__)

def acquire(compound, db, max_pages=20):
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    store, api = EvidenceStore(db), APIClient()
    counts = {}
    try:
        tasks = [
            ('pubchem', 'compound', lambda: [PubChemAgent(api).compound(compound)], lambda x: x.get('CID')),
            ('chembl', 'molecule', lambda: ChEMBLAgent(api).search_molecules(compound), lambda x: x.get('molecule_chembl_id')),
            ('europe_pmc', 'publication', lambda: LiteratureAgent(api).search(f'"{compound}" OR "TKI258"'), lambda x: f"{x.get('source','')}:{x.get('id','')}"),
            ('rcsb', 'structure_candidate', lambda: StructuralAgent(api).search_by_ligand_name(compound), lambda x: x.get('identifier')),
        ]
        molecules = []
        for source, kind, fetch, id_fn in tasks:
            try:
                records = fetch()
                counts[source] = 0
                for item in records:
                    identifier = id_fn(item)
                    if identifier is None: continue
                    store.add(source, kind, identifier, compound, item)
                    counts[source] += 1
                if source == 'chembl': molecules = records
                store.commit()
            except Exception as exc:
                log.warning('%s failed: %s', source, exc)
                counts[source] = 'FAILED'
        ids = sorted({m.get('molecule_chembl_id') for m in molecules if m.get('molecule_chembl_id') and
                      (compound.lower() in str(m.get('pref_name') or '').lower() or
                       any(compound.lower() in str(s.get('molecule_synonym','')).lower() for s in m.get('molecule_synonyms') or []))})
        counts['chembl_activities'] = 0
        for mid in ids:
            try:
                for item in ChEMBLAgent(api).activities(mid, max_pages=max_pages):
                    identifier = item.get('activity_id')
                    if identifier is None: continue
                    store.add('chembl', 'activity', identifier, compound, item)
                    counts['chembl_activities'] += 1
                store.commit()
            except Exception as exc:
                log.warning('Activities for %s failed: %s', mid, exc)
        if not ids: log.warning('No exact synonym/pref_name match in ChEMBL; activities not fetched.')
        return counts
    finally:
        store.close()

def main():
    parser = argparse.ArgumentParser(description='Acquire dovitinib evidence from public APIs')
    parser.add_argument('--compound', default='dovitinib')
    parser.add_argument('--db', default='data/evidence.sqlite')
    parser.add_argument('--max-pages', type=int, default=20)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    for source, count in acquire(args.compound, args.db, args.max_pages).items():
        print(f'{source}: {count}')
if __name__ == '__main__': main()
