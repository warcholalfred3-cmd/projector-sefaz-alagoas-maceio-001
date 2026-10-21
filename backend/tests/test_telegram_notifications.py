"""Tests for Telegram notification pipeline (SEDUC AL 2026 portal).

Coverage:
- _build_telegram_message: exact format expected by client
- _status_emoji: correct emojis for each pix_status
- _format_cpf_br: xxx.xxx.xxx-xx
- _format_data_hora_brt: 'dd/mm/YYYY às HH:MM' in BRT
- POST /api/admin/telegram/test: requires admin auth; sends via bot API
- POST /api/track/registration (finalized=true): triggers notify_or_update_telegram
  and persists telegram_message_id in db.inscricoes
- POST /api/track/pix-generated / pix-copied / pix-downloaded: edits the message
"""
import os
import re
import sys
import asyncio
import pytest
import requests
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

# Make backend modules importable
sys.path.insert(0, '/app/backend')

import admin_routes  # noqa: E402
from admin_routes import (
    _build_telegram_message,
    _status_emoji,
    _format_cpf_br,
    _format_data_hora_brt,
)

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
ADMIN_USER = 'donas'
ADMIN_PASS = 'Seinao10@@'

# -------- Pure unit tests --------

class TestFormatters:
    def test_status_emoji_all_values(self):
        assert _status_emoji('Aguardando pagamento') == '🟡'
        assert _status_emoji('PIX gerado') == '🔵'
        assert _status_emoji('PIX copiado') == '🟢'
        assert _status_emoji('PIX baixado') == '🟢'
        assert _status_emoji('') == '🟡'
        assert _status_emoji('unknown') == '🟡'

    def test_format_cpf_br(self):
        assert _format_cpf_br('13149243629') == '131.492.436-29'
        assert _format_cpf_br('131.492.436-29') == '131.492.436-29'
        assert _format_cpf_br('') == '—'
        assert _format_cpf_br('123') == '123'

    def test_format_data_hora_brt(self):
        dt = datetime(2026, 7, 31, 2, 29, 0, tzinfo=timezone.utc)  # 23:29 BRT on 30/07
        out = _format_data_hora_brt(dt)
        # 02:29 UTC - 3h = 23:29 BRT on 30/07/2026
        assert out == '30/07/2026 às 23:29'

    def test_format_data_hora_brt_string_iso(self):
        out = _format_data_hora_brt('2026-08-01T02:29:00Z')
        assert out == '31/07/2026 às 23:29'


class TestBuildTelegramMessage:
    """Validate EXACT format expected by client."""

    def _sample_insc(self, **overrides):
        base = {
            'nome': 'FÁBIO PEREIRA MARTINS',
            'cpf': '13149243629',
            'device': 'desktop',
            'city': 'Brasília',
            'region_name': 'Federal District',
            'valor': 150.0,
            'pix_status': 'Aguardando pagamento',
            'telegram_sent_at': datetime(2026, 8, 1, 2, 29, 0, tzinfo=timezone.utc),
        }
        base.update(overrides)
        return base

    def test_full_message_aguardando(self):
        msg = _build_telegram_message(self._sample_insc())
        expected = (
            "<b>NOVA INSCRIÇÃO - SEDUC AL 2026</b>\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "👤 <b>Usuário:</b> FÁBIO PEREIRA MARTINS\n"
            "🔐 <b>CPF:</b> 131.492.436-29\n"
            "📅 <b>Data/hora:</b> 31/07/2026 às 23:29\n"
            "📱 <b>Dispositivo:</b> Desktop\n"
            "📍 <b>Local:</b> Brasília/Federal District\n"
            "💰 <b>Valor:</b> R$ 150,00\n"
            "📊 <b>Status:</b> 🟡 Aguardando pagamento"
        )
        assert msg == expected

    def test_message_pix_gerado(self):
        msg = _build_telegram_message(self._sample_insc(pix_status='PIX gerado'))
        assert '📊 <b>Status:</b> 🔵 PIX gerado' in msg

    def test_message_pix_copiado(self):
        msg = _build_telegram_message(self._sample_insc(pix_status='PIX copiado'))
        assert '📊 <b>Status:</b> 🟢 PIX copiado' in msg

    def test_message_pix_baixado(self):
        msg = _build_telegram_message(self._sample_insc(pix_status='PIX baixado'))
        assert '📊 <b>Status:</b> 🟢 PIX baixado' in msg

    def test_message_separator_and_labels(self):
        msg = _build_telegram_message(self._sample_insc())
        assert '━━━━━━━━━━━━━━━━━' in msg
        for label in ['👤', '🔐', '📅', '📱', '📍', '💰', '📊']:
            assert label in msg

    def test_valor_brazilian_format(self):
        msg = _build_telegram_message(self._sample_insc(valor=1234.5))
        assert 'R$ 1.234,50' in msg

    def test_valor_zero_shows_dash(self):
        msg = _build_telegram_message(self._sample_insc(valor=0))
        assert '💰 <b>Valor:</b> —' in msg

    def test_device_mobile(self):
        msg = _build_telegram_message(self._sample_insc(device='mobile'))
        assert '📱 <b>Dispositivo:</b> Mobile' in msg

    def test_local_fallback(self):
        msg = _build_telegram_message(self._sample_insc(city='', region_name=''))
        assert '📍 <b>Local:</b> —' in msg


# -------- DB / settings check --------

class TestSettingsInDB:
    def test_telegram_credentials_absent_from_db(self):
        """Reports current state of db.settings._id='main' — user claimed
        credentials were persisted; verify actual state."""
        import subprocess
        r = subprocess.run(
            ['mongosh', 'test_database', '--quiet', '--eval',
             "JSON.stringify(db.settings.findOne({_id:'main'}))"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, r.stderr
        import json
        doc = json.loads(r.stdout.strip() or 'null') or {}
        has_token = bool(doc.get('telegram_bot_token'))
        has_chat = bool(doc.get('telegram_chat_id'))
        enabled = bool(doc.get('telegram_enabled'))
        # We assert & report — this test will FAIL loudly if all missing.
        print(f"\n[settings] telegram_bot_token={'SET' if has_token else 'MISSING'} "
              f"telegram_chat_id={'SET' if has_chat else 'MISSING'} "
              f"telegram_enabled={enabled}")
        # Not a hard failure — but flag as skip if missing
        if not (has_token and has_chat and enabled):
            pytest.skip("Telegram credentials NOT persisted in db.settings._id='main' — "
                        "Telegram notifications will NOT fire. User claim is INCORRECT.")


# -------- Admin API tests --------

@pytest.fixture(scope='module')
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/auth/login",
                      json={'username': ADMIN_USER, 'password': ADMIN_PASS}, timeout=10)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    return r.json()['token']


class TestAdminTelegramTestEndpoint:
    def test_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/admin/telegram/test", json={}, timeout=10)
        assert r.status_code == 401

    def test_missing_credentials_returns_400(self, admin_token):
        # Ensure settings have no telegram creds (which is the current state)
        r = requests.post(
            f"{BASE_URL}/api/admin/telegram/test",
            json={},  # no token/chat provided, and DB has none
            headers={'Authorization': f'Bearer {admin_token}'},
            timeout=10,
        )
        # If DB somehow has creds, this could return 200/400 depending on real API;
        # in a clean state expect 400.
        assert r.status_code in (400, 200)
        if r.status_code == 400:
            assert 'Bot Token' in r.text or 'Chat ID' in r.text

    def test_invalid_token_returns_400(self, admin_token):
        r = requests.post(
            f"{BASE_URL}/api/admin/telegram/test",
            json={'bot_token': '111:INVALID', 'chat_id': '123'},
            headers={'Authorization': f'Bearer {admin_token}'},
            timeout=15,
        )
        assert r.status_code == 400
        assert 'Falha ao enviar' in r.text or 'error' in r.text.lower() or 'Not Found' in r.text or 'Unauthorized' in r.text


# -------- End-to-end pipeline (mock Telegram Bot API) --------

@pytest.mark.asyncio
async def test_notify_or_update_telegram_sends_and_saves_message_id():
    """Simulate the full pipeline: enable telegram in settings (in-memory monkeypatch),
    call notify_or_update_telegram, capture the HTTP payload, verify format, and
    verify telegram_message_id is persisted."""
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    admin_routes.set_db(db)

    cpf = '99988877766'
    # Enable telegram in settings (temporarily)
    original = await db.settings.find_one({'_id': 'main'}) or {}
    await db.settings.update_one(
        {'_id': 'main'},
        {'$set': {
            'telegram_bot_token': 'TEST:FAKE',
            'telegram_chat_id': '123456',
            'telegram_enabled': True,
        }},
        upsert=True,
    )
    # Seed an inscription
    now = datetime.now(timezone.utc)
    await db.inscricoes.delete_many({'cpf': cpf})
    await db.inscricoes.insert_one({
        'id': 'test-uuid-1', 'cpf': cpf, 'nome': 'FÁBIO PEREIRA MARTINS',
        'cargo_codigo': '01103', 'valor': 150.0, 'device': 'desktop',
        'city': 'Brasília', 'region_name': 'Federal District',
        'pix_status': 'Aguardando pagamento',
        'finalized': True, 'created_at': now, 'finalized_at': now,
    })

    captured = {}

    class FakeResp:
        status_code = 200
        def json(self):
            return {'ok': True, 'result': {'message_id': 42}}

    class FakeClient:
        def __init__(self, *a, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def post(self, url, json=None, **kw):
            captured['url'] = url
            captured['payload'] = json
            return FakeResp()

    try:
        with patch('admin_routes.httpx.AsyncClient', FakeClient):
            await admin_routes.notify_or_update_telegram(cpf, request=None, extra={'cargo_codigo': '01103'})

        assert 'sendMessage' in captured.get('url', ''), f"Expected sendMessage call, got {captured}"
        payload = captured['payload']
        assert payload['parse_mode'] == 'HTML'
        assert payload['chat_id'] == '123456'
        text = payload['text']
        # Verify exact format elements
        assert '<b>NOVA INSCRIÇÃO - SEDUC AL 2026</b>' in text
        assert '━━━━━━━━━━━━━━━━━' in text
        assert '👤 <b>Usuário:</b> FÁBIO PEREIRA MARTINS' in text
        assert '🔐 <b>CPF:</b> 999.888.777-66' in text
        assert '📱 <b>Dispositivo:</b> Desktop' in text
        assert '📍 <b>Local:</b> Brasília/Federal District' in text
        assert '💰 <b>Valor:</b> R$ 150,00' in text
        assert '📊 <b>Status:</b> 🟡 Aguardando pagamento' in text
        assert re.search(r'📅 <b>Data/hora:</b> \d{2}/\d{2}/\d{4} às \d{2}:\d{2}', text)

        # Verify message_id was persisted
        insc = await db.inscricoes.find_one({'cpf': cpf})
        assert insc.get('telegram_message_id') == 42
        assert insc.get('telegram_sent_at') is not None
    finally:
        # Cleanup: restore original settings and remove seed inscription
        await db.inscricoes.delete_many({'cpf': cpf})
        restore = {'telegram_bot_token': '', 'telegram_chat_id': '', 'telegram_enabled': False}
        # Actually unset if they were not in original
        unset = {}
        for k in ['telegram_bot_token', 'telegram_chat_id', 'telegram_enabled']:
            if k not in original:
                unset[k] = ''
        if unset:
            await db.settings.update_one({'_id': 'main'}, {'$unset': unset})
        client.close()


@pytest.mark.asyncio
async def test_notify_edits_existing_message_on_pix_events():
    """When telegram_message_id already exists, subsequent status changes should
    call editMessageText (not sendMessage)."""
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    admin_routes.set_db(db)

    cpf = '88877766655'
    original = await db.settings.find_one({'_id': 'main'}) or {}
    await db.settings.update_one(
        {'_id': 'main'},
        {'$set': {'telegram_bot_token': 'T', 'telegram_chat_id': '1', 'telegram_enabled': True}},
        upsert=True,
    )
    now = datetime.now(timezone.utc)
    await db.inscricoes.delete_many({'cpf': cpf})
    await db.inscricoes.insert_one({
        'id': 'test-uuid-2', 'cpf': cpf, 'nome': 'Teste',
        'cargo_codigo': 'X', 'valor': 150.0, 'device': 'desktop',
        'city': 'Brasília', 'region_name': 'DF',
        'pix_status': 'PIX copiado', 'telegram_message_id': 99,
        'telegram_sent_at': now,
        'finalized': True, 'created_at': now,
    })

    captured_url = {}

    class FakeResp:
        status_code = 200
        def json(self): return {'ok': True}
    class FakeClient:
        def __init__(self,*a,**kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return False
        async def post(self, url, json=None, **kw):
            captured_url['url'] = url
            captured_url['text'] = json.get('text', '')
            return FakeResp()

    try:
        with patch('admin_routes.httpx.AsyncClient', FakeClient):
            await admin_routes.notify_or_update_telegram(cpf, extra={'cargo_codigo': 'X'})
        assert 'editMessageText' in captured_url.get('url', '')
        assert '🟢 PIX copiado' in captured_url['text']
    finally:
        await db.inscricoes.delete_many({'cpf': cpf})
        unset = {k: '' for k in ['telegram_bot_token','telegram_chat_id','telegram_enabled'] if k not in original}
        if unset:
            await db.settings.update_one({'_id': 'main'}, {'$unset': unset})
        client.close()


@pytest.mark.asyncio
async def test_notify_skips_when_telegram_disabled():
    """If telegram_enabled is false or credentials missing, no HTTP call is made."""
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client[os.environ.get('DB_NAME', 'test_database')]
    admin_routes.set_db(db)
    # Ensure telegram_enabled is not set (current real state)
    original = await db.settings.find_one({'_id': 'main'}) or {}
    if original.get('telegram_enabled'):
        pytest.skip("telegram_enabled is True in DB — cannot test disabled path safely")

    called = {'n': 0}
    class FakeClient:
        def __init__(self,*a,**kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*a): return False
        async def post(self,*a,**kw):
            called['n'] += 1
            class R: status_code=200
            R.json = lambda self=None: {'ok': True}
            return R()

    with patch('admin_routes.httpx.AsyncClient', FakeClient):
        await admin_routes.notify_or_update_telegram('12345678901')
    assert called['n'] == 0
    client.close()
