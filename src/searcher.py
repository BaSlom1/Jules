import requests
import time

def ask_ai(prompt):
    """
    Sends a POST request to text.pollinations.ai with the given prompt.
    Implements network bypass techniques: realistic headers and alternative mirrors.
    Returns (success: bool, response: str).
    """
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "openai"
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://pollinations.ai",
        "Referer": "https://pollinations.ai/"
    }

    # List of endpoints to try: main domain, and alternative mirrors
    endpoints = [
        "https://text.pollinations.ai/",
        # Pollinations is hosted behind Cloudflare, so trying the same API
        # via another Pollinations subdomain as a fallback mirror
        "https://image.pollinations.ai/text/",
    ]

    max_retries = 3

    for url in endpoints:
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return True, response.text
            except requests.exceptions.RequestException as e:
                # If we're on the last attempt for this URL, move to the next URL
                if attempt == max_retries - 1:
                    break
                time.sleep(1) # wait a bit before retrying

    return False, ""

if __name__ == "__main__":
    success, text = ask_ai("Привет, кто ты?")
    print(f"Success: {success}\nText: {text}")
