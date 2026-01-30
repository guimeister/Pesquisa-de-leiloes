"""Database operations for storing and searching watch items."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import WatchItem


class WatchDatabase:
    """SQLite database for watch auction items."""

    def __init__(self, db_path: str = "watches.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT UNIQUE,
                    source_site TEXT,
                    auction_id TEXT,

                    current_price REAL,
                    starting_price REAL,
                    currency TEXT DEFAULT 'BRL',

                    description TEXT,
                    brand TEXT,
                    year INTEGER,
                    model TEXT,
                    specification TEXT,
                    material TEXT,
                    weight TEXT,
                    bracelet_material TEXT,

                    image_url TEXT,
                    auction_end_date TEXT,
                    lot_number TEXT,

                    scraped_at TEXT,
                    raw_description TEXT
                )
            """)

            # Create indexes for common search fields
            conn.execute("CREATE INDEX IF NOT EXISTS idx_brand ON watches(brand)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_material ON watches(material)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON watches(year)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price ON watches(current_price)")

            # Full-text search table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS watches_fts USING fts5(
                    description,
                    brand,
                    model,
                    specification,
                    material,
                    content='watches',
                    content_rowid='id'
                )
            """)

            # Triggers to keep FTS in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS watches_ai AFTER INSERT ON watches BEGIN
                    INSERT INTO watches_fts(rowid, description, brand, model, specification, material)
                    VALUES (new.id, new.description, new.brand, new.model, new.specification, new.material);
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS watches_ad AFTER DELETE ON watches BEGIN
                    INSERT INTO watches_fts(watches_fts, rowid, description, brand, model, specification, material)
                    VALUES ('delete', old.id, old.description, old.brand, old.model, old.specification, old.material);
                END
            """)

            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS watches_au AFTER UPDATE ON watches BEGIN
                    INSERT INTO watches_fts(watches_fts, rowid, description, brand, model, specification, material)
                    VALUES ('delete', old.id, old.description, old.brand, old.model, old.specification, old.material);
                    INSERT INTO watches_fts(rowid, description, brand, model, specification, material)
                    VALUES (new.id, new.description, new.brand, new.model, new.specification, new.material);
                END
            """)

            conn.commit()

    def insert(self, watch: WatchItem) -> int:
        """Insert a watch item, returns the ID."""
        data = watch.to_dict()
        del data['id']  # Let DB auto-generate

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO watches (
                    source_url, source_site, auction_id,
                    current_price, starting_price, currency,
                    description, brand, year, model, specification,
                    material, weight, bracelet_material,
                    image_url, auction_end_date, lot_number,
                    scraped_at, raw_description
                ) VALUES (
                    :source_url, :source_site, :auction_id,
                    :current_price, :starting_price, :currency,
                    :description, :brand, :year, :model, :specification,
                    :material, :weight, :bracelet_material,
                    :image_url, :auction_end_date, :lot_number,
                    :scraped_at, :raw_description
                )
            """, data)
            conn.commit()
            return cursor.lastrowid

    def insert_many(self, watches: List[WatchItem]) -> int:
        """Insert multiple watches, returns count inserted."""
        count = 0
        for watch in watches:
            try:
                self.insert(watch)
                count += 1
            except sqlite3.IntegrityError:
                pass  # Skip duplicates
        return count

    def search(
        self,
        query: Optional[str] = None,
        brand: Optional[str] = None,
        material: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WatchItem]:
        """Search for watches with various filters."""
        conditions = []
        params = {}

        if query:
            conditions.append("id IN (SELECT rowid FROM watches_fts WHERE watches_fts MATCH :query)")
            params['query'] = query

        if brand:
            conditions.append("LOWER(brand) LIKE :brand")
            params['brand'] = f"%{brand.lower()}%"

        if material:
            conditions.append("LOWER(material) LIKE :material")
            params['material'] = f"%{material.lower()}%"

        if min_price is not None:
            conditions.append("current_price >= :min_price")
            params['min_price'] = min_price

        if max_price is not None:
            conditions.append("current_price <= :max_price")
            params['max_price'] = max_price

        if year_from is not None:
            conditions.append("year >= :year_from")
            params['year_from'] = year_from

        if year_to is not None:
            conditions.append("year <= :year_to")
            params['year_to'] = year_to

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params['limit'] = limit
        params['offset'] = offset

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT * FROM watches
                WHERE {where_clause}
                ORDER BY scraped_at DESC
                LIMIT :limit OFFSET :offset
            """, params)

            return [WatchItem.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_by_id(self, watch_id: int) -> Optional[WatchItem]:
        """Get a watch by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM watches WHERE id = ?", (watch_id,))
            row = cursor.fetchone()
            if row:
                return WatchItem.from_dict(dict(row))
        return None

    def get_all_brands(self) -> List[str]:
        """Get all unique brands."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT brand FROM watches
                WHERE brand != '' ORDER BY brand
            """)
            return [row[0] for row in cursor.fetchall()]

    def get_all_materials(self) -> List[str]:
        """Get all unique materials."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT material FROM watches
                WHERE material != '' ORDER BY material
            """)
            return [row[0] for row in cursor.fetchall()]

    def get_stats(self) -> dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM watches").fetchone()[0]
            brands = conn.execute("SELECT COUNT(DISTINCT brand) FROM watches WHERE brand != ''").fetchone()[0]
            avg_price = conn.execute("SELECT AVG(current_price) FROM watches WHERE current_price > 0").fetchone()[0]
            min_price = conn.execute("SELECT MIN(current_price) FROM watches WHERE current_price > 0").fetchone()[0]
            max_price = conn.execute("SELECT MAX(current_price) FROM watches WHERE current_price > 0").fetchone()[0]

            return {
                "total_watches": total,
                "unique_brands": brands,
                "avg_price": avg_price or 0,
                "min_price": min_price or 0,
                "max_price": max_price or 0,
            }

    def count(self, **filters) -> int:
        """Count watches matching filters."""
        results = self.search(limit=999999, **filters)
        return len(results)
