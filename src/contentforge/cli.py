"""ContentForge CLI — Command-line interface for the 8-agent content pipeline."""

from __future__ import annotations

import asyncio
import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .core.config import ContentForgeConfig
from .pipeline.orchestrator import PipelineOrchestrator

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="contentforge")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config YAML file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.pass_context
def main(ctx: click.Context, config: str | None, verbose: bool) -> None:
    """ContentForge — 8-Agent AI Content Pipeline.

    Provider-agnostic: runs on any OpenAI-compatible LLM endpoint
    (OpenAI, OpenRouter, Ollama, MiMo, ...).
    """
    import logging

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    ctx.ensure_object(dict)
    if config:
        ctx.obj["config"] = ContentForgeConfig.from_yaml(config)
    else:
        ctx.obj["config"] = ContentForgeConfig.from_env()


@main.command()
@click.argument("topic")
@click.option("--words", "-w", default=2000, help="Target word count")
@click.option("--language", "-l", default="en", help="Content language")
@click.option("--output", "-o", default="./output", help="Output directory")
@click.option("--format", "-f", "fmt", default="markdown", help="Output format")
@click.option("--seo/--no-seo", default=True, help="Enable SEO optimization")
@click.option("--translate", "-t", multiple=True, help="Target languages for translation")
@click.option("--threshold", default=0.8, help="Quality threshold (0-1)")
@click.option("--max-iter", default=3, help="Max editor-quality iterations")
@click.pass_context
def generate(
    ctx: click.Context,
    topic: str,
    words: int,
    language: str,
    output: str,
    fmt: str,
    seo: bool,
    translate: tuple[str, ...],
    threshold: float,
    max_iter: int,
) -> None:
    """Generate content for a given topic using all 8 agents."""
    config: ContentForgeConfig = ctx.obj.get("config") or ContentForgeConfig.from_env()
    config.pipeline.topic = topic
    config.pipeline.target_word_count = words
    config.pipeline.language = language
    config.pipeline.output_format = fmt
    config.pipeline.seo_enabled = seo
    config.pipeline.quality_threshold = threshold
    config.pipeline.max_iterations = max_iter
    config.output_dir = output

    if translate:
        config.pipeline.enable_translation = True
        config.pipeline.target_languages = list(translate)

    console.print(
        Panel(
            f"[bold cyan]MiMo ContentForge v{__version__}[/]\n"
            f"Topic: [green]{topic}[/]\n"
            f"Words: {words} | Lang: {language} | Format: {fmt}\n"
            f"SEO: {'ON' if seo else 'OFF'} | Quality: {threshold}\n"
            f"Translate: {', '.join(translate) if translate else 'disabled'}",
            title="Pipeline Configuration",
            border_style="cyan",
        )
    )

    result = asyncio.run(_run_pipeline(config, topic))

    if result.ok:
        console.print()
        console.print(
            Panel(
                f"[bold green]Pipeline Complete![/]\n"
                f"Article: {len(result.article.split())} words\n"
                f"Tokens: {result.total_tokens:,}\n"
                f"Duration: {result.pipeline_duration_s:.1f}s\n"
                f"Metrics: {result.metrics_path}",
                title="Results",
                border_style="green",
            )
        )
    else:
        console.print(f"[red]Pipeline failed: {result.status}[/]")
        sys.exit(1)


@main.command()
@click.pass_context
def agents(ctx: click.Context) -> None:
    """List all available agents."""
    _config: ContentForgeConfig = ctx.obj.get("config") or ContentForgeConfig.from_env()

    table = Table(title="ContentForge Agents", border_style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Calls", justify="right")
    table.add_column("Tokens", justify="right")

    from .agents import AGENT_REGISTRY

    for name, cls in AGENT_REGISTRY.items():
        table.add_row(name, cls.description, "0", "0")

    console.print(table)
    console.print(f"\nTotal: {len(AGENT_REGISTRY)} agents")


@main.command()
@click.argument("metrics_file", type=click.Path(exists=True))
def report(metrics_file: str) -> None:
    """Display token consumption report from a metrics JSON file."""
    with open(metrics_file) as f:
        data = json.load(f)

    table = Table(title="Token Consumption Report", border_style="cyan")
    table.add_column("Agent", style="bold")
    table.add_column("Calls", justify="right")
    table.add_column("Total Tokens", justify="right")
    table.add_column("Avg/Call", justify="right")
    table.add_column("Cache Hit", justify="right")

    total_tokens = 0
    for agent_name, metrics in data.get("agents", {}).items():
        total_tokens += metrics.get("total_tokens", 0)
        table.add_row(
            agent_name,
            str(metrics.get("calls", 0)),
            f"{metrics.get('total_tokens', 0):,}",
            f"{metrics.get('tokens_per_call', 0):,.0f}",
            metrics.get("cache_hit_rate", "0%"),
        )

    console.print(table)
    console.print(f"\nTotal tokens: {total_tokens:,}")
    console.print(f"Duration: {data.get('pipeline_duration_s', 0):.1f}s")


@main.command()
@click.option("--output", "-o", default="contentforge.yaml", help="Output path")
def init(output: str) -> None:
    """Generate a default configuration file."""
    config = ContentForgeConfig()
    import yaml

    with open(output, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Config written to {output}[/]")
    console.print("Edit MIMO_API_KEY or set the environment variable before running.")


async def _run_pipeline(config: ContentForgeConfig, topic: str):
    """Run the pipeline with progress display."""
    orchestrator = PipelineOrchestrator(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running content pipeline...", total=None)
        result = await orchestrator.run(topic=topic)
        progress.update(task, description="Pipeline complete!")

    return result


if __name__ == "__main__":
    main()
