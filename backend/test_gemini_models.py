import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash", "gemini-3.6-flash"]:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents="Say 'UrbanMind Operational' in JSON format: {\"status\": \"OK\"}"
                )
                print(f"Model {model_name}: SUCCESS -> {resp.text.strip()}")
            except Exception as exc:
                print(f"Model {model_name}: FAILED -> {exc}")
    except Exception as e:
        print(f"genai client error: {e}")
