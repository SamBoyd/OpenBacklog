#!/usr/bin/env python3
"""
Render Environment Management Script

Manages suspension and resumption of services and PostgreSQL databases in Render environments.
Supports safe operations with confirmation prompts and dry-run mode.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import asyncio
import logging

import typer
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.prompt import Confirm

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

app = typer.Typer(help="Manage Render services and PostgreSQL databases by environment")
console = Console()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

@dataclass
class RenderService:
    """Represents a Render service"""

    id: str
    name: str
    service_type: str
    environment: str
    status: str
    suspenders: Optional[List[str]] = None


@dataclass
class RenderPostgres:
    """Represents a Render PostgreSQL database"""

    id: str
    name: str
    database_name: str
    environment: str
    status: str
    plan: str


class RenderAPIClient:
    """Client for interacting with the Render API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def get_services_by_environment(
        self, environment_id: str
    ) -> List[RenderService]:
        """Fetch all services for a given environment ID with detailed status"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/services",
                    headers=self.headers,
                    params={"environmentId": environment_id},
                )
                response.raise_for_status()

                data = response.json()
                services = []

                for returned_object in data:
                    service_data = returned_object.get("service", {})
                    service_id = service_data["id"]

                    # Get detailed service information for accurate status
                    detailed_service = await self.get_service_details(service_id)

                    if detailed_service:
                        # Use detailed information with accurate status
                        status = (
                            "suspended"
                            if detailed_service.get("suspended") == "suspended"
                            else "active"
                        )
                        service_type = detailed_service.get(
                            "type", service_data.get("type", "unknown")
                        )
                        suspenders = (
                            detailed_service.get("suspenders", [])
                            if status == "suspended"
                            else None
                        )
                    else:
                        # Fallback to list data if individual call fails
                        status = service_data.get("status", "unknown")
                        service_type = service_data.get("type", "unknown")
                        suspenders = None
                        logger.warning(
                            f"Failed to get detailed info for service {service_id}, using list data"
                        )

                    service = RenderService(
                        id=service_id,
                        name=service_data["name"],
                        service_type=service_type,
                        environment=service_data.get("environment", "preprod"),
                        status=status,
                        suspenders=suspenders,
                    )
                    services.append(service)

                return services

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching services: {e.response.status_code}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error fetching services: {e}")
                raise

    async def suspend_service(self, service_id: str) -> bool:
        """Suspend a service by ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/services/{service_id}/suspend",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error suspending service {service_id}: {e.response.status_code}"
                )
                return False
            except httpx.RequestError as e:
                logger.error(f"Request error suspending service {service_id}: {e}")
                return False

    async def resume_service(self, service_id: str) -> bool:
        """Resume a service by ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/services/{service_id}/resume",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error resuming service {service_id}: {e.response.status_code}"
                )
                return False
            except httpx.RequestError as e:
                logger.error(f"Request error resuming service {service_id}: {e}")
                return False

    async def get_postgres_by_environment(
        self, environment_id: str
    ) -> List[RenderPostgres]:
        """Fetch all PostgreSQL databases for a given environment ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/postgres",
                    headers=self.headers,
                    params={"environmentId": environment_id},
                )
                response.raise_for_status()

                data = response.json()
                databases = []

                for returned_object in data:
                    postgres_data = returned_object.get("postgres", {})
                    database = RenderPostgres(
                        id=postgres_data["id"],
                        name=postgres_data["name"],
                        database_name=postgres_data.get("databaseName", ""),
                        environment=postgres_data.get("environment", "preprod"),
                        status=postgres_data.get("status", "unknown"),
                        plan=postgres_data.get("plan", "unknown"),
                    )
                    databases.append(database)

                return databases

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching postgres: {e.response.status_code}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error fetching postgres: {e}")
                raise

    async def suspend_postgres(self, postgres_id: str) -> bool:
        """Suspend a PostgreSQL database by ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/postgres/{postgres_id}/suspend",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error suspending postgres {postgres_id}: {e.response.status_code}"
                )
                return False
            except httpx.RequestError as e:
                logger.error(f"Request error suspending postgres {postgres_id}: {e}")
                return False

    async def resume_postgres(self, postgres_id: str) -> bool:
        """Resume a PostgreSQL database by ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/postgres/{postgres_id}/resume",
                    headers=self.headers,
                )
                response.raise_for_status()
                return True

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error resuming postgres {postgres_id}: {e.response.status_code}"
                )
                return False
            except httpx.RequestError as e:
                logger.error(f"Request error resuming postgres {postgres_id}: {e}")
                return False

    async def get_service_details(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific service by ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/services/{service_id}",
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error fetching service details {service_id}: {e.response.status_code}"
                )
                return None
            except httpx.RequestError as e:
                logger.error(
                    f"Request error fetching service details {service_id}: {e}"
                )
                return None


def get_preprod_environment_id() -> str:
    """Get and validate the preprod environment ID from environment variables"""
    env_id = os.getenv("render_preprod_env_id")
    if not env_id:
        console.print(
            "[red]Error: render_preprod_env_id not found in environment[/red]"
        )
        raise typer.Exit(1)
    return env_id


def display_services_table(services: List[RenderService]) -> None:
    """Display services in a formatted table"""
    if not services:
        console.print("[yellow]No services found[/yellow]")
        return

    table = Table(title="Services")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Suspended By", style="yellow")
    table.add_column("ID", style="dim")

    for service in services:
        # Format suspenders information
        suspended_by = ""
        if service.status == "suspended" and service.suspenders:
            suspended_by = ", ".join(service.suspenders)
        elif service.status == "suspended":
            suspended_by = "unknown"

        table.add_row(
            service.name, service.service_type, service.status, suspended_by, service.id
        )

    console.print(table)


def display_postgres_table(databases: List[RenderPostgres]) -> None:
    """Display PostgreSQL databases in a formatted table"""
    if not databases:
        console.print("[yellow]No PostgreSQL databases found[/yellow]")
        return

    table = Table(title="PostgreSQL Databases")
    table.add_column("Name", style="cyan")
    table.add_column("Database", style="blue")
    table.add_column("Plan", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("ID", style="dim")

    for db in databases:
        table.add_row(db.name, db.database_name, db.plan, db.status, db.id)

    console.print(table)


async def process_services(
    client: RenderAPIClient,
    services: List[RenderService],
    operation: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Process services with the given operation"""
    results = {"success": [], "failed": []}

    if dry_run:
        console.print(
            f"[yellow]DRY RUN: Would {operation} {len(services)} services[/yellow]"
        )
        for service in services:
            console.print(f"  - {service.name} ({service.id})")
        return results

    with Progress() as progress:
        task = progress.add_task(
            f"[green]{operation.title()}ing services...", total=len(services)
        )

        for service in services:
            try:
                if operation == "suspend":
                    success = await client.suspend_service(service.id)
                elif operation == "resume":
                    success = await client.resume_service(service.id)
                else:
                    raise ValueError(f"Unknown operation: {operation}")

                if success:
                    results["success"].append(service)
                    console.print(
                        f"[green]✓[/green] {operation.title()}ed {service.name}"
                    )
                else:
                    results["failed"].append(service)
                    console.print(f"[red]✗[/red] Failed to {operation} {service.name}")

            except Exception as e:
                results["failed"].append(service)
                console.print(f"[red]✗[/red] Error {operation}ing {service.name}: {e}")

            progress.update(task, advance=1)

    return results


async def process_postgres(
    client: RenderAPIClient,
    databases: List[RenderPostgres],
    operation: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Process PostgreSQL databases with the given operation"""
    results = {"success": [], "failed": []}

    if dry_run:
        console.print(
            f"[yellow]DRY RUN: Would {operation} {len(databases)} PostgreSQL databases[/yellow]"
        )
        for db in databases:
            console.print(f"  - {db.name} ({db.id})")
        return results

    with Progress() as progress:
        task = progress.add_task(
            f"[green]{operation.title()}ing PostgreSQL databases...",
            total=len(databases),
        )

        for db in databases:
            try:
                if operation == "suspend":
                    success = await client.suspend_postgres(db.id)
                elif operation == "resume":
                    success = await client.resume_postgres(db.id)
                else:
                    raise ValueError(f"Unknown operation: {operation}")

                if success:
                    results["success"].append(db)
                    console.print(f"[green]✓[/green] {operation.title()}ed {db.name}")
                else:
                    results["failed"].append(db)
                    console.print(f"[red]✗[/red] Failed to {operation} {db.name}")

            except Exception as e:
                results["failed"].append(db)
                console.print(f"[red]✗[/red] Error {operation}ing {db.name}: {e}")

            progress.update(task, advance=1)

    return results


@app.command()
def suspend(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Suspend all services and PostgreSQL databases in the preprod environment"""
    asyncio.run(_suspend(dry_run, force))


async def _suspend(dry_run: bool, force: bool):
    api_key = os.getenv("render_api_key")
    if not api_key:
        console.print("[red]Error: render_api_key not found in environment[/red]")
        raise typer.Exit(1)

    environment_id = get_preprod_environment_id()
    client = RenderAPIClient(api_key)

    try:
        console.print(
            "[blue]Fetching services and PostgreSQL databases for preprod environment[/blue]"
        )
        services = await client.get_services_by_environment(environment_id)
        databases = await client.get_postgres_by_environment(environment_id)

        if not services and not databases:
            console.print(
                "[yellow]No services or databases found in this environment[/yellow]"
            )
            return

        if services:
            display_services_table(services)
        if databases:
            display_postgres_table(databases)

        total_count = len(services) + len(databases)
        if not dry_run and not force:
            if not Confirm.ask(
                f"Suspend {len(services)} services and {len(databases)} PostgreSQL databases in preprod?"
            ):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        service_results = {"success": [], "failed": []}
        postgres_results = {"success": [], "failed": []}

        if services:
            service_results = await process_services(
                client, services, "suspend", dry_run
            )

        if databases:
            postgres_results = await process_postgres(
                client, databases, "suspend", dry_run
            )

        if not dry_run:
            total_success = len(service_results["success"]) + len(
                postgres_results["success"]
            )
            total_failed = len(service_results["failed"]) + len(
                postgres_results["failed"]
            )

            console.print(
                f"\n[green]Successfully suspended: {total_success} items[/green]"
            )
            if service_results["success"]:
                console.print(f"  - Services: {len(service_results['success'])}")
            if postgres_results["success"]:
                console.print(
                    f"  - PostgreSQL databases: {len(postgres_results['success'])}"
                )

            if total_failed > 0:
                console.print(f"[red]Failed to suspend: {total_failed} items[/red]")
                if service_results["failed"]:
                    console.print(f"  - Services: {len(service_results['failed'])}")
                if postgres_results["failed"]:
                    console.print(
                        f"  - PostgreSQL databases: {len(postgres_results['failed'])}"
                    )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def resume(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Resume all services and PostgreSQL databases in the preprod environment"""
    asyncio.run(_resume(dry_run, force))


async def _resume(dry_run: bool, force: bool):
    api_key = os.getenv("render_api_key")
    if not api_key:
        console.print("[red]Error: render_api_key not found in environment[/red]")
        raise typer.Exit(1)

    environment_id = get_preprod_environment_id()
    client = RenderAPIClient(api_key)

    try:
        console.print(
            "[blue]Fetching services and PostgreSQL databases for preprod environment[/blue]"
        )
        services = await client.get_services_by_environment(environment_id)
        databases = await client.get_postgres_by_environment(environment_id)

        if not services and not databases:
            console.print(
                "[yellow]No services or databases found in this environment[/yellow]"
            )
            return

        if services:
            display_services_table(services)
        if databases:
            display_postgres_table(databases)

        if not dry_run and not force:
            if not Confirm.ask(
                f"Resume {len(services)} services and {len(databases)} PostgreSQL databases in preprod?"
            ):
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        service_results = {"success": [], "failed": []}
        postgres_results = {"success": [], "failed": []}

        if services:
            service_results = await process_services(
                client, services, "resume", dry_run
            )

        if databases:
            postgres_results = await process_postgres(
                client, databases, "resume", dry_run
            )

        if not dry_run:
            total_success = len(service_results["success"]) + len(
                postgres_results["success"]
            )
            total_failed = len(service_results["failed"]) + len(
                postgres_results["failed"]
            )

            console.print(
                f"\n[green]Successfully resumed: {total_success} items[/green]"
            )
            if service_results["success"]:
                console.print(f"  - Services: {len(service_results['success'])}")
            if postgres_results["success"]:
                console.print(
                    f"  - PostgreSQL databases: {len(postgres_results['success'])}"
                )

            if total_failed > 0:
                console.print(f"[red]Failed to resume: {total_failed} items[/red]")
                if service_results["failed"]:
                    console.print(f"  - Services: {len(service_results['failed'])}")
                if postgres_results["failed"]:
                    console.print(
                        f"  - PostgreSQL databases: {len(postgres_results['failed'])}"
                    )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_services():
    """List all services and PostgreSQL databases in the preprod environment"""
    asyncio.run(_list_services())


async def _list_services():
    api_key = os.getenv("render_api_key")
    if not api_key:
        console.print("[red]Error: render_api_key not found in environment[/red]")
        raise typer.Exit(1)

    environment_id = get_preprod_environment_id()
    client = RenderAPIClient(api_key)

    try:
        console.print(
            "[blue]Fetching services and PostgreSQL databases for preprod environment[/blue]"
        )
        services = await client.get_services_by_environment(environment_id)
        databases = await client.get_postgres_by_environment(environment_id)

        if services:
            display_services_table(services)
        if databases:
            display_postgres_table(databases)

        if not services and not databases:
            console.print(
                "[yellow]No services or databases found in this environment[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
