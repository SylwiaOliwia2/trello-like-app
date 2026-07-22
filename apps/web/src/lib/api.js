const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (window.location.hostname === "web"
    ? "http://api:8000"
    : "http://localhost:8000");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }

  return data;
}

export async function register(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function confirmRegister(payload) {
  return request("/auth/register/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMe(token) {
  return request("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

export async function listBoards(token) {
  return request("/boards", { headers: authHeaders(token) });
}

export async function createBoard(token, name) {
  return request("/boards", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ name }),
  });
}

export async function getBoard(token, boardId) {
  return request(`/boards/${boardId}`, { headers: authHeaders(token) });
}

export async function deleteBoard(token, boardId) {
  return request(`/boards/${boardId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export async function addBoardMember(token, boardId, email) {
  return request(`/boards/${boardId}/members`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ email }),
  });
}

export async function removeBoardMember(token, boardId, userId) {
  return request(`/boards/${boardId}/members/${userId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export async function leaveBoard(token, boardId) {
  return request(`/boards/${boardId}/leave`, {
    method: "POST",
    headers: authHeaders(token),
  });
}

export async function listUsers(token) {
  return request("/users", { headers: authHeaders(token) });
}
