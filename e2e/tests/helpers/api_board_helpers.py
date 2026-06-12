import requests


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


def get_board_member_id_by_email(
    e2e_api_url: str,
    api_session: requests.Session,
    board_id: int,
    email: str,
    token: str | None = None,
) -> int:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    response = api_session.get(
        f"{e2e_api_url}/boards/{board_id}",
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return next(m["user_id"] for m in response.json()["members"] if m["email"] == email)
