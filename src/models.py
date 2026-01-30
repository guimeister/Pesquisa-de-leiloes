"""Data models for watch auction items."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class WatchItem:
    """Represents a watch item from an auction."""

    # Identification
    id: Optional[int] = None
    source_url: str = ""
    source_site: str = ""
    auction_id: str = ""

    # Pricing
    current_price: Optional[float] = None
    starting_price: Optional[float] = None
    currency: str = "BRL"

    # Structured description fields
    description: str = ""
    brand: str = ""
    year: Optional[int] = None
    model: str = ""
    specification: str = ""
    material: str = ""  # aço, aço e ouro, ouro, ouro rosa, etc
    weight: str = ""
    bracelet_material: str = ""  # material da pulseira

    # Additional info
    image_url: str = ""
    auction_end_date: Optional[datetime] = None
    lot_number: str = ""

    # Metadata
    scraped_at: datetime = field(default_factory=datetime.now)
    raw_description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        data = asdict(self)
        # Convert datetime to ISO string
        if data['auction_end_date']:
            data['auction_end_date'] = data['auction_end_date'].isoformat()
        data['scraped_at'] = data['scraped_at'].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'WatchItem':
        """Create instance from dictionary."""
        if data.get('auction_end_date') and isinstance(data['auction_end_date'], str):
            data['auction_end_date'] = datetime.fromisoformat(data['auction_end_date'])
        if data.get('scraped_at') and isinstance(data['scraped_at'], str):
            data['scraped_at'] = datetime.fromisoformat(data['scraped_at'])
        return cls(**data)
