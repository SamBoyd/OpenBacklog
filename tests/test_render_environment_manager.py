import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from render_environment_manager import (
    RenderAPIClient,
    RenderPostgres,
    RenderService,
    _list_services,
    _resume,
    _suspend,
    get_preprod_environment_id,
    process_postgres,
    process_services,
)


class TestRenderService:
    """Test the RenderService dataclass"""

    def test_render_service_creation(self):
        service = RenderService(
            id="srv-123",
            name="test-service",
            service_type="web_service",
            environment="preprod",
            status="active",
        )

        assert service.id == "srv-123"
        assert service.name == "test-service"
        assert service.service_type == "web_service"
        assert service.environment == "preprod"
        assert service.status == "active"
        assert service.suspenders is None

    def test_render_service_creation_with_suspenders(self):
        service = RenderService(
            id="srv-123",
            name="test-service",
            service_type="web_service",
            environment="preprod",
            status="suspended",
            suspenders=["admin", "user"],
        )

        assert service.id == "srv-123"
        assert service.name == "test-service"
        assert service.service_type == "web_service"
        assert service.environment == "preprod"
        assert service.status == "suspended"
        assert service.suspenders == ["admin", "user"]


class TestRenderPostgres:
    """Test the RenderPostgres dataclass"""

    def test_render_postgres_creation(self):
        postgres = RenderPostgres(
            id="pg-123",
            name="test-postgres",
            database_name="testdb",
            environment="preprod",
            status="available",
            plan="starter",
        )

        assert postgres.id == "pg-123"
        assert postgres.name == "test-postgres"
        assert postgres.database_name == "testdb"
        assert postgres.environment == "preprod"
        assert postgres.status == "available"
        assert postgres.plan == "starter"


class TestRenderAPIClient:
    """Test the RenderAPIClient class"""

    @pytest.fixture
    def client(self):
        return RenderAPIClient("test-api-key")

    @pytest.mark.asyncio
    async def test_get_services_by_environment_success(self, client):
        mock_response_data = [
            {
                "service": {
                    "id": "srv-123",
                    "name": "test-service-1",
                    "type": "web_service",
                    "environment": "preprod",
                    "status": "active",
                }
            },
            {
                "service": {
                    "id": "srv-456",
                    "name": "test-service-2",
                    "type": "background_worker",
                    "environment": "preprod",
                    "status": "suspended",
                }
            },
        ]

        mock_service_details = [
            {
                "id": "srv-123",
                "name": "test-service-1",
                "type": "web_service",
                "suspended": "not_suspended",
                "suspenders": [],
            },
            {
                "id": "srv-456",
                "name": "test-service-2",
                "type": "background_worker",
                "suspended": "suspended",
                "suspenders": ["admin"],
            },
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            # Mock individual service detail calls
            mock_detail_responses = []
            for detail in mock_service_details:
                detail_response = MagicMock()
                detail_response.json.return_value = detail
                detail_response.raise_for_status.return_value = None
                mock_detail_responses.append(detail_response)

            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_response
            ] + mock_detail_responses

            services = await client.get_services_by_environment("env-123")

            # Verify correct API calls were made
            expected_calls = [
                call(
                    "https://api.render.com/v1/services",
                    headers=client.headers,
                    params={"environmentId": "env-123"},
                ),
                call(
                    "https://api.render.com/v1/services/srv-123",
                    headers=client.headers,
                ),
                call(
                    "https://api.render.com/v1/services/srv-456",
                    headers=client.headers,
                ),
            ]
            mock_client.return_value.__aenter__.return_value.get.assert_has_calls(
                expected_calls
            )

            assert len(services) == 2
            assert services[0].id == "srv-123"
            assert services[0].name == "test-service-1"
            assert services[0].service_type == "web_service"
            assert services[0].status == "active"
            assert services[0].suspenders is None

            assert services[1].id == "srv-456"
            assert services[1].name == "test-service-2"
            assert services[1].service_type == "background_worker"
            assert services[1].status == "suspended"
            assert services[1].suspenders == ["admin"]

    @pytest.mark.asyncio
    async def test_get_services_by_environment_empty_response(self, client):
        mock_response_data = []

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            services = await client.get_services_by_environment("env-123")

            assert len(services) == 0
            # Should only call the list endpoint, no individual service calls
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                "https://api.render.com/v1/services",
                headers=client.headers,
                params={"environmentId": "env-123"},
            )

    @pytest.mark.asyncio
    async def test_suspend_service_success(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.suspend_service("srv-123")

            assert result is True
            mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
                "https://api.render.com/v1/services/srv-123/suspend",
                headers=client.headers,
            )

    @pytest.mark.asyncio
    async def test_suspend_service_http_error(self, client):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP Error", request=MagicMock(), response=MagicMock()
            )

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.suspend_service("srv-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_resume_service_success(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.resume_service("srv-123")

            assert result is True
            mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
                "https://api.render.com/v1/services/srv-123/resume",
                headers=client.headers,
            )

    @pytest.mark.asyncio
    async def test_resume_service_http_error(self, client):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP Error", request=MagicMock(), response=MagicMock()
            )

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.resume_service("srv-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_postgres_by_environment_success(self, client):
        mock_response_data = [
            {
                "postgres": {
                    "id": "pg-123",
                    "name": "test-postgres-1",
                    "databaseName": "testdb1",
                    "environment": "preprod",
                    "status": "available",
                    "plan": "starter",
                }
            },
            {
                "postgres": {
                    "id": "pg-456",
                    "name": "test-postgres-2",
                    "databaseName": "testdb2",
                    "environment": "preprod",
                    "status": "suspended",
                    "plan": "standard",
                }
            },
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            databases = await client.get_postgres_by_environment("env-123")

            # Verify correct API call was made
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                "https://api.render.com/v1/postgres",
                headers=client.headers,
                params={"environmentId": "env-123"},
            )

            assert len(databases) == 2
            assert databases[0].id == "pg-123"
            assert databases[0].name == "test-postgres-1"
            assert databases[0].database_name == "testdb1"
            assert databases[1].id == "pg-456"
            assert databases[1].name == "test-postgres-2"
            assert databases[1].plan == "standard"

    @pytest.mark.asyncio
    async def test_suspend_postgres_success(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.suspend_postgres("pg-123")

            assert result is True
            mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
                "https://api.render.com/v1/postgres/pg-123/suspend",
                headers=client.headers,
            )

    @pytest.mark.asyncio
    async def test_suspend_postgres_http_error(self, client):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP Error", request=MagicMock(), response=MagicMock()
            )

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.suspend_postgres("pg-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_resume_postgres_success(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.resume_postgres("pg-123")

            assert result is True
            mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
                "https://api.render.com/v1/postgres/pg-123/resume",
                headers=client.headers,
            )

    @pytest.mark.asyncio
    async def test_resume_postgres_http_error(self, client):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP Error", request=MagicMock(), response=MagicMock()
            )

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await client.resume_postgres("pg-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_service_details_success(self, client):
        mock_service_details = {
            "id": "srv-123",
            "name": "test-service",
            "type": "web_service",
            "suspended": "suspended",
            "suspenders": ["admin"],
            "environmentId": "env-123",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_service_details
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await client.get_service_details("srv-123")

            assert result == mock_service_details
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                "https://api.render.com/v1/services/srv-123",
                headers=client.headers,
            )

    @pytest.mark.asyncio
    async def test_get_service_details_http_error(self, client):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "HTTP Error", request=MagicMock(), response=MagicMock()
            )

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await client.get_service_details("srv-123")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_service_details_request_error(self, client):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.RequestError("Network error")
            )

            result = await client.get_service_details("srv-123")

            assert result is None


class TestGetPreprodEnvironmentId:
    """Test the get_preprod_environment_id function"""

    def test_get_preprod_environment_id_success(self):
        with patch.dict(os.environ, {"render_preprod_env_id": "env-123"}):
            env_id = get_preprod_environment_id()
            assert env_id == "env-123"

    def test_get_preprod_environment_id_missing(self):
        from typer import Exit

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exit):
                get_preprod_environment_id()


class TestProcessServices:
    """Test the process_services function"""

    @pytest.fixture
    def sample_services(self):
        return [
            RenderService(
                "srv-1", "service-1", "web_service", "preprod", "active", None
            ),
            RenderService("srv-2", "service-2", "worker", "preprod", "active", None),
        ]

    @pytest.mark.asyncio
    async def test_process_services_dry_run(self, sample_services):
        client = AsyncMock()

        results = await process_services(
            client, sample_services, "suspend", dry_run=True
        )

        # Dry run should not call any client methods
        client.suspend_service.assert_not_called()
        client.resume_service.assert_not_called()

        # Results should be empty for dry run
        assert results["success"] == []
        assert results["failed"] == []

    @pytest.mark.asyncio
    async def test_process_services_suspend_success(self, sample_services):
        client = AsyncMock()
        client.suspend_service.return_value = True

        with patch("render_environment_manager.console"):
            results = await process_services(
                client, sample_services, "suspend", dry_run=False
            )

        # Should call suspend for each service
        assert client.suspend_service.call_count == 2
        client.suspend_service.assert_has_calls([call("srv-1"), call("srv-2")])

        # All should be successful
        assert len(results["success"]) == 2
        assert len(results["failed"]) == 0

    @pytest.mark.asyncio
    async def test_process_services_resume_success(self, sample_services):
        client = AsyncMock()
        client.resume_service.return_value = True

        with patch("render_environment_manager.console"):
            results = await process_services(
                client, sample_services, "resume", dry_run=False
            )

        # Should call resume for each service
        assert client.resume_service.call_count == 2
        client.resume_service.assert_has_calls([call("srv-1"), call("srv-2")])

        # All should be successful
        assert len(results["success"]) == 2
        assert len(results["failed"]) == 0

    @pytest.mark.asyncio
    async def test_process_services_mixed_results(self, sample_services):
        client = AsyncMock()
        # First call succeeds, second fails
        client.suspend_service.side_effect = [True, False]

        with patch("render_environment_manager.console"):
            results = await process_services(
                client, sample_services, "suspend", dry_run=False
            )

        # One successful, one failed
        assert len(results["success"]) == 1
        assert len(results["failed"]) == 1
        assert results["success"][0].id == "srv-1"
        assert results["failed"][0].id == "srv-2"


class TestProcessPostgres:
    """Test the process_postgres function"""

    @pytest.fixture
    def sample_postgres(self):
        return [
            RenderPostgres(
                "pg-1", "postgres-1", "db1", "preprod", "available", "starter"
            ),
            RenderPostgres(
                "pg-2", "postgres-2", "db2", "preprod", "available", "standard"
            ),
        ]

    @pytest.mark.asyncio
    async def test_process_postgres_dry_run(self, sample_postgres):
        client = AsyncMock()

        results = await process_postgres(
            client, sample_postgres, "suspend", dry_run=True
        )

        # Dry run should not call any client methods
        client.suspend_postgres.assert_not_called()
        client.resume_postgres.assert_not_called()

        # Results should be empty for dry run
        assert results["success"] == []
        assert results["failed"] == []

    @pytest.mark.asyncio
    async def test_process_postgres_suspend_success(self, sample_postgres):
        client = AsyncMock()
        client.suspend_postgres.return_value = True

        with patch("render_environment_manager.console"):
            results = await process_postgres(
                client, sample_postgres, "suspend", dry_run=False
            )

        # Should call suspend for each database
        assert client.suspend_postgres.call_count == 2
        client.suspend_postgres.assert_has_calls([call("pg-1"), call("pg-2")])

        # All should be successful
        assert len(results["success"]) == 2
        assert len(results["failed"]) == 0

    @pytest.mark.asyncio
    async def test_process_postgres_resume_success(self, sample_postgres):
        client = AsyncMock()
        client.resume_postgres.return_value = True

        with patch("render_environment_manager.console"):
            results = await process_postgres(
                client, sample_postgres, "resume", dry_run=False
            )

        # Should call resume for each database
        assert client.resume_postgres.call_count == 2
        client.resume_postgres.assert_has_calls([call("pg-1"), call("pg-2")])

        # All should be successful
        assert len(results["success"]) == 2
        assert len(results["failed"]) == 0

    @pytest.mark.asyncio
    async def test_process_postgres_mixed_results(self, sample_postgres):
        client = AsyncMock()
        # First call succeeds, second fails
        client.suspend_postgres.side_effect = [True, False]

        with patch("render_environment_manager.console"):
            results = await process_postgres(
                client, sample_postgres, "suspend", dry_run=False
            )

        # One successful, one failed
        assert len(results["success"]) == 1
        assert len(results["failed"]) == 1
        assert results["success"][0].id == "pg-1"
        assert results["failed"][0].id == "pg-2"


class TestCommandFunctions:
    """Test the main command functions"""

    @pytest.mark.asyncio
    async def test_suspend_success(self):
        mock_services = [
            RenderService(
                "srv-1", "service-1", "web_service", "preprod", "active", None
            )
        ]
        mock_databases = [
            RenderPostgres(
                "pg-1", "postgres-1", "db1", "preprod", "available", "starter"
            )
        ]

        with patch.dict(
            os.environ,
            {"render_api_key": "test-key", "render_preprod_env_id": "env-123"},
        ):
            with patch(
                "render_environment_manager.RenderAPIClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_services_by_environment.return_value = mock_services
                mock_client.get_postgres_by_environment.return_value = mock_databases
                mock_client_class.return_value = mock_client

                with patch(
                    "render_environment_manager.process_services"
                ) as mock_process_services:
                    with patch(
                        "render_environment_manager.process_postgres"
                    ) as mock_process_postgres:
                        mock_process_services.return_value = {
                            "success": mock_services,
                            "failed": [],
                        }
                        mock_process_postgres.return_value = {
                            "success": mock_databases,
                            "failed": [],
                        }

                        with patch("render_environment_manager.console"):
                            await _suspend(dry_run=True, force=True)

                        mock_client.get_services_by_environment.assert_called_once_with(
                            "env-123"
                        )
                        mock_client.get_postgres_by_environment.assert_called_once_with(
                            "env-123"
                        )
                        mock_process_services.assert_called_once()
                        mock_process_postgres.assert_called_once()

    @pytest.mark.asyncio
    async def test_suspend_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):  # Clear environment
            from typer import Exit

            with pytest.raises(Exit):
                await _suspend(dry_run=True, force=True)

    @pytest.mark.asyncio
    async def test_resume_success(self):
        mock_services = [
            RenderService(
                "srv-1", "service-1", "web_service", "preprod", "suspended", ["admin"]
            )
        ]
        mock_databases = [
            RenderPostgres(
                "pg-1", "postgres-1", "db1", "preprod", "suspended", "starter"
            )
        ]

        with patch.dict(
            os.environ,
            {"render_api_key": "test-key", "render_preprod_env_id": "env-123"},
        ):
            with patch(
                "render_environment_manager.RenderAPIClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_services_by_environment.return_value = mock_services
                mock_client.get_postgres_by_environment.return_value = mock_databases
                mock_client_class.return_value = mock_client

                with patch(
                    "render_environment_manager.process_services"
                ) as mock_process_services:
                    with patch(
                        "render_environment_manager.process_postgres"
                    ) as mock_process_postgres:
                        mock_process_services.return_value = {
                            "success": mock_services,
                            "failed": [],
                        }
                        mock_process_postgres.return_value = {
                            "success": mock_databases,
                            "failed": [],
                        }

                        with patch("render_environment_manager.console"):
                            await _resume(dry_run=True, force=True)

                        mock_client.get_services_by_environment.assert_called_once_with(
                            "env-123"
                        )
                        mock_client.get_postgres_by_environment.assert_called_once_with(
                            "env-123"
                        )
                        mock_process_services.assert_called_once()
                        mock_process_postgres.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_services_success(self):
        mock_services = [
            RenderService(
                "srv-1", "service-1", "web_service", "preprod", "active", None
            ),
            RenderService(
                "srv-2", "service-2", "worker", "preprod", "suspended", ["user"]
            ),
        ]
        mock_databases = [
            RenderPostgres(
                "pg-1", "postgres-1", "db1", "preprod", "available", "starter"
            ),
            RenderPostgres(
                "pg-2", "postgres-2", "db2", "preprod", "suspended", "standard"
            ),
        ]

        with patch.dict(
            os.environ,
            {"render_api_key": "test-key", "render_preprod_env_id": "env-123"},
        ):
            with patch(
                "render_environment_manager.RenderAPIClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get_services_by_environment.return_value = mock_services
                mock_client.get_postgres_by_environment.return_value = mock_databases
                mock_client_class.return_value = mock_client

                with patch("render_environment_manager.console"):
                    await _list_services()

                mock_client.get_services_by_environment.assert_called_once_with(
                    "env-123"
                )
                mock_client.get_postgres_by_environment.assert_called_once_with(
                    "env-123"
                )
