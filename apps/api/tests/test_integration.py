from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_cors_allows_chrome_extension_origin():
    """
    Verify that CORSMiddleware is active and correctly accepts
    requests from a chrome-extension origin.
    """
    origin = "chrome-extension://abcdefghijklmnop"

    response = client.options(
        "/api/v1/events/batch",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin


def test_cors_rejects_standard_web_origin():
    """
    Verify that standard web origins (like https://malicious.com)
    are NOT echoed in the allow-origin header by default.
    """
    origin = "https://malicious.com"

    response = client.options(
        "/api/v1/events/batch",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    # The header should NOT be present, or should not equal the malicious origin
    assert response.headers.get("access-control-allow-origin") != origin
