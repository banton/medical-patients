#!/usr/bin/env python3
"""
Medical Patients Generator - API Key Management CLI

A command-line interface for managing API keys in the medical patients generator system.
Provides comprehensive key lifecycle management, usage analytics, and administrative tools.

Usage:
    python scripts/api_key_cli.py create --name "Team Name" [--email email@domain.com]
    python scripts/api_key_cli.py list [--active] [--demo] [--format json|table|csv]
    python scripts/api_key_cli.py show <key-id>
    python scripts/api_key_cli.py activate <key-id>
    python scripts/api_key_cli.py deactivate <key-id>
    python scripts/api_key_cli.py delete <key-id> [--confirm]
    python scripts/api_key_cli.py usage <key-id>
    python scripts/api_key_cli.py stats [--days 30]
    python scripts/api_key_cli.py limits <key-id> --patients <max> --daily <max> --hourly <max> --minute <max>
    python scripts/api_key_cli.py extend <key-id> --days <days>
    python scripts/api_key_cli.py cleanup [--dry-run]
    python scripts/api_key_cli.py rotate <key-id> [--name "New Name"]

Examples:
    # Create a new API key for development team
    python scripts/api_key_cli.py create --name "Development Team" --email "dev@company.com"

    # List all active keys in table format
    python scripts/api_key_cli.py list --active --format table

    # Show detailed information about a specific key
    python scripts/api_key_cli.py show 12345678-1234-1234-1234-123456789012

    # Update rate limits for a key
    python scripts/api_key_cli.py limits 12345678-1234-1234-1234-123456789012 --daily 500 --patients 2000

    # Rotate an API key (deactivate old, create new)
    python scripts/api_key_cli.py rotate 12345678-1234-1234-1234-123456789012 --name "Updated Key"
"""

import asyncio
import csv
from datetime import datetime, timedelta
from io import StringIO
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import config
from src.domain.models.api_key import APIKey
from src.domain.repositories.api_key_repository import APIKeyRepository

console = Console()


class APIKeyCLI:
    """Main CLI application class for API key management."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.repository = None

    async def initialize(self):
        """Initialize database connection and repository."""
        try:
            # Create async database engine
            database_url = config.DATABASE_URL
            if not database_url:
                raise ValueError("DATABASE_URL not configured")

            self.engine = create_async_engine(database_url, echo=False)
            self.session_factory = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

            # Test connection
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                self.repository = APIKeyRepository(session)

        except Exception as e:
            console.print(f"[red]Error connecting to database: {e}[/red]")
            sys.exit(1)

    async def cleanup(self):
        """Clean up database connections."""
        if self.engine:
            await self.engine.dispose()

    def format_key_display(self, key: str) -> str:
        """Format API key for safe display (show only prefix)."""
        if not key:
            return "N/A"
        return f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key[:8] + "..."

    def format_datetime(self, dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "Never"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def format_usage_stats(self, api_key: APIKey) -> Dict[str, Any]:
        """Format API key usage statistics."""
        return {
            "total_requests": api_key.total_requests,
            "total_patients": api_key.total_patients_generated,
            "daily_requests": api_key.daily_requests,
            "last_used": self.format_datetime(api_key.last_used_at),
            "last_reset": self.format_datetime(api_key.last_reset_at),
        }

    def format_limits(self, api_key: APIKey) -> Dict[str, Any]:
        """Format API key rate limits."""
        return {
            "patients_per_request": api_key.max_patients_per_request,
            "requests_per_day": api_key.max_requests_per_day or "Unlimited",
            "requests_per_hour": api_key.max_requests_per_hour,
            "requests_per_minute": api_key.max_requests_per_minute,
        }


# Create CLI instance
cli_app = APIKeyCLI()


@click.group()
@click.pass_context
def main(ctx):
    """Medical Patients Generator API Key Management CLI."""
    ctx.ensure_object(dict)


@main.command()
@click.option("--name", required=True, help="Human-readable name for the API key")
@click.option("--email", help="Contact email for the key holder")
@click.option("--demo", is_flag=True, help="Create a demo key with restricted access")
@click.option("--expires-days", type=int, help="Number of days until expiration")
@click.option("--patients", type=int, default=1000, help="Max patients per request (default: 1000)")
@click.option("--daily", type=int, help="Max requests per day (default: unlimited)")
@click.option("--hourly", type=int, default=1000, help="Max requests per hour (default: 1000)")
@click.option("--minute", type=int, default=60, help="Max requests per minute (default: 60)")
@click.option("--format", type=click.Choice(["json", "table"]), default="table", help="Output format")
async def create(name, email, demo, expires_days, patients, daily, hourly, minute, format):
    """Create a new API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            # Calculate expiration date if specified
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)

            # Create the API key
            api_key = await repository.create_api_key(
                name=name,
                email=email,
                is_demo=demo,
                expires_at=expires_at,
                max_patients_per_request=patients,
                max_requests_per_day=daily,
                max_requests_per_hour=hourly,
                max_requests_per_minute=minute,
            )

            if format == "json":
                result = {
                    "id": str(api_key.id),
                    "key": api_key.key,
                    "name": api_key.name,
                    "email": api_key.email,
                    "is_demo": api_key.is_demo,
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "created_at": api_key.created_at.isoformat(),
                    "limits": cli_app.format_limits(api_key),
                }
                print(json.dumps(result, indent=2))
            else:
                console.print("[green]✓[/green] API Key created successfully!")
                console.print(f"[bold]ID:[/bold] {api_key.id}")
                console.print(f"[bold]Key:[/bold] {api_key.key}")
                console.print(f"[bold]Name:[/bold] {api_key.name}")
                if api_key.email:
                    console.print(f"[bold]Email:[/bold] {api_key.email}")
                console.print(f"[bold]Demo Key:[/bold] {'Yes' if api_key.is_demo else 'No'}")
                if api_key.expires_at:
                    console.print(f"[bold]Expires:[/bold] {cli_app.format_datetime(api_key.expires_at)}")

                console.print("\n[bold]Rate Limits:[/bold]")
                limits = cli_app.format_limits(api_key)
                for key, value in limits.items():
                    console.print(f"  {key.replace('_', ' ').title()}: {value}")

                console.print("\n[yellow]⚠️  Store this API key securely - it cannot be displayed again![/yellow]")

    except Exception as e:
        console.print(f"[red]Error creating API key: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.option("--active", is_flag=True, help="Show only active keys")
@click.option("--demo", is_flag=True, help="Show only demo keys")
@click.option("--search", help="Search by name or email")
@click.option("--format", type=click.Choice(["json", "table", "csv"]), default="table", help="Output format")
@click.option("--limit", type=int, default=50, help="Maximum number of keys to display")
async def list(active, demo, search, format, limit):
    """List API keys."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            # Build filters
            filters = {}
            if active:
                filters["is_active"] = True
            if demo:
                filters["is_demo"] = True

            # Get keys
            if search:
                api_keys = await repository.search_keys(search, limit=limit, **filters)
            else:
                api_keys = await repository.list_keys(limit=limit, **filters)

            if not api_keys:
                console.print("[yellow]No API keys found matching criteria.[/yellow]")
                return

            if format == "json":
                result = []
                for key in api_keys:
                    result.append(
                        {
                            "id": str(key.id),
                            "key_prefix": cli_app.format_key_display(key.key),
                            "name": key.name,
                            "email": key.email,
                            "is_active": key.is_active,
                            "is_demo": key.is_demo,
                            "created_at": key.created_at.isoformat(),
                            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                            "usage": cli_app.format_usage_stats(key),
                            "limits": cli_app.format_limits(key),
                        }
                    )
                print(json.dumps(result, indent=2))

            elif format == "csv":
                output = StringIO()
                writer = csv.writer(output)

                # Write header
                writer.writerow(
                    [
                        "ID",
                        "Key Prefix",
                        "Name",
                        "Email",
                        "Active",
                        "Demo",
                        "Created",
                        "Expires",
                        "Last Used",
                        "Total Requests",
                        "Daily Requests",
                    ]
                )

                # Write data
                for key in api_keys:
                    writer.writerow(
                        [
                            str(key.id),
                            cli_app.format_key_display(key.key),
                            key.name,
                            key.email or "",
                            "Yes" if key.is_active else "No",
                            "Yes" if key.is_demo else "No",
                            cli_app.format_datetime(key.created_at),
                            cli_app.format_datetime(key.expires_at),
                            cli_app.format_datetime(key.last_used_at),
                            key.total_requests,
                            key.daily_requests,
                        ]
                    )

                console.print(output.getvalue())

            else:  # table format
                table = Table(title=f"API Keys ({len(api_keys)} found)")
                table.add_column("ID", style="dim")
                table.add_column("Key", style="cyan")
                table.add_column("Name", style="bold")
                table.add_column("Email")
                table.add_column("Status")
                table.add_column("Type")
                table.add_column("Requests", justify="right")
                table.add_column("Last Used")

                for key in api_keys:
                    status = "[green]Active[/green]" if key.is_active else "[red]Inactive[/red]"
                    key_type = "[yellow]Demo[/yellow]" if key.is_demo else "Live"

                    table.add_row(
                        str(key.id)[:8],
                        cli_app.format_key_display(key.key),
                        key.name,
                        key.email or "-",
                        status,
                        key_type,
                        f"{key.total_requests:,}",
                        cli_app.format_datetime(key.last_used_at),
                    )

                console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing API keys: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


# Add the async command runner
def run_async_command(func):
    """Decorator to run async commands."""

    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@main.command()
@click.argument("key_id")
@click.option("--format", type=click.Choice(["json", "table"]), default="table", help="Output format")
async def show(key_id, format):
    """Show detailed information about a specific API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            # Try to get by ID first, then by key
            api_key = await repository.get_by_id(key_id)
            if not api_key:
                api_key = await repository.get_by_key(key_id)

            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            if format == "json":
                result = {
                    "id": str(api_key.id),
                    "key_prefix": cli_app.format_key_display(api_key.key),
                    "name": api_key.name,
                    "email": api_key.email,
                    "is_active": api_key.is_active,
                    "is_demo": api_key.is_demo,
                    "created_at": api_key.created_at.isoformat(),
                    "updated_at": api_key.updated_at.isoformat() if api_key.updated_at else None,
                    "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                    "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    "last_reset_at": api_key.last_reset_at.isoformat() if api_key.last_reset_at else None,
                    "usage": cli_app.format_usage_stats(api_key),
                    "limits": cli_app.format_limits(api_key),
                    "metadata": api_key.key_metadata,
                }
                print(json.dumps(result, indent=2))
            else:
                console.print("[bold]API Key Details[/bold]")
                console.print(f"ID: {api_key.id}")
                console.print(f"Key: {cli_app.format_key_display(api_key.key)}")
                console.print(f"Name: {api_key.name}")
                console.print(f"Email: {api_key.email or 'Not set'}")

                status = "[green]Active[/green]" if api_key.is_active else "[red]Inactive[/red]"
                console.print(f"Status: {status}")
                console.print(f"Type: {'Demo' if api_key.is_demo else 'Live'}")

                console.print("\n[bold]Timestamps[/bold]")
                console.print(f"Created: {cli_app.format_datetime(api_key.created_at)}")
                console.print(f"Updated: {cli_app.format_datetime(api_key.updated_at)}")
                console.print(f"Expires: {cli_app.format_datetime(api_key.expires_at)}")
                console.print(f"Last Used: {cli_app.format_datetime(api_key.last_used_at)}")
                console.print(f"Last Reset: {cli_app.format_datetime(api_key.last_reset_at)}")

                console.print("\n[bold]Usage Statistics[/bold]")
                usage = cli_app.format_usage_stats(api_key)
                for key, value in usage.items():
                    console.print(f"{key.replace('_', ' ').title()}: {value}")

                console.print("\n[bold]Rate Limits[/bold]")
                limits = cli_app.format_limits(api_key)
                for key, value in limits.items():
                    console.print(f"{key.replace('_', ' ').title()}: {value}")

                if api_key.key_metadata:
                    console.print("\n[bold]Metadata[/bold]")
                    for key, value in api_key.key_metadata.items():
                        console.print(f"{key}: {value}")

    except Exception as e:
        console.print(f"[red]Error showing API key: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
async def activate(key_id):
    """Activate an API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            api_key = await repository.get_by_id(key_id)
            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            if api_key.is_active:
                console.print(f"[yellow]API key '{api_key.name}' is already active[/yellow]")
                return

            await repository.activate_key(key_id)
            console.print(f"[green]✓[/green] API key '{api_key.name}' activated successfully")

    except Exception as e:
        console.print(f"[red]Error activating API key: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
async def deactivate(key_id):
    """Deactivate an API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            api_key = await repository.get_by_id(key_id)
            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            if not api_key.is_active:
                console.print(f"[yellow]API key '{api_key.name}' is already inactive[/yellow]")
                return

            await repository.deactivate_key(key_id)
            console.print(f"[green]✓[/green] API key '{api_key.name}' deactivated successfully")

    except Exception as e:
        console.print(f"[red]Error deactivating API key: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
async def delete(key_id, confirm):
    """Delete an API key permanently."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            api_key = await repository.get_by_id(key_id)
            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            if not confirm:
                if not Confirm.ask(f"Are you sure you want to permanently delete API key '{api_key.name}'?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return

            await repository.delete_key(key_id)
            console.print(f"[green]✓[/green] API key '{api_key.name}' deleted successfully")

    except Exception as e:
        console.print(f"[red]Error deleting API key: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
@click.option("--format", type=click.Choice(["json", "table"]), default="table", help="Output format")
async def usage(key_id, format):
    """Show usage statistics for an API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            api_key = await repository.get_by_id(key_id)
            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            if format == "json":
                result = {
                    "key_id": str(api_key.id),
                    "key_name": api_key.name,
                    "usage": cli_app.format_usage_stats(api_key),
                    "limits": cli_app.format_limits(api_key),
                }
                print(json.dumps(result, indent=2))
            else:
                console.print(f"[bold]Usage Statistics for '{api_key.name}'[/bold]")
                console.print(f"Key ID: {api_key.id}")

                usage = cli_app.format_usage_stats(api_key)
                limits = cli_app.format_limits(api_key)

                table = Table(title="Current Usage")
                table.add_column("Metric", style="bold")
                table.add_column("Current", justify="right")
                table.add_column("Limit", justify="right")
                table.add_column("Status")

                # Daily requests
                daily_limit = limits["requests_per_day"]
                daily_used = usage["total_requests"]  # Should be daily_requests
                if daily_limit != "Unlimited":
                    daily_status = "[green]OK[/green]" if daily_used < daily_limit else "[red]EXCEEDED[/red]"
                else:
                    daily_status = "[green]OK[/green]"

                table.add_row("Daily Requests", str(daily_used), str(daily_limit), daily_status)
                table.add_row("Total Requests", str(usage["total_requests"]), "-", "-")
                table.add_row("Total Patients", str(usage["total_patients"]), "-", "-")

                console.print(table)

                console.print("\n[bold]Timeline[/bold]")
                console.print(f"Last Used: {usage['last_used']}")
                console.print(f"Last Reset: {usage['last_reset']}")

    except Exception as e:
        console.print(f"[red]Error showing usage: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.option("--days", type=int, default=30, help="Number of days to include in statistics")
@click.option("--format", type=click.Choice(["json", "table"]), default="table", help="Output format")
async def stats(days, format):
    """Show overall API usage statistics."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            # Get usage statistics
            stats_data = await repository.get_usage_stats()

            if format == "json":
                result = {"period_days": days, "statistics": stats_data, "generated_at": datetime.utcnow().isoformat()}
                print(json.dumps(result, indent=2))
            else:
                console.print(f"[bold]API Usage Statistics (Last {days} days)[/bold]")

                if stats_data:
                    table = Table(title="System Statistics")
                    table.add_column("Metric", style="bold")
                    table.add_column("Value", justify="right")

                    for key, value in stats_data.items():
                        metric_name = key.replace("_", " ").title()
                        table.add_row(metric_name, str(value))

                    console.print(table)
                else:
                    console.print("[yellow]No usage statistics available[/yellow]")

    except Exception as e:
        console.print(f"[red]Error showing statistics: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
@click.option("--patients", type=int, help="Max patients per request")
@click.option("--daily", type=int, help="Max requests per day")
@click.option("--hourly", type=int, help="Max requests per hour")
@click.option("--minute", type=int, help="Max requests per minute")
async def limits(key_id, patients, daily, hourly, minute):
    """Update rate limits for an API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            api_key = await repository.get_by_id(key_id)
            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            # Build update dict with only specified values
            updates = {}
            if patients is not None:
                updates["max_patients_per_request"] = patients
            if daily is not None:
                updates["max_requests_per_day"] = daily
            if hourly is not None:
                updates["max_requests_per_hour"] = hourly
            if minute is not None:
                updates["max_requests_per_minute"] = minute

            if not updates:
                console.print("[yellow]No limit updates specified[/yellow]")
                return

            await repository.update_limits(key_id, **updates)

            console.print(f"[green]✓[/green] Updated limits for API key '{api_key.name}'")
            for key, value in updates.items():
                metric_name = key.replace("_", " ").replace("max ", "").title()
                console.print(f"  {metric_name}: {value}")

    except Exception as e:
        console.print(f"[red]Error updating limits: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
@click.option("--days", type=int, required=True, help="Number of days to extend expiration")
async def extend(key_id, days):
    """Extend the expiration date of an API key."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            api_key = await repository.get_by_id(key_id)
            if not api_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            # Calculate new expiration date
            current_expiry = api_key.expires_at or datetime.utcnow()
            new_expiry = current_expiry + timedelta(days=days)

            await repository.extend_expiration(key_id, new_expiry)

            console.print(f"[green]✓[/green] Extended expiration for API key '{api_key.name}'")
            console.print(f"Previous expiry: {cli_app.format_datetime(api_key.expires_at)}")
            console.print(f"New expiry: {cli_app.format_datetime(new_expiry)}")

    except Exception as e:
        console.print(f"[red]Error extending expiration: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without actually deleting")
async def cleanup(dry_run):
    """Remove expired API keys."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            deleted_count = await repository.cleanup_expired_keys(dry_run=dry_run)

            if dry_run:
                console.print(f"[yellow]Dry run: Would delete {deleted_count} expired API keys[/yellow]")
            else:
                console.print(f"[green]✓[/green] Cleaned up {deleted_count} expired API keys")

    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


@main.command()
@click.argument("key_id")
@click.option("--name", help='Name for the new API key (defaults to old name + " (Rotated)")')
async def rotate(key_id, name):
    """Rotate an API key (deactivate old, create new with same settings)."""
    await cli_app.initialize()

    try:
        async with cli_app.session_factory() as session:
            repository = APIKeyRepository(session)

            # Get the existing key
            old_key = await repository.get_by_id(key_id)
            if not old_key:
                console.print(f"[red]API key not found: {key_id}[/red]")
                sys.exit(1)

            # Determine new name
            new_name = name or f"{old_key.name} (Rotated)"

            # Confirm the rotation
            if not Confirm.ask(f"Rotate API key '{old_key.name}' to '{new_name}'? This will deactivate the old key."):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

            # Create new key with same settings
            new_key = await repository.create_api_key(
                name=new_name,
                email=old_key.email,
                is_demo=old_key.is_demo,
                expires_at=old_key.expires_at,
                max_patients_per_request=old_key.max_patients_per_request,
                max_requests_per_day=old_key.max_requests_per_day,
                max_requests_per_hour=old_key.max_requests_per_hour,
                max_requests_per_minute=old_key.max_requests_per_minute,
            )

            # Deactivate old key
            await repository.deactivate_key(key_id)

            console.print("[green]✓[/green] API key rotated successfully!")
            console.print(f"Old key '{old_key.name}' deactivated")
            console.print(f"New key '{new_key.name}' created")
            console.print(f"[bold]New API Key:[/bold] {new_key.key}")
            console.print("[yellow]⚠️  Store this new API key securely - it cannot be displayed again![/yellow]")

    except Exception as e:
        console.print(f"[red]Error rotating API key: {e}[/red]")
        sys.exit(1)

    finally:
        await cli_app.cleanup()


# Apply async decorator to all commands
create = run_async_command(create)
list = run_async_command(list)
show = run_async_command(show)
activate = run_async_command(activate)
deactivate = run_async_command(deactivate)
delete = run_async_command(delete)
usage = run_async_command(usage)
stats = run_async_command(stats)
limits = run_async_command(limits)
extend = run_async_command(extend)
cleanup = run_async_command(cleanup)
rotate = run_async_command(rotate)

if __name__ == "__main__":
    main()
