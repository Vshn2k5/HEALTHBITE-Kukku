import requests

def test_security():
    base_url = "http://127.0.0.1:8000"
    
    print("--- Testing Security Fixes ---")
    
    # 1. Test JWT Bypass
    print("\n1. Testing fake-jwt-token bypass...")
    try:
        headers = {"Authorization": "Bearer fake-jwt-token"}
        resp = requests.get(f"{base_url}/api/health/profile", headers=headers)
        print(f"Result: {resp.status_code} {resp.text}")
        if resp.status_code == 401:
            print("[PASS] Bypass removed.")
        else:
            print("[FAIL] Bypass still works!")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Removed Endpoint: verify-identity
    print("\n2. Testing /api/auth/verify-identity...")
    try:
        resp = requests.post(f"{base_url}/api/auth/verify-identity", json={"email": "test@test.com", "name": "Test"})
        print(f"Result: {resp.status_code} {resp.text}")
        if resp.status_code == 404:
            print("[PASS] Endpoint removed.")
        else:
            print("[FAIL] Endpoint still exists!")
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Removed Endpoint: reset-password-direct
    print("\n3. Testing /api/auth/reset-password-direct...")
    try:
        resp = requests.post(f"{base_url}/api/auth/reset-password-direct", json={"email": "test@test.com", "new_password": "Password123!"})
        print(f"Result: {resp.status_code} {resp.text}")
        if resp.status_code == 404:
            print("[PASS] Endpoint removed.")
        else:
            print("[FAIL] Endpoint still exists!")
    except Exception as e:
        print(f"Error: {e}")

    # 4. Test CSP Headers
    print("\n4. Testing Security Headers...")
    try:
        resp = requests.get(f"{base_url}/")
        csp = resp.headers.get("Content-Security-Policy")
        print(f"CSP Header: {csp}")
        if csp:
            print("[PASS] Security headers present.")
        else:
            print("[FAIL] Security headers missing!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_security()
