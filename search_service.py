"""
Internet search service for OLLAMA Chat
Provides web search functionality to enhance AI responses with current information
"""

import requests
import json
from typing import List, Dict, Optional
import logging
from urllib.parse import quote_plus
import re
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class SearchService:
    """Service for performing internet searches and extracting relevant information"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search using DuckDuckGo Instant Answer API
        Returns a list of search results with title, snippet, and URL
        """
        try:
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract instant answer if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'DuckDuckGo Answer'),
                    'snippet': data.get('Abstract', ''),
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo Instant Answer'
                })
            
            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '')[:100] + '...' if len(topic.get('Text', '')) > 100 else topic.get('Text', ''),
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo Related'
                    })
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def search_wikipedia(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search Wikipedia for relevant articles
        """
        try:
            # Wikipedia API search
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(query)
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    return [{
                        'title': data.get('title', ''),
                        'snippet': data.get('extract', ''),
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'source': 'Wikipedia'
                    }]
            
            # Fallback to search API
            search_api_url = "https://en.wikipedia.org/api/rest_v1/page/search"
            params = {'q': query, 'limit': max_results}
            
            response = self.session.get(search_api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for page in data.get('pages', [])[:max_results]:
                results.append({
                    'title': page.get('title', ''),
                    'snippet': page.get('description', '') or page.get('extract', ''),
                    'url': f"https://en.wikipedia.org/wiki/{quote_plus(page.get('title', ''))}",
                    'source': 'Wikipedia'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []
    
    def search_web_basic(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Basic web search using multiple sources
        Combines DuckDuckGo and Wikipedia results
        """
        all_results = []
        
        # Search DuckDuckGo
        ddg_results = self.search_duckduckgo(query, max_results=3)
        all_results.extend(ddg_results)
        
        # Search Wikipedia
        wiki_results = self.search_wikipedia(query, max_results=2)
        all_results.extend(wiki_results)
        
        # Remove duplicates and limit results
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results[:max_results]
    
    def format_search_results(self, results: List[Dict], query: str) -> str:
        """
        Format search results into a readable text for AI context
        """
        if not results:
            return f"No search results found for: {query}"
        
        formatted = f"Internet search results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description available')
            url = result.get('url', '')
            source = result.get('source', 'Unknown')
            
            # Clean up snippet
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            if len(snippet) > 300:
                snippet = snippet[:300] + '...'
            
            formatted += f"{i}. **{title}** ({source})\n"
            formatted += f"   {snippet}\n"
            if url:
                formatted += f"   URL: {url}\n"
            formatted += "\n"
        
        formatted += "---\n\n"
        return formatted
    
    def search_and_format(self, query: str, max_results: int = 5) -> str:
        """
        Perform search and return formatted results ready for AI context
        """
        try:
            results = self.search_web_basic(query, max_results)
            formatted = self.format_search_results(results, query)
            return formatted
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Search failed for '{query}': {str(e)}"

class SearchError(Exception):
    """Custom exception for search-related errors"""
    pass

# Global search service instance
search_service = SearchService()