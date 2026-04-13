"""Interactive CLI interface for kakao2notion"""

from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
import os

console = Console()


class InteractiveCLI:
    """Interactive command-line interface for kakao2notion"""

    def __init__(self):
        self.session = PromptSession()
        self.config_manager = None

    def _show_auth_status(self):
        """Show authentication status"""
        try:
            from .config import ConfigManager
            from .llm import check_llm_status

            config = ConfigManager()
            llm_status = check_llm_status()

            console.print("\n[cyan]Authentication Status:[/cyan]")

            # Notion status
            notion_status = "✓" if config.config.notion_api_key else "✗"
            console.print(f"  {notion_status} Notion API: ", end="")
            if config.config.notion_api_key:
                console.print("[green]Configured[/green]")
            else:
                console.print("[yellow]Not configured[/yellow]")

            # LLM status
            console.print(f"  Providers: ", end="")
            provider_statuses = []
            for provider_name, status in llm_status.items():
                if status.get("is_authenticated"):
                    provider_statuses.append(f"[green]{provider_name}[/green]")
                else:
                    provider_statuses.append(f"[yellow]{provider_name}[/yellow]")
            console.print(" ".join(provider_statuses))

        except Exception:
            # Silently skip auth status if there's any error
            pass

    def run(self):
        """Run interactive CLI"""
        console.print(
            Panel(
                "[bold cyan]kakao2notion[/bold cyan]\n[yellow]KakaoTalk → Notion Converter[/yellow]",
                expand=False,
            )
        )

        # Show quick auth status
        self._show_auth_status()

        while True:
            console.print()
            choice = self._show_main_menu()

            if choice == "1":
                self._process_flow()
            elif choice == "2":
                self._upload_flow()
            elif choice == "3":
                self._configure_flow()
            elif choice == "4":
                self._test_flow()
            elif choice == "5":
                console.print("[yellow]Goodbye![/yellow]")
                break
            else:
                console.print("[red]Invalid choice[/red]")

    def _show_main_menu(self) -> str:
        """Show main menu and get choice"""
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]1[/cyan]", "📊 Process messages (preview only)")
        table.add_row("[cyan]2[/cyan]", "📤 Upload to Notion")
        table.add_row("[cyan]3[/cyan]", "⚙️  Configure (API key, LLM)")
        table.add_row("[cyan]4[/cyan]", "🧪 Test connection")
        table.add_row("[cyan]5[/cyan]", "❌ Exit")

        console.print(table)
        return Prompt.ask("[bold]Choose option[/bold]", choices=["1", "2", "3", "4", "5"])

    def _get_input_file(self) -> Optional[Path]:
        """Get input file from user"""
        while True:
            file_path = Prompt.ask(
                "📁 Enter path to KakaoTalk export file",
                default="chat_export.json",
            )
            path = Path(file_path)

            if path.exists():
                return path
            else:
                console.print(f"[red]✗ File not found: {file_path}[/red]")

    def _get_file_format(self) -> str:
        """Get file format"""
        console.print("\n[cyan]File format detection:[/cyan]")
        format_choice = Prompt.ask(
            "Choose format",
            choices=["auto", "json", "txt"],
            default="auto",
        )
        return format_choice

    def _get_cluster_settings(self) -> Tuple[Optional[int], bool, str]:
        """Get clustering settings"""
        console.print("\n[cyan]Clustering settings:[/cyan]")

        auto_clusters = Confirm.ask(
            "🤖 Automatically find optimal clusters?",
            default=True,
        )

        if auto_clusters:
            console.print("\n[cyan]Optimization methods:[/cyan]")
            methods = {
                "1": "silhouette",
                "2": "davies_bouldin",
                "3": "calinski",
                "4": "elbow",
                "5": "ensemble",
            }

            table = Table(show_header=False, box=None)
            table.add_row("[cyan]1[/cyan]", "Silhouette Score (default, recommended)")
            table.add_row("[cyan]2[/cyan]", "Davies-Bouldin Index")
            table.add_row("[cyan]3[/cyan]", "Calinski-Harabasz")
            table.add_row("[cyan]4[/cyan]", "Elbow Method")
            table.add_row("[cyan]5[/cyan]", "Ensemble Voting (all methods)")

            console.print(table)
            method_choice = Prompt.ask(
                "Choose method",
                choices=list(methods.keys()),
                default="1",
            )
            method = methods[method_choice]
            return None, True, method
        else:
            n_clusters = Prompt.ask(
                "Number of clusters",
                default="5",
                cast=int,
            )
            return n_clusters, False, "none"

    def _get_similarity_threshold(self) -> float:
        """Get message merge threshold"""
        console.print("\n[cyan]Message merge settings:[/cyan]")
        threshold = Prompt.ask(
            "Similarity threshold (0-1, higher = less merging)",
            default="0.7",
            cast=float,
        )
        return max(0.0, min(1.0, threshold))

    def _get_llm_settings(self) -> bool:
        """Get LLM settings"""
        console.print("\n[cyan]Category naming:[/cyan]")
        use_llm = Confirm.ask(
            "🧠 Use LLM for category names?",
            default=True,
        )
        return use_llm

    def _get_database_id(self) -> str:
        """Get Notion database ID"""
        while True:
            db_id = Prompt.ask("🗄️  Notion database ID")

            if len(db_id) > 20:  # Simple validation
                return db_id
            else:
                console.print(
                    "[yellow]⚠️  Database ID seems too short. Are you sure? [/yellow]"
                )
                if Confirm.ask("Continue anyway?"):
                    return db_id

    def _get_output_file(self) -> Optional[str]:
        """Get output file for results"""
        save_results = Confirm.ask(
            "Save results to JSON file?",
            default=True,
        )

        if save_results:
            output_file = Prompt.ask(
                "Output file path",
                default="results.json",
            )
            return output_file
        return None

    def _process_flow(self):
        """Interactive process flow"""
        console.print("\n" + "=" * 50)
        console.print("[bold cyan]PROCESS MESSAGES[/bold cyan]")
        console.print("=" * 50)

        # Get settings
        input_file = self._get_input_file()
        if not input_file:
            return

        file_format = self._get_file_format()
        n_clusters, auto_clusters, method = self._get_cluster_settings()
        threshold = self._get_similarity_threshold()
        use_llm = self._get_llm_settings()
        output_file = self._get_output_file()

        # Show summary
        self._show_settings_summary(
            input_file=input_file,
            format=file_format,
            n_clusters=n_clusters,
            auto_clusters=auto_clusters,
            cluster_method=method,
            threshold=threshold,
            use_llm=use_llm,
            output_file=output_file,
        )

        if not Confirm.ask("\n✅ Proceed with these settings?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        # Build command and execute
        self._execute_process(
            input_file=input_file,
            file_format=file_format,
            n_clusters=n_clusters,
            auto_clusters=auto_clusters,
            cluster_method=method,
            threshold=threshold,
            use_llm=use_llm,
            output_file=output_file,
        )

    def _upload_flow(self):
        """Interactive upload flow"""
        console.print("\n" + "=" * 50)
        console.print("[bold cyan]UPLOAD TO NOTION[/bold cyan]")
        console.print("=" * 50)

        # Get settings
        input_file = self._get_input_file()
        if not input_file:
            return

        database_id = self._get_database_id()
        file_format = self._get_file_format()
        n_clusters, auto_clusters, method = self._get_cluster_settings()
        use_llm = self._get_llm_settings()

        # Show summary
        self._show_settings_summary(
            input_file=input_file,
            format=file_format,
            database_id=database_id,
            n_clusters=n_clusters,
            auto_clusters=auto_clusters,
            cluster_method=method,
            use_llm=use_llm,
        )

        if not Confirm.ask("\n✅ Proceed with upload?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        # Build command and execute
        self._execute_upload(
            input_file=input_file,
            database_id=database_id,
            file_format=file_format,
            n_clusters=n_clusters,
            auto_clusters=auto_clusters,
            cluster_method=method,
            use_llm=use_llm,
        )

    def _configure_flow(self):
        """Interactive configuration flow"""
        console.print("\n" + "=" * 50)
        console.print("[bold cyan]CONFIGURATION[/bold cyan]")
        console.print("=" * 50)

        # Get API key
        api_key = Prompt.ask(
            "🔑 Notion API key",
            hide_input=True,
            password=True,
        )

        # Check LLM provider status
        console.print("\n[cyan]Checking LLM providers...[/cyan]")
        from .llm import check_llm_status
        llm_status = check_llm_status()

        # Display provider status
        console.print("\n[bold]Available LLM Providers:[/bold]")
        providers_table = Table(show_header=True, box=None)
        providers_table.add_column("Provider", style="cyan")
        providers_table.add_column("Status", style="magenta")

        for provider_name, status in llm_status.items():
            status_msg = status.get("status_message", "Unknown")
            providers_table.add_row(provider_name.upper(), status_msg)

        console.print(providers_table)

        # Get LLM provider choice
        console.print("\n[cyan]LLM Provider:[/cyan]")
        providers = {"1": "codex", "2": "claude"}
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]1[/cyan]", "Codex (via CLI)")
        table.add_row("[cyan]2[/cyan]", "Claude (API)")
        console.print(table)

        provider_choice = Prompt.ask(
            "Choose provider",
            choices=["1", "2"],
            default="1",
        )
        provider = providers[provider_choice]

        # Save config
        import json
        from pathlib import Path

        config_dir = Path.home() / ".kakao2notion"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.json"

        config = {
            "notion_api_key": api_key,
            "llm_provider": provider,
        }

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        console.print("[green]✓ Configuration saved[/green]")

        # Verify selected provider is authenticated
        selected_status = llm_status.get(provider, {})
        if not selected_status.get("is_authenticated", False):
            console.print(f"\n[yellow]⚠️  Warning: {provider.upper()} is not authenticated[/yellow]")
            console.print(f"[yellow]{selected_status.get('status_message', 'Authentication required')}[/yellow]")

    def _test_flow(self):
        """Interactive test flow"""
        console.print("\n" + "=" * 50)
        console.print("[bold cyan]TESTING CONNECTIONS[/bold cyan]")
        console.print("=" * 50)

        try:
            from .config import ConfigManager
            from .notion_client import NotionClient
            from .llm import check_llm_status

            config = ConfigManager()

            # Test Notion
            console.print("\n[cyan]Testing Notion connection...[/cyan]")
            notion = NotionClient(config.config.notion_api_key)

            if notion.test_connection():
                console.print("[green]✓ Notion connection successful[/green]")
            else:
                console.print("[red]✗ Notion connection failed[/red]")

            # Test LLM providers
            console.print("\n[cyan]Checking LLM providers...[/cyan]")
            llm_status = check_llm_status()

            status_table = Table(show_header=True, box=None)
            status_table.add_column("Provider", style="cyan")
            status_table.add_column("Status", style="magenta")

            for provider_name, status in llm_status.items():
                status_msg = status.get("status_message", "Unknown")
                status_table.add_row(provider_name.upper(), status_msg)

            console.print(status_table)

        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")

    def _show_settings_summary(self, **kwargs):
        """Show summary of settings"""
        console.print("\n[bold]Settings Summary:[/bold]")
        table = Table(show_header=False, box=None)

        for key, value in kwargs.items():
            if value is None or value == "none":
                continue

            key_display = key.replace("_", " ").title()

            if isinstance(value, bool):
                value_display = "✓ Yes" if value else "✗ No"
            else:
                value_display = str(value)

            table.add_row(f"[cyan]{key_display}[/cyan]", value_display)

        console.print(table)

    def _execute_process(self, **kwargs):
        """Execute process command"""
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "kakao2notion.cli", "process"]

        cmd.extend([str(kwargs["input_file"])])
        cmd.extend(["--format", kwargs["format"]])

        if kwargs["auto_clusters"]:
            cmd.append("--auto-clusters")
            cmd.extend(["--cluster-method", kwargs["cluster_method"]])
        else:
            cmd.extend(["--n-clusters", str(kwargs["n_clusters"])])

        cmd.extend(["--similarity-threshold", str(kwargs["threshold"])])

        if kwargs["use_llm"]:
            cmd.append("--use-llm")

        if kwargs["output_file"]:
            cmd.extend(["--output", kwargs["output_file"]])

        console.print(f"\n[dim]$ {' '.join(cmd)}[/dim]\n")

        try:
            subprocess.run(cmd, check=True)
            console.print("\n[green]✓ Process completed[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"\n[red]✗ Process failed: {e}[/red]")

    def _execute_upload(self, **kwargs):
        """Execute upload command"""
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "kakao2notion.cli", "upload"]

        cmd.extend([str(kwargs["input_file"])])
        cmd.extend(["--database-id", kwargs["database_id"]])
        cmd.extend(["--format", kwargs["format"]])

        if kwargs["auto_clusters"]:
            cmd.append("--auto-clusters")
            cmd.extend(["--cluster-method", kwargs["cluster_method"]])
        else:
            cmd.extend(["--n-clusters", str(kwargs["n_clusters"])])

        if kwargs["use_llm"]:
            cmd.append("--use-llm")

        console.print(f"\n[dim]$ {' '.join(cmd)}[/dim]\n")

        try:
            subprocess.run(cmd, check=True)
            console.print("\n[green]✓ Upload completed[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"\n[red]✗ Upload failed: {e}[/red]")


def run_interactive():
    """Entry point for interactive CLI"""
    cli = InteractiveCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
