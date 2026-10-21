"""End-to-end backend tests for Donas ENARE 2026.

Covers:
- Public static pages (home/cronograma/inscricao/inscricoes)
- Admin auth (JWT) via /api/admin/auth/login
- Dashboard KPIs (auth required)
- Public tracking endpoints (/api/track/access)
- Public pix-config and pix/generate (BR Code EMV)
- Admin settings, inscriptions and cadastros listings
"""
import os
import re
import base64
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # fallback to frontend/.env at file scope
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip()
                    break
BASE_URL = (BASE_URL or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

ADMIN_USER = "donas"
ADMIN_PASS = "Seinao10@@"


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def http():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(http):
    r = http.post(f"{BASE_URL}/api/admin/auth/login",
                  json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 10
    return data["token"]


@pytest.fixture(scope="session")
def auth_http(http, token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {token}"})
    return s


# ---------- Public static pages ----------
@pytest.mark.parametrize("path", ["/home.html", "/cronograma.html",
                                  "/inscricao.html", "/inscricoes.html"])
def test_public_html_pages_load(http, path):
    r = http.get(f"{BASE_URL}{path}", timeout=30)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    assert "<html" in r.text.lower() or "<!doctype" in r.text.lower()


def test_home_contains_enare_2026(http):
    r = http.get(f"{BASE_URL}/home.html", timeout=30)
    assert r.status_code == 200
    body = r.text.lower()
    # at least one identifying token from the ENARE 2026 home
    assert ("enare" in body) and ("2026" in body), "home.html does not look like ENARE 2026 page"


# ---------- Admin auth ----------
def test_admin_login_invalid_credentials(http):
    r = http.post(f"{BASE_URL}/api/admin/auth/login",
                  json={"username": "donas", "password": "wrong"}, timeout=30)
    assert r.status_code == 401


def test_admin_login_success(token):
    # token fixture validates structure; ensure JWT format
    assert token.count(".") == 2


def test_admin_me(auth_http):
    r = auth_http.get(f"{BASE_URL}/api/admin/auth/me", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data.get("username") == ADMIN_USER


def test_admin_kpis_requires_auth(http):
    r = http.get(f"{BASE_URL}/api/admin/dashboard/kpis", timeout=30)
    assert r.status_code in (401, 403)


def test_admin_kpis_ok(auth_http):
    r = auth_http.get(f"{BASE_URL}/api/admin/dashboard/kpis", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    # KPI structure should expose totals/today maps
    assert isinstance(data, dict)
    # there should be at least one of the expected keys
    keys = set(data.keys())
    assert keys & {"total", "today", "kpis", "accesses", "registrations"}, f"unexpected KPI keys: {keys}"


# ---------- Tracking (public) ----------
def test_track_access_public(http, auth_http):
    # baseline count
    r0 = auth_http.get(f"{BASE_URL}/api/admin/dashboard/kpis", timeout=60).json()
    before = ((r0.get("total") or {}).get("accesses")
              if isinstance(r0.get("total"), dict) else None)

    r = http.post(f"{BASE_URL}/api/track/access",
                  json={"page": "/home.html", "user_agent": "pytest-agent", "extra": {}},
                  timeout=30)
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is True

    # verify counter increased (if total.accesses present)
    if before is not None:
        r1 = auth_http.get(f"{BASE_URL}/api/admin/dashboard/kpis", timeout=60).json()
        after = (r1.get("total") or {}).get("accesses")
        assert after is None or after >= before + 1


# ---------- Pix ----------
def test_pix_config_public(http):
    r = http.get(f"{BASE_URL}/api/pix-config", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    for k in ("key", "nome", "cidade"):
        assert k in data
    assert data["key"], "pix key not configured"
    # configured key from seeds
    assert "@enare-inscricoes.com.br" in data["key"]


def test_pix_generate(http):
    r = http.post(f"{BASE_URL}/api/pix/generate",
                  json={"valor": 150.0, "cpf": "12345678901",
                        "txid": "TESTPYT", "info": "Teste"},
                  timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "pix_code" in data and isinstance(data["pix_code"], str)
    code = data["pix_code"]
    # BR Code EMV starts with 00020126 (Payload Format Indicator + Merchant Account)
    assert code.startswith("000201"), f"unexpected BRCode prefix: {code[:10]}"
    assert 100 <= len(code) <= 512, f"unexpected BRCode length: {len(code)}"
    # CRC16 trailer 6304XXXX
    assert re.search(r"6304[0-9A-F]{4}$", code), "missing CRC16 trailer"

    assert "qr_png_base64" in data and data["qr_png_base64"]
    # validate base64 PNG
    raw = base64.b64decode(data["qr_png_base64"][:200] + "==")
    assert raw[:4] == b"\x89PNG"


# ---------- Admin Settings ----------
def test_admin_settings(auth_http):
    r = auth_http.get(f"{BASE_URL}/api/admin/settings", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("pix_key"), "pix_key missing from settings"
    assert "@enare-inscricoes.com.br" in data["pix_key"]


# ---------- Admin listings ----------
def test_admin_inscriptions_list(auth_http):
    r = auth_http.get(f"{BASE_URL}/api/admin/inscriptions", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    # accept both wrapped or list responses
    assert isinstance(data, (dict, list))
    if isinstance(data, dict):
        assert "items" in data or "total" in data or "inscriptions" in data


def test_admin_cadastros_list(auth_http):
    r = auth_http.get(f"{BASE_URL}/api/admin/cadastros", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, (dict, list))


# ---------- Admin panel static ----------
def test_admin_panel_static_loads(http):
    r = http.get(f"{BASE_URL}/donaspainel/", timeout=30)
    assert r.status_code == 200
    assert "<html" in r.text.lower()
