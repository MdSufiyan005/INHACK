import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient

@dataclass
class SimpleEventOpportunity:
    event_name: str
    event_type: str
    date: str
    location: str
    contact_info: Dict[str, str]
    description: str
    source_url: str
    relevance_score: int

class SimplifiedVendorAgent:
    def __init__(self, tavily_api_key: str):
        self.tavily_client = TavilyClient(api_key=tavily_api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Reliable domains that usually work well for scraping
        self.reliable_domains = [
            "eventbrite.com",
            "meetup.com", 
            "timeout.com",
            "allevents.in",
            "10times.com",
            "eventful.com",
            "bandsintown.com"
        ]
    
    async def find_opportunities(self, location: str, max_results: int = 20) -> List[SimpleEventOpportunity]:
        """Find vendor opportunities with simplified approach"""
        
        print(f"🔍 Searching for events in {location}...")
        
        # Search queries focused on vendor opportunities
        search_queries = [
            f"food festival vendor application {location} 2024 2025",
            f"street fair vendor booth {location}",
            f"farmers market vendor space {location}",
            f"outdoor event food vendor {location}",
            f"festival vendor registration {location}"
        ]
        
        all_opportunities = []
        
        for query in search_queries:
            try:
                print(f"   Searching: {query}")
                
                results = self.tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=5,
                    include_domains=self.reliable_domains
                )
                
                for result in results.get('results', []):
                    opportunity = await self._process_search_result(result)
                    if opportunity:
                        all_opportunities.append(opportunity)
                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Search error for '{query}': {e}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_opportunities = self._deduplicate_opportunities(all_opportunities)
        sorted_opportunities = sorted(unique_opportunities, 
                                    key=lambda x: x.relevance_score, 
                                    reverse=True)
        
        return sorted_opportunities[:max_results]
    
    async def _process_search_result(self, result: Dict) -> Optional[SimpleEventOpportunity]:
        """Process a single search result"""
        
        url = result.get('url', '')
        title = result.get('title', '')
        content = result.get('content', '')
        
        if not url or not title:
            return None
        
        # Skip problematic URLs
        if any(domain in url.lower() for domain in ['facebook.com', 'instagram.com', 'twitter.com']):
            return None
        
        # Calculate relevance score based on content
        relevance_score = self._calculate_relevance_score(title, content)
        
        if relevance_score < 3:  # Skip low-relevance results
            return None
        
        # Try to extract additional details by scraping
        additional_info = await self._scrape_additional_info(url)
        
        # Extract basic information
        event_name = title
        event_type = self._classify_event_type(title + " " + content)
        date = self._extract_date_from_text(content)
        location = self._extract_location_from_text(content)
        
        # Combine contact info
        contact_info = {'website': url}
        if additional_info:
            contact_info.update(additional_info.get('contact', {}))
        
        return SimpleEventOpportunity(
            event_name=event_name,
            event_type=event_type,
            date=date,
            location=location,
            contact_info=contact_info,
            description=content[:300],
            source_url=url,
            relevance_score=relevance_score
        )
    
    def _calculate_relevance_score(self, title: str, content: str) -> int:
        """Calculate how relevant this result is for food vendors"""
        
        text = (title + " " + content).lower()
        score = 0
        
        # High-value keywords
        high_value_keywords = ['vendor', 'food vendor', 'stall', 'booth', 'registration', 'application']
        score += sum(3 for keyword in high_value_keywords if keyword in text)
        
        # Medium-value keywords  
        medium_value_keywords = ['food', 'festival', 'market', 'fair', 'event']
        score += sum(2 for keyword in medium_value_keywords if keyword in text)
        
        # Event type indicators
        event_keywords = ['concert', 'music', 'outdoor', 'street', 'community']
        score += sum(1 for keyword in event_keywords if keyword in text)
        
        # Date relevance (future events)
        if any(year in text for year in ['2024', '2025']):
            score += 2
        
        return score
    
    def _classify_event_type(self, text: str) -> str:
        """Classify the type of event"""
        text = text.lower()
        
        if any(word in text for word in ['food festival', 'culinary', 'taste']):
            return 'food festival'
        elif any(word in text for word in ['farmers market', 'market']):
            return 'farmers market'  
        elif any(word in text for word in ['street fair', 'fair']):
            return 'street fair'
        elif any(word in text for word in ['music festival', 'concert']):
            return 'music festival'
        elif any(word in text for word in ['outdoor', 'park']):
            return 'outdoor event'
        else:
            return 'community event'
    
    def _extract_date_from_text(self, text: str) -> str:
        """Extract date information from text"""
        
        # Look for date patterns
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\b\d{1,2}/\d{1,2}/\d{4}',
            r'\b\d{1,2}-\d{1,2}-\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Look for relative dates
        if 'this weekend' in text.lower():
            return 'This weekend'
        elif 'next month' in text.lower():
            return 'Next month'
        elif any(month in text.lower() for month in ['january', 'february', 'march', 'april']):
            return 'Check website for dates'
        
        return 'TBD'
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extract location from text"""
        
        # Look for common location patterns
        location_patterns = [
            r'\b\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b',
            r'\b[\w\s]+,\s*[A-Z]{2}\s*\d{5}',  # City, State ZIP
            r'\b[\w\s]+,\s*(?:NY|New York|NYC)\b'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return 'Check website for location'
    
    async def _scrape_additional_info(self, url: str) -> Optional[Dict]:
        """Try to scrape additional information from the URL"""
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract contact information
            contact_info = {}
            
            # Look for email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, soup.get_text())
            if emails:
                contact_info['email'] = emails[0]
            
            # Look for phone numbers
            phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
            phones = re.findall(phone_pattern, soup.get_text())
            if phones:
                contact_info['phone'] = phones[0]
            
            return {'contact': contact_info}
            
        except Exception as e:
            print(f"   Could not scrape {url}: {e}")
            return None
    
    def _deduplicate_opportunities(self, opportunities: List[SimpleEventOpportunity]) -> List[SimpleEventOpportunity]:
        """Remove duplicate opportunities"""
        
        seen_urls = set()
        unique_opportunities = []
        
        for opp in opportunities:
            if opp.source_url not in seen_urls:
                seen_urls.add(opp.source_url)
                unique_opportunities.append(opp)
        
        return unique_opportunities
    
    def export_opportunities(self, opportunities: List[SimpleEventOpportunity], filename: str):
        """Export opportunities to JSON file"""
        
        data = [asdict(opp) for opp in opportunities]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Exported {len(opportunities)} opportunities to {filename}")

# Test function
async def test_simplified_agent():
    """Test the simplified agent"""
    
    tavily_api_key = "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"  # Replace with your actual key
    
    if tavily_api_key == "your-tavily-api-key-here":
        print("⚠️  Please set your Tavily API key")
        return
    
    try:
        agent = SimplifiedVendorAgent(tavily_api_key)
        
        opportunities = await agent.find_opportunities("New York City", max_results=10)
        
        print(f"\n📊 Found {len(opportunities)} vendor opportunities:")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n{i}. {opp.event_name}")
            print(f"   📅 Date: {opp.date}")
            print(f"   🏷️  Type: {opp.event_type}")
            print(f"   📍 Location: {opp.location}")
            print(f"   📞 Contact: {opp.contact_info}")  
            print(f"   ⭐ Score: {opp.relevance_score}")
            print(f"   🔗 URL: {opp.source_url}")
        
        if opportunities:
            filename = f"simple_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            agent.export_opportunities(opportunities, filename)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simplified_agent())