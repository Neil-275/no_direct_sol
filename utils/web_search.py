from serpapi import GoogleSearch
import os

def serpapi_search(query):
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": os.getenv('SERPAPI_KEY'),
            "num": 3,
            "hl": "vi"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic = results.get("organic_results", [])
        if not organic:
            return "Không tìm thấy kết quả web search."
        output = ["Đây là một số tài liệu đáng tin cậy mà tôi tìm được \n"]
        for item in organic:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            output.append(f"- **{title}**\n{snippet}\n{link}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Không thể lấy kết quả web search: {e}"