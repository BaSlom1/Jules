import requests
import time

def ask_ai(prompt):
    """
    Sends a POST request to text.pollinations.ai with the given prompt.
    Retries up to 3 times with a 10s timeout on failure.
    Returns (success: bool, response: str).
    """
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "openai"
    }
    headers = {
        "Content-Type": "application/json"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True, response.text
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                return False, ""
            time.sleep(1) # wait a bit before retrying

    return False, ""

if __name__ == "__main__":
    success, text = ask_ai("Привет, кто ты?")
    print(f"Success: {success}\nText: {text}")
