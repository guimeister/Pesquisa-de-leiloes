#!/usr/bin/env python3
"""
Watch Auction Scraper CLI

Scrapes watch auction sites and provides a searchable database.
"""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.database import WatchDatabase
from src.scraper import run_scraper
from src.models import WatchItem

console = Console()


@click.group()
@click.option('--db', default='watches.db', help='Database file path')
@click.pass_context
def cli(ctx, db):
    """Watch Auction Scraper - Pesquisa de relógios em leilões."""
    ctx.ensure_object(dict)
    ctx.obj['db'] = WatchDatabase(db)


@cli.command()
@click.option('--max-pages', default=5, help='Maximum listing pages to scrape')
@click.option('--max-items', default=None, type=int, help='Maximum items to scrape')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.pass_context
def scrape(ctx, max_pages, max_items, headless):
    """Scrape watches from auction sites."""
    db: WatchDatabase = ctx.obj['db']

    console.print(Panel.fit(
        "[bold blue]Watch Auction Scraper[/bold blue]\n"
        f"Scraping leiloesbr.com.br (max {max_pages} pages)",
        border_style="blue"
    ))

    async def run():
        watches = await run_scraper(
            headless=headless,
            max_pages=max_pages,
            max_items=max_items
        )
        return watches

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping watches...", total=None)

        try:
            watches = asyncio.run(run())
        except Exception as e:
            console.print(f"[red]Error during scraping: {e}[/red]")
            return

        progress.update(task, description="Saving to database...")

        saved = db.insert_many(watches)

    console.print(f"\n[green]Scraped {len(watches)} watches, saved {saved} new entries.[/green]")

    # Show summary
    stats = db.get_stats()
    console.print(f"\nDatabase now contains [bold]{stats['total_watches']}[/bold] watches")


@cli.command()
@click.option('-q', '--query', default=None, help='Full-text search query')
@click.option('-b', '--brand', default=None, help='Filter by brand')
@click.option('-m', '--material', default=None, help='Filter by material')
@click.option('--min-price', default=None, type=float, help='Minimum price')
@click.option('--max-price', default=None, type=float, help='Maximum price')
@click.option('--year-from', default=None, type=int, help='Year from')
@click.option('--year-to', default=None, type=int, help='Year to')
@click.option('--limit', default=20, help='Maximum results')
@click.pass_context
def search(ctx, query, brand, material, min_price, max_price, year_from, year_to, limit):
    """Search for watches in the database."""
    db: WatchDatabase = ctx.obj['db']

    results = db.search(
        query=query,
        brand=brand,
        material=material,
        min_price=min_price,
        max_price=max_price,
        year_from=year_from,
        year_to=year_to,
        limit=limit
    )

    if not results:
        console.print("[yellow]No watches found matching your criteria.[/yellow]")
        return

    table = Table(title=f"Found {len(results)} watches")
    table.add_column("ID", style="dim")
    table.add_column("Brand", style="cyan")
    table.add_column("Model")
    table.add_column("Material", style="green")
    table.add_column("Price", style="yellow", justify="right")
    table.add_column("Year")
    table.add_column("Description", max_width=40)

    for watch in results:
        price_str = f"R$ {watch.current_price:,.2f}" if watch.current_price else "-"
        year_str = str(watch.year) if watch.year else "-"

        table.add_row(
            str(watch.id),
            watch.brand or "-",
            watch.model or "-",
            watch.material or "-",
            price_str,
            year_str,
            (watch.description[:37] + "...") if len(watch.description) > 40 else watch.description
        )

    console.print(table)


@cli.command()
@click.argument('watch_id', type=int)
@click.pass_context
def show(ctx, watch_id):
    """Show detailed information about a watch."""
    db: WatchDatabase = ctx.obj['db']

    watch = db.get_by_id(watch_id)

    if not watch:
        console.print(f"[red]Watch with ID {watch_id} not found.[/red]")
        return

    price_str = f"R$ {watch.current_price:,.2f}" if watch.current_price else "N/A"

    panel_content = f"""
[bold cyan]Brand:[/bold cyan] {watch.brand or 'N/A'}
[bold cyan]Model:[/bold cyan] {watch.model or 'N/A'}
[bold cyan]Year:[/bold cyan] {watch.year or 'N/A'}

[bold green]Material:[/bold green] {watch.material or 'N/A'}
[bold green]Bracelet:[/bold green] {watch.bracelet_material or 'N/A'}
[bold green]Weight:[/bold green] {watch.weight or 'N/A'}

[bold yellow]Price:[/bold yellow] {price_str}
[bold yellow]Lot:[/bold yellow] {watch.lot_number or 'N/A'}

[bold]Specification:[/bold]
{watch.specification or 'N/A'}

[bold]Description:[/bold]
{watch.description}

[bold]Full Description:[/bold]
{watch.raw_description or 'N/A'}

[dim]Source: {watch.source_url}[/dim]
"""

    console.print(Panel(
        panel_content,
        title=f"Watch #{watch.id}",
        border_style="blue"
    ))


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    db: WatchDatabase = ctx.obj['db']

    stats = db.get_stats()
    brands = db.get_all_brands()
    materials = db.get_all_materials()

    console.print(Panel.fit(
        f"""
[bold]Database Statistics[/bold]

Total watches: [cyan]{stats['total_watches']}[/cyan]
Unique brands: [cyan]{stats['unique_brands']}[/cyan]

[bold]Prices (BRL):[/bold]
  Min: [green]R$ {stats['min_price']:,.2f}[/green]
  Max: [green]R$ {stats['max_price']:,.2f}[/green]
  Avg: [green]R$ {stats['avg_price']:,.2f}[/green]

[bold]Brands found:[/bold]
{', '.join(brands[:15])}{'...' if len(brands) > 15 else ''}

[bold]Materials found:[/bold]
{', '.join(materials)}
""",
        title="Statistics",
        border_style="blue"
    ))


@cli.command()
@click.pass_context
def brands(ctx):
    """List all brands in the database."""
    db: WatchDatabase = ctx.obj['db']

    brands = db.get_all_brands()

    if not brands:
        console.print("[yellow]No brands found in database.[/yellow]")
        return

    table = Table(title="Brands in Database")
    table.add_column("Brand", style="cyan")
    table.add_column("Count", justify="right")

    for brand in brands:
        count = db.count(brand=brand)
        table.add_row(brand, str(count))

    console.print(table)


@cli.command()
@click.pass_context
def materials(ctx):
    """List all materials in the database."""
    db: WatchDatabase = ctx.obj['db']

    materials = db.get_all_materials()

    if not materials:
        console.print("[yellow]No materials found in database.[/yellow]")
        return

    table = Table(title="Materials in Database")
    table.add_column("Material", style="green")
    table.add_column("Count", justify="right")

    for material in materials:
        count = db.count(material=material)
        table.add_row(material, str(count))

    console.print(table)


@cli.command()
@click.option('--format', 'fmt', type=click.Choice(['csv', 'json']), default='csv')
@click.option('-o', '--output', default='watches_export', help='Output filename (without extension)')
@click.pass_context
def export(ctx, fmt, output):
    """Export database to CSV or JSON."""
    import json
    import csv

    db: WatchDatabase = ctx.obj['db']

    watches = db.search(limit=999999)

    if not watches:
        console.print("[yellow]No watches to export.[/yellow]")
        return

    filename = f"{output}.{fmt}"

    if fmt == 'json':
        with open(filename, 'w', encoding='utf-8') as f:
            data = [w.to_dict() for w in watches]
            json.dump(data, f, ensure_ascii=False, indent=2)

    elif fmt == 'csv':
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'brand', 'model', 'year', 'material', 'bracelet_material',
                'weight', 'specification', 'current_price', 'description',
                'source_url', 'image_url', 'lot_number', 'scraped_at'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for watch in watches:
                data = watch.to_dict()
                row = {k: data.get(k, '') for k in fieldnames}
                writer.writerow(row)

    console.print(f"[green]Exported {len(watches)} watches to {filename}[/green]")


if __name__ == '__main__':
    cli()
