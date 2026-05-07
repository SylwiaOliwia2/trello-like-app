import requests


def get_auth_me(
    e2e_api_url: str, api_session: requests.Session, token: str | None = None
) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    return api_session.get(f"{e2e_api_url}/auth/me", headers=headers, timeout=10)


def post_auth_login(
    e2e_api_url: str, api_session: requests.Session, email: str, password: str
) -> requests.Response:
    return api_session.post(
        f"{e2e_api_url}/auth/login",
        json={"email": email, "password": password, "otp": None},
        timeout=10,
    )
