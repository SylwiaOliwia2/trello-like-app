import requests


def post_create_board(
    e2e_api_url: str,
    api_session: requests.Session,
    name: str,
    token: str | None = None,
) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    return api_session.post(
        f"{e2e_api_url}/boards",
        json={"name": name},
        headers=headers,
        timeout=10,
    )


def add_user_to_board(
    e2e_api_url: str,
    api_session: requests.Session,
    board_id: int,
    email: str,
    token: str | None = None,
) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    return api_session.post(
        f"{e2e_api_url}/boards/{board_id}/members",
        json={"email": email},
        headers=headers,
        timeout=10,
    )


def get_board(
    e2e_api_url: str,
    api_session: requests.Session,
    board_id: int,
    token: str | None = None,
) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    return api_session.get(
        f"{e2e_api_url}/boards/{board_id}",
        headers=headers,
        timeout=10,
    )
