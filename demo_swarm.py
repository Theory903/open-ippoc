
import requests
import json
import sys

CORTEX_URL = "http://localhost:8001/v1/chat/completions"

def chat_with_cortex(prompt):
    print(f"\n🧠 Sending to Cortex: {prompt}")
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "gpt-4o"
    }
    
    try:
        response = requests.post(CORTEX_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"\n🤖 Cortex Replied:\n{content}")
        return content
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    prompt = "Who are you and what is your purpose?"
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    
    chat_with_cortex(prompt)
