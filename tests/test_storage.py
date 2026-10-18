from kinase_agents.storage import EvidenceStore

def test_upsert(tmp_path):
    store = EvidenceStore(tmp_path / 'test.sqlite')
    store.add('chembl', 'activity', 123, 'dovitinib', {'standard_value': '10'})
    store.add('chembl', 'activity', 123, 'dovitinib', {'standard_value': '20'})
    store.commit()
    rows = store.connection.execute('SELECT payload_json FROM evidence').fetchall()
    assert len(rows) == 1
    assert '20' in rows[0][0]
    store.close()
