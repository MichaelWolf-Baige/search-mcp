"""CLI interface for search tool"""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from search_tool import __version__
from search_tool.api import (
    search,
    search_web,
    search_news,
    search_social,
    get_latest_news,
    list_available_engines,
)
from search_tool.utils.formatter import format_results, print_results
from search_tool.utils.auth import export_cookies_help


console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Search Tool - Personal quick search utility

    Search across web, news, and social media.
    """
    pass


@cli.command()
@click.argument("query", required=False)
@click.option(
    "--engine", "-e",
    default="search",
    type=click.Choice(["search", "news", "social", "all"]),
    help="Engine type to use",
)
@click.option(
    "--platform", "-p",
    default=None,
    help="Specific platform (weibo, reddit, hackernews, etc.)",
)
@click.option(
    "--limit", "-n",
    default=10,
    help="Maximum number of results",
)
@click.option(
    "--format", "-f",
    default="table",
    type=click.Choice(["table", "json", "simple"]),
    help="Output format",
)
def search_cmd(query, engine, platform, limit, format):
    """Search for information"""
    if not query:
        console.print("[red]Error: Please provide a search query[/red]")
        return

    console.print(f"\n[bold cyan]Searching for:[/bold cyan] {query}")
    console.print(f"[dim]Engine: {engine}, Platform: {platform or 'all'}, Limit: {limit}[/dim]\n")

    # Perform search
    engines = [engine] if engine != "all" else ["search", "news", "social"]

    with console.status("[bold green]Searching..."):
        results = search(
            query=query,
            engines=engines,
            limit=limit,
            platform=platform,
        )

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    # Display results
    if format == "table":
        _display_table(results)
    elif format == "json":
        output = format_results(results, query, "json")
        console.print(output)
    else:
        output = format_results(results, query, "simple")
        console.print(output)


@cli.command()
@click.argument("query", required=False)
@click.option("--limit", "-n", default=10, help="Number of results")
def web(query, limit):
    """Quick web search"""
    if not query:
        query = Prompt.ask("Enter search query")

    with console.status("[bold green]Searching web..."):
        results = search_web(query, limit)

    _display_results(results, query)


@cli.command()
@click.argument("query", required=False)
@click.option("--limit", "-n", default=10, help="Number of results")
@click.option("--source", "-s", default=None, help="News source")
def news(query, limit, source):
    """Search news"""
    if source and not query:
        # Get latest news from source
        with console.status(f"[bold green]Fetching news from {source}..."):
            results = get_latest_news(source, limit)
        _display_results(results, f"Latest from {source}")
    else:
        if not query:
            query = Prompt.ask("Enter search query")

        with console.status("[bold green]Searching news..."):
            results = search_news(query, limit)
        _display_results(results, query)


@cli.command()
@click.argument("query", required=False)
@click.option("--limit", "-n", default=10, help="Number of results")
@click.option("--platform", "-p", default=None, help="Social platform (weibo, reddit, hackernews, nitter, zhihu)")
def social(query, limit, platform):
    """Search social media"""
    if not query:
        query = Prompt.ask("Enter search query")

    with console.status(f"[bold green]Searching social media{f' ({platform})' if platform else ''}..."):
        results = search_social(query, limit, platform)

    _display_results(results, query)


@cli.command()
@click.option("--source", "-s", default=None, help="Specific news source")
@click.option("--limit", "-n", default=20, help="Number of results")
def latest(source, limit):
    """Get latest news headlines"""
    with console.status("[bold green]Fetching latest news..."):
        results = get_latest_news(source, limit)

    _display_results(results, "Latest News")


@cli.command()
def interactive():
    """Start interactive search mode"""
    console.print(Panel.fit(
        "[bold cyan]Search Tool - Interactive Mode[/bold cyan]\n"
        "Type your query to search. Commands: :q (quit), :help, :engines",
        title="Search Tool",
    ))

    while True:
        console.print()
        query = Prompt.ask("[bold cyan]Search[/bold cyan]")

        if query.lower() in [":q", ":quit", "exit", "quit"]:
            console.print("[dim]Goodbye![/dim]")
            break

        if query.lower() == ":help":
            _show_help()
            continue

        if query.lower() == ":engines":
            _show_engines()
            continue

        if query.startswith(":"):
            console.print("[red]Unknown command. Type :help for help.[/red]")
            continue

        # Perform search
        with console.status("[bold green]Searching..."):
            results = search(query, engines=["search", "news"], limit=5)

        if results:
            _display_table(results)
        else:
            console.print("[yellow]No results found[/yellow]")


@cli.command()
def engines():
    """List available engines and platforms"""
    _show_engines()


@cli.command()
def cookies_help():
    """Show help for exporting cookies"""
    export_cookies_help()


def _display_results(results, query):
    """Display search results"""
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    _display_table(results)


def _display_table(results):
    """Display results in a rich table"""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", width=50)
    table.add_column("Platform", width=12)
    table.add_column("Source", width=8)

    for i, result in enumerate(results, 1):
        # Truncate title if too long
        title = result.title[:47] + "..." if len(result.title) > 50 else result.title
        table.add_row(
            str(i),
            title,
            result.platform,
            result.source,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(results)} results[/dim]")

    # Show details option
    console.print("[dim]Tip: Use --format json for full details[/dim]")


def _show_help():
    """Show help message"""
    console.print("""
[bold]Commands:[/bold]
  :q, :quit    Exit interactive mode
  :help        Show this help
  :engines     List available engines

[bold]Tips:[/bold]
  - Search queries are sent to multiple engines by default
  - Use specific engines with CLI options: --engine news
  - Use specific platforms with: --platform weibo
""")


def _show_engines():
    """Show available engines"""
    engines_dict = list_available_engines()

    console.print("\n[bold cyan]Available Engines:[/bold cyan]\n")

    for engine_type, platforms in engines_dict.items():
        console.print(f"[bold]{engine_type.upper()}[/bold]")
        for p in platforms:
            console.print(f"  - {p}")
        console.print()


# Create shorter aliases
@cli.command("s")
@click.pass_context
def search_short(ctx, **kwargs):
    """Short alias for search"""
    ctx.forward(search_cmd)


# Main entry point
if __name__ == "__main__":
    cli()