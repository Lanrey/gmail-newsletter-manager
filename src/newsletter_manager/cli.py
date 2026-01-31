"""Main CLI interface for newsletter manager - argparse version."""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timedelta

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import Config
from .database import Database
from .gogcli_wrapper import GogCLI, GogCLIError
from .label_manager import LabelManager
from .newsletter_detector import NewsletterDetector

console = Console()


class NewsletterCLI:
    """Newsletter Manager CLI application."""

    def __init__(self):
        self.config = None
        self.db = None
        self.gog = None
        self.detector = None
        self.label_manager = None
        self.account = None

    def initialize(self, account=None):
        """Initialize all components."""
        try:
            self.config = Config()
            self.config.load()

            # Use provided account, or default from config
            if not account:
                account = self.config.get_default_account()

            self.account = account
            self.db = Database(self.config.db_path)
            self.db.connect()
            self.gog = GogCLI(account=account)
            self.detector = NewsletterDetector(self.config)
            self.label_manager = LabelManager(self.gog)
        except GogCLIError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    def cmd_discover(self, args):
        """Discover newsletters in your inbox."""
        if args.all or args.days is None:
            console.print("[bold blue]Discovering newsletters from ALL your emails...[/bold blue]")
            console.print(
                f"[yellow]Scanning in batches of {args.batch_size} (max {args.max_results} total) to avoid rate limits[/yellow]"
            )
            query = "in:anywhere"
        else:
            console.print(
                f"[bold blue]Discovering newsletters from the last {args.days} days...[/bold blue]"
            )
            days_ago = (datetime.now() - timedelta(days=args.days)).strftime("%Y/%m/%d")
            query = f"after:{days_ago}"

        start_time = time.time()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Fetching messages (page 1)...", total=None)

            def update_progress(page_info, total_so_far):
                if isinstance(page_info, str):
                    progress.update(task, description=f"{page_info} ({total_so_far} messages)")
                else:
                    progress.update(
                        task,
                        description=f"Fetching page {page_info}... ({total_so_far} messages so far)",
                    )

            try:
                actual_max = (
                    min(args.max_results, args.batch_size) if args.max_results else args.batch_size
                )
                messages = self.gog.search_all_messages(
                    query,
                    max_total=actual_max,
                    page_size=500,
                    progress_callback=update_progress,
                    rate_limit_delay=5.0,
                )
                progress.update(task, description=f"Found {len(messages)} messages")
            except GogCLIError as e:
                console.print(f"[red]Error fetching messages:[/red] {e}")
                return

            progress.update(task, description="Analyzing messages...")

            newsletters_found = 0
            for i, message in enumerate(messages):
                is_newsletter, platform, reasons = self.detector.is_newsletter(message)

                if is_newsletter:
                    newsletters_found += 1

                    from_email = self.detector._get_from_email(message)
                    from_name = self.detector._get_from_name(message)
                    subject = message.get("subject", "")
                    snippet = message.get("snippet", "")
                    date_str = self.detector._get_date(message)

                    category, confidence = self.detector.categorize_newsletter(
                        from_email, subject, snippet
                    )

                    newsletter_id = self.db.upsert_newsletter(
                        sender_email=from_email,
                        sender_name=from_name,
                        category=category,
                        platform=platform,
                        first_seen=date_str,
                        last_seen=date_str,
                        auto_categorized=bool(category),
                    )

                    message_id = message.get("id")
                    is_read = "UNREAD" not in message.get("labelIds", [])
                    self.db.add_message(
                        message_id=message_id,
                        newsletter_id=newsletter_id,
                        subject=subject,
                        received_date=date_str,
                        is_read=is_read,
                        labels=message.get("labelIds", []),
                    )

                if i % 50 == 0:
                    progress.update(task, description=f"Analyzed {i+1}/{len(messages)} messages...")

            progress.update(task, description="Analysis complete!")

        duration = time.time() - start_time

        self.db.record_scan(
            days_scanned=args.days if args.days else 0,
            messages_processed=len(messages),
            newsletters_found=newsletters_found,
            duration_seconds=duration,
        )

        console.print(
            f"\n[green]✓[/green] Discovered {newsletters_found} newsletters from {len(messages)} messages"
        )
        console.print(f"[dim]Scan took {duration:.1f} seconds[/dim]")

        newsletters = self.db.get_all_newsletters()
        categorized = sum(1 for n in newsletters if n["category"])
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Total newsletters: {len(newsletters)}")
        console.print(f"  Auto-categorized: {categorized}")
        console.print(f"  Uncategorized: {len(newsletters) - categorized}")

    def cmd_list(self, args):
        """List all detected newsletters."""
        newsletters = self.db.get_all_newsletters(category=args.category)

        if args.unread_only:
            newsletters = [n for n in newsletters if n["unread_count"] > 0]

        # Sort
        if args.sort == "count":
            newsletters.sort(key=lambda n: n["total_count"], reverse=True)
        elif args.sort == "name":
            newsletters.sort(key=lambda n: n["sender_name"] or n["sender_email"])
        else:  # last-seen
            newsletters.sort(key=lambda n: n["last_seen"], reverse=True)

        if not newsletters:
            console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
            return

        table = Table(title="Newsletters")
        table.add_column("Sender", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Unread", justify="right", style="yellow")
        table.add_column("Last Seen", style="blue")
        table.add_column("Platform", style="dim")

        for newsletter in newsletters:
            sender = newsletter["sender_name"] or newsletter["sender_email"]
            category_display = newsletter["category"] or "[dim]uncategorized[/dim]"
            last_seen = datetime.fromisoformat(newsletter["last_seen"]).strftime("%Y-%m-%d")
            platform = newsletter["platform"] or "-"

            table.add_row(
                sender,
                category_display,
                str(newsletter["total_count"]),
                str(newsletter["unread_count"]),
                last_seen,
                platform,
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(newsletters)} newsletters[/dim]")

    def cmd_organize(self, args):
        """Organize newsletters with labels."""
        newsletters = self.db.get_all_newsletters()

        if not newsletters:
            console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
            return

        console.print(f"[bold blue]Organizing {len(newsletters)} newsletters...[/bold blue]")

        if args.dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

        categories = list(self.config.get_categories().keys())

        if not args.dry_run:
            console.print("Creating label hierarchy...")
            self.label_manager.create_newsletter_labels(categories)

        organized_count = 0

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Organizing newsletters...", total=len(newsletters))

            for newsletter in newsletters:
                category = newsletter["category"]
                sender_email = newsletter["sender_email"]

                if category:
                    label_name = f"Newsletters/{category}"
                    organized_count += 1
                    progress.console.print(f"  [green]✓[/green] {sender_email} → {label_name}")
                else:
                    progress.console.print(
                        f"  [yellow]![/yellow] {sender_email} → [dim]Newsletters[/dim] (uncategorized)"
                    )

                progress.advance(task)

        if args.dry_run:
            console.print(
                f"\n[yellow]DRY RUN:[/yellow] Would organize {organized_count} newsletters"
            )
        else:
            console.print(f"\n[green]✓[/green] Organized {organized_count} newsletters")
            console.print("[dim]Note: Run 'create-filters' to auto-label future newsletters[/dim]")

    def cmd_stats(self, args):
        """Show detailed statistics."""
        last_scan = self.db.get_last_scan()

        if not last_scan:
            console.print("[yellow]No scans performed yet. Run 'discover' first.[/yellow]")
            return

        newsletters = self.db.get_all_newsletters()

        table = Table(title="Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Newsletters", str(len(newsletters)))
        table.add_row("Total Messages", str(sum(n["total_count"] for n in newsletters)))
        table.add_row(
            "Last Scan", datetime.fromisoformat(last_scan["scan_date"]).strftime("%Y-%m-%d %H:%M")
        )
        table.add_row("Messages Scanned", str(last_scan["messages_processed"]))
        table.add_row("Scan Duration", f"{last_scan['duration_seconds']:.1f}s")

        console.print(table)

    def cmd_report(self, args):
        """Generate newsletter engagement report."""
        newsletters = self.db.get_all_newsletters()

        if not newsletters:
            console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
            return

        total_newsletters = len(newsletters)
        categorized = sum(1 for n in newsletters if n["category"])
        total_messages = sum(n["total_count"] for n in newsletters)
        total_unread = sum(n["unread_count"] for n in newsletters)

        console.print("[bold]Newsletter Report[/bold]\n")
        console.print(f"  Total Newsletters: {total_newsletters}")
        console.print(f"  Categorized: {categorized} ({categorized/total_newsletters*100:.1f}%)")
        console.print(f"  Total Messages: {total_messages}")
        console.print(f"  Unread Messages: {total_unread}")

        categories = {}
        for n in newsletters:
            cat = n["category"] or "Uncategorized"
            if cat not in categories:
                categories[cat] = {"count": 0, "messages": 0}
            categories[cat]["count"] += 1
            categories[cat]["messages"] += n["total_count"]

        console.print("\n[bold]By Category:[/bold]")
        for cat, stats in sorted(categories.items(), key=lambda x: x[1]["messages"], reverse=True):
            console.print(f"  {cat}: {stats['count']} newsletters, {stats['messages']} messages")

        last_scan = self.db.get_last_scan()
        if last_scan:
            scan_date = datetime.fromisoformat(last_scan["scan_date"])
            console.print(f"\n[dim]Last scan: {scan_date.strftime('%Y-%m-%d %H:%M')}[/dim]")

    def cmd_export(self, args):
        """Export newsletter list."""
        newsletters = self.db.get_all_newsletters()

        if not newsletters:
            console.print("[yellow]No newsletters found.[/yellow]")
            return

        if args.format == "csv":
            output_file = args.output or "newsletters.csv"
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "sender_email",
                        "sender_name",
                        "category",
                        "total_count",
                        "unread_count",
                        "last_seen",
                        "platform",
                    ],
                )
                writer.writeheader()
                for n in newsletters:
                    writer.writerow(
                        {
                            "sender_email": n["sender_email"],
                            "sender_name": n["sender_name"],
                            "category": n["category"],
                            "total_count": n["total_count"],
                            "unread_count": n["unread_count"],
                            "last_seen": n["last_seen"],
                            "platform": n["platform"],
                        }
                    )
        else:  # json
            output_file = args.output or "newsletters.json"
            with open(output_file, "w") as f:
                json.dump(newsletters, f, indent=2)

        console.print(f"[green]✓[/green] Exported {len(newsletters)} newsletters to {output_file}")

    def cmd_import_takeout(self, args):
        """Import Gmail Takeout MBOX into the database."""
        from .takeout_importer import import_mbox

        console.print(f"[bold blue]Importing Takeout MBOX:[/bold blue] {args.mbox_path}")
        if args.dry_run:
            console.print("[bold yellow]DRY RUN MODE - No data will be written[/bold yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Importing messages...", total=None)

            def update_progress(processed, found):
                progress.update(task, description=f"Processed {processed} | Newsletters {found}")

            start_time = time.time()
            processed, found = import_mbox(
                mbox_path=args.mbox_path,
                detector=self.detector,
                db=self.db,
                max_messages=args.max_messages,
                dry_run=args.dry_run,
                progress_callback=update_progress,
            )

        duration = time.time() - start_time
        if not args.dry_run:
            self.db.record_scan(
                days_scanned=0,
                messages_processed=processed,
                newsletters_found=found,
                duration_seconds=duration,
            )

        console.print(
            f"[bold green]✓ Imported {processed} messages ({found} newsletters)[/bold green]"
        )

    def cmd_account_list(self, args):
        """List all configured accounts."""
        accounts = self.config.get_accounts()
        default = self.config.get_default_account()

        if not accounts:
            console.print("[yellow]No accounts configured.[/yellow]")
            console.print("Use [bold]newsletter-manager account add <email>[/bold] to add one.")
            return

        console.print("[bold blue]Configured Accounts:[/bold blue]")
        for email in accounts:
            marker = " [green]✓[/green]" if email == default else ""
            console.print(f"  • {email}{marker}")

        if default:
            console.print(f"\n[dim]Default:[/dim] {default}")

    def cmd_account_add(self, args):
        """Add a new Gmail account."""
        if args.email in self.config.get_accounts():
            console.print(f"[yellow]Account {args.email} already exists.[/yellow]")
            return

        self.config.add_account(args.email)
        console.print(f"[green]✓ Added account:[/green] {args.email}")
        console.print(f"[dim]Use --account {args.email} to use this account with commands[/dim]")

    def cmd_account_set_default(self, args):
        """Set default account."""
        try:
            self.config.set_default_account(args.email)
            console.print(f"[green]✓ Default account set to:[/green] {args.email}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")

    def cmd_account_remove(self, args):
        """Remove an account."""
        if args.email not in self.config.get_accounts():
            console.print(f"[yellow]Account {args.email} not found.[/yellow]")
            return

        if not args.force:
            response = input(f"Remove account {args.email}? [y/N]: ")
            if response.lower() not in ["y", "yes"]:
                console.print("[dim]Cancelled.[/dim]")
                return

        self.config.remove_account(args.email)
        console.print(f"[green]✓ Removed account:[/green] {args.email}")

    def cmd_train_topics(self, args):
        """Train topic modeling for newsletter categorization."""
        from .topic_modeler import TopicModeler

        console.print("[bold blue]Training topic model...[/bold blue]")

        # Get all newsletters from database
        newsletters = self.db.get_all_newsletters()

        if not newsletters:
            console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
            return

        if len(newsletters) < 50:
            console.print(
                f"[yellow]Warning: Only {len(newsletters)} newsletters found. "
                "Consider discovering more for better topic modeling.[/yellow]"
            )

        # Get messages for each newsletter to extract subjects and snippets
        console.print(f"Preparing training data from {len(newsletters)} newsletters...")

        training_data = []
        for newsletter in newsletters[: args.max_newsletters]:
            messages = self.db.get_messages_by_newsletter(newsletter["id"])
            if messages:
                # Use first message as representative
                msg = messages[0]
                training_data.append(
                    (newsletter["sender_email"], msg["subject"], msg.get("snippet", ""))
                )

        if not training_data:
            console.print("[red]Error: No message data available for training[/red]")
            return

        console.print(f"Training on {len(training_data)} newsletters...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Training LDA model...", total=None)

            # Train model
            modeler = TopicModeler(n_topics=args.n_topics, min_df=args.min_df, max_df=args.max_df)
            topic_words = modeler.train(training_data)

            progress.update(task, description="Saving model...")

            # Save model
            model_path = self.config.config_dir / "topic_model.pkl"
            modeler.save_model(model_path)

            progress.update(task, description="Complete!")

        console.print(f"\n[green]✓ Model trained and saved to:[/green] {model_path}")
        console.print("\n[bold]Discovered Topics:[/bold]")

        for topic_id, words in topic_words.items():
            label = modeler.topic_labels.get(topic_id, f"Topic_{topic_id}")
            console.print(f"\n  {label} (Topic {topic_id}):")
            console.print(f"    {', '.join(words[:8])}")

        console.print("\n[dim]Topic model will be automatically used for categorization[/dim]")


def _setup_parsers():
    """Setup all CLI argument parsers."""
    parser = argparse.ArgumentParser(
        prog="newsletter-manager",
        description="Gmail Newsletter Manager - Intelligent newsletter management",
    )
    parser.add_argument("--account", help="Gmail account to use")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # discover command
    parser_discover = subparsers.add_parser("discover", help="Discover newsletters in your inbox")
    parser_discover.add_argument(
        "--days", type=int, default=None, help="Number of days to scan back (default: all time)"
    )
    parser_discover.add_argument(
        "--min-frequency",
        type=int,
        default=2,
        help="Minimum emails per month to consider as newsletter",
    )
    parser_discover.add_argument(
        "--max-results", type=int, default=10000, help="Maximum messages to scan per run"
    )
    parser_discover.add_argument(
        "--all", action="store_true", help="Scan all emails from inception"
    )
    parser_discover.add_argument(
        "--batch-size", type=int, default=5000, help="Number of messages to fetch in one batch"
    )

    # list command
    parser_list = subparsers.add_parser("list", help="List all detected newsletters")
    parser_list.add_argument("--category", help="Filter by category")
    parser_list.add_argument(
        "--unread-only", action="store_true", help="Show only newsletters with unread messages"
    )
    parser_list.add_argument(
        "--sort", choices=["last-seen", "count", "name"], default="last-seen", help="Sort order"
    )

    # organize command
    parser_organize = subparsers.add_parser("organize", help="Organize newsletters with labels")
    parser_organize.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )
    parser_organize.add_argument(
        "--auto-categorize",
        action="store_true",
        default=True,
        help="Automatically categorize newsletters",
    )

    # stats command
    subparsers.add_parser("stats", help="Show detailed statistics")

    # report command
    parser_report = subparsers.add_parser("report", help="Generate newsletter engagement report")
    parser_report.add_argument("--period", default="30d", help="Report period")

    # export command
    parser_export = subparsers.add_parser("export", help="Export newsletter list")
    parser_export.add_argument(
        "--format", choices=["csv", "json"], default="csv", help="Export format"
    )
    parser_export.add_argument("--output", help="Output file path")

    # import-takeout command
    parser_import = subparsers.add_parser("import-takeout", help="Import Gmail Takeout MBOX")
    parser_import.add_argument("mbox_path", help="Path to MBOX file")
    parser_import.add_argument("--max-messages", type=int, help="Limit messages processed")
    parser_import.add_argument(
        "--dry-run", action="store_true", help="Analyze without writing to DB"
    )

    # account subcommands
    parser_account = subparsers.add_parser("account", help="Manage Gmail accounts")
    account_subparsers = parser_account.add_subparsers(
        dest="account_command", help="Account commands"
    )

    account_subparsers.add_parser("list", help="List all configured accounts")

    parser_account_add = account_subparsers.add_parser("add", help="Add a new Gmail account")
    parser_account_add.add_argument("email", help="Email address")

    parser_account_default = account_subparsers.add_parser(
        "set-default", help="Set default account"
    )
    parser_account_default.add_argument("email", help="Email address")

    parser_account_remove = account_subparsers.add_parser("remove", help="Remove an account")
    parser_account_remove.add_argument("email", help="Email address")
    parser_account_remove.add_argument("--force", action="store_true", help="Skip confirmation")

    # train-topics command
    parser_train = subparsers.add_parser(
        "train-topics", help="Train topic model for smart categorization"
    )
    parser_train.add_argument(
        "--n-topics", type=int, default=10, help="Number of topics to discover (default: 10)"
    )
    parser_train.add_argument(
        "--min-df", type=int, default=2, help="Minimum document frequency (default: 2)"
    )
    parser_train.add_argument(
        "--max-df", type=float, default=0.7, help="Maximum document frequency (default: 0.7)"
    )
    parser_train.add_argument(
        "--max-newsletters",
        type=int,
        default=1000,
        help="Max newsletters to train on (default: 1000)",
    )

    return parser


def _handle_commands(cli, args):
    """Route commands to appropriate handlers."""
    if args.command == "discover":
        cli.cmd_discover(args)
    elif args.command == "list":
        cli.cmd_list(args)
    elif args.command == "organize":
        cli.cmd_organize(args)
    elif args.command == "stats":
        cli.cmd_stats(args)
    elif args.command == "report":
        cli.cmd_report(args)
    elif args.command == "export":
        cli.cmd_export(args)
    elif args.command == "import-takeout":
        cli.cmd_import_takeout(args)
    elif args.command == "train-topics":
        cli.cmd_train_topics(args)
    elif args.command == "account":
        _handle_account_commands(cli, args)


def _handle_account_commands(cli, args):
    """Handle account subcommands."""
    if args.account_command == "list":
        cli.cmd_account_list(args)
    elif args.account_command == "add":
        cli.cmd_account_add(args)
    elif args.account_command == "set-default":
        cli.cmd_account_set_default(args)
    elif args.account_command == "remove":
        cli.cmd_account_remove(args)


def main():
    """Main entry point for CLI."""
    parser = _setup_parsers()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    cli = NewsletterCLI()
    cli.initialize(account=args.account)
    _handle_commands(cli, args)


if __name__ == "__main__":
    main()
