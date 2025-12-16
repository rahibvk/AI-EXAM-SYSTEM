import asyncio
import httpx
import sys

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def test_registration():
    url = "http://localhost:8000/api/v1/register"
    payload = {
        "email": "test_verify_user@example.com",
        "password": "password123",
        "full_name": "Test User",
        "role": "student"
    }
    
    print(f"Testing Registration Endpoint: {url}")
    print(f"Payload: {payload}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print(f"{GREEN}SUCCESS: Registration successful!{RESET}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"{GREEN}SUCCESS: Backend reachable (User already exists).{RESET}")
                return True
            else:
                print(f"{RED}FAILURE: Backend returned an error.{RESET}")
                return False
    except Exception as e:
        print(f"{RED}CRITICAL FAILURE: Could not connect to backend.{RESET}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(test_registration())
    except ImportError:
        # Fallback if httpx is not installed, though it should be in standard env or reachable
        print("httpx not found, installing...")
        import os
        os.system("pip install httpx")
        import httpx
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(test_registration())
