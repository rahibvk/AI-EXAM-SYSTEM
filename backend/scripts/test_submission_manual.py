import asyncio
import httpx
import sys

# Define base URL - assuming local dev server
BASE_URL = "http://localhost:8000"
API_V1 = "/api/v1"

async def test_submit_endpoint():
    print(f"Testing connectivity to {BASE_URL}...")
    
    async with httpx.AsyncClient() as client:
        # 1. Check Root
        try:
            res = await client.get(f"{BASE_URL}/")
            print(f"Root '/': {res.status_code}")
        except Exception as e:
            print(f"❌ Server is DOWN? {e}")
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
                    print(f"✅ Route Found in OpenAPI: {target_path} [POST]")
                else:
                    print(f"❌ Route MISSING in OpenAPI: {target_path}")
            else:
                print(f"⚠️ Could not fetchopenapi.json: {res.status_code}")
        except Exception as e:
            print(f"Error fetching schema: {e}")

        # 3. Try Direct Hit
        print(f"\nDirect Hit Check: {BASE_URL}{API_V1}/submissions/submit")
        res = await client.post(f"{BASE_URL}{API_V1}/submissions/submit", json={})
        print(f"Status: {res.status_code}")
        if res.status_code == 404:
            print("❌ Still 404 Not Found")
        
if __name__ == "__main__":
    try:
        asyncio.run(test_submit_endpoint())
    except KeyboardInterrupt:
        pass
