"""
Revixa v2 — JWT Authentication Automated Tests
===============================================
Kullanıcı kayıt, giriş, şifre doğrulama ve JWT token testleri.
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


def test_user_register_and_login():
    test_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "securepassword123"

    # 1. User Registration
    reg_res = client.post("/auth/register", json={"email": test_email, "password": test_password})
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["email"] == test_email
    assert "id" in data

    # 2. Duplicate Registration Error
    dup_res = client.post("/auth/register", json={"email": test_email, "password": test_password})
    assert dup_res.status_code == 400
    assert "zaten kayıtlı" in dup_res.json()["detail"]

    # 3. User Login
    login_res = client.post("/auth/login", json={"email": test_email, "password": test_password})
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Fetch Current User Profile with JWT Header
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == test_email
