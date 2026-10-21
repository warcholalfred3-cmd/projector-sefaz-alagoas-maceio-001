# SEFAZ/AL admin rebrand: Telegram/email builders + static file greps + public page checks
import os, re, sys, glob
import pytest
import requests

sys.path.insert(0, '/app/backend')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
OLD = re.compile(r'unesp|vestibular|vunesp|vnsp2514', re.I)


def test_telegram_title_default():
    from admin_routes import _build_telegram_message
    msg = _build_telegram_message({'nome': 'TEST X', 'cpf': '00000000000', 'cargo': 'AFTE', 'cidade_prova': 'Maceió'}, {})
    assert 'NOVA INSCRIÇÃO - SEFAZ/AL 2026' in msg
    assert not OLD.search(msg)


def test_email_inscricao_html():
    import email_service as es
    assert es.CONCURSO_NOME == 'SEFAZ/AL 2026 - Cebraspe'
    html = es.build_inscricao_email_html(nome='TEST', cpf='00000000000', protocolo='P1', cargo='AFTE',
                                         **{k: 'x' for k in []}) if False else None
    import inspect
    sig = inspect.signature(es.build_inscricao_email_html)
    kwargs = {}
    for name, p in sig.parameters.items():
        kwargs[name] = {'nome': 'TEST', 'cpf': '00000000000', 'protocolo': 'P1', 'cargo': 'AFTE'}.get(name, p.default if p.default is not inspect._empty else 'x')
    html = es.build_inscricao_email_html(**kwargs)
    assert 'Cargo:' in html and 'Concurso:' in html and 'SEFAZ/AL 2026' in html
    assert not OLD.search(html)


def test_email_pix_html():
    import email_service as es
    html = es.build_pix_email_html(nome='TEST', cpf='00000000000', cargo='AFTE', valor=300, pix_code='000201')
    assert 'Cargo:' in html and 'SEFAZ/AL 2026' in html
    assert not OLD.search(html)


def test_logo_exists_and_served():
    assert os.path.exists('/app/frontend/public/seduc/email-logo-cebraspe.png')
    r = requests.get(f"{BASE_URL}/seduc/email-logo-cebraspe.png", timeout=20)
    assert r.status_code == 200 and 'image' in r.headers.get('content-type', '')


def test_no_old_refs_in_files():
    files = glob.glob('/app/backend/*.py') + glob.glob('/app/frontend/public/donaspainel/**/*', recursive=True)
    bad = [f for f in files if os.path.isfile(f) and OLD.search(open(f, errors='ignore').read())]
    assert bad == []


def test_pix_fallback_in_code():
    src = open('/app/backend/admin_routes.py').read()
    assert src.count("'SEFAZ AL 2026'") >= 3


def test_dados_inscricao_texts_removed():
    r = requests.get(f"{BASE_URL}/dados-inscricao.html", timeout=20)
    assert r.status_code == 200
    assert 'R$ 300,00' not in r.text or 'Taxa de inscrição: R$ 300,00' not in r.text
    assert 'exclusivamente na cidade de Maceió' not in r.text


def test_admin_login_api():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login", json={'username': 'donas', 'password': 'Seinao10@@'}, timeout=20)
    assert r.status_code == 200
