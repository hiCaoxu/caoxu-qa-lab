def test_register_success(api):
    response = api.register("auth_register_success", id_no="110101199001011111")
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "auth_register_success"
    assert body["role"] == "USER"
    assert "password_hash" not in body


def test_register_duplicate_username(api):
    assert api.register("auth_duplicate").status_code == 201
    response = api.register("auth_duplicate")
    assert response.status_code == 409
    assert response.json()["code"] == "USERNAME_EXISTS"


def test_login_success(api):
    api.register("auth_login_success", password="Login@123")
    response = api.login("auth_login_success", "Login@123")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"]


def test_login_wrong_password(api):
    api.register("auth_wrong_password", password="Right@123")
    response = api.login("auth_wrong_password", "Wrong@123")
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_me_with_token(user_api):
    response = user_api.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["username"].startswith("u_")


def test_me_without_token(api):
    response = api.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_admin_me(admin_api):
    response = admin_api.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
