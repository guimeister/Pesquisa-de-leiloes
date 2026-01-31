#!/usr/bin/env python3
"""
Flask web application for Watch Auction Scraper.
"""

import asyncio
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
import json

from src.database import WatchDatabase
from src.scraper import run_scraper

app = Flask(__name__)
db = WatchDatabase("watches.db")

# Scraping status
scraping_status = {
    "is_running": False,
    "progress": 0,
    "message": "",
    "items_found": 0
}


# ==================== Pages ====================

@app.route('/')
def index():
    """Home page with search interface."""
    stats = db.get_stats()
    brands = db.get_all_brands()
    materials = db.get_all_materials()
    return render_template('index.html', stats=stats, brands=brands, materials=materials)


@app.route('/watch/<int:watch_id>')
def watch_detail(watch_id):
    """Watch detail page."""
    watch = db.get_by_id(watch_id)
    if not watch:
        return render_template('404.html'), 404
    return render_template('detail.html', watch=watch)


@app.route('/scraper')
def scraper_page():
    """Scraper control page."""
    return render_template('scraper.html', status=scraping_status)


# ==================== API ====================

@app.route('/api/search')
def api_search():
    """API endpoint for searching watches."""
    query = request.args.get('q', None)
    brand = request.args.get('brand', None)
    material = request.args.get('material', None)
    min_price = request.args.get('min_price', None, type=float)
    max_price = request.args.get('max_price', None, type=float)
    year_from = request.args.get('year_from', None, type=int)
    year_to = request.args.get('year_to', None, type=int)
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    results = db.search(
        query=query if query else None,
        brand=brand if brand else None,
        material=material if material else None,
        min_price=min_price,
        max_price=max_price,
        year_from=year_from,
        year_to=year_to,
        limit=limit,
        offset=offset
    )

    return jsonify({
        "count": len(results),
        "results": [w.to_dict() for w in results]
    })


@app.route('/api/watch/<int:watch_id>')
def api_watch(watch_id):
    """API endpoint for getting a single watch."""
    watch = db.get_by_id(watch_id)
    if not watch:
        return jsonify({"error": "Watch not found"}), 404
    return jsonify(watch.to_dict())


@app.route('/api/stats')
def api_stats():
    """API endpoint for database statistics."""
    stats = db.get_stats()
    brands = db.get_all_brands()
    materials = db.get_all_materials()
    return jsonify({
        "stats": stats,
        "brands": brands,
        "materials": materials
    })


@app.route('/api/brands')
def api_brands():
    """API endpoint for listing all brands."""
    brands = db.get_all_brands()
    brand_counts = []
    for brand in brands:
        count = db.count(brand=brand)
        brand_counts.append({"name": brand, "count": count})
    return jsonify(brand_counts)


@app.route('/api/materials')
def api_materials():
    """API endpoint for listing all materials."""
    materials = db.get_all_materials()
    material_counts = []
    for material in materials:
        count = db.count(material=material)
        material_counts.append({"name": material, "count": count})
    return jsonify(material_counts)


@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint to start scraping."""
    global scraping_status

    if scraping_status["is_running"]:
        return jsonify({"error": "Scraping already in progress"}), 400

    max_pages = request.json.get('max_pages', 5) if request.json else 5
    max_items = request.json.get('max_items', None) if request.json else None

    def run_scraping():
        global scraping_status
        scraping_status["is_running"] = True
        scraping_status["progress"] = 0
        scraping_status["message"] = "Starting scraper..."
        scraping_status["items_found"] = 0

        try:
            async def scrape():
                watches = await run_scraper(
                    headless=True,
                    max_pages=max_pages,
                    max_items=max_items
                )
                return watches

            watches = asyncio.run(scrape())

            scraping_status["message"] = "Saving to database..."
            saved = db.insert_many(watches)

            scraping_status["items_found"] = len(watches)
            scraping_status["message"] = f"Completed! Found {len(watches)} watches, saved {saved} new."
            scraping_status["progress"] = 100

        except Exception as e:
            scraping_status["message"] = f"Error: {str(e)}"

        finally:
            scraping_status["is_running"] = False

    thread = threading.Thread(target=run_scraping)
    thread.start()

    return jsonify({"status": "started"})


@app.route('/api/scrape/status')
def api_scrape_status():
    """API endpoint to check scraping status."""
    return jsonify(scraping_status)


@app.route('/api/export/<format>')
def api_export(format):
    """API endpoint to export data."""
    watches = db.search(limit=999999)

    if format == 'json':
        data = json.dumps([w.to_dict() for w in watches], ensure_ascii=False, indent=2)
        return Response(
            data,
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment;filename=watches_export.json'}
        )

    elif format == 'csv':
        import csv
        from io import StringIO

        output = StringIO()
        fieldnames = [
            'id', 'brand', 'model', 'year', 'material', 'bracelet_material',
            'weight', 'specification', 'current_price', 'description',
            'source_url', 'image_url', 'lot_number', 'scraped_at'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for watch in watches:
            data = watch.to_dict()
            row = {k: data.get(k, '') for k in fieldnames}
            writer.writerow(row)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=watches_export.csv'}
        )

    return jsonify({"error": "Invalid format"}), 400


# ==================== Template Filters ====================

@app.template_filter('currency')
def currency_filter(value):
    """Format value as Brazilian currency."""
    if value is None:
        return "N/A"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value:
        return value.strftime("%d/%m/%Y %H:%M")
    return "N/A"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
