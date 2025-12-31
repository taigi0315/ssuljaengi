"""Tavily web search tool for finding trending Reddit discussions."""

import logging
from typing import Any, Optional

from pydantic import BaseModel

from gossiptoon.core.exceptions import APIError
from gossiptoon.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Web search result."""

    title: str
    url: str
    content: str
    score: float


class TavilySearchTool:
    """Tool for web search using Tavily API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Tavily search tool.

        Args:
            api_key: Tavily API key
        """
        self.api_key = api_key
        self._client: Optional[Any] = None

    def _init_client(self) -> Any:
        """Initialize Tavily client (lazy loading).

        Returns:
            Tavily client instance

        Raises:
            APIError: If initialization fails
        """
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise APIError(
                "Tavily API key not configured. Set TAVILY_API_KEY in .env"
            )

        try:
            from tavily import TavilyClient

            self._client = TavilyClient(api_key=self.api_key)
            logger.info("Tavily client initialized")
            return self._client
        except ImportError:
            raise APIError(
                "Tavily package not installed. Install with: pip install tavily-python"
            )
        except Exception as e:
            raise APIError(f"Failed to initialize Tavily client: {e}") from e

    @retry_with_backoff(max_retries=3, exceptions=(APIError,))
    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_domains: Optional[list[str]] = None,
    ) -> list[SearchResult]:
        """Search the web using Tavily.

        Args:
            query: Search query
            max_results: Maximum number of results
            include_domains: Optional list of domains to include

        Returns:
            List of search results

        Raises:
            APIError: If search fails
        """
        try:
            client = self._init_client()

            # Build search parameters
            search_params: dict[str, Any] = {
                "query": query,
                "max_results": max_results,
            }

            if include_domains:
                search_params["include_domains"] = include_domains

            # Perform search
            response = client.search(**search_params)

            # Parse results
            results = []
            for result in response.get("results", []):
                results.append(
                    SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        content=result.get("content", ""),
                        score=result.get("score", 0.0),
                    )
                )

            logger.info(f"Found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            raise APIError(f"Tavily search failed: {e}") from e

    async def search_reddit_stories(
        self,
        keywords: Optional[list[str]] = None,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search for trending Reddit stories.

        Args:
            keywords: Optional keywords to include in search
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        # Build query for Reddit stories
        query_parts = ["site:reddit.com", "viral story"]

        if keywords:
            query_parts.extend(keywords)

        # Add popular subreddit names
        query_parts.append(
            "(AITA OR relationship_advice OR AmItheAsshole OR tifu)"
        )

        query = " ".join(query_parts)

        return await self.search(
            query=query,
            max_results=max_results,
            include_domains=["reddit.com"],
        )
