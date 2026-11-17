import requests


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = None

    def request(self, method, path, json=None, headers=None, token=None, **kwargs):
        final_headers = dict(headers or {})
        active_token = token if token is not None else self.token
        if active_token:
            final_headers["Authorization"] = f"Bearer {active_token}"
        return self.session.request(
            method,
            self.base_url + path,
            json=json,
            headers=final_headers,
            timeout=10,
            **kwargs,
        )

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, json=None, **kwargs):
        return self.request("POST", path, json=json, **kwargs)

    def register(
        self,
        username,
        password="Test@123",
        full_name="Automation Tester",
        phone="13800000000",
        id_no="110101199001011234",
    ):
        return self.post(
            "/api/v1/auth/register",
            json={
                "username": username,
                "password": password,
                "full_name": full_name,
                "phone": phone,
                "id_no": id_no,
            },
        )

    def login(self, username, password):
        return self.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    def register_and_login(self, username, password="Test@123", **kwargs):
        registered = self.register(username=username, password=password, **kwargs)
        assert registered.status_code == 201, registered.text
        logged_in = self.login(username, password)
        assert logged_in.status_code == 200, logged_in.text
        return logged_in.json()
