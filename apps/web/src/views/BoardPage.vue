<template>
  <section class="board-page">
    <p>
      <router-link to="/home" data-testid="back-to-home"
        >&larr; Back</router-link
      >
    </p>

    <p v-if="loading" data-testid="board-loading">Loading...</p>

    <p v-if="loadError" class="error" data-testid="board-load-error">
      {{ loadError }}
    </p>

    <section v-if="board && !loadError" class="board-content">
      <header class="board-header">
        <h2 data-testid="board-name">{{ board.name }}</h2>
        <span class="role-badge" data-testid="board-my-role">
          You: {{ board.role }}
        </span>
      </header>

      <section class="members-section">
        <h3>Members</h3>
        <ul class="members-list" data-testid="members-list">
          <li
            v-for="m in board.members"
            :key="m.user_id"
            class="member-item"
            :data-testid="`member-item-${m.user_id}`"
          >
            <span :data-testid="`member-email-${m.user_id}`">
              {{ m.email }}
            </span>
            <span class="role-badge" :data-testid="`member-role-${m.user_id}`">
              {{ m.role }}
            </span>
            <button
              v-if="isOwner && m.user_id !== board.owner_id"
              @click="onRemoveMember(m.user_id)"
              class="danger-btn"
              :data-testid="`remove-member-${m.user_id}`"
            >
              Remove
            </button>
          </li>
        </ul>

        <section
          v-if="isOwner"
          class="add-member"
          data-testid="add-member-section"
        >
          <h4>Add member</h4>
          <select
            v-model="selectedEmail"
            data-testid="add-member-select"
            class="member-select"
          >
            <option value="" disabled>Select a user by email...</option>
            <option
              v-for="u in addableUsers"
              :key="u.id"
              :value="u.email"
              :data-testid="`add-member-option-${u.id}`"
            >
              {{ u.email }}
            </option>
          </select>
          <button
            @click="onAddMember"
            :disabled="!selectedEmail"
            data-testid="add-member-submit"
          >
            Add member
          </button>
          <p v-if="addError" class="error" data-testid="add-member-error">
            {{ addError }}
          </p>
        </section>
      </section>

      <section class="lists-area" data-testid="lists-placeholder">
        <p class="hint">Lists will appear here in a future phase.</p>
      </section>

      <section class="board-actions">
        <button
          v-if="!isOwner"
          @click="onLeaveBoard"
          class="danger-btn"
          data-testid="leave-board"
        >
          Leave board
        </button>

        <button
          v-if="isOwner"
          @click="confirmDelete = true"
          class="danger-btn"
          data-testid="delete-board"
        >
          Delete board
        </button>
      </section>

      <section
        v-if="confirmDelete"
        class="confirm-popup"
        data-testid="delete-board-confirm"
      >
        <p>
          Are you sure you want to delete this board? This cannot be undone.
        </p>
        <div class="confirm-actions">
          <button
            @click="onDeleteBoard"
            class="danger-btn"
            data-testid="delete-board-confirm-yes"
          >
            Yes, delete
          </button>
          <button
            @click="confirmDelete = false"
            data-testid="delete-board-confirm-no"
          >
            Cancel
          </button>
        </div>
      </section>

      <p v-if="actionError" class="error" data-testid="board-action-error">
        {{ actionError }}
      </p>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  addBoardMember,
  deleteBoard,
  getBoard,
  getMe,
  leaveBoard,
  listUsers,
  removeBoardMember,
} from "../lib/api";

const route = useRoute();
const router = useRouter();

const board = ref(null);
const me = ref(null);
const users = ref([]);
const loading = ref(true);
const loadError = ref("");
const actionError = ref("");
const addError = ref("");
const selectedEmail = ref("");
const confirmDelete = ref(false);

const isOwner = computed(() => board.value && board.value.role === "owner");

const addableUsers = computed(() => {
  if (!board.value) return [];
  const memberIds = new Set(board.value.members.map((m) => m.user_id));
  return users.value.filter((u) => !memberIds.has(u.id));
});

function getToken() {
  return localStorage.getItem("auth_token");
}

async function refreshBoard() {
  loadError.value = "";
  const token = getToken();
  if (!token) {
    router.push("/login");
    return;
  }
  try {
    board.value = await getBoard(token, route.params.id);
  } catch (err) {
    loadError.value = err.message || "Failed to load board";
    board.value = null;
  }
}

async function refreshUsers() {
  const token = getToken();
  if (!token) return;
  try {
    users.value = await listUsers(token);
  } catch {
    users.value = [];
  }
}

async function onAddMember() {
  addError.value = "";
  const token = getToken();
  if (!token || !selectedEmail.value) return;
  try {
    await addBoardMember(token, route.params.id, selectedEmail.value);
    selectedEmail.value = "";
    await refreshBoard();
  } catch (err) {
    addError.value = err.message || "Failed to add member";
  }
}

async function onRemoveMember(userId) {
  actionError.value = "";
  const token = getToken();
  if (!token) return;
  try {
    await removeBoardMember(token, route.params.id, userId);
    await refreshBoard();
  } catch (err) {
    actionError.value = err.message || "Failed to remove member";
  }
}

async function onLeaveBoard() {
  actionError.value = "";
  const token = getToken();
  if (!token) return;
  try {
    await leaveBoard(token, route.params.id);
    router.push("/home");
  } catch (err) {
    actionError.value = err.message || "Failed to leave board";
  }
}

async function onDeleteBoard() {
  actionError.value = "";
  const token = getToken();
  if (!token) return;
  try {
    await deleteBoard(token, route.params.id);
    router.push("/home");
  } catch (err) {
    actionError.value = err.message || "Failed to delete board";
    confirmDelete.value = false;
  }
}

onMounted(async () => {
  const token = getToken();
  if (!token) {
    router.push("/login");
    return;
  }
  try {
    me.value = await getMe(token);
  } catch {
    localStorage.removeItem("auth_token");
    router.push("/login");
    return;
  }
  await refreshBoard();
  await refreshUsers();
  loading.value = false;
});
</script>

<style scoped>
.board-page {
  color: #0f172a;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.role-badge {
  font-size: 0.8rem;
  background: #e2e8f0;
  color: #334155;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  text-transform: capitalize;
}

.members-section {
  margin-top: 1rem;
}

.members-list {
  list-style: none;
  padding: 0;
  margin: 0 0 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.member-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.5rem 0.7rem;
  background: #f8fafc;
}

.add-member {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  align-items: center;
}

.add-member h4 {
  grid-column: 1 / -1;
  margin: 0.2rem 0;
}

.member-select {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.55rem 0.7rem;
  font-size: 0.95rem;
  background: #fff;
}

.add-member button {
  border: 0;
  border-radius: 10px;
  padding: 0.6rem 0.9rem;
  background: #2563eb;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.add-member button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.danger-btn {
  border: 0;
  border-radius: 10px;
  padding: 0.45rem 0.75rem;
  background: #dc2626;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.lists-area {
  margin-top: 1.2rem;
  padding: 1rem;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  text-align: center;
  background: #f8fafc;
}

.hint {
  color: #64748b;
  margin: 0;
}

.board-actions {
  margin-top: 1.2rem;
  display: flex;
  gap: 0.5rem;
}

.confirm-popup {
  margin-top: 0.8rem;
  padding: 0.8rem;
  border: 1px solid #fecaca;
  background: #fef2f2;
  border-radius: 10px;
}

.confirm-actions {
  display: flex;
  gap: 0.5rem;
}

.confirm-actions button {
  border: 0;
  border-radius: 10px;
  padding: 0.5rem 0.8rem;
  background: #334155;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.error {
  color: #b91c1c;
}
</style>
