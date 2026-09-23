def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "uptime_checks_total" in response.text or response.text is not None


def test_create_and_list_targets(client):
    created = client.post(
        "/targets",
        json={"name": "Example", "url": "https://example.com/health"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Example"
    assert body["last_status"] == "unknown"

    listed = client.get("/targets")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_duplicate_url_conflict(client):
    payload = {"name": "A", "url": "https://example.com/health"}
    assert client.post("/targets", json=payload).status_code == 201
    assert client.post("/targets", json=payload).status_code == 409


def test_dashboard_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "uptime-ops" in response.text
