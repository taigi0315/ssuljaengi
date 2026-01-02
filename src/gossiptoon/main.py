"""GossipToon CLI - AI-powered video generation from Reddit stories.

Usage:
    gossiptoon run <story_url>      - Generate video from Reddit URL
    gossiptoon resume <project_id>  - Resume from checkpoint
    gossiptoon validate             - Validate API keys and setup
    gossiptoon list                 - List checkpoints
    gossiptoon clean                - Clean old checkpoints
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from gossiptoon.core.config import ConfigManager
from gossiptoon.pipeline.checkpoint import PipelineStage
from gossiptoon.pipeline.orchestrator import PipelineOrchestrator
from gossiptoon.youtube.comments import CommentManager

import logging
from rich.logging import RichHandler

console = Console()

# Configure logging to work with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)]
)
logger = logging.getLogger("gossiptoon")


@click.group()
@click.version_option(version="0.1.0", prog_name="GossipToon")
def cli():
    """GossipToon - AI-powered video generation from Reddit stories.

    Transform viral Reddit gossip into engaging YouTube Shorts with:
    - Five-act narrative structure
    - Emotional voice acting
    - Cinematic AI-generated visuals
    - Dynamic captions with word-level sync
    """
    pass


@cli.command()
@click.argument("story_url")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
def run(story_url: str, config: Optional[str]):
    """Generate video from Reddit story URL.

    Example:
        gossiptoon run https://reddit.com/r/AmItheAsshole/comments/...
    """
    asyncio.run(_run_pipeline(story_url, config_path=config))


@cli.command()
@click.argument("project_id")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
def resume(project_id: str, config: Optional[str]):
    """Resume pipeline from checkpoint.

    Example:
        gossiptoon resume project_20250131_123456
    """
    asyncio.run(_resume_pipeline(project_id, config_path=config))


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
def validate(config: Optional[str]):
    """Validate API keys and environment setup.

    Checks:
    - API keys (OpenAI, Gemini, ElevenLabs)
    - FFmpeg installation
    - Whisper installation
    - Output directories
    """
    asyncio.run(_validate_setup(config_path=config))


@cli.command()
@click.option(
    "--subreddits",
    "-s",
    default=None,
    help="Comma-separated list of subreddits (defaults to config)"
)
@click.option(
    "--time-filter",
    "-t",
    type=click.Choice(["hour", "day", "week", "month", "year", "all"]),
    default="week",
    help="Time filter for top posts"
)
@click.option(
    "--limit",
    "-l",
    default=10,
    type=int,
    help="Number of stories to discover"
)
@click.option(
    "--min-upvotes",
    "-u",
    default=None,
    type=int,
    help="Minimum upvote threshold (defaults to config)"
)
@click.option(
    "--min-comments",
    "-m",
    default=None,
    type=int,
    help="Minimum comment count (defaults to config)"
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
def discover(
    subreddits: Optional[str],
    time_filter: str,
    limit: int,
    min_upvotes: Optional[int],
    min_comments: Optional[int],
    config: Optional[str],
):
    """Discover viral Reddit stories automatically.

    Example:
        gossiptoon discover --subreddits AITA,TIFU --limit 10
    """
    target_subreddits = subreddits.split(",") if subreddits else None

    asyncio.run(_discover_stories(
        subreddits=target_subreddits,
        time_filter=time_filter,
        limit=limit,
        min_upvotes=min_upvotes,
        min_comments=min_comments,
        config_path=config,
    ))


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
def list(config: Optional[str]):
    """List all pipeline checkpoints."""
    _list_checkpoints(config_path=config)


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
@click.option(
    "--days",
    "-d",
    type=int,
    default=7,
    help="Delete checkpoints older than N days",
)
def clean(config: Optional[str], days: int):
    """Clean old checkpoints.

    Example:
        gossiptoon clean --days 7
    """
    _clean_checkpoints(config_path=config, max_age_days=days)


@cli.command()
@click.argument("url")
@click.option(
    "--template",
    "-t",
    default="engagement_default",
    help="Comment template to use (engagement_default, engagement_controversial, engagement_update)"
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config file",
)
def comment(url: str, template: str, config: Optional[str]):
    """Generate YouTube comment text.

    Example:
        gossiptoon comment "https://short.url/story" --template engagement_controversial
    """
    _generate_comment(url, template, config_path=config)


async def _run_pipeline(story_url: str, config_path: Optional[str] = None):
    """Run complete pipeline."""
    try:
        # Load config
        config = _load_config(config_path)

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(config)

        # Display header
        console.print(
            Panel.fit(
                "[bold cyan]GossipToon Pipeline[/bold cyan]\n"
                f"[dim]Story: {story_url}[/dim]",
                border_style="cyan",
            )
        )

        # Run with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Initializing pipeline...", total=None)

            # Execute pipeline
            result = await orchestrator.run(story_url=story_url)

            progress.update(task, description="[green]Pipeline complete!")

        # Display results
        if result.success:
            _display_success(result)
        else:
            _display_error(result)

        return 0 if result.success else 1

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


async def _resume_pipeline(project_id: str, config_path: Optional[str] = None):
    """Resume pipeline from checkpoint."""
    try:
        # Load config
        config = _load_config(config_path)

        # Set context for correct paths
        config.set_job_context(project_id)

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(config)

        # Load checkpoint to show current stage
        checkpoint = orchestrator.checkpoint_manager.load_checkpoint(project_id)

        # Display header
        console.print(
            Panel.fit(
                "[bold cyan]GossipToon Pipeline - Resume[/bold cyan]\n"
                f"[dim]Project: {project_id}[/dim]\n"
                f"[dim]Current stage: {checkpoint.current_stage.value}[/dim]",
                border_style="cyan",
            )
        )

        # Run with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Resuming pipeline...", total=None)

            # Execute pipeline
            result = await orchestrator.run(project_id=project_id, resume=True)

            progress.update(task, description="[green]Pipeline complete!")

        # Display results
        if result.success:
            _display_success(result)
        else:
            _display_error(result)

        return 0 if result.success else 1

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


async def _validate_setup(config_path: Optional[str] = None):
    """Validate setup."""
    try:
        # Load config
        config = _load_config(config_path)

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(config)

        console.print("\n[bold cyan]Validating GossipToon setup...[/bold cyan]\n")

        # Run validation
        results = await orchestrator.validate_setup()

        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", justify="center")

        # Add rows
        for component, status in results.items():
            if component == "ready":
                continue

            status_str = "[green]✓ OK[/green]" if status else "[red]✗ FAILED[/red]"
            table.add_row(component.replace("_", " ").title(), status_str)

        console.print(table)

        # Overall status
        if results["ready"]:
            console.print("\n[bold green]✓ Setup is ready![/bold green]\n")
            return 0
        else:
            console.print("\n[bold red]✗ Setup incomplete. Please fix the issues above.[/bold red]\n")
            return 1

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def _list_checkpoints(config_path: Optional[str] = None):
    """List checkpoints."""
    try:
        # Load config
        config = _load_config(config_path)

        # Initialize checkpoint manager
        from gossiptoon.pipeline.checkpoint import CheckpointManager

        checkpoint_manager = CheckpointManager(config.checkpoints_dir)

        # Get checkpoints
        checkpoints = checkpoint_manager.list_checkpoints()

        if not checkpoints:
            console.print("\n[dim]No checkpoints found.[/dim]\n")
            return 0

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Project ID", style="cyan")
        table.add_column("Stage", style="yellow")
        table.add_column("Updated", style="dim")

        for project_id in checkpoints:
            try:
                checkpoint = checkpoint_manager.load_checkpoint(project_id)
                table.add_row(
                    project_id,
                    checkpoint.current_stage.value,
                    checkpoint.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception as e:
                table.add_row(project_id, "[red]Error[/red]", str(e))

        console.print("\n")
        console.print(table)
        console.print(f"\n[dim]Total: {len(checkpoints)} checkpoint(s)[/dim]\n")

        return 0

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def _clean_checkpoints(config_path: Optional[str] = None, max_age_days: int = 7):
    """Clean old checkpoints."""
    try:
        # Load config
        config = _load_config(config_path)

        # Initialize checkpoint manager
        from gossiptoon.pipeline.checkpoint import CheckpointManager

        checkpoint_manager = CheckpointManager(config.checkpoints_dir)

        # Clean checkpoints
        deleted = checkpoint_manager.clean_old_checkpoints(max_age_days)

        if deleted > 0:
            console.print(f"\n[green]Deleted {deleted} old checkpoint(s).[/green]\n")
        else:
            console.print("\n[dim]No old checkpoints to delete.[/dim]\n")

        return 0

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def _generate_comment(url: str, template: str, config_path: Optional[str] = None):
    """Generate comment text helper."""
    try:
        # Load config
        config = _load_config(config_path)
        
        # Initialize manager
        manager = CommentManager(config)
        
        # Generate
        comment_text = manager.generate_comment(source_url=url, template_name=template)
        
        # Display
        console.print("\n[bold cyan]Generated Comment:[/bold cyan]\n")
        console.print(Panel(comment_text, title=f"Template: {template}", border_style="green"))
        console.print("\n[dim]Copy the text above and pin it to your YouTube video.[/dim]\n")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def _load_config(config_path: Optional[str] = None) -> ConfigManager:
    """Load configuration."""
    # ConfigManager loads from .env automatically, config_path is unused for now
    return ConfigManager()


def _display_success(result):
    """Display success message."""
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold green]✓ Video generation complete![/bold green]\n\n"
            f"[cyan]Project ID:[/cyan] {result.project_id}\n"
            f"[cyan]Output:[/cyan] {result.video_project.output_path}\n"
            f"[cyan]Duration:[/cyan] {result.video_project.total_duration:.1f}s\n"
            f"[cyan]Resolution:[/cyan] {result.video_project.render_config.resolution}",
            border_style="green",
        )
    )
    console.print("\n")


def _display_error(result):
    """Display error message."""
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold red]✗ Pipeline failed[/bold red]\n\n"
            f"[cyan]Project ID:[/cyan] {result.project_id}\n"
            f"[cyan]Error:[/cyan] {result.error}\n"
            f"[cyan]Completed stages:[/cyan] {len(result.completed_stages)}\n\n"
            f"[dim]Use 'gossiptoon resume {result.project_id}' to retry[/dim]",
            border_style="red",
        )
    )
    console.print("\n")


async def _discover_stories(
    subreddits: Optional[List[str]],
    time_filter: str,
    limit: int,
    min_upvotes: Optional[int],
    min_comments: Optional[int],
    config_path: Optional[str] = None,
):
    """Discover viral stories from Reddit."""
    from gossiptoon.scrapers.reddit_crawler import RedditCrawler

    try:
        # Load config
        config = _load_config(config_path)

        # Use defaults from config if not provided
        target_subreddits = subreddits or config.reddit.subreddits
        target_min_upvotes = min_upvotes if min_upvotes is not None else config.reddit.min_upvotes
        target_min_comments = min_comments if min_comments is not None else config.reddit.min_comments

        # Display header
        console.print(
            Panel.fit(
                "[bold magenta]Reddit Story Discovery[/bold magenta]\n"
                f"[dim]Subreddits: {', '.join(['r/' + s for s in target_subreddits])}[/dim]\n"
                f"[dim]Time filter: {time_filter} | Limit: {limit}[/dim]",
                border_style="magenta",
            )
        )

        # Initialize crawler
        crawler = RedditCrawler(
            client_id=config.api.reddit_client_id,
            client_secret=config.api.reddit_client_secret,
            user_agent=config.api.reddit_user_agent,
        )

        # Discover stories
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task("Discovering stories...", total=None)
            stories = await crawler.discover_stories(
                subreddits=target_subreddits,
                time_filter=time_filter,
                limit=limit,
                min_upvotes=target_min_upvotes,
                min_comments=target_min_comments,
            )

        # Display results
        if not stories:
            console.print("[yellow]⚠ No stories found matching criteria[/yellow]")
            return

        table = Table(title=f"Top {len(stories)} Discovered Stories", show_lines=True)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Title", style="white", width=50)
        table.add_column("Subreddit", style="green", width=20)
        table.add_column("Score", style="yellow", justify="right")
        table.add_column("Upvotes", style="magenta", justify="right")
        table.add_column("Comments", style="blue", justify="right")
        table.add_column("Viral Score", style="red", justify="right")

        for i, story in enumerate(stories[:limit], 1):
            # Truncate title if too long
            title = story.title if len(story.title) <= 50 else story.title[:47] + "..."
            
            table.add_row(
                str(i),
                title,
                f"r/{story.subreddit}",
                f"{story.upvotes + story.num_comments:,}",
                f"{story.upvotes:,}",
                f"{story.num_comments:,}",
                f"{story.viral_score:.1f}",
            )

        console.print(table)
        console.print(f"\n[dim]Total discovered: {len(stories)} stories[/dim]")
        
        # Display URLs for easy copy-paste
        console.print("\n[bold cyan]📎 Story URLs:[/bold cyan]")
        for i, story in enumerate(stories[:limit], 1):
            console.print(f"  [cyan]{i}.[/cyan] {story.url}")
        
        console.print("\n[dim]Use 'gossiptoon run <url>' to generate video[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗ Discovery failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        sys.exit(cli())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
