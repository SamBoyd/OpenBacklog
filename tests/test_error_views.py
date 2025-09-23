from src.main import app


class TestErrorEndpoints:
    def test_test_internal_server_error(self, test_client):
        # This should raise a 500 error which will be caught by the exception handler
        response = test_client.get("/test-internal-server-error")
        assert response.status_code == 500

    def test_test_not_found(self, test_client):
        # This should raise a 404 error which will be caught by the exception handler
        response = test_client.get("/definitely-not-a-real-route")
        assert response.status_code == 404
