"""Web scraper for watch auction sites using Playwright."""

import asyncio
import re
import time
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Page, Browser

from .models import WatchItem
from .parser import WatchDescriptionParser


class LeiloesBRScraper:
    """Scraper for leiloesbr.com.br watch auctions."""

    BASE_URL = "https://www.leiloesbr.com.br"
    WATCHES_URL = f"{BASE_URL}/joalheria/relogios"

    def __init__(self, headless: bool = True, slow_mo: int = 100):
        self.headless = headless
        self.slow_mo = slow_mo
        self.parser = WatchDescriptionParser()
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """Start the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _create_page(self) -> Page:
        """Create a new page with realistic browser settings."""
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
        )
        page = await context.new_page()
        return page

    async def scrape_listing_page(self, page: Page, url: str) -> List[dict]:
        """Scrape a listing page and return basic item info."""
        items = []

        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)  # Wait for dynamic content

        # Try different selectors that might match the site structure
        selectors = [
            ".product-item",
            ".item-lote",
            ".lote",
            "[class*='product']",
            "[class*='item']",
            ".card",
            "article",
        ]

        item_elements = []
        for selector in selectors:
            item_elements = await page.query_selector_all(selector)
            if item_elements:
                break

        for element in item_elements:
            try:
                item = {}

                # Try to get the link
                link = await element.query_selector("a")
                if link:
                    href = await link.get_attribute("href")
                    if href:
                        item["url"] = urljoin(self.BASE_URL, href)

                # Try to get title/description
                for title_sel in [".title", "h2", "h3", ".name", ".description"]:
                    title_el = await element.query_selector(title_sel)
                    if title_el:
                        item["title"] = await title_el.text_content()
                        break

                # Try to get price
                for price_sel in [".price", ".valor", "[class*='price']", "[class*='valor']"]:
                    price_el = await element.query_selector(price_sel)
                    if price_el:
                        price_text = await price_el.text_content()
                        item["price_text"] = price_text
                        break

                # Try to get image
                img = await element.query_selector("img")
                if img:
                    item["image"] = await img.get_attribute("src")

                if item.get("url"):
                    items.append(item)

            except Exception as e:
                print(f"Error extracting item: {e}")
                continue

        return items

    async def scrape_detail_page(self, page: Page, url: str) -> Optional[WatchItem]:
        """Scrape a product detail page."""
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(1)

            watch = WatchItem(source_url=url, source_site="leiloesbr.com.br")

            # Get full description
            desc_selectors = [
                ".product-description",
                ".description",
                ".descricao",
                ".lote-description",
                "[class*='description']",
                ".content",
            ]

            for selector in desc_selectors:
                desc_el = await page.query_selector(selector)
                if desc_el:
                    watch.raw_description = await desc_el.text_content()
                    watch.raw_description = watch.raw_description.strip()
                    break

            # Get title
            title_selectors = ["h1", ".product-title", ".title", ".nome"]
            for selector in title_selectors:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.text_content()
                    if title:
                        watch.description = title.strip()
                        break

            # Get price
            price_selectors = [
                ".current-bid",
                ".lance-atual",
                ".price",
                ".valor",
                "[class*='price']",
                "[class*='valor']",
                "[class*='lance']",
            ]

            for selector in price_selectors:
                price_el = await page.query_selector(selector)
                if price_el:
                    price_text = await price_el.text_content()
                    watch.current_price = self._parse_price(price_text)
                    if watch.current_price:
                        break

            # Get image
            img_selectors = [
                ".product-image img",
                ".gallery img",
                ".image img",
                "img[class*='product']",
                "img[class*='main']",
            ]

            for selector in img_selectors:
                img_el = await page.query_selector(selector)
                if img_el:
                    watch.image_url = await img_el.get_attribute("src")
                    if watch.image_url:
                        watch.image_url = urljoin(self.BASE_URL, watch.image_url)
                        break

            # Get lot number
            lot_selectors = [".lot-number", ".lote-numero", "[class*='lote']"]
            for selector in lot_selectors:
                lot_el = await page.query_selector(selector)
                if lot_el:
                    lot_text = await lot_el.text_content()
                    lot_match = re.search(r'(\d+)', lot_text)
                    if lot_match:
                        watch.lot_number = lot_match.group(1)
                        break

            # Parse structured data from description
            full_text = f"{watch.description} {watch.raw_description}"
            parsed = self.parser.parse(full_text)

            watch.brand = parsed.get("brand", "")
            watch.year = parsed.get("year")
            watch.model = parsed.get("model", "")
            watch.specification = parsed.get("specification", "")
            watch.material = parsed.get("material", "")
            watch.weight = parsed.get("weight", "")
            watch.bracelet_material = parsed.get("bracelet_material", "")

            return watch

        except Exception as e:
            print(f"Error scraping detail page {url}: {e}")
            return None

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text like 'R$ 1.234,56'."""
        if not price_text:
            return None

        # Remove currency symbol and whitespace
        cleaned = re.sub(r'[R$\s]', '', price_text)
        # Handle Brazilian format: 1.234,56 -> 1234.56
        cleaned = cleaned.replace('.', '').replace(',', '.')

        try:
            return float(cleaned)
        except ValueError:
            return None

    async def scrape_all(
        self,
        max_pages: int = 5,
        max_items: Optional[int] = None,
        callback=None
    ) -> List[WatchItem]:
        """
        Scrape all watches from the site.

        Args:
            max_pages: Maximum number of listing pages to scrape
            max_items: Maximum number of items to scrape (None for unlimited)
            callback: Optional callback(watch) called for each scraped item

        Returns:
            List of WatchItem objects
        """
        watches = []
        page = await self._create_page()

        try:
            # Collect all item URLs first
            all_items = []
            current_url = self.WATCHES_URL

            for page_num in range(1, max_pages + 1):
                print(f"Scraping listing page {page_num}...")

                if page_num > 1:
                    current_url = f"{self.WATCHES_URL}?page={page_num}"

                items = await self.scrape_listing_page(page, current_url)

                if not items:
                    print(f"No items found on page {page_num}, stopping.")
                    break

                all_items.extend(items)
                print(f"Found {len(items)} items on page {page_num}")

                if max_items and len(all_items) >= max_items:
                    all_items = all_items[:max_items]
                    break

                await asyncio.sleep(1)  # Rate limiting

            # Now scrape each detail page
            print(f"\nScraping {len(all_items)} item detail pages...")

            for i, item in enumerate(all_items):
                if not item.get("url"):
                    continue

                print(f"[{i+1}/{len(all_items)}] Scraping: {item.get('url', 'unknown')}")

                watch = await self.scrape_detail_page(page, item["url"])

                if watch:
                    watches.append(watch)
                    if callback:
                        callback(watch)

                await asyncio.sleep(0.5)  # Rate limiting

        finally:
            await page.context.close()

        return watches


async def run_scraper(
    headless: bool = True,
    max_pages: int = 5,
    max_items: Optional[int] = None
) -> List[WatchItem]:
    """Run the scraper and return results."""
    async with LeiloesBRScraper(headless=headless) as scraper:
        return await scraper.scrape_all(
            max_pages=max_pages,
            max_items=max_items
        )
