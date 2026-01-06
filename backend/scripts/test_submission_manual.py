"""
Manual Submission Endpoint Tester

Purpose:
    A connectivity test script that:
    1. Checks if the backend is reachable (Root URL).
    2. Inspects `openapi.json` to verify the `/submissions/submit` route is registered.
    3. Attempts a direct POST request (which expects 422/400, confirming the endpoint is active).
"""
import asyncio
import httpx
import sys

# Define base URL - assuming local dev server
BASE_URL = "http://localhost:8000"
API_V1 = "/api/v1"

async def test_submit_endpoint():
    """
    Runs connectivity checks against the running backend.
    """
    print(f"Testing connectivity to {BASE_URL}...")
    
    async with httpx.AsyncClient() as client:
        # 1. Check Root
        try:
            res = await client.get(f"{BASE_URL}/")
            print(f"Root '/': {res.status_code}")
        except Exception as e:
            print(f"[ERROR] Server is DOWN? {e}")
            return

        # 2. Check OpenAPI Schema for route existence
        print("\nChecking OpenAPI schema for route registration...")
        try:
            res = await client.get(f"{BASE_URL}/openapi.json")
            if res.status_code == 200:
                schema = res.json()
                paths = schema.get("paths", {})
                target_path = f"{API_V1}/submissions/submit"
                if target_path in paths and 'post' in paths[target_path]:
                    print(f"[SUCCESS] Route Found in OpenAPI: {target_path} [POST]")
                else:
                    print(f"[ERROR] Route MISSING in OpenAPI: {target_path}")
            else:
                print(f"[WARN] Could not fetch openapi.json: {res.status_code}")
        except Exception as e:
            print(f"Error fetching schema: {e}")

        # 3. Try Direct Hit
        print(f"\nDirect Hit Check: {BASE_URL}{API_V1}/submissions/submit")
        res = await client.post(f"{BASE_URL}{API_V1}/submissions/submit", json={})
        print(f"Status: {res.status_code}")
        if res.status_code == 404:
            print("[ERROR] Still 404 Not Found")
        
if __name__ == "__main__":
    try:
        asyncio.run(test_submit_endpoint())
    except KeyboardInterrupt:
        pass
