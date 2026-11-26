import os
import json
import requests

GEOGPT_URL = "https://geogpt-sg.zero2x.org/be-api/service/api/model/v1/chat/completions"
GEOGPT_TOKEN = os.getenv("GEOGPT_API_KEY")

def geogpt_call(prompt: str, temperature: float = 0.3) -> str:
    if not GEOGPT_TOKEN:
        return "❌ GEOGPT_API_KEY non impostata."

    headers = {
        "Authorization": f"Bearer {GEOGPT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a geoscience expert specializing in hydrology, wetlands, and lake ecosystems."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "stream": True
    }

    response = requests.post(
        GEOGPT_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    final_text = []

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        if line.startswith("data:"):
            chunk = line.replace("data:", "").strip()

            if chunk == "[DONE]":
                break

            try:
                data = json.loads(chunk)
                delta = data["choices"][0].get("delta", {}).get("content")
                if delta:
                    final_text.append(delta)
            except Exception:
                continue

    return "".join(final_text).strip()
