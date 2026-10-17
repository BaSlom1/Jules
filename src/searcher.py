import requests
from bs4 import BeautifulSoup

def search_duckduckgo_fallback(query, max_results=5):
    """
    Fallback method using direct HTML parsing of duckduckgo.com.
    """
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.find_all('a', class_='result__snippet', limit=max_results):
            # DuckDuckGo HTML structure often has result__title, result__snippet
            parent = a.find_parent('div', class_='result__body')
            if parent:
                title_elem = parent.find('a', class_='result__url')
                if not title_elem:
                    title_elem = parent.find('a', class_='result__title')

                title = title_elem.text.strip() if title_elem else "Нет заголовка"
                href = title_elem.get('href') if title_elem else ""

                # Cleanup DuckDuckGo redirect link
                if href and href.startswith('//duckduckgo.com/l/?uddg='):
                    import urllib.parse
                    href = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])

                snippet = a.text.strip()

                results.append({
                    "title": title,
                    "body": snippet,
                    "href": href
                })
    except Exception as e:
        print(f"Fallback search failed: {e}")

    return results

def search(query, max_results=5):
    """
    Search using duckduckgo-search with a fallback to direct HTML parsing.
    """
    results = []

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            # text() returns an iterator of dicts: {'title': ..., 'href': ..., 'body': ...}
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get('title', 'Нет заголовка'),
                    "body": r.get('body', ''),
                    "href": r.get('href', '')
                })
    except Exception as e:
        print(f"DDGS failed, using fallback: {e}")
        results = search_duckduckgo_fallback(query, max_results)

    return results

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "python what is it"
    print(search(query))
