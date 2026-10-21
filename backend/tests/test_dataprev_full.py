"""End-to-end backend regression tests for Dataprev/SEDUC-AL inscription portal."""
import os
import base64
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_USER = "donas"
ADMIN_PASS = "Seinao10@@"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post(f"{API}/admin/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ---------- Root ----------
def test_root(client):
    r = client.get(f"{API}/", timeout=30)
    assert r.status_code == 200
    assert r.json().get("message") == "Painel Administrativo API"


# ---------- Auth ----------
def test_login_success(client):
    r = client.post(f"{API}/admin/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10


def test_login_bad_password(client):
    r = client.post(f"{API}/admin/auth/login", json={"username": ADMIN_USER, "password": "wrong"}, timeout=30)
    assert r.status_code == 401


def test_auth_me(client, auth_headers):
    r = client.get(f"{API}/admin/auth/me", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data.get("username") == ADMIN_USER or "user" in data or "id" in data


# ---------- Dashboard ----------
def test_dashboard_kpis(client, auth_headers):
    r = client.get(f"{API}/admin/dashboard/kpis", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    for k in ["acessos", "inscricoes", "pix_gerados", "valor_total", "today"]:
        assert k in data, f"missing key {k} in kpis: {data}"


def test_dashboard_funnel(client, auth_headers):
    r = client.get(f"{API}/admin/dashboard/funnel", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    # funnel likely returns list or dict with items
    items = data if isinstance(data, list) else data.get("items", data.get("funnel", []))
    assert isinstance(items, list)
    assert len(items) == 6, f"expected 6 funnel stages, got {len(items)}: {items}"


def test_dashboard_activity_24h(client, auth_headers):
    r = client.get(f"{API}/admin/dashboard/activity?range=24h", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    buckets = data if isinstance(data, list) else data.get("buckets", data.get("items", []))
    assert isinstance(buckets, list)
    assert len(buckets) == 24, f"expected 24 buckets, got {len(buckets)}"


def test_dashboard_activity_7d(client, auth_headers):
    r = client.get(f"{API}/admin/dashboard/activity?range=7d", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    buckets = data if isinstance(data, list) else data.get("buckets", data.get("items", []))
    assert isinstance(buckets, list)
    assert len(buckets) == 7, f"expected 7 buckets, got {len(buckets)}"


def test_dashboard_realtime(client, auth_headers):
    r = client.get(f"{API}/admin/dashboard/realtime", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "events" in data or isinstance(data, list)


def test_dashboard_locations(client, auth_headers):
    r = client.get(f"{API}/admin/dashboard/locations", headers=auth_headers, timeout=30)
    assert r.status_code == 200


# ---------- Lists ----------
def test_inscriptions_list(client, auth_headers):
    r = client.get(f"{API}/admin/inscriptions", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "items" in d and "total" in d


def test_cadastros_list(client, auth_headers):
    r = client.get(f"{API}/admin/cadastros", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "items" in d and "total" in d


def test_accesses_list(client, auth_headers):
    r = client.get(f"{API}/admin/accesses", headers=auth_headers, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "items" in d and "total" in d


# ---------- Tracking ----------
def test_track_access_increments(client, auth_headers):
    import uuid
    kpis_before = client.get(f"{API}/admin/dashboard/kpis", headers=auth_headers, timeout=30).json()
    before = int(kpis_before.get("acessos", 0))

    # Unique visitor_id to bypass 30-min dedupe
    r = client.post(f"{API}/track/access", json={
        "page": "/inicio.html",
        "user_agent": "pytest-agent",
        "extra": {"visitor_id": f"pytest-{uuid.uuid4()}", "city": "SP", "uf": "SP"}
    }, timeout=30)
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"
    body = r.json()
    assert body.get("ok") is True and not body.get("skipped"), f"track_access skipped: {body}"

    kpis_after = client.get(f"{API}/admin/dashboard/kpis", headers=auth_headers, timeout=30).json()
    after = int(kpis_after.get("acessos", 0))
    assert after >= before + 1, f"acessos didn't increment: before={before} after={after}"


def test_track_registration_cadastro(client):
    payload = {
        "page": "/inscricao.html",
        "extra": {
            "stage": "cadastro",
            "cpf": "12345678909",
            "nome": "TEST User",
            "email": "test@example.com",
            "telefone": "82999999999",
            "concurso": "SEDUC-AL-26-001",
        },
    }
    r = client.post(f"{API}/track/registration", json=payload, timeout=30)
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"


def test_track_registration_finalized(client, auth_headers):
    payload = {
        "page": "/confirmacao.html",
        "extra": {
            "stage": "inscricao_finalizada",
            "finalized": True,
            "cpf": "12345678909",
            "nome": "TEST User",
            "email": "test@example.com",
            "concurso": "SEDUC-AL-26-001",
            "cargo_codigo": "01103",
            "taxa": "110,00",
        },
    }
    r = client.post(f"{API}/track/registration", json=payload, timeout=30)
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"

    lst = client.get(f"{API}/admin/inscriptions?limit=50", headers=auth_headers, timeout=30).json()
    assert lst.get("total", 0) >= 1, f"inscription not persisted: {lst}"


# ---------- PIX (public + generate before/after settings) ----------
def test_pix_config_public_empty_initially(client):
    r = client.get(f"{API}/pix-config", timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ["key", "nome", "cidade"]:
        assert k in d


def test_zz_pix_generate_before_settings_fails(client):
    """This test should run before the settings PUT. Uses 'aaa' prefix in name? — we control via order."""
    # This runs alphabetically; keep independent using a marker approach
    pytest.skip("Covered by explicit ordered test file section below (test_a_ / test_z_)")


# Ordered flow: no PIX -> put settings -> generate PIX
def test_a1_pix_generate_no_key_fails(client):
    r = client.post(f"{API}/pix/generate", json={
        "valor": 110, "txid": "IDCT01", "cpf": "12345678909", "cargo_codigo": "01103"
    }, timeout=30)
    # expect 400 with 'Chave PIX não configurada'
    assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"
    assert "PIX" in r.text or "pix" in r.text.lower()


def test_a2_put_settings_configures_pix(client, auth_headers):
    payload = {
        "pix_key": "danielmmm950@gmail.com",
        "pix_nome": "CONCURSO DATAPREV",
        "pix_cidade": "BRASILIA DF",
    }
    r = client.put(f"{API}/admin/settings", headers=auth_headers, json=payload, timeout=30)
    assert r.status_code in (200, 201), f"{r.status_code} {r.text}"


def test_a3_pix_config_public_reflects(client):
    r = client.get(f"{API}/pix-config", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("key") == "danielmmm950@gmail.com"
    assert "DATAPREV" in (d.get("nome") or "").upper()
    assert "BRASILIA" in (d.get("cidade") or "").upper()


def test_a4_pix_generate_success(client):
    r = client.post(f"{API}/pix/generate", json={
        "valor": 110, "txid": "IDCT01", "cpf": "12345678909", "cargo_codigo": "01103"
    }, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    d = r.json()
    assert "pix_code" in d and d["pix_code"].startswith("000201")  # EMV BR Code starts with payload format indicator
    assert "qr_png_base64" in d and len(d["qr_png_base64"]) > 100
    # ensure valid base64
    base64.b64decode(d["qr_png_base64"][:100] + "==")


def test_a5_pix_qr_png(client):
    r = client.get(f"{API}/pix/qr.png?valor=110", timeout=30)
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("image/png")
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


# ---------- CEP ----------
def test_cep_valid(client):
    r = client.get(f"{API}/cep/01310100", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("logradouro") or d.get("street")
    assert (d.get("cidade") or d.get("localidade") or "").upper().startswith("SÃ") or "SAO" in (d.get("cidade") or d.get("localidade") or "").upper()
    assert (d.get("uf") or d.get("estado") or "") == "SP"


def test_cep_invalid(client):
    r = client.get(f"{API}/cep/00000000", timeout=30)
    assert r.status_code >= 400 or r.json().get("erro") or r.json().get("error")
