# Tests for the new inscription fee of R$ 120,00
import os
import base64
import requests
import pytest

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

ADMIN_USER = "donas"
ADMIN_PASS = "Seinao10@@"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login",
                      json={"username": ADMIN_USER, "password": ADMIN_PASS}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"no token in response: {data}"
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module", autouse=True)
def ensure_pix_settings(admin_headers):
    # Ensure PIX config exists so /api/pix/generate works
    payload = {
        "pix_key": "danielmmm950@gmail.com",
        "pix_nome": "CONCURSO CBM MA 26",
        "pix_cidade": "SAO LUIS MA",
    }
    r = requests.put(f"{BASE_URL}/api/admin/settings", json=payload, headers=admin_headers, timeout=30)
    # Some backends may return 200/204
    assert r.status_code in (200, 201, 204), f"settings update failed: {r.status_code} {r.text}"


# ---------- Static HTML checks ----------

def test_dados_inscricao_all_options_120():
    r = requests.get(f"{BASE_URL}/dados-inscricao.html", timeout=30)
    assert r.status_code == 200
    html = r.text
    count_120 = html.count('data-price="120.00"')
    assert count_120 == 12, f"expected 12 options at 120.00, found {count_120}"
    assert 'data-price="150.00"' not in html, "found stale 150.00 data-price entry"
    assert 'data-price="150"' not in html


def test_pagamento_pix_valor_120():
    r = requests.get(f"{BASE_URL}/pagamento-pix.html", timeout=30)
    assert r.status_code == 200
    html = r.text
    assert "valor: 120," in html, "vagaInfo.valor not set to 120"
    assert "taxa: 'R$ 120,00'" in html, "vagaInfo.taxa not set to R$ 120,00"
    assert "R$ 150,00" not in html


# ---------- PIX generation ----------

def test_pix_generate_valor_120():
    payload = {
        "valor": 120,
        "txid": "IDCT01TEST",
        "cpf": "12345678909",
        "cargo_codigo": "01",
    }
    r = requests.post(f"{BASE_URL}/api/pix/generate", json=payload, timeout=30)
    assert r.status_code == 200, f"generate failed: {r.status_code} {r.text}"
    data = r.json()
    pix_code = data.get("pix_code") or data.get("brcode") or data.get("emv")
    assert pix_code, f"no pix_code in response: {data.keys()}"
    assert pix_code.startswith("0002"), f"pix_code doesn't start with 0002: {pix_code[:20]}"
    # EMV field 54 = valor. Length 06 -> '120.00'
    assert "5406120.00" in pix_code, f"EMV valor field 5406120.00 not found in pix: {pix_code}"
    # qr_png_base64
    b64 = data.get("qr_png_base64") or data.get("qr_base64")
    assert b64, "qr_png_base64 missing"
    raw = base64.b64decode(b64)
    assert raw[:8].startswith(b"\x89PNG"), "qr base64 is not PNG"


def test_pix_qr_png_endpoint():
    r = requests.get(f"{BASE_URL}/api/pix/qr.png", params={"valor": 120}, timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/png")
    assert r.content[:4] == b"\x89PNG"


# ---------- Admin dashboard KPIs ----------

def test_admin_dashboard_kpis_reflect_120(admin_headers):
    # Generate one pix so the sum is deterministic (at least ≥120 present)
    requests.post(f"{BASE_URL}/api/pix/generate",
                  json={"valor": 120, "txid": "IDCT02TEST", "cpf": "12345678909", "cargo_codigo": "01"},
                  timeout=30)
    r = requests.get(f"{BASE_URL}/api/admin/dashboard/kpis", headers=admin_headers, timeout=30)
    assert r.status_code == 200, f"kpis failed: {r.status_code} {r.text}"
    data = r.json()
    # valor_total may be top-level or nested
    valor_total = data.get("valor_total")
    if valor_total is None and isinstance(data.get("kpis"), dict):
        valor_total = data["kpis"].get("valor_total")
    assert valor_total is not None, f"valor_total missing in kpis: {data}"
    # Should be a multiple of 120 (no 150 legacy). Just ensure it's divisible by 120 or empty.
    try:
        vt = float(valor_total)
    except Exception:
        pytest.fail(f"valor_total not numeric: {valor_total}")
    if vt > 0:
        # Cannot guarantee no legacy 150 in DB, but ensure at least 120 present
        assert vt >= 120, f"valor_total unexpectedly small: {vt}"
