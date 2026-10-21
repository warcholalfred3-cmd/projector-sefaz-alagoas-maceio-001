# Home Cebraspe (SEFAZ/AL 2026) - static page + visitor tracking -> admin dashboard
import os
import re
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
ADMIN = {"username": "donas", "password": "Seinao10@@"}


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login", json=ADMIN, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"admin login failed {r.status_code}")
    d = r.json()
    t = d.get("token") or d.get("access_token")
    assert t
    return t


def H(t):
    return {"Authorization": f"Bearer {t}"}


# Static page served & content
class TestHomeStatic:
    def test_index_redirects(self):
        r = requests.get(f"{BASE_URL}/", timeout=20)
        assert r.status_code == 200
        # either a redirect stub or inicio.html served directly
        assert "/inicio.html" in r.text or "Secretaria de Estado da Fazenda de Alagoas" in r.text

    def test_inicio_content(self):
        r = requests.get(f"{BASE_URL}/inicio.html", timeout=30)
        assert r.status_code == 200
        t = r.text
        for s in ["Secretaria de Estado da Fazenda de Alagoas", "25.270,68", "home-fazer-inscricao-btn",
                  "mobile-menu-drawer", "/api/track/access"]:
            assert s in t, s

    def test_no_external_hrefs(self):
        t = requests.get(f"{BASE_URL}/inicio.html", timeout=30).text
        hrefs = re.findall(r'<a\b[^>]*?\bhref=("[^"]*"|\'[^\']*\'|[^\s>]+)', t)
        ext = [h for h in hrefs if re.match(r'["\']?(https?:)?//', h)]
        assert ext == [], ext

    def test_termos_and_minhas_exist(self):
        for p in ["/termos.html", "/minhas-inscricoes.html"]:
            assert requests.get(f"{BASE_URL}{p}", timeout=20).status_code == 200


# Tracking -> admin KPIs
class TestTracking:
    def test_track_access_increments_kpis(self, token):
        before = requests.get(f"{BASE_URL}/api/admin/dashboard/kpis", headers=H(token), timeout=20).json()["acessos"]
        vid = "TEST_" + uuid.uuid4().hex[:10]
        r = requests.post(f"{BASE_URL}/api/track/access", json={
            "page": "/inicio.html", "user_agent": "Mozilla/5.0 (Linux; Android 13) Mobile TESTAGENT",
            "extra": {"visitor_id": vid}}, timeout=20)
        assert r.status_code == 200
        assert r.json() == {"ok": True}
        after = requests.get(f"{BASE_URL}/api/admin/dashboard/kpis", headers=H(token), timeout=20).json()["acessos"]
        assert after == before + 1
        acc = requests.get(f"{BASE_URL}/api/admin/accesses", params={"q": "TESTAGENT", "limit": 5},
                           headers=H(token), timeout=20).json()
        assert any(i.get("visitor_id") == vid and i["device"] == "mobile" for i in acc["items"])

    def test_track_access_dedup(self):
        vid = "TEST_" + uuid.uuid4().hex[:10]
        body = {"page": "/inicio.html", "user_agent": "TESTAGENT", "extra": {"visitor_id": vid}}
        assert requests.post(f"{BASE_URL}/api/track/access", json=body, timeout=20).json() == {"ok": True}
        r2 = requests.post(f"{BASE_URL}/api/track/access", json=body, timeout=20).json()
        assert r2.get("skipped") == "duplicate"

    def test_kpis_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard/kpis", timeout=20)
        assert r.status_code in (401, 403)
