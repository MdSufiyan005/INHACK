from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio
import json
import re
from tavily import TavilyClient
from bs4 import BeautifulSoup
import requests
from models.VendorEvent import VendorEvent        
from schemas.Vendor_Event import VendorEventRead  

from models.vendor import Vendor
from models.VendorEvent import VendorEvent
from db.database import get_db  # Assume this function provides the database session

# Pydantic models for API request and response
class EventResponse(BaseModel):
    event_name: str
    description: str
    location: str
    contact_phone: Optional[str] = None
    stall_info: str
    event_date: Optional[str] = None
    source_url: Optional[str] = None
    created_at: datetime = datetime.utcnow()

class VendorEventsRequest(BaseModel):
    vendor_id: str
    radius_km: Optional[int] = 50
    max_results: Optional[int] = 10

# Event discovery service class
class EventDiscoveryService:
    def __init__(self, tavily_api_key: str):
        self.tavily_client = TavilyClient(api_key=tavily_api_key)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    async def find_vendor_events(self, vendor: Vendor, radius_km: int = 50, max_results: int = 10) -> List[EventResponse]:
        """Find events for a specific vendor based on their location and business info."""
        search_queries = self._generate_search_queries(vendor, radius_km)
        all_events = []
        for query in search_queries:
            try:
                results = self.tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=[
                        "eventbrite.com", "meetup.com", "timeout.com",
                        "allevents.in", "10times.com", "eventful.com",
                        "localevents.com", "citygov.com"
                    ]
                )
                for result in results.get('results', []):
                    event = await self._process_event_result(result, vendor)
                    if event:
                        all_events.append(event)
                await asyncio.sleep(0.5)  # Reduced rate limit delay for better performance
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                continue
        unique_events = self._deduplicate_and_filter_events(all_events, vendor)
        return unique_events[:max_results]

    def _generate_search_queries(self, vendor: Vendor, radius_km: int) -> List[str]:
        """Generate targeted search queries based on vendor info with refined location and business info."""
        location = vendor.Location.lower().strip()
        business_type = vendor.BusinessInfo.lower().strip()
        city = location.split(',')[-1].strip() if ',' in location else location

        # Base queries with precise location and business context
        queries = [
            f"upcoming food festivals {city} vendor opportunities 2024 2025",
            f"street food events {location} vendor registration",
            f"local markets {city} food stalls near me",
            f"community events {location} food vendors",
            f"{business_type} festivals {city} vendor application"
        ]

        # Business-specific query enhancements
        if any(word in business_type for word in ['vada pav', 'snacks', 'street food']):
            queries.extend([
                f"street food festival {city} vendor booth {business_type}",
                f"food truck events {location} {business_type}",
                f"cultural food events {city} {business_type} stalls"
            ])
        if any(word in business_type for word in ['juice', 'drinks', 'beverages']):
            queries.extend([
                f"summer festivals {city} beverage vendors {business_type}",
                f"outdoor markets {location} drink stalls",
                f"food and drink events {city} {business_type}"
            ])
        if any(word in business_type for word in ['college', 'university', 'student']):
            queries.extend([
                f"college fest {city} food vendors {business_type}",
                f"university events {location} vendor registration",
                f"student festivals {city} {business_type} stalls"
            ])

        # Add radius-based query for nearby locations
        if radius_km > 0:
            queries.append(f"food events near {location} within {radius_km}km vendor opportunities")

        return queries

    async def _process_event_result(self, result: dict, vendor: Vendor) -> Optional[EventResponse]:
        """Process a single search result into an event."""
        try:
            url = result.get('url', '')
            title = result.get('title', '')
            content = result.get('content', '')
            if not url or not title:
                return None
            if any(domain in url.lower() for domain in ['facebook.com', 'instagram.com', 'twitter.com']):
                return None
            relevance_score = self._calculate_relevance_score(title, content, vendor)
            if relevance_score < 8:  # Increased threshold for better quality
                return None
            event_details = await self._extract_event_details(url, title, content)
            if not event_details:
                return None
            return EventResponse(
                event_name=event_details['name'],
                description=event_details['description'],
                location=event_details['location'],
                contact_phone=event_details.get('phone'),
                stall_info=event_details['stall_info'],
                event_date=event_details.get('date'),
                source_url=url
            )
        except Exception as e:
            print(f"Error processing event result: {e}")
            return None

    def _calculate_relevance_score(self, title: str, content: str, vendor: Vendor) -> int:
        """Calculate relevance score for the vendor with enhanced location and business matching."""
        text = (title + " " + content).lower()
        score = 0
        vendor_keywords = ['vendor', 'stall', 'booth', 'food vendor', 'registration', 'application']
        score += sum(6 for keyword in vendor_keywords if keyword in text)  # Increased weight for vendor keywords
        event_keywords = ['festival', 'fair', 'celebration', 'fest', 'market', 'event']
        score += sum(4 for keyword in event_keywords if keyword in text)  # Increased weight for event keywords
        if vendor.Location.lower() in text:
            score += 15  # Higher weight for exact location match
        elif any(word in text for word in vendor.Location.lower().split(',')):
            score += 8  # Partial location match
        business_words = [word for word in vendor.BusinessInfo.lower().split() if len(word) > 3]
        score += sum(3 for word in business_words if word in text)  # Increased weight for business keywords
        if any(year in text for year in ['2024', '2025', '2026']):
            score += 5  # Include 2026 for future-proofing
        return score

    async def _extract_event_details(self, url: str, title: str, content: str) -> Optional[dict]:
        """Extract detailed event information using web scraping with improved location extraction."""
        try:
            response = self.session.get(url, timeout=8)  # Reduced timeout for faster processing
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
            phone_matches = re.findall(phone_pattern, soup.get_text())
            phone = phone_matches[0] if phone_matches else None
            date = self._extract_date_from_text(soup.get_text())
            location = self._extract_location_from_content(content, soup.get_text())
            stall_info = self._extract_stall_info(soup.get_text(), content)
            return {
                'name': title,
                'description': content[:250] + "..." if len(content) > 250 else content,  # Extended description length
                'location': location,
                'phone': phone,
                'date': date,
                'stall_info': stall_info
            }
        except Exception as e:
            return {
                'name': title,
                'description': content[:250] + "..." if len(content) > 250 else content,
                'location': self._extract_location_from_content(content, ""),
                'phone': None,
                'date': "Check website for dates",
                'stall_info': "Contact organizer for vendor registration details"
            }

    def _extract_date_from_text(self, text: str) -> str:
        """Extract date from text with additional patterns."""
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}',
            r'\b\d{1,2}/\d{1,2}/\d{4}',
            r'\b\d{1,2}-\d{1,2}-\d{4}',
            r'\b\d{4}-\d{2}-\d{2}'  # ISO date format
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Check website for dates"

    def _extract_location_from_content(self, content: str, full_text: str = "") -> str:
        """Extract location from content with refined patterns."""
        text = content + " " + full_text
        location_patterns = [
            r'\b\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Circle|Cir)\b',
            r'\b[\w\s]+,\s*[A-Z]{2}\s*\d{5}\b',
            r'\b[\w\s]+,\s*(?:Mumbai|Delhi|Bangalore|Chennai|Kolkata|Pune|Hyderabad|Ahmedabad|Jaipur|Lucknow)\b',
            r'\b(?:Mumbai|Delhi|Bangalore|Chennai|Kolkata|Pune|Hyderabad|Ahmedabad|Jaipur|Lucknow)\b'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Location details on website"

    def _extract_stall_info(self, full_text: str, content: str) -> str:
        """Extract stall/vendor information with more specific conditions."""
        text = (full_text + " " + content).lower()
        if 'vendor' in text and 'registration' in text:
            return "Vendor registration open - apply via website"
        elif 'stall' in text and 'booking' in text:
            return "Stall booking required - contact organizer"
        elif 'food' in text and 'vendor' in text:
            return "Food vendors welcome - check website for details"
        elif any(word in text for word in ['₹', 'rs.', 'fee', 'cost']):
            return "Vendor fees apply - see website for pricing"
        else:
            return "Contact event organizer for vendor opportunities"

    def _deduplicate_and_filter_events(self, events: List[EventResponse], vendor: Vendor) -> List[EventResponse]:
        """Remove duplicates and apply location-based filtering."""
        seen_urls = set()
        seen_names = set()
        unique_events = []
        for event in events:
            if (event.source_url in seen_urls or
                any(abs(len(event.event_name) - len(seen_name)) < 8 and
                    event.event_name.lower() in seen_name.lower() for seen_name in seen_names)):
                continue
            # Filter events by location proximity
            if vendor.Location.lower() in event.location.lower() or any(city in event.location.lower() for city in vendor.Location.lower().split(',')):
                seen_urls.add(event.source_url)
                seen_names.add(event.event_name)
                unique_events.append(event)
        return unique_events

# FastAPI Router with corrected prefix
event_router = APIRouter(prefix="/vendor-events", tags=["vendor-events"])

# Initialize the service with your Tavily API key
TAVILY_API_KEY = "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"  # Replace with your actual Tavily API key
event_service = EventDiscoveryService(TAVILY_API_KEY)
@event_router.get("/events", response_model=List[EventResponse])
async def get_vendor_events(
    vendor_id: str,
    radius_km: int = 50,
    max_results: int = 10,
    db: Session = Depends(get_db)
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # First try fetching from the DB
    db_events = db.query(VendorEvent).filter(
        VendorEvent.vendor_id == vendor_id
    ).all()

    filtered_events = [
        EventResponse(
            event_name=e.event_name,
            description=e.description,
            location=e.location,
            contact_phone=e.contact_phone,
            stall_info=e.stall_info,
            event_date=e.event_date,
            source_url=e.source_url,
            created_at=e.created_at,
        )
        for e in db_events if vendor.Location.lower() in e.location.lower() 
        or vendor.BusinessInfo.lower() in e.description.lower()
    ]

    if filtered_events:
        return filtered_events[:max_results]

    # If not found, call Tavily
    try:
        events = await event_service.find_vendor_events(
            vendor=vendor,
            radius_km=radius_km,
            max_results=max_results
        )

        # Save new events to DB
        for event in events:
            if not db.query(VendorEvent).filter_by(source_url=event.source_url).first():
                new_event = VendorEvent(
                    vendor_id=vendor_id,
                    event_name=event.event_name,
                    description=event.description,
                    location=event.location,
                    contact_phone=event.contact_phone,
                    stall_info=event.stall_info,
                    event_date=event.event_date,
                    source_url=event.source_url
                )
                db.add(new_event)
        db.commit()

        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding events: {str(e)}")



@event_router.get(
    "/events",
    response_model=List[VendorEventRead],          # or List[EventResponse] if you prefer
)
async def get_vendor_events(
    vendor_id: str,
    radius_km: int = 50,
    max_results: int = 10,
    db: Session = Depends(get_db),
):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    # 1️⃣ Try local cache first
    db_events = (
        db.query(VendorEvent)
          .filter(VendorEvent.vendor_id == vendor_id)
          .all()
    )

    # optional filtering logic
    filtered = [
        e for e in db_events
        if vendor.Location.lower() in e.location.lower()
           or vendor.BusinessInfo.lower() in e.description.lower()
    ]
    if filtered:
        return filtered[:max_results]

    # 2️⃣ Fallback to Tavily
    events = await event_service.find_vendor_events(vendor, radius_km, max_results)

    # 3️⃣ Persist any brand‑new events
    for ev in events:
        exists = (
            db.query(VendorEvent)
              .filter_by(source_url=ev.source_url)
              .first()
        )
        if not exists:
            db_event = VendorEvent(
                vendor_id=vendor_id,
                event_name=ev.event_name,
                description=ev.description,
                location=ev.location,
                contact_phone=ev.contact_phone,
                stall_info=ev.stall_info,
                event_date=ev.event_date,
                source_url=ev.source_url,
            )
            db.add(db_event)
    db.commit()

    return events
