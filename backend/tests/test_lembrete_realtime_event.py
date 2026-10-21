# Lembrete de pagamento -> evento kind='lembrete' no feed realtime do dashboard
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
ADMIN = {"username": "donas", "password": "Seinao10@@"}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/auth/login", json=ADMIN, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert isinstance(d.get("token"), str) and d["token"]
    assert d["user"]["username"] == "donas"
    s.headers.update({"Authorization": f"Bearer {d['token']}"})
    return s


# Auth
def test_login_invalid():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login", json={"username": "donas", "password": "x"}, timeout=20)
    assert r.status_code in (400, 401)


def test_lembrete_requires_auth():
    r = requests.post(f"{BASE_URL}/api/admin/inscricoes/lembrete-pagamento", timeout=20)
    assert r.status_code in (401, 403)


# Resumo
def test_resumo(client):
    r = client.get(f"{BASE_URL}/api/admin/inscricoes/lembrete-pagamento/resumo", timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] >= 1


# Core bug: job -> event in realtime
def test_lembrete_job_creates_realtime_event(client):
    before = client.get(f"{BASE_URL}/api/admin/dashboard/realtime?limit=200", timeout=20).json()
    before_n = sum(1 for e in before if e.get("kind") == "lembrete")

    r = client.post(f"{BASE_URL}/api/admin/inscricoes/lembrete-pagamento", timeout=20)
    assert r.status_code == 200, r.text
    job = r.json()
    assert job.get("id") and job.get("status") == "enviando"
    assert "_id" not in job

    status = None
    for _ in range(30):
        time.sleep(1)
        s = client.get(f"{BASE_URL}/api/admin/inscricoes/lembrete-pagamento/status/{job['id']}", timeout=20)
        assert s.status_code == 200
        status = s.json()
        if status["status"] != "enviando":
            break
    print("JOB:", status)
    assert status["status"] == "concluido", status
    assert status["enviados"] >= 1, status

    r = client.get(f"{BASE_URL}/api/admin/dashboard/realtime?limit=10", timeout=20)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) <= 10
    lem = [e for e in items if e.get("kind") == "lembrete"]
    assert lem, f"no lembrete event in top 10: {[e.get('kind') for e in items]}"
    assert lem[0]["description"].startswith("Lembrete de pagamento enviado -")
    assert isinstance(lem[0]["created_at"], str)
    assert "_id" not in lem[0]

    after = client.get(f"{BASE_URL}/api/admin/dashboard/realtime?limit=200", timeout=20).json()
    after_n = sum(1 for e in after if e.get("kind") == "lembrete")
    assert after_n >= before_n + status["enviados"] or after_n == 200


def test_status_404(client):
    r = client.get(f"{BASE_URL}/api/admin/inscricoes/lembrete-pagamento/status/nonexistent", timeout=20)
    assert r.status_code == 404


# Other kinds still returned, sorted desc
def test_realtime_other_kinds_and_sort(client):
    r = client.get(f"{BASE_URL}/api/admin/dashboard/realtime?limit=500", timeout=20)
    assert r.status_code == 200
    items = r.json()
    kinds = {e.get("kind") for e in items}
    print("KINDS:", kinds)
    assert kinds - {"lembrete"}, "only lembrete kinds present"
    ts = [e["created_at"] for e in items if e.get("created_at")]
    assert ts == sorted(ts, reverse=True)
    for e in items:
        assert "kind" in e and "description" in e
