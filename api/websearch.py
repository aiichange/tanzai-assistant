from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 5):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    # keep critical fields only
    return [{"title": r.get("title"), "href": r.get("href"), "body": r.get("body")} for r in results]
