"""RAG System CLI - Main entry point."""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import get_settings, Settings
from src.embeddings.base import EmbedderFactory
from src.chunking.semantic_chunker import DocumentChunker
from src.vector_store.pinecone_store import PineconeManager
from src.retrieval.retriever import SemanticRetriever
from src.generation.gemini_generator import GeminiGenerator
from src.pipeline.ingestion import IngestionPipeline
from src.pipeline.query import QueryPipeline

app = typer.Typer(help="RAG System - Retrieval-Augmented Generation with Pinecone and Gemini")
console = Console()


def setup_logging(log_level: str):
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_environment(settings: Settings) -> bool:
    """
    Validate that all required components are accessible.

    Returns:
        True if validation passes, False otherwise
    """
    console.print("\n[bold]Validating system configuration...[/bold]\n")

    checks = []

    # Check API keys
    try:
        if settings.pinecone_api_key and len(settings.pinecone_api_key) > 10:
            checks.append(("Pinecone API Key", True, "Configured"))
        else:
            checks.append(("Pinecone API Key", False, "Missing or invalid"))
    except Exception as e:
        checks.append(("Pinecone API Key", False, str(e)))

    try:
        if settings.google_api_key and len(settings.google_api_key) > 10:
            checks.append(("Google API Key", True, "Configured"))
        else:
            checks.append(("Google API Key", False, "Missing or invalid"))
    except Exception as e:
        checks.append(("Google API Key", False, str(e)))

    # Check data directory
    try:
        data_path = Path(settings.data_dir)
        if data_path.exists():
            checks.append(("Data Directory", True, str(data_path)))
        else:
            checks.append(("Data Directory", False, "Does not exist"))
    except Exception as e:
        checks.append(("Data Directory", False, str(e)))

    # Display results
    for check_name, passed, message in checks:
        if passed:
            console.print(f"✓ {check_name}: [green]{message}[/green]")
        else:
            console.print(f"✗ {check_name}: [red]{message}[/red]")

    all_passed = all(passed for _, passed, _ in checks)

    if not all_passed:
        console.print("\n[red]Validation failed! Please check your .env file.[/red]")
        console.print("[yellow]Copy .env.example to .env and fill in your API keys.[/yellow]")

    return all_passed


def initialize_components(settings: Settings):
    """Initialize all RAG components."""
    # Create embeddings (sentence-transformers only)
    embeddings = EmbedderFactory.create_embedder(
        "sentence-transformers",
        model_name=settings.sentence_transformer_model
    )

    # Create chunker
    chunker = DocumentChunker(embeddings=embeddings)

    # Create Pinecone manager
    pinecone_manager = PineconeManager(
        api_key=settings.pinecone_api_key,
        environment=settings.pinecone_environment,
        index_name=settings.pinecone_index_name,
        embedding_dimension=settings.get_embedding_dimension()
    )

    # Create generator
    generator = GeminiGenerator(
        api_key=settings.google_api_key,
        model=settings.gemini_model,
        temperature=settings.temperature
    )

    return embeddings, chunker, pinecone_manager, generator


@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to file or directory to ingest"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively process subdirectories")
):
    """Ingest documents into the vector database."""
    settings = get_settings()
    setup_logging(settings.log_level)

    if not validate_environment(settings):
        raise typer.Exit(1)

    path_obj = Path(path)
    if not path_obj.exists():
        console.print(f"[red]Error: Path not found: {path}[/red]")
        raise typer.Exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing RAG system...", total=None)

            embeddings, chunker, pinecone_manager, _ = initialize_components(settings)

            progress.update(task, description="Creating ingestion pipeline...")
            pipeline = IngestionPipeline(
                chunker=chunker,
                vector_store_manager=pinecone_manager,
                embeddings=embeddings
            )

            # Ingest
            if path_obj.is_file():
                progress.update(task, description=f"Ingesting {path_obj.name}...")
                result = pipeline.ingest_file(str(path_obj))

                progress.stop()

                if result["status"] == "success":
                    console.print(f"\n[green]Successfully ingested {path_obj.name}[/green]")
                    console.print(f"  Documents loaded: {result['documents_loaded']}")
                    console.print(f"  Chunks created: {result['chunks_created']}")
                    console.print(f"  Chunks upserted: {result['chunks_upserted']}")
                else:
                    console.print(f"\n[red]Failed to ingest {path_obj.name}[/red]")
                    console.print(f"  Error: {result.get('error', 'Unknown error')}")

            else:  # Directory
                progress.update(task, description=f"Scanning directory...")
                result = pipeline.ingest_directory(
                    str(path_obj),
                    recursive=recursive
                )

                progress.stop()

                # Display summary
                console.print(f"\n[bold]Ingestion Summary[/bold]")
                console.print(f"  Total files: {result['total_files']}")
                console.print(f"  Successful: [green]{result['successful']}[/green]")
                console.print(f"  Failed: [red]{result['failed']}[/red]")
                console.print(f"  Skipped: [yellow]{result['skipped']}[/yellow]")

                # Show detailed results if there were failures
                if result['failed'] > 0:
                    console.print("\n[yellow]Failed files:[/yellow]")
                    for file_result in result['results']:
                        if file_result['status'] == 'failed':
                            console.print(f"  - {file_result['file']}: {file_result.get('error', 'Unknown')}")

    except Exception as e:
        console.print(f"\n[red]Error during ingestion: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Your question"),
    top_k: Optional[int] = typer.Option(None, "--top-k", "-k", help="Number of results to retrieve"),
    show_sources: bool = typer.Option(True, "--sources/--no-sources", help="Display source documents")
):
    """Query the RAG system."""
    settings = get_settings()
    setup_logging(settings.log_level)

    if not validate_environment(settings):
        raise typer.Exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing RAG system...", total=None)

            embeddings, _, pinecone_manager, generator = initialize_components(settings)

            progress.update(task, description="Setting up query pipeline...")

            # Create retriever and query pipeline
            vector_store = pinecone_manager.get_vector_store(embeddings)
            retriever = SemanticRetriever(
                vector_store=vector_store,
                top_k=top_k or settings.top_k_results
            )
            query_pipeline = QueryPipeline(retriever=retriever, generator=generator)

            progress.update(task, description="Processing your query...")
            result = query_pipeline.query(question, top_k=top_k)

        # Display answer
        console.print(f"\n[bold]Question:[/bold] {result['question']}\n")
        console.print(Panel(result['answer'], title="Answer", border_style="green"))

        # Display sources
        if show_sources and result['sources']:
            console.print(f"\n[bold]Sources ({len(result['sources'])}):[/bold]")

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Source", style="cyan")
            table.add_column("Pages", style="yellow")
            table.add_column("Relevance", style="green")

            for source in result['sources']:
                pages = ", ".join(str(p) for p in source.get('pages', [])) if source.get('pages') else "N/A"
                score = f"{source.get('relevance_score', 0):.4f}"
                table.add_row(source['source'], pages, score)

            console.print(table)

        console.print(f"\n[dim]Retrieved {result['retrieved_chunks']} chunks using {result['retrieval_method']} search[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error during query: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def reset():
    """Clear all documents from the vector database."""
    settings = get_settings()
    setup_logging(settings.log_level)

    if not validate_environment(settings):
        raise typer.Exit(1)

    # Confirmation prompt
    confirm = typer.confirm(
        "Are you sure you want to delete ALL documents from the vector database? This cannot be undone."
    )

    if not confirm:
        console.print("[yellow]Reset cancelled.[/yellow]")
        return

    try:
        pinecone_manager = PineconeManager(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name,
            embedding_dimension=settings.get_embedding_dimension()
        )

        with console.status("[bold red]Deleting all vectors..."):
            pinecone_manager.delete_all()

        console.print("[green]All documents deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error during reset: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show system status and configuration."""
    settings = get_settings()
    setup_logging(settings.log_level)

    console.print("\n[bold]RAG System Status[/bold]\n")

    # Configuration
    config_table = Table(show_header=True, header_style="bold cyan")
    config_table.add_column("Setting", style="yellow")
    config_table.add_column("Value", style="white")

    for key, value in settings.display_config().items():
        config_table.add_row(key, str(value))

    console.print(config_table)

    # Validate environment
    console.print()
    validate_environment(settings)

    # Pinecone stats
    try:
        pinecone_manager = PineconeManager(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name,
            embedding_dimension=settings.get_embedding_dimension()
        )

        if pinecone_manager.index_exists():
            stats = pinecone_manager.get_stats()

            console.print("\n[bold]Pinecone Index Statistics[/bold]\n")
            stats_table = Table(show_header=False)
            stats_table.add_column("Metric", style="yellow")
            stats_table.add_column("Value", style="white")

            stats_table.add_row("Total Vectors", str(stats['total_vectors']))
            stats_table.add_row("Dimension", str(stats['dimension']))
            stats_table.add_row("Index Fullness", f"{stats['index_fullness']:.2%}")

            console.print(stats_table)
        else:
            console.print("\n[yellow]Pinecone index does not exist yet. Ingest documents to create it.[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Could not retrieve Pinecone stats: {e}[/red]")


if __name__ == "__main__":
    app()
