"""Script uji in-process semua endpoint API Whenyhh.ai."""
import sys, tempfile, pathlib, os
sys.path.insert(0, '.')

_tmpdir = tempfile.mkdtemp()
os.environ["WHENYHH_DB_PATH"] = str(pathlib.Path(_tmpdir) / "smoke.db")

from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:

    def chk(label, r):
        ok = "OK" if r.status_code < 400 else "FAIL"
        print(f"{ok} [{r.status_code}] {label}: {r.text[:120]}")
        return r

    chk("GET /healthz", client.get('/healthz'))
    chk("GET /readyz", client.get('/readyz'))

    # /api/scenarios mengembalikan list langsung
    r = chk("GET /api/scenarios", client.get('/api/scenarios'))
    sc_list = r.json()   # list of scenario dicts
    print(f"  -> {len(sc_list)} skenario dimuat")

    sid = sc_list[0]['scenario_id']
    r = chk(f"GET /api/scenarios/{sid}", client.get(f'/api/scenarios/{sid}'))

    r = chk("GET /graph", client.get(f'/api/scenarios/{sid}/graph'))
    g = r.json()
    print(f"  -> {len(g['nodes'])} nodes, {len(g['branches'])} branches")

    bid = g['branches'][0]['branch_id']
    root = next(n for n in g['nodes'] if not n.get('parent_id'))

    r = chk("POST /api/turns", client.post('/api/turns', json={
        'scenario_id': sid,
        'branch_id': bid,
        'parent_node_id': root['node_id'],
        'user_action': 'Selidiki situasi lebih lanjut',
        'llm_config': {'provider': 'mock', 'temperature': 0.7, 'max_tokens': 256}
    }))
    t = r.json()
    print(f"  -> node={t['node_id'][:8]}... is_fallback={t['is_fallback']} prompt_tokens={t['prompt_tokens']}")

    chk("POST /fork", client.post('/api/branches/fork', json={
        'scenario_id': sid,
        'from_node_id': t['node_id'],
        'new_branch_name': 'cabang-test'
    }))

    chk("POST /checkout", client.post('/api/branches/checkout', json={
        'branch_id': bid,
        'target_node_id': t['node_id']
    }))

    chk("POST /api/llm/test", client.post('/api/llm/test', json={
        'provider': 'mock', 'temperature': 0.7, 'max_tokens': 1
    }))

    chk("GET /api/llm/models", client.get('/api/llm/models'))

    r = chk("GET /export json", client.get(f'/api/scenarios/{sid}/export?format=json'))
    print(f"  -> {len(r.text)} bytes")

    r = chk("GET /export md", client.get(f'/api/scenarios/{sid}/export?format=markdown'))
    print(f"  -> {len(r.text)} bytes")

    r = chk("GET /", client.get('/'))
    print(f"  -> {len(r.text)} bytes HTML")

    chk("GET static CSS", client.get('/static/css/app.css'))

print("--- SELESAI ---")
