from ddgs import DDGS


def search_web(
    query: str,
    max_results: int = 5,
) -> list[dict[str, str]]:
    """
    Search the web and return structured results.
    """

    results = DDGS().text(
        query,
        max_results=max_results,
    )

    return [
        {
            "title": result.get("title", ""),
            "url": result.get("href", ""),
            "snippet": result.get("body", ""),
        }
        for result in results
    ]