<template>
  <section class="home">
    <header class="home-header">
      <h2 data-testid="home-title">Home</h2>
      <button @click="logout" data-testid="logout-button" class="logout-btn">
        Logout
      </button>
    </header>

    <p v-if="email" data-testid="home-email">
      Logged in as <strong>{{ email }}</strong>
    </p>
    <p v-else>Loading profile...</p>

    <section class="boards-section">
      <h3>My boards</h3>

      <form @submit.prevent="onCreateBoard" class="create-board-form">
        <input
          v-model="newBoardName"
          type="text"
          placeholder="Board name"
          required
          data-testid="create-board-name"
        />
        <button type="submit" data-testid="create-board-submit">
          Create board
        </button>
      </form>

      <p v-if="boardsError" class="error" data-testid="boards-error">
        {{ boardsError }}
      </p>

      <ul v-if="boards.length" class="boards-list" data-testid="boards-list">
        <li
          v-for="b in boards"
          :key="b.id"
          class="board-item"
          :data-testid="`board-item-${b.id}`"
        >
          <router-link
            :to="`/boards/${b.id}`"
            :data-testid="`board-link-${b.id}`"
            class="board-link"
          >
            {{ b.name }}
          </router-link>
          <span class="role-badge" :data-testid="`board-role-${b.id}`">
            {{ b.role }}
          </span>
        </li>
      </ul>
      <p v-else-if="!loading" data-testid="boards-empty">
        You don't belong to any boards yet.
      </p>
    </section>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { createBoard, getMe, listBoards } from "../lib/api";

const router = useRouter();
const email = ref("");
const boards = ref([]);
const newBoardName = ref("");
const boardsError = ref("");
const loading = ref(true);

function logout() {
  localStorage.removeItem("auth_token");
  router.push("/login");
}

async function loadBoards() {
  boardsError.value = "";
  const token = localStorage.getItem("auth_token");
  if (!token) return;
  try {
    boards.value = await listBoards(token);
  } catch (err) {
    boardsError.value = err.message || "Failed to load boards";
  }
}

async function onCreateBoard() {
  boardsError.value = "";
  const token = localStorage.getItem("auth_token");
  if (!token) return;
  try {
    const board = await createBoard(token, newBoardName.value.trim());
    boards.value = [board, ...boards.value];
    newBoardName.value = "";
  } catch (err) {
    boardsError.value = err.message || "Failed to create board";
  }
}

onMounted(async () => {
  const token = localStorage.getItem("auth_token");
  if (!token) {
    router.push("/login");
    return;
  }
  try {
    const me = await getMe(token);
    email.value = me.email;
    await loadBoards();
  } catch {
    logout();
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.home {
  color: #0f172a;
}

.home-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logout-btn {
  border: 0;
  border-radius: 10px;
  padding: 0.5rem 0.8rem;
  background: #dc2626;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.boards-section {
  margin-top: 1.2rem;
}

.boards-section h3 {
  margin: 0 0 0.6rem;
}

.create-board-form {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.create-board-form input {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.6rem 0.8rem;
  font-size: 0.95rem;
}

.create-board-form button {
  border: 0;
  border-radius: 10px;
  padding: 0.6rem 0.9rem;
  background: #2563eb;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.boards-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.board-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.6rem 0.8rem;
  background: #f8fafc;
}

.board-link {
  color: #1e3a8a;
  text-decoration: none;
  font-weight: 600;
}

.board-link:hover {
  text-decoration: underline;
}

.role-badge {
  font-size: 0.8rem;
  background: #e2e8f0;
  color: #334155;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  text-transform: capitalize;
}

.error {
  color: #b91c1c;
}
</style>
