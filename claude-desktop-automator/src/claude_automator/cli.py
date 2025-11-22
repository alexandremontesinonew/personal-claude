"""Command-line interface for Claude Desktop Automator."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core.automator import Automator
from .utils.config import Config
from .utils.logger import Logger, get_logger

console = Console()
logger = get_logger(__name__)


def setup_logger(verbose: bool = False) -> None:
    """
    Setup logging based on verbosity.

    Args:
        verbose: Enable verbose logging
    """
    config = Config()

    # Override log level if verbose
    if verbose:
        config._config["logging"]["level"] = "DEBUG"

    Logger.setup(config)


def print_banner() -> None:
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          Claude Desktop Automator v0.1.0                  ║
    ║          Automated Claude Desktop Interaction             ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_stats(automator: Automator) -> None:
    """
    Print automation statistics.

    Args:
        automator: Automator instance
    """
    stats = automator.get_stats()

    table = Table(title="Session Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Session ID", stats["session_id"])
    table.add_row("Start Time", stats["start_time"])
    table.add_row("Uptime (minutes)", f"{stats['uptime_minutes']:.2f}")
    table.add_row("Total Messages", str(stats["total_messages"]))
    table.add_row("Prompts Sent", str(stats["prompts_sent"]))
    table.add_row("Responses Received", str(stats["responses_received"]))
    table.add_row("Recoveries", str(stats["recoveries"]))
    table.add_row("Recovery Attempts", str(stats["recovery_attempts"]))
    table.add_row("Limit Detections", str(stats["limit_detections"]))

    console.print(table)


def run_interactive(config_path: Optional[str] = None) -> int:
    """
    Run in interactive mode.

    Args:
        config_path: Optional path to config file

    Returns:
        Exit code
    """
    try:
        console.print("\n[bold green]Starting interactive mode...[/bold green]\n")

        automator = Automator(config_path)
        automator.send_interactive()

        console.print("\n[bold green]Interactive session completed[/bold green]")
        print_stats(automator)

        return 0

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.error(f"Interactive mode error: {e}")
        return 1


def run_batch(
    prompts_file: Path, config_path: Optional[str] = None, show_progress: bool = True
) -> int:
    """
    Run in batch mode with prompts from file.

    Args:
        prompts_file: Path to prompts file
        config_path: Optional path to config file
        show_progress: Show progress bar

    Returns:
        Exit code
    """
    try:
        console.print(f"\n[bold green]Running batch mode with:[/bold green] {prompts_file}\n")

        automator = Automator(config_path)

        # Load prompts
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]

        console.print(f"[cyan]Loaded {len(prompts)} prompts[/cyan]\n")

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing prompts...", total=len(prompts))

                if not automator.initialize():
                    console.print("[bold red]Initialization failed[/bold red]")
                    return 1

                for i, prompt in enumerate(prompts):
                    progress.update(task, description=f"Processing prompt {i + 1}/{len(prompts)}")

                    response = automator.send_with_retry(prompt)
                    if response is None:
                        console.print(f"\n[bold red]Failed on prompt {i + 1}[/bold red]")
                        return 1

                    progress.advance(task)

        else:
            success = automator.send_batch(prompts_file)
            if not success:
                console.print("\n[bold red]Batch processing failed[/bold red]")
                return 1

        console.print("\n[bold green]Batch processing completed successfully[/bold green]")
        print_stats(automator)

        return 0

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.error(f"Batch mode error: {e}")
        return 1


def run_single(prompt: str, config_path: Optional[str] = None) -> int:
    """
    Run a single prompt.

    Args:
        prompt: Prompt text
        config_path: Optional path to config file

    Returns:
        Exit code
    """
    try:
        console.print("\n[bold green]Sending single prompt...[/bold green]\n")

        automator = Automator(config_path)

        if not automator.initialize():
            console.print("[bold red]Initialization failed[/bold red]")
            return 1

        response = automator.send_with_retry(prompt)

        if response:
            console.print(Panel(response, title="Claude's Response", border_style="green"))
            return 0
        else:
            console.print("[bold red]Failed to get response[/bold red]")
            return 1

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.error(f"Single prompt error: {e}")
        return 1


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Claude Desktop Automator - Automate interactions with Claude Desktop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to configuration file",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Don't show banner",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Interactive mode
    subparsers.add_parser(
        "interactive",
        help="Run in interactive mode (enter prompts one by one)",
        aliases=["i"],
    )

    # Batch mode
    batch_parser = subparsers.add_parser(
        "batch",
        help="Run in batch mode with prompts from file",
        aliases=["b"],
    )
    batch_parser.add_argument(
        "file",
        type=Path,
        help="Path to file containing prompts (one per line)",
    )
    batch_parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Don't show progress bar",
    )

    # Single prompt mode
    single_parser = subparsers.add_parser(
        "send",
        help="Send a single prompt",
        aliases=["s"],
    )
    single_parser.add_argument(
        "prompt",
        type=str,
        help="Prompt text to send",
    )

    # Stats mode
    subparsers.add_parser(
        "stats",
        help="Show statistics from last session",
    )

    # Parse arguments
    args = parser.parse_args()

    # Show banner
    if not args.no_banner:
        print_banner()

    # Setup logging
    setup_logger(args.verbose)

    # Handle commands
    if args.command in ["interactive", "i"]:
        return run_interactive(args.config)

    elif args.command in ["batch", "b"]:
        return run_batch(args.file, args.config, not args.no_progress)

    elif args.command in ["send", "s"]:
        return run_single(args.prompt, args.config)

    elif args.command == "stats":
        # Load last session and show stats
        try:
            automator = Automator(args.config)
            print_stats(automator)
            return 0
        except Exception as e:
            console.print(f"[bold red]Error loading stats:[/bold red] {e}")
            return 1

    else:
        # No command specified, show help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
