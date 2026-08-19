import os
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Try loading from multiple paths
root_env = Path(__file__).resolve().parents[1] / ".env"
backend_env = Path(__file__).resolve().parent / ".env"
print(f"Checking root .env exists: {root_env.exists()} ({root_env})")
print(f"Checking backend .env exists: {backend_env.exists()} ({backend_env})")

load_dotenv(root_env, override=True)
load_dotenv(backend_env, override=True)

waqi_token = os.environ.get("WAQI_API_TOKEN") or os.environ.get("WAQI_TOKEN")
gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

print(f"WAQI token found: {waqi_token[:8] if waqi_token else 'NONE'}...")
print(f"Gemini key found: {gemini_key[:8] if gemini_key else 'NONE'}...")

# 1. Test WAQI
if waqi_token:
    for feed in ["@14722", "tashkent", "geo:41.2995;69.2401"]:
        url = f"https://api.waqi.info/feed/{feed}/?token={waqi_token}"
        try:
            r = httpx.get(url, timeout=8.0)
            print(f"WAQI feed '{feed}': status={r.status_code}, data={r.json().get('status')}")
            if r.json().get('status') == 'ok':
                d = r.json().get('data', {})
                print(f"   AQI={d.get('aqi')}, City={d.get('city', {}).get('name')}, PM2.5={d.get('iaqi', {}).get('pm25', {}).get('v')}")
        except Exception as e:
            print(f"WAQI feed '{feed}' error: {e}")

# 2. Test Gemini
if gemini_key and gemini_key != "your-gemini-api-key-here":
    print("Testing Gemini API...")
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'UrbanMind operational'",
        )
        print(f"Gemini response: {resp.text}")
    except Exception as e:
        print(f"Gemini test error: {e}")
