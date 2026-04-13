"""Command-line interface for kakao2notion"""

import click
import sys
from pathlib import Path
from typing import Optional
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .config import ConfigManager
from .parser import parse_kakaotalk_messages, Message
from .vectorizer import Vectorizer
from .clusterer import KNNClusterer
from .merger import MessageMerger
from .notion_client import NotionClient
from .llm import get_llm_provider

console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """KakaoTalk → Notion converter with intelligent clustering

    Run without arguments for interactive mode:
        kakao2notion

    Or use specific commands:
        kakao2notion process input.json
        kakao2notion upload input.json --database-id ID
        kakao2notion configure
    """
    # If no command provided, run interactive mode
    if ctx.invoked_subcommand is None:
        from .interactive import run_interactive
        run_interactive()


@cli.command()
@click.option(
    "--api-key",
    prompt="Enter your Notion API key",
    hide_input=True,
    help="Notion API token",
)
@click.option(
    "--llm-provider",
    default="codex",
    type=click.Choice(["codex", "claude"]),
    help="LLM provider for category naming",
)
def configure(api_key: str, llm_provider: str):
    """Configure kakao2notion"""
    config_manager = ConfigManager()

    config_manager.update_config(
        notion_api_key=api_key,
        llm_provider=llm_provider,
    )

    console.print("[green]✓ Configuration saved[/green]")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--format",
    default="auto",
    type=click.Choice(["json", "txt", "auto"]),
    help="Input file format",
)
@click.option(
    "--n-clusters",
    default=None,
    type=int,
    help="Number of clusters (if not set, auto-calculate)",
)
@click.option(
    "--auto-clusters",
    is_flag=True,
    default=False,
    help="Automatically find optimal number of clusters",
)
@click.option(
    "--cluster-method",
    type=click.Choice(["silhouette", "davies_bouldin", "calinski", "elbow", "ensemble"]),
    default="silhouette",
    help="Method for finding optimal clusters",
)
@click.option(
    "--similarity-threshold",
    default=0.7,
    type=float,
    help="Message merge similarity threshold (0-1)",
)
@click.option(
    "--use-llm",
    default=True,
    is_flag=True,
    help="Use LLM to generate category names",
)
@click.option(
    "--output",
    default=None,
    type=click.Path(),
    help="Output file for processed messages (JSON)",
)
def process(
    input_file: str,
    format: str,
    n_clusters: Optional[int],
    auto_clusters: bool,
    cluster_method: str,
    similarity_threshold: float,
    use_llm: bool,
    output: Optional[str],
):
    """Process KakaoTalk messages: vectorize, cluster, and optionally merge"""
    input_path = Path(input_file)

    with console.status("[bold green]Processing..."):
        # Step 1: Parse messages
        console.print(f"[cyan]Parsing messages from {input_file}...[/cyan]")
        messages = parse_kakaotalk_messages(input_path, format=format)
        console.print(f"[green]✓ Loaded {len(messages)} messages[/green]")

        # Step 2: Merge similar messages
        console.print("[cyan]Merging similar messages...[/cyan]")
        vectorizer = Vectorizer(model_type="tfidf")
        texts = [m.content for m in messages]
        vectorizer.fit(texts)

        merger = MessageMerger(vectorizer, similarity_threshold)
        merged_messages = merger.merge_messages(messages)
        console.print(f"[green]✓ Merged to {len(merged_messages)} messages[/green]")

        # Step 3: Determine optimal clusters
        merged_texts = [m.content for m in merged_messages]
        vectors = vectorizer.fit_transform(merged_texts)

        if auto_clusters:
            console.print("[cyan]Finding optimal number of clusters...[/cyan]")
            if cluster_method == "ensemble":
                clusterer = KNNClusterer(random_state=42)
                optimal_k, results = clusterer.find_optimal_clusters_ensemble(vectors)
                console.print(f"[green]✓ Ensemble voting results: {results}[/green]")
                n_clusters = optimal_k
            else:
                clusterer = KNNClusterer(random_state=42)
                n_clusters = clusterer.find_optimal_clusters(
                    vectors,
                    method=cluster_method
                )
            console.print(f"[green]✓ Optimal clusters: {n_clusters}[/green]")
        else:
            if n_clusters is None:
                # Quick estimate based on data size
                clusterer = KNNClusterer(random_state=42)
                n_clusters = clusterer.estimate_optimal_clusters_by_size(len(merged_messages))
                console.print(f"[cyan]Using estimated optimal clusters: {n_clusters}[/cyan]")

        # Step 4: Cluster
        console.print(f"[cyan]Clustering into {n_clusters} categories...[/cyan]")
        clusterer = KNNClusterer(n_clusters=n_clusters)
        clusterer.fit(vectors)

        clusters = clusterer.get_clusters()
        quality = clusterer.get_cluster_quality_report()
        console.print(f"[green]✓ Created {len(clusters)} clusters[/green]")
        console.print(f"[cyan]  Silhouette Score: {quality['silhouette_score']} ({quality['quality_interpretation']})[/cyan]")

        # Step 4: Generate category names
        if use_llm:
            console.print("[cyan]Generating category names with LLM...[/cyan]")
            config = ConfigManager()
            try:
                llm = get_llm_provider(
                    provider=config.config.llm_provider,
                    model=config.config.llm_model,
                )

                for cluster in clusters:
                    cluster_messages = [merged_messages[i] for i in cluster.indices]
                    name, desc = llm.generate_category_name(cluster_messages)
                    cluster.category_name = name
                    cluster.category_description = desc

                console.print("[green]✓ Generated category names[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ LLM generation failed: {e}[/yellow]")
                console.print("[cyan]Using default category names[/cyan]")
                for i, cluster in enumerate(clusters):
                    cluster.category_name = f"Category {i + 1}"
                    cluster.category_description = f"{len(cluster)} items"

    # Display results
    table = Table(title="Clustering Results")
    table.add_column("Category", style="cyan")
    table.add_column("Items", style="green")
    table.add_column("Description", style="magenta")

    for cluster in clusters:
        table.add_row(
            cluster.category_name or f"Cluster {cluster.label}",
            str(len(cluster)),
            cluster.category_description or "",
        )

    console.print(table)

    # Save output if requested
    if output:
        output_path = Path(output)
        output_data = {
            "total_messages": len(messages),
            "merged_messages": len(merged_messages),
            "clusters": len(clusters),
            "categories": {
                c.category_name or f"Cluster {c.label}": {
                    "description": c.category_description,
                    "items": len(c),
                    "message_indices": c.indices,
                }
                for c in clusters
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Results saved to {output}[/green]")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--database-id",
    prompt="Notion database ID",
    help="Database to store messages",
)
@click.option(
    "--format",
    default="auto",
    type=click.Choice(["json", "txt", "auto"]),
    help="Input file format",
)
@click.option(
    "--n-clusters",
    default=None,
    type=int,
    help="Number of clusters (if not set, auto-calculate)",
)
@click.option(
    "--auto-clusters",
    is_flag=True,
    default=False,
    help="Automatically find optimal number of clusters",
)
@click.option(
    "--cluster-method",
    type=click.Choice(["silhouette", "davies_bouldin", "calinski", "elbow", "ensemble"]),
    default="silhouette",
    help="Method for finding optimal clusters",
)
@click.option(
    "--use-llm",
    default=True,
    is_flag=True,
    help="Use LLM to generate category names",
)
def upload(
    input_file: str,
    database_id: str,
    format: str,
    n_clusters: Optional[int],
    auto_clusters: bool,
    cluster_method: str,
    use_llm: bool,
):
    """Process and upload to Notion"""
    config = ConfigManager()

    if not config.config.notion_api_key:
        console.print("[red]Error: Notion API key not configured[/red]")
        console.print("Run: kakao2notion configure")
        sys.exit(1)

    input_path = Path(input_file)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Parse
        task = progress.add_task("Parsing messages...", total=None)
        messages = parse_kakaotalk_messages(input_path, format=format)
        progress.stop_task(task)
        console.print(f"[green]✓ Loaded {len(messages)} messages[/green]")

        # Vectorize and merge
        task = progress.add_task("Vectorizing and merging...", total=None)
        vectorizer = Vectorizer(model_type="tfidf")
        texts = [m.content for m in messages]
        vectorizer.fit(texts)
        merger = MessageMerger(vectorizer)
        merged_messages = merger.merge_messages(messages)
        progress.stop_task(task)
        console.print(f"[green]✓ Merged to {len(merged_messages)} messages[/green]")

        # Determine optimal clusters
        merged_texts = [m.content for m in merged_messages]
        vectors = vectorizer.fit_transform(merged_texts)

        if auto_clusters:
            task = progress.add_task("Finding optimal clusters...", total=None)
            if cluster_method == "ensemble":
                clusterer = KNNClusterer(random_state=42)
                optimal_k, results = clusterer.find_optimal_clusters_ensemble(vectors)
                console.print(f"[green]✓ Ensemble voting: {results}[/green]")
                n_clusters = optimal_k
            else:
                clusterer = KNNClusterer(random_state=42)
                n_clusters = clusterer.find_optimal_clusters(vectors, method=cluster_method)
            console.print(f"[green]✓ Optimal clusters: {n_clusters}[/green]")
            progress.stop_task(task)
        else:
            if n_clusters is None:
                clusterer = KNNClusterer(random_state=42)
                n_clusters = clusterer.estimate_optimal_clusters_by_size(len(merged_messages))
                console.print(f"[cyan]Using estimated clusters: {n_clusters}[/cyan]")

        # Cluster
        task = progress.add_task("Clustering...", total=None)
        clusterer = KNNClusterer(n_clusters=n_clusters)
        clusterer.fit(vectors)
        clusters = clusterer.get_clusters()
        quality = clusterer.get_cluster_quality_report()
        console.print(f"[cyan]Silhouette Score: {quality['silhouette_score']} ({quality['quality_interpretation']})[/cyan]")
        progress.stop_task(task)

        # Generate names
        if use_llm:
            task = progress.add_task("Generating category names...", total=None)
            try:
                llm = get_llm_provider(
                    provider=config.config.llm_provider,
                )
                for cluster in clusters:
                    cluster_messages = [merged_messages[i] for i in cluster.indices]
                    name, desc = llm.generate_category_name(cluster_messages)
                    cluster.category_name = name
                    cluster.category_description = desc
                progress.stop_task(task)
            except Exception as e:
                progress.stop_task(task)
                console.print(f"[yellow]⚠ LLM failed: {e}[/yellow]")

        # Upload to Notion
        task = progress.add_task("Uploading to Notion...", total=None)
        notion = NotionClient(config.config.notion_api_key)

        categories_data = {}
        for cluster in clusters:
            cat_name = cluster.category_name or f"Cluster {cluster.label}"
            cat_messages = [merged_messages[i] for i in cluster.indices]
            categories_data[cat_name] = cat_messages

        notion.create_hierarchy(database_id, categories_data)
        progress.stop_task(task)
        console.print("[green]✓ Upload complete[/green]")


@cli.command()
def test():
    """Test Notion connection"""
    config = ConfigManager()

    if not config.config.notion_api_key:
        console.print("[red]Error: Notion API key not configured[/red]")
        sys.exit(1)

    notion = NotionClient(config.config.notion_api_key)
    if notion.test_connection():
        console.print("[green]✓ Connection successful[/green]")
    else:
        console.print("[red]✗ Connection failed[/red]")
        sys.exit(1)


def main():
    """Entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
