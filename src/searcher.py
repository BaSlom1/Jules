import requests
import json
import urllib.parse

def ask_ai(prompt):
    """
    Sends a request to text.pollinations.ai with the given prompt.
    """
    # pollinations.ai accepts prompt in the URL path for GET requests
    # e.g., https://text.pollinations.ai/prompt

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error querying AI: {e}")
        return f"Ошибка при получении данных: {e}"

if __name__ == "__main__":
    print(ask_ai("Привет, кто ты?"))
