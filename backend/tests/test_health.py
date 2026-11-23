from fastapi.testclient import TestClient

from ridedesk.main import create_app
from ridedesk.settings import Settings


def test_health_reports_ok_when_database_is_reachable(client: TestClient) -> None:
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_when_database_is_unreachable() -> None:
    # Port 1 on localhost refuses connections, so the check fails fast.
    settings = Settings(database_url="postgresql+psycopg://nobody@127.0.0.1:1/none")

    with TestClient(create_app(settings)) as client:
        response = client.get("/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}
