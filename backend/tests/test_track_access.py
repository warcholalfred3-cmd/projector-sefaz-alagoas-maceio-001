"""Tests for /api/track/access endpoint and KPI incrementing."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_USER = "donas"
ADMIN_PASS = "Seinao10@@"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/admin/auth/login", json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token") or data.get("jwt")
    assert tok, f"no token in response: {data}"
    return tok


def test_track_access_new_visitor():
    vid = f"test_visitor_{uuid.uuid4().hex}"
    r = requests.post(f"{API}/track/access", json={
        "page": "/inicio.html",
        "user_agent": "pytest-agent",
        "extra": {"visitor_id": vid},
    }, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is True
    assert "skipped" not in body, f"expected new access, got {body}"


def test_track_access_duplicate_visitor():
    vid = f"test_visitor_{uuid.uuid4().hex}"
    p = {"page": "/inicio.html", "user_agent": "pytest-agent", "extra": {"visitor_id": vid}}
    r1 = requests.post(f"{API}/track/access", json=p, timeout=15)
    assert r1.status_code == 200
    assert r1.json().get("ok") is True
    r2 = requests.post(f"{API}/track/access", json=p, timeout=15)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2.get("ok") is True
    assert body2.get("skipped") == "duplicate", body2


def test_track_access_admin_path_skipped():
    vid = f"test_visitor_{uuid.uuid4().hex}"
    r = requests.post(f"{API}/track/access", json={
        "page": "/donaspainel/#/dashboard",
        "user_agent": "pytest-agent",
        "extra": {"visitor_id": vid},
    }, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("skipped") == "admin", body


def test_kpi_increments_on_new_access(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r1 = requests.get(f"{API}/admin/dashboard/kpis", headers=headers, timeout=15)
    assert r1.status_code == 200, r1.text
    before = r1.json().get("acessos", 0)
    assert isinstance(before, int)

    vid = f"test_visitor_{uuid.uuid4().hex}"
    rp = requests.post(f"{API}/track/access", json={
        "page": "/inicio.html",
        "user_agent": "pytest-agent",
        "extra": {"visitor_id": vid},
    }, timeout=15)
    assert rp.status_code == 200
    assert rp.json().get("ok") is True and "skipped" not in rp.json()

    time.sleep(0.5)
    r2 = requests.get(f"{API}/admin/dashboard/kpis", headers=headers, timeout=15)
    assert r2.status_code == 200
    after = r2.json().get("acessos", 0)
    assert after >= before + 1, f"acessos did not increment: before={before} after={after}"


def test_inicio_html_has_csp_connect_src():
    r = requests.get(f"{BASE_URL}/inicio.html", timeout=15)
    assert r.status_code == 200
    html = r.text
    assert "content-security-policy" in html.lower()
    # find CSP meta
    import re
    # meta may have content and http-equiv in any order
    metas = re.findall(r'<meta[^>]*http-equiv="content-security-policy"[^>]*>', html, re.IGNORECASE)
    assert metas, "CSP meta not found"
    m = re.search(r'content="([^"]+)"', metas[0], re.IGNORECASE)
    assert m, f"CSP content not found in meta: {metas[0]}"
    csp = m.group(1)
    assert "connect-src" in csp and "'self'" in csp, f"connect-src 'self' not in CSP: {csp}"


def test_inicio_html_has_tracker_script():
    r = requests.get(f"{BASE_URL}/inicio.html", timeout=15)
    assert r.status_code == 200
    assert "__ceb_tracker" in r.text
    assert "/api/track/access" in r.text
