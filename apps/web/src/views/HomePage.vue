<template>
  <section class="home">
    <h2 data-testid="home-title">Home</h2>
    <p v-if="email" data-testid="home-email">
      Logged in as <strong>{{ email }}</strong>
    </p>
    <p v-else>Loading profile...</p>
    <button @click="logout" data-testid="logout-button" class="logout-btn">
      Logout
    </button>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getMe } from "../lib/api";

const router = useRouter();
const email = ref("");

function logout() {
  localStorage.removeItem("auth_token");
  router.push("/login");
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
  } catch {
    logout();
  }
});
</script>

<style scoped>
.home {
  color: #0f172a;
}

.logout-btn {
  margin-top: 0.75rem;
  border: 0;
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  background: #dc2626;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
</style>
