import os
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

class SearchProvider:
    """
    Web search provider for CatalogIQ.

    This component only performs web searches.
    It does not perform AI enrichment.
    """

    def __init__(self) -> None:
        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not configured."
            )

        self.client = TavilyClient(
            api_key=api_key
        )

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search the web and return structured results.
        """

        if not query.strip():
            return []

        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=limit,
            include_answer=False,
            include_raw_content=False,
        )

        results = response.get(
            "results",
            [],
        )

        return [
            {
                "title": result.get(
                    "title",
                    "",
                ),
                "url": result.get(
                    "url",
                    "",
                ),
                "content": result.get(
                    "content",
                    "",
                ),
                "score": result.get(
                    "score",
                    0.0,
                ),
            }
            for result in results
            if result.get("url")
        ]