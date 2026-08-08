"""
Revixa v2 — Saved Apps Dashboard Automated Tests
=================================================
Kullanıcının panelinde uygulama kaydetme, listeleme ve silme testleri.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app
from database import init_db

client = TestClient(app)


import uuid


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_saved_apps_crud():
    test_email = f"app_owner_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "password123"

    # 1. Register & Login
    client.post("/auth/register", json={"email": test_email, "password": test_password})
    login_res = client.post("/auth/login", json={"email": test_email, "password": test_password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add Saved App
    create_res = client.post(
        "/user/apps",
        json={
            "title": "Goodnotes Test",
            "play_url": "https://play.google.com/store/apps/details?id=com.orion.notein.global&hl=tr"
        },
        headers=headers
    )
    assert create_res.status_code == 201
    app_data = create_res.json()
    assert app_data["title"] == "Goodnotes Test"
    app_id = app_data["id"]

    # 3. Get Saved Apps List
    get_res = client.get("/user/apps", headers=headers)
    assert get_res.status_code == 200
    apps_list = get_res.json()
    assert len(apps_list) >= 1
    assert any(a["id"] == app_id for a in apps_list)

    # 4. Delete Saved App
    del_res = client.delete(f"/user/apps/{app_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify App is Deleted
    get_res2 = client.get("/user/apps", headers=headers)
    assert not any(a["id"] == app_id for a in get_res2.json())
