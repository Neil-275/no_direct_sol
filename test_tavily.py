# To install: pip install tavily-python
from tavily import TavilyClient
client = TavilyClient("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")
response = client.search(
    query="who is Bill Gate ?"
)
print(response)