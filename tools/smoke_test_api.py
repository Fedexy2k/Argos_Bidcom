import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient

def run_smoke_tests():
    from api.main import app
    client = TestClient(app)
    tests = []
    
    # 1. Healthcheck
    try:
        r = client.get("/api/health")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert data.get("status") == "ok", f"Data: {data}"
        assert data.get("version") == "3.2.2", f"Version: {data.get('version')}"
        tests.append(("GET /api/health", "PASSED", f"Version: {data.get('version')}"))
    except Exception as e:
        tests.append(("GET /api/health", "FAILED", str(e)))
        
    # 2. Config
    try:
        r = client.get("/api/config")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert "empresa" in data, "No empresa in config"
        assert "sociedades_extension" in data, "No sociedades_extension in config"
        tests.append(("GET /api/config", "PASSED", f"Empresa: {data.get('empresa', {}).get('razon_social')}"))
    except Exception as e:
        tests.append(("GET /api/config", "FAILED", str(e)))
        
    # 3. Budget Summary
    try:
        r = client.get("/api/budget/summary")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        tests.append(("GET /api/budget/summary", "PASSED", f"Keys: {list(data.keys())}"))
    except Exception as e:
        tests.append(("GET /api/budget/summary", "FAILED", str(e)))
        
    # 4. Budget Ledger
    try:
        r = client.get("/api/budget/ledger")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        assert "entries" in data, "No entries in ledger"
        tests.append(("GET /api/budget/ledger", "PASSED", f"Total entries: {len(data.get('entries', []))}"))
    except Exception as e:
        tests.append(("GET /api/budget/ledger", "FAILED", str(e)))

    # 5. EE Families
    try:
        r = client.get("/api/ee/families")
        assert r.status_code == 200, f"Status {r.status_code}"
        data = r.json()
        families = data.get("families", [])
        assert len(families) >= 11, f"Expected >= 11 families, got {len(families)}"
        tests.append(("GET /api/ee/families", "PASSED", f"Loaded {len(families)} families"))
    except Exception as e:
        tests.append(("GET /api/ee/families", "FAILED", str(e)))

    # 6. WebSocket Logs
    try:
        with client.websocket_connect("/ws/log") as websocket:
            websocket.send_text("ping")
        tests.append(("WS /ws/log", "PASSED", "WebSocket connect & disconnect OK"))
    except Exception as e:
        tests.append(("WS /ws/log", "FAILED", str(e)))

    print("\n" + "="*70)
    print("           ARGOS API SMOKE TEST RESULTS")
    print("="*70)
    all_passed = True
    for endpoint, status, detail in tests:
        mark = "[OK]" if status == "PASSED" else "[FAIL]"
        print(f"{mark:<6} {endpoint:<30} {status:<8} | {detail}")
        if status != "PASSED":
            all_passed = False
    print("="*70)
    if all_passed:
        print("TODOS LOS TESTS DE HUMO PASARON SATISFACTORIAMENTE.")
        return 0
    else:
        print("HUBO FALLAS EN LOS TESTS.")
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_tests())
