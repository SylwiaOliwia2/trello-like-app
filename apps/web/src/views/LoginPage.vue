<template>
  <section class="page">
    <h2>Login</h2>

    <form @submit.prevent="onLogin" class="form">
      <input v-model="email" type="email" placeholder="Email" required data-testid="login-email" />

      <div class="password-row">
        <input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          placeholder="Password"
          required
          data-testid="login-password"
        />
        <button type="button" @click="showPassword = !showPassword" class="small-btn">
          {{ showPassword ? "Hide" : "Show" }}
        </button>
      </div>

      <input
        v-if="mfaRequired"
        v-model="otp"
        type="text"
        placeholder="6-digit code"
        required
        data-testid="login-otp"
      />

      <button type="submit" data-testid="login-submit">
        {{ mfaRequired ? "Verify OTP & Login" : "Login" }}
      </button>
    </form>

    <p v-if="mfaRequired" class="hint">Enter code from Google Authenticator / Authy / Microsoft Authenticator.</p>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="footer-link">
      No account?
      <router-link to="/register" data-testid="go-to-register">Register</router-link>
    </p>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../lib/api";

const router = useRouter();
const email = ref("");
const password = ref("");
const otp = ref("");
const mfaRequired = ref(false);
const error = ref("");
const showPassword = ref(false);

async function onLogin() {
  error.value = "";
  try {
    const payload = {
      email: email.value,
      password: password.value,
      otp: otp.value || null,
    };
    const response = await login(payload);
    if (response.mfa_required) {
      mfaRequired.value = true;
      return;
    }
    localStorage.setItem("auth_token", response.access_token);
    router.push("/home");
  } catch (err) {
    error.value = err.message || "Login failed";
  }
}
</script>

<style scoped>
.page {
  color: #0f172a;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

input {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.7rem 0.8rem;
  font-size: 0.95rem;
}

button {
  border: 0;
  border-radius: 10px;
  padding: 0.75rem 0.9rem;
  background: #2563eb;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.password-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
}

.small-btn {
  background: #334155;
  padding: 0.5rem 0.8rem;
  font-size: 0.85rem;
}

.hint {
  margin-top: 0.7rem;
  color: #334155;
  font-size: 0.9rem;
}

.error {
  color: #b91c1c;
}

.footer-link {
  margin-top: 0.6rem;
}
</style>
