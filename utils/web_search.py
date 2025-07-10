from serpapi import GoogleSearch

def serpapi_search(query, api_key):
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 3,
            "hl": "vi"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic = results.get("organic_results", [])
        if not organic:
            return "Không tìm thấy kết quả web search."
        output = []
        for item in organic:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            output.append(f"- **{title}**\n{snippet}\n{link}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Không thể lấy kết quả web search: {e}"