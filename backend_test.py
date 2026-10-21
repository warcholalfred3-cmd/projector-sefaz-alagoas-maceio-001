#!/usr/bin/env python3
"""
Backend API Testing for SEAP-MA Admin Panel
Tests the 150 seeded inscriptions and admin endpoints
"""
import requests
import sys
from collections import Counter

# Base URL from frontend/.env
BASE_URL = "https://concurso-seduc-ce.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Admin credentials
ADMIN_USERNAME = "donas"
ADMIN_PASSWORD = "Seinao10@@"

# Expected cargo titles and valores
EXPECTED_CARGOS = {
    "Inspetor de Polícia Penal": 150.0,
    "Monitor de Ressocialização": 85.0,
    "Especialidade: Assistência Social": 180.0,
    "Especialidade: Direito": 180.0,
    "Especialidade: Enfermagem": 180.0,
    "Especialidade: Pedagogia": 180.0,
    "Especialidade: Psicologia": 180.0,
    "Especialidade: Técnico Administrativo": 120.0,
    "Especialidade: Técnico de Enfermagem": 120.0,
}

def test_admin_login():
    """Test 1: POST /api/admin/auth/login"""
    print("\n" + "="*70)
    print("TEST 1: Admin Login")
    print("="*70)
    
    url = f"{API_BASE}/admin/auth/login"
    payload = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        print(f"Response: {data}")
        
        # Verify token exists
        if 'token' not in data:
            print("❌ FAILED: No 'token' in response")
            return None
        
        # Verify user.username
        if 'user' not in data or data['user'].get('username') != ADMIN_USERNAME:
            print(f"❌ FAILED: user.username != '{ADMIN_USERNAME}'")
            return None
        
        print(f"✅ PASSED: Login successful, token received")
        print(f"   Token (first 20 chars): {data['token'][:20]}...")
        print(f"   Username: {data['user']['username']}")
        return data['token']
        
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        return None


def test_inscriptions(token):
    """Test 2: GET /api/admin/inscriptions - verify 150+ inscriptions"""
    print("\n" + "="*70)
    print("TEST 2: Admin Inscriptions List")
    print("="*70)
    
    url = f"{API_BASE}/admin/inscriptions"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        total = data.get('total', 0)
        items = data.get('items', [])
        
        print(f"Total inscriptions: {total}")
        print(f"Items returned: {len(items)}")
        
        # Check 1: Total >= 150
        if total < 150:
            print(f"❌ FAILED: Expected total >= 150, got {total}")
            return False
        print(f"✅ Check 1 PASSED: Total inscriptions >= 150 ({total})")
        
        # Check 2: Device mix (desktop and mobile)
        device_counter = Counter()
        cargo_counter = Counter()
        valor_mismatches = []
        cpf_list = []
        
        for item in items:
            device = item.get('device', 'unknown')
            device_counter[device] += 1
            
            cargo_titulo = item.get('cargo_titulo', '')
            cargo_counter[cargo_titulo] += 1
            
            # Check valor matches cargo
            valor = item.get('valor', 0)
            expected_valor = EXPECTED_CARGOS.get(cargo_titulo)
            if expected_valor and abs(valor - expected_valor) > 0.01:
                valor_mismatches.append({
                    'cargo': cargo_titulo,
                    'expected': expected_valor,
                    'actual': valor,
                    'cpf': item.get('cpf', '')
                })
            
            # Collect CPF for document test
            if item.get('cpf'):
                cpf_list.append(item.get('cpf'))
            
            # Verify required fields
            if not item.get('nome'):
                print(f"⚠️  Warning: Item missing 'nome': {item.get('cpf', 'unknown')}")
            if not item.get('cpf') or len(item.get('cpf', '')) != 11:
                print(f"⚠️  Warning: Item has invalid CPF: {item.get('cpf', 'none')}")
            if not item.get('email'):
                print(f"⚠️  Warning: Item missing 'email': {item.get('cpf', 'unknown')}")
            if 'Administração Penitenciária do Maranhão' not in item.get('concurso', ''):
                print(f"⚠️  Warning: Item has unexpected concurso: {item.get('concurso', '')[:50]}")
        
        print(f"\nDevice distribution:")
        for device, count in device_counter.items():
            print(f"  {device}: {count}")
        
        desktop_count = device_counter.get('desktop', 0)
        mobile_count = device_counter.get('mobile', 0)
        
        if desktop_count < 50:
            print(f"❌ FAILED: Expected at least 50 desktop, got {desktop_count}")
            return False
        if mobile_count < 50:
            print(f"❌ FAILED: Expected at least 50 mobile, got {mobile_count}")
            return False
        print(f"✅ Check 2 PASSED: Device mix is balanced (desktop: {desktop_count}, mobile: {mobile_count})")
        
        # Check 3: Cargo titles
        print(f"\nCargo distribution:")
        for cargo, count in sorted(cargo_counter.items()):
            print(f"  {cargo}: {count}")
        
        cargo_set = set(cargo_counter.keys())
        expected_cargo_set = set(EXPECTED_CARGOS.keys())
        
        if not cargo_set.issubset(expected_cargo_set):
            unexpected = cargo_set - expected_cargo_set
            print(f"❌ FAILED: Unexpected cargo titles: {unexpected}")
            return False
        
        print(f"✅ Check 3 PASSED: All cargo_titulo values are within expected set")
        
        # Check 4: Valor matches cargo
        if valor_mismatches:
            print(f"\n❌ FAILED: Found {len(valor_mismatches)} valor mismatches:")
            for mm in valor_mismatches[:5]:  # Show first 5
                print(f"  CPF {mm['cpf']}: {mm['cargo']} - expected {mm['expected']}, got {mm['actual']}")
            return False
        print(f"✅ Check 4 PASSED: All valor fields match their cargo")
        
        # Return a CPF for document testing
        return cpf_list[0] if cpf_list else None
        
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_kpis(token):
    """Test 3: GET /api/admin/dashboard/kpis"""
    print("\n" + "="*70)
    print("TEST 3: Dashboard KPIs")
    print("="*70)
    
    url = f"{API_BASE}/admin/dashboard/kpis"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        print(f"Response: {data}")
        
        inscricoes = data.get('inscricoes', 0)
        acessos = data.get('acessos', 0)
        
        print(f"\nKPI Values:")
        print(f"  Inscrições: {inscricoes}")
        print(f"  Acessos: {acessos}")
        
        # Check inscricoes >= 150
        if inscricoes < 150:
            print(f"❌ FAILED: Expected inscricoes >= 150, got {inscricoes}")
            return False
        print(f"✅ Check 1 PASSED: inscricoes >= 150 ({inscricoes})")
        
        # Check acessos >= 150 (150 inscriptions + 220 extra accesses = 370 total)
        if acessos < 150:
            print(f"❌ FAILED: Expected acessos >= 150, got {acessos}")
            return False
        print(f"✅ Check 2 PASSED: acessos >= 150 ({acessos})")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_documentos_list(token):
    """Test 4: GET /api/admin/documentos"""
    print("\n" + "="*70)
    print("TEST 4: Documents List")
    print("="*70)
    
    url = f"{API_BASE}/admin/documentos"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        data = response.json()
        total = data.get('total', 0)
        items = data.get('items', [])
        
        print(f"Total documents: {total}")
        print(f"Items returned: {len(items)}")
        
        if total == 0:
            print(f"❌ FAILED: Expected total > 0, got {total}")
            return None
        print(f"✅ Check 1 PASSED: Documents list returned with total > 0 ({total})")
        
        # Find a candidate with has_frente=True
        candidate_with_frente = None
        for item in items:
            if item.get('has_frente'):
                candidate_with_frente = {
                    'cpf': item.get('cpf'),
                    'nome': item.get('nome'),
                    'doc_tipo': item.get('doc_tipo'),
                    'has_frente': item.get('has_frente'),
                    'has_verso': item.get('has_verso'),
                }
                break
        
        if not candidate_with_frente:
            print(f"❌ FAILED: No candidate with has_frente=True found")
            return None
        
        print(f"\nFound candidate with document:")
        print(f"  CPF: {candidate_with_frente['cpf']}")
        print(f"  Nome: {candidate_with_frente['nome']}")
        print(f"  Doc Tipo: {candidate_with_frente['doc_tipo']}")
        print(f"  Has Frente: {candidate_with_frente['has_frente']}")
        print(f"  Has Verso: {candidate_with_frente['has_verso']}")
        
        return candidate_with_frente
        
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_documento_image(token, cpf):
    """Test 5: GET /api/admin/documentos/{cpf}/frente?token=<jwt>"""
    print("\n" + "="*70)
    print("TEST 5: Document Image Retrieval")
    print("="*70)
    
    url = f"{API_BASE}/admin/documentos/{cpf}/frente"
    params = {"token": token}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
        
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"❌ FAILED: Expected Content-Type to start with 'image/', got '{content_type}'")
            return False
        
        if len(response.content) < 100:
            print(f"❌ FAILED: Image content too small ({len(response.content)} bytes)")
            return False
        
        print(f"✅ PASSED: Document image retrieved successfully")
        print(f"   Content-Type: {content_type}")
        print(f"   Size: {len(response.content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_protected_route_without_auth():
    """Test 6: GET /api/admin/inscriptions without Authorization - should return 401"""
    print("\n" + "="*70)
    print("TEST 6: Protected Route Without Auth")
    print("="*70)
    
    url = f"{API_BASE}/admin/inscriptions"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 401:
            print(f"❌ FAILED: Expected 401, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print(f"✅ PASSED: Protected route correctly returns 401 without auth")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Exception - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all backend tests"""
    print("\n" + "="*70)
    print("SEAP-MA ADMIN PANEL BACKEND API TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Admin User: {ADMIN_USERNAME}")
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': 6
    }
    
    # Test 1: Login
    token = test_admin_login()
    if not token:
        results['failed'] += 1
        print("\n❌ Cannot proceed without valid token. Stopping tests.")
        print_summary(results)
        return 1
    results['passed'] += 1
    
    # Test 2: Inscriptions
    cpf_for_doc_test = test_inscriptions(token)
    if cpf_for_doc_test:
        results['passed'] += 1
    else:
        results['failed'] += 1
        cpf_for_doc_test = None
    
    # Test 3: Dashboard KPIs
    if test_dashboard_kpis(token):
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 4: Documents List
    candidate = test_documentos_list(token)
    if candidate:
        results['passed'] += 1
        # Use the CPF from documents list for image test
        cpf_for_doc_test = candidate['cpf']
    else:
        results['failed'] += 1
    
    # Test 5: Document Image (only if we have a CPF)
    if cpf_for_doc_test:
        if test_documento_image(token, cpf_for_doc_test):
            results['passed'] += 1
        else:
            results['failed'] += 1
    else:
        print("\n⚠️  Skipping Test 5: No CPF available for document image test")
        results['failed'] += 1
    
    # Test 6: Protected Route
    if test_protected_route_without_auth():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    print_summary(results)
    
    return 0 if results['failed'] == 0 else 1


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {results['passed']/results['total']*100:.1f}%")
    print("="*70)


if __name__ == "__main__":
    sys.exit(main())
