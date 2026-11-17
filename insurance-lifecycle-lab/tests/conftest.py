import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import pytest
import requests

from .client import APIClient
from .helpers import issue_policy

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def server():
    temp_dir = tempfile.mkdtemp(prefix="insurelab-test-")
    db_path = os.path.join(temp_dir, "test.db")
    port = _free_port()

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["JWT_SECRET"] = "test-jwt-secret"
    env["CALLBACK_TOKEN"] = "test-callback-token"
    env["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"

    ready = False
    for _ in range(100):
        if process.poll() is not None:
            break
        try:
            response = requests.get(f"{base_url}/health", timeout=0.5)
            if response.status_code == 200:
                ready = True
                break
        except requests.RequestException:
            pass
        time.sleep(0.1)

    if not ready:
        process.terminate()
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError("InsureLab test server failed to start")

    yield base_url

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def api(server):
    return APIClient(server)


@pytest.fixture
def unique_username():
    return f"u_{uuid.uuid4().hex[:10]}"


@pytest.fixture
def user_token(api, unique_username):
    return api.register_and_login(
        username=unique_username,
        id_no="110101199001011234",
    )["access_token"]


@pytest.fixture
def other_user_token(api):
    username = f"o_{uuid.uuid4().hex[:10]}"
    return api.register_and_login(
        username=username,
        id_no="110101199001019876",
    )["access_token"]


@pytest.fixture
def admin_token(api):
    response = api.login("admin", "Admin@123")
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def user_api(server, user_token):
    client = APIClient(server)
    client.token = user_token
    return client


@pytest.fixture
def other_user_api(server, other_user_token):
    client = APIClient(server)
    client.token = other_user_token
    return client


@pytest.fixture
def admin_api(server, admin_token):
    client = APIClient(server)
    client.token = admin_token
    return client


@pytest.fixture
def policy_context(user_api, admin_api):
    return issue_policy(user_api, admin_api)


@pytest.fixture
def policy(policy_context):
    return policy_context["policy"]
