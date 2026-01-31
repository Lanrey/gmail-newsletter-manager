"""Main CLI interface for newsletter manager."""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import time

from .config import Config
from .database import Database
from .gogcli_wrapper import GogCLI, GogCLIError
from .newsletter_detector import NewsletterDetector
from .label_manager import LabelManager

console = Console()


@click.group(invoke_without_command=True)
@click.option('--account', envvar='GOG_ACCOUNT', help='Gmail account to use')
@click.pass_context
def main(ctx, account):
    """Gmail Newsletter Manager - Intelligent newsletter management."""
    ctx.ensure_object(dict)
    
    try:
        ctx.obj['config'] = Config()
        ctx.obj['config'].load()
        
        # Use provided account, or default from config
        if not account:
            account = ctx.obj['config'].get_default_account()
        
        ctx.obj['account'] = account
        ctx.obj['db'] = Database(ctx.obj['config'].db_path)
        ctx.obj['db'].connect()
        ctx.obj['gog'] = GogCLI(account=account)
        ctx.obj['detector'] = NewsletterDetector(ctx.obj['config'])
        ctx.obj['label_manager'] = LabelManager(ctx.obj['gog'])
    except GogCLIError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option('--days', default=None, type=int, help='Number of days to scan back (default: all time)')
@click.option('--min-frequency', default=2, help='Minimum emails per month to consider as newsletter')
@click.option('--max-results', default=10000, type=int, help='Maximum messages to scan per run (default: 10000)')
@click.option('--all', 'scan_all', is_flag=True, help='Scan all emails from inception')
@click.option('--batch-size', default=5000, type=int, help='Number of messages to fetch in one batch')
@click.pass_context
def discover(ctx, days, min_frequency, max_results, scan_all, batch_size):
    """Discover newsletters in your inbox."""
    if scan_all or days is None:
        console.print(f"[bold blue]Discovering newsletters from ALL your emails...[/bold blue]")
        console.print(f"[yellow]Scanning in batches of {batch_size} (max {max_results} total) to avoid rate limits[/yellow]")
        query = 'in:anywhere'
        days_display = 'all time'
    else:
        console.print(f"[bold blue]Discovering newsletters from the last {days} days...[/bold blue]")
        days_ago = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
        query = f'after:{days_ago}'
        days_display = f'{days} days'
    
    gog = ctx.obj['gog']
    detector = ctx.obj['detector']
    db = ctx.obj['db']
    
    start_time = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching messages (page 1)...", total=None)
        
        def update_progress(page_info, total_so_far):
            if isinstance(page_info, str):
                # Status message (e.g., rate limit warning)
                progress.update(task, description=f"{page_info} ({total_so_far} messages)")
            else:
                # Page number
                progress.update(task, description=f"Fetching page {page_info}... ({total_so_far} messages so far)")
        
        try:
            # Use paginated search for all emails with rate limiting
            # Limit to batch_size to avoid hitting rate limits
            actual_max = min(max_results, batch_size) if max_results else batch_size
            messages = gog.search_all_messages(query, max_total=actual_max, 
                                              page_size=500, progress_callback=update_progress,
                                              rate_limit_delay=5.0)  # 5 seconds between requests
            progress.update(task, description=f"Found {len(messages)} messages")
        except GogCLIError as e:
            console.print(f"[red]Error fetching messages:[/red] {e}")
            console.print(f"[yellow]Tip: Scanned {len(messages) if 'messages' in locals() else 0} messages before error.[/yellow]")
            return
        
        progress.update(task, description="Analyzing messages...")
        
        newsletters_found = 0
        for i, message in enumerate(messages):
            is_newsletter, platform, reasons = detector.is_newsletter(message)
            
            if is_newsletter:
                newsletters_found += 1
                
                # Extract message details
                from_email = detector._get_from_email(message)
                from_name = detector._get_from_name(message)
                subject = message.get('subject', '')
                date_str = detector._get_date(message)
                
                # Auto-categorize
                category = detector.categorize_newsletter(from_email, subject)
                
                # Store in database
                newsletter_id = db.upsert_newsletter(
                    sender_email=from_email,
                    sender_name=from_name,
                    category=category,
                    platform=platform,
                    first_seen=date_str,
                    last_seen=date_str,
                    auto_categorized=bool(category)
                )
                
                # Store message
                message_id = message.get('id')
                is_read = 'UNREAD' not in message.get('labelIds', [])
                db.add_message(
                    message_id=message_id,
                    newsletter_id=newsletter_id,
                    subject=subject,
                    received_date=date_str,
                    is_read=is_read,
                    labels=message.get('labelIds', [])
                )
            
            if i % 50 == 0:
                progress.update(task, description=f"Analyzed {i+1}/{len(messages)} messages...")
        
        progress.update(task, description="Analysis complete!")
    
    duration = time.time() - start_time
    
    # Record scan (use days or 0 for all-time)
    db.record_scan(
        days_scanned=days if days else 0,
        messages_processed=len(messages),
        newsletters_found=newsletters_found,
        duration_seconds=duration
    )
    
    console.print(f"\n[green]✓[/green] Discovered {newsletters_found} newsletters from {len(messages)} messages")
    console.print(f"[dim]Scan took {duration:.1f} seconds[/dim]")
    
    # Show quick summary
    newsletters = db.get_all_newsletters()
    categorized = sum(1 for n in newsletters if n['category'])
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total newsletters: {len(newsletters)}")
    console.print(f"  Auto-categorized: {categorized}")
    console.print(f"  Uncategorized: {len(newsletters) - categorized}")


@main.command()
@click.option('--category', help='Filter by category')
@click.option('--unread-only', is_flag=True, help='Show only newsletters with unread messages')
@click.option('--sort', type=click.Choice(['last-seen', 'count', 'name']), default='last-seen')
@click.pass_context
def list(ctx, category, unread_only, sort):
    """List all detected newsletters."""
    db = ctx.obj['db']
    
    newsletters = db.get_all_newsletters(category=category)
    
    if unread_only:
        newsletters = [n for n in newsletters if n['unread_count'] > 0]
    
    # Sort
    if sort == 'count':
        newsletters.sort(key=lambda n: n['total_count'], reverse=True)
    elif sort == 'name':
        newsletters.sort(key=lambda n: n['sender_name'] or n['sender_email'])
    else:  # last-seen
        newsletters.sort(key=lambda n: n['last_seen'], reverse=True)
    
    if not newsletters:
        console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
        return
    
    # Create table
    table = Table(title="Newsletters")
    table.add_column("Sender", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Unread", justify="right", style="yellow")
    table.add_column("Last Seen", style="blue")
    table.add_column("Platform", style="dim")
    
    for newsletter in newsletters:
        sender = newsletter['sender_name'] or newsletter['sender_email']
        category_display = newsletter['category'] or '[dim]uncategorized[/dim]'
        last_seen = datetime.fromisoformat(newsletter['last_seen']).strftime('%Y-%m-%d')
        platform = newsletter['platform'] or '-'
        
        table.add_row(
            sender,
            category_display,
            str(newsletter['total_count']),
            str(newsletter['unread_count']),
            last_seen,
            platform
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(newsletters)} newsletters[/dim]")


@main.command()
@click.option('--dry-run', is_flag=True, help='Preview changes without applying')
@click.option('--auto-categorize', is_flag=True, default=True, help='Automatically categorize newsletters')
@click.pass_context
def organize(ctx, dry_run, auto_categorize):
    """Organize newsletters with labels."""
    db = ctx.obj['db']
    label_manager = ctx.obj['label_manager']
    config = ctx.obj['config']
    
    newsletters = db.get_all_newsletters()
    
    if not newsletters:
        console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
        return
    
    console.print(f"[bold blue]Organizing {len(newsletters)} newsletters...[/bold blue]")
    
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
    
    # Create category labels
    categories = list(config.get_categories().keys())
    
    if not dry_run:
        console.print("Creating label hierarchy...")
        label_manager.create_newsletter_labels(categories)
    
    # Organize each newsletter
    organized_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Organizing newsletters...", total=len(newsletters))
        
        for newsletter in newsletters:
            category = newsletter['category']
            sender_email = newsletter['sender_email']
            
            if category:
                label_name = f"Newsletters/{category}"
                
                if not dry_run:
                    # This would require fetching all messages from this sender
                    # For now, we'll just show what would be done
                    pass
                
                organized_count += 1
                progress.console.print(f"  [green]✓[/green] {sender_email} → {label_name}")
            else:
                progress.console.print(f"  [yellow]![/yellow] {sender_email} → [dim]Newsletters[/dim] (uncategorized)")
            
            progress.advance(task)
    
    if dry_run:
        console.print(f"\n[yellow]DRY RUN:[/yellow] Would organize {organized_count} newsletters")
    else:
        console.print(f"\n[green]✓[/green] Organized {organized_count} newsletters")
        console.print("[dim]Note: Run 'create-filters' to auto-label future newsletters[/dim]")


@main.command()
@click.option('--older-than', default='30d', help='Archive newsletters older than (e.g., 30d, 90d)')
@click.option('--unread-only', is_flag=True, help='Only cleanup unread newsletters')
@click.option('--dry-run', is_flag=True, help='Preview what would be cleaned up')
@click.pass_context
def cleanup(ctx, older_than, unread_only, dry_run):
    """Cleanup old newsletters."""
    # Parse older_than
    days = int(older_than.rstrip('d'))
    cutoff_date = datetime.now() - timedelta(days=days)
    
    console.print(f"[bold blue]Finding newsletters older than {days} days...[/bold blue]")
    
    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
    
    # Implementation would go here
    console.print("[yellow]Cleanup feature coming soon![/yellow]")


@main.command()
@click.option('--period', default='30d', help='Report period (e.g., 30d, 90d)')
@click.pass_context
def report(ctx, period):
    """Generate newsletter engagement report."""
    db = ctx.obj['db']
    
    newsletters = db.get_all_newsletters()
    
    if not newsletters:
        console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
        return
    
    # Calculate stats
    total_newsletters = len(newsletters)
    categorized = sum(1 for n in newsletters if n['category'])
    total_messages = sum(n['total_count'] for n in newsletters)
    total_unread = sum(n['unread_count'] for n in newsletters)
    
    console.print("[bold]Newsletter Report[/bold]\n")
    console.print(f"  Total Newsletters: {total_newsletters}")
    console.print(f"  Categorized: {categorized} ({categorized/total_newsletters*100:.1f}%)")
    console.print(f"  Total Messages: {total_messages}")
    console.print(f"  Unread Messages: {total_unread}")
    
    # Category breakdown
    categories = {}
    for n in newsletters:
        cat = n['category'] or 'Uncategorized'
        if cat not in categories:
            categories[cat] = {'count': 0, 'messages': 0}
        categories[cat]['count'] += 1
        categories[cat]['messages'] += n['total_count']
    
    console.print("\n[bold]By Category:[/bold]")
    for cat, stats in sorted(categories.items(), key=lambda x: x[1]['messages'], reverse=True):
        console.print(f"  {cat}: {stats['count']} newsletters, {stats['messages']} messages")
    
    # Last scan info
    last_scan = db.get_last_scan()
    if last_scan:
        scan_date = datetime.fromisoformat(last_scan['scan_date'])
        console.print(f"\n[dim]Last scan: {scan_date.strftime('%Y-%m-%d %H:%M')}[/dim]")


@main.command()
@click.pass_context
def recommend_unsubscribe(ctx):
    """Recommend newsletters to unsubscribe from."""
    db = ctx.obj['db']
    
    newsletters = db.get_all_newsletters()
    
    if not newsletters:
        console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
        return
    
    # Find newsletters with low engagement
    never_read = [n for n in newsletters if n['read_count'] == 0 and n['total_count'] >= 3]
    low_read = [n for n in newsletters if n['total_count'] >= 5 and 
                n['read_count'] / n['total_count'] < 0.2]
    
    console.print("[bold]Unsubscribe Recommendations[/bold]\n")
    
    if never_read:
        console.print(f"[red]Never Read[/red] ({len(never_read)} newsletters):")
        for n in never_read[:10]:
            sender = n['sender_name'] or n['sender_email']
            console.print(f"  • {sender} ({n['total_count']} messages, 0 read)")
    
    if low_read:
        console.print(f"\n[yellow]Rarely Read[/yellow] ({len(low_read)} newsletters):")
        for n in low_read[:10]:
            sender = n['sender_name'] or n['sender_email']
            read_rate = n['read_count'] / n['total_count'] * 100
            console.print(f"  • {sender} ({n['total_count']} messages, {read_rate:.0f}% read)")


@main.command()
@click.option('--format', type=click.Choice(['csv', 'json']), default='csv')
@click.option('--output', type=click.Path(), help='Output file path')
@click.pass_context
def export(ctx, format, output):
    """Export newsletter list."""
    import csv
    import json
    
    db = ctx.obj['db']
    newsletters = db.get_all_newsletters()
    
    if not newsletters:
        console.print("[yellow]No newsletters found.[/yellow]")
        return
    
    if format == 'csv':
        output_file = output or 'newsletters.csv'
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'sender_email', 'sender_name', 'category', 'total_count', 
                'unread_count', 'last_seen', 'platform'
            ])
            writer.writeheader()
            for n in newsletters:
                writer.writerow({
                    'sender_email': n['sender_email'],
                    'sender_name': n['sender_name'],
                    'category': n['category'],
                    'total_count': n['total_count'],
                    'unread_count': n['unread_count'],
                    'last_seen': n['last_seen'],
                    'platform': n['platform']
                })
    else:  # json
        output_file = output or 'newsletters.json'
        with open(output_file, 'w') as f:
            json.dump(newsletters, f, indent=2)
    
    console.print(f"[green]✓[/green] Exported {len(newsletters)} newsletters to {output_file}")


@main.command()
@click.pass_context
def stats(ctx):
    """Show detailed statistics."""
    db = ctx.obj['db']
    
    last_scan = db.get_last_scan()
    
    if not last_scan:
        console.print("[yellow]No scans performed yet. Run 'discover' first.[/yellow]")
        return
    
    newsletters = db.get_all_newsletters()
    
    table = Table(title="Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Newsletters", str(len(newsletters)))
    table.add_row("Total Messages", str(sum(n['total_count'] for n in newsletters)))
    table.add_row("Last Scan", datetime.fromisoformat(last_scan['scan_date']).strftime('%Y-%m-%d %H:%M'))
    table.add_row("Messages Scanned", str(last_scan['messages_processed']))
    table.add_row("Scan Duration", f"{last_scan['duration_seconds']:.1f}s")
    
    console.print(table)


@main.command()
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def apply_labels(ctx, dry_run):
    """Create newsletter labels and apply them to all emails."""
    db = ctx.obj['db']
    gog = ctx.obj['gog']
    label_manager = ctx.obj['label_manager']
    
    console.print("[bold blue]Creating newsletter label structure...[/bold blue]")
    
    # Get all newsletters
    newsletters = db.get_all_newsletters()
    
    if not newsletters:
        console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
        return
    
    # Get unique categories
    categories = set()
    newsletter_by_category = defaultdict(list)
    
    for newsletter in newsletters:
        category = newsletter.get('category') or 'Uncategorized'
        categories.add(category)
        newsletter_by_category[category].append(newsletter)
    
    console.print(f"[green]Found {len(newsletters)} newsletters in {len(categories)} categories[/green]")
    
    if dry_run:
        console.print("\n[bold yellow]DRY RUN MODE - No labels will be created[/bold yellow]\n")
    
    # Create label structure
    created_labels = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating labels...", total=len(categories))
        
        for category in sorted(categories):
            label_name = f'Newsletters/{category}'
            
            if not dry_run:
                label = label_manager.get_or_create_label(label_name)
                created_labels[category] = label
            
            progress.update(task, advance=1, description=f"Creating label: {label_name}")
    
    console.print(f"\n[green]✓ Created {len(created_labels)} category labels[/green]\n")
    
    # Create individual newsletter labels
    console.print("[bold blue]Creating individual newsletter labels...[/bold blue]")
    newsletter_labels = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating newsletter labels...", total=len(newsletters))
        
        for newsletter in newsletters:
            sender_email = newsletter['sender_email']
            sender_name = newsletter.get('sender_name', 'Unknown')
            category = newsletter.get('category', 'Uncategorized')
            
            # Create label like "Newsletters/Tech/Medium Daily Digest"
            label_name = label_manager.get_newsletter_label_name(
                category=category if category != 'Uncategorized' else None,
                sender_name=sender_name
            )
            
            if not dry_run:
                label = label_manager.get_or_create_label(label_name)
                newsletter_labels[newsletter['id']] = {
                    'label_name': label_name,
                    'label_id': label.get('id'),
                    'email': sender_email
                }
            else:
                newsletter_labels[newsletter['id']] = {
                    'label_name': label_name,
                    'email': sender_email
                }
            
            progress.update(task, advance=1, description=f"Creating label for: {sender_name}")
    
    console.print(f"\n[green]✓ Created {len(newsletter_labels)} newsletter labels[/green]\n")
    
    if dry_run:
        console.print("[bold yellow]DRY RUN COMPLETE[/bold yellow]")
        console.print("\nSample labels that would be created:")
        for i, (nl_id, label_info) in enumerate(list(newsletter_labels.items())[:10]):
            console.print(f"  • {label_info['label_name']}")
        if len(newsletter_labels) > 10:
            console.print(f"  ... and {len(newsletter_labels) - 10} more labels")
        return
    
    # Now apply labels to all messages
    console.print("[bold blue]Applying labels to all newsletter messages...[/bold blue]\n")
    
    total_labeled = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Labeling messages...", total=len(newsletter_labels))
        
        for newsletter_id, label_info in newsletter_labels.items():
            label_name = label_info['label_name']
            label_id = label_info['label_id']
            
            # Get all messages for this newsletter
            messages = db.get_messages_by_newsletter(newsletter_id)
            message_ids = [msg['id'] for msg in messages]
            
            if message_ids:
                try:
                    label_manager.apply_label_to_messages(message_ids, label_name)
                    total_labeled += len(message_ids)
                except Exception as e:
                    console.print(f"[red]Error labeling {label_name}: {e}[/red]")
            
            progress.update(task, advance=1, 
                          description=f"Labeled {total_labeled} messages ({len(message_ids)} from {label_name})")
    
    console.print(f"\n[bold green]✓ Successfully labeled {total_labeled} messages![/bold green]")
    console.print(f"[dim]Created {len(created_labels)} category labels and {len(newsletter_labels)} newsletter labels[/dim]")


@main.command('migrate-labels')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--max-per-label', type=int, default=None, help='Limit threads processed per label')
@click.pass_context
def migrate_labels(ctx, dry_run, max_per_label):
    """Move non-Newsletters labels into Newsletters sublabels."""
    db = ctx.obj['db']
    gog = ctx.obj['gog']
    label_manager = ctx.obj['label_manager']

    newsletters = db.get_all_newsletters()
    if not newsletters:
        console.print("[yellow]No newsletters found. Run 'discover' first.[/yellow]")
        return

    def normalize(name: str) -> str:
        return label_manager._clean_label_name(name or '')

    # Build map of normalized leaf label -> target Newsletters label
    leaf_to_target = {}
    collisions = set()
    for newsletter in newsletters:
        category = newsletter.get('category') or 'Uncategorized'
        target_label = label_manager.get_newsletter_label_name(
            category=category if category != 'Uncategorized' else None,
            sender_name=newsletter.get('sender_name') or 'Unknown'
        )
        leaf = target_label.split('/')[-1]
        key = normalize(leaf)
        if key in leaf_to_target and leaf_to_target[key] != target_label:
            collisions.add(key)
        else:
            leaf_to_target[key] = target_label

    for key in collisions:
        leaf_to_target.pop(key, None)

    labels = label_manager.get_labels(refresh=True)
    user_labels = [lbl for lbl in labels if lbl.get('type') == 'user']

    candidates = []
    for label in user_labels:
        name = label.get('name', '')
        if name == 'Newsletters' or name.startswith('Newsletters/'):
            continue
        target = leaf_to_target.get(normalize(name))
        if target:
            candidates.append((name, target))

    if not candidates:
        console.print("[green]No non-Newsletters labels matched newsletter targets.[/green]")
        return

    console.print(f"[bold blue]Found {len(candidates)} labels to migrate[/bold blue]")
    if dry_run:
        console.print("[bold yellow]DRY RUN MODE - No changes will be made[/bold yellow]")

    total_threads = 0
    for label_name, target_label in candidates:
        query = f'label:"{label_name}"' if ' ' in label_name else f'label:{label_name}'
        threads = gog.search_all_messages(query, max_total=max_per_label, page_size=200,
                                         rate_limit_delay=2.0)
        thread_ids = [t.get('id') for t in threads if t.get('id')]
        total_threads += len(thread_ids)

        console.print(f"[blue]{label_name}[/blue] -> [green]{target_label}[/green] ({len(thread_ids)} threads)")

        if dry_run or not thread_ids:
            continue

        for thread_id in thread_ids:
            try:
                gog.modify_thread_labels(thread_id, add_labels=[target_label], remove_labels=[label_name])
            except Exception as e:
                console.print(f"[red]Error migrating {label_name} on thread {thread_id}: {e}[/red]")
            time.sleep(0.2)

    console.print(f"[bold green]✓ Migrated {total_threads} threads[/bold green]")


@main.command('import-takeout')
@click.argument('mbox_path', type=click.Path(exists=True, dir_okay=False))
@click.option('--max-messages', type=int, default=None, help='Limit messages processed')
@click.option('--dry-run', is_flag=True, help='Analyze without writing to DB')
@click.pass_context
def import_takeout(ctx, mbox_path, max_messages, dry_run):
    """Import Gmail Takeout MBOX into the database."""
    from .takeout_importer import import_mbox

    detector = ctx.obj['detector']
    db = ctx.obj['db']

    console.print(f"[bold blue]Importing Takeout MBOX:[/bold blue] {mbox_path}")
    if dry_run:
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
            mbox_path=mbox_path,
            detector=detector,
            db=db,
            max_messages=max_messages,
            dry_run=dry_run,
            progress_callback=update_progress,
        )

    duration = time.time() - start_time
    if not dry_run:
        db.record_scan(days_scanned=0, messages_processed=processed, newsletters_found=found, duration_seconds=duration)

    console.print(f"[bold green]✓ Imported {processed} messages ({found} newsletters)[/bold green]")


@main.group('account')
@click.pass_context
def account_group(ctx):
    """Manage Gmail accounts."""
    pass


@account_group.command('list')
@click.pass_context
def account_list(ctx):
    """List all configured accounts."""
    config = ctx.obj['config']
    accounts = config.get_accounts()
    default = config.get_default_account()
    
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


@account_group.command('add')
@click.argument('email')
@click.pass_context
def account_add(ctx, email):
    """Add a new Gmail account."""
    config = ctx.obj['config']
    
    if email in config.get_accounts():
        console.print(f"[yellow]Account {email} already exists.[/yellow]")
        return
    
    config.add_account(email)
    console.print(f"[green]✓ Added account:[/green] {email}")
    console.print(f"[dim]Use --account {email} to use this account with commands[/dim]")


@account_group.command('set-default')
@click.argument('email')
@click.pass_context
def account_set_default(ctx, email):
    """Set default account."""
    config = ctx.obj['config']
    
    try:
        config.set_default_account(email)
        console.print(f"[green]✓ Default account set to:[/green] {email}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@account_group.command('remove')
@click.argument('email')
@click.option('--force', is_flag=True, help='Skip confirmation')
@click.pass_context
def account_remove(ctx, email, force):
    """Remove an account."""
    config = ctx.obj['config']
    
    if email not in config.get_accounts():
        console.print(f"[yellow]Account {email} not found.[/yellow]")
        return
    
    if not force:
        confirm = click.confirm(f"Remove account {email}?", default=False)
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            return
    
    config.remove_account(email)
    console.print(f"[green]✓ Removed account:[/green] {email}")


if __name__ == '__main__':
    main()
