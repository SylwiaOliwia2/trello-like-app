<template>
  <section class="page">
    <h2>Register</h2>

    <form @submit.prevent="onRegister" class="form">
      <input v-model="email" type="email" placeholder="Email" required data-testid="register-email" />

      <div class="password-row">
        <input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          placeholder="Password"
          required
          data-testid="register-password"
        />
      </div>

      <input
        v-model="confirmPassword"
        :type="showPassword ? 'text' : 'password'"
        placeholder="Confirm password"
        required
        data-testid="register-password-confirm"
      />

      <button type="button" @click="showPassword = !showPassword" class="small-btn">
          {{ showPassword ? "Hide" : "Show" }}
        </button>

      <label class="checkbox-row">
        <input v-model="mfaEnabled" type="checkbox" data-testid="register-mfa-enabled" />
        Enable MFA (recommended)
      </label>

      <button type="submit" data-testid="register-submit">Create account</button>
    </form>

    <section v-if="showMfaSetup" class="mfa-card" data-testid="register-mfa-setup">
      <h3>MFA setup</h3>
      <p>Scan QR in your authenticator app. This is shown only once.</p>
      <img v-if="mfaQrCodeDataUrl" :src="mfaQrCodeDataUrl" alt="MFA QR code" class="qr" />
      <p class="hint">Then login and enter the 6-digit code.</p>
    </section>

    <p v-if="success" class="success">{{ success }}</p>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="footer-link">
      Already have account?
      <router-link to="/login" data-testid="go-to-login">Login</router-link>
    </p>
  </section>
</template>

<script setup>
import { ref } from "vue";
import QRCode from "qrcode";
import { register } from "../lib/api";

const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const showPassword = ref(false);
const mfaEnabled = ref(false);
const success = ref("");
const error = ref("");
const showMfaSetup = ref(false);
const mfaQrCodeDataUrl = ref("");

async function onRegister() {
  success.value = "";
  error.value = "";
  showMfaSetup.value = false;
  mfaQrCodeDataUrl.value = "";

  if (password.value !== confirmPassword.value) {
    error.value = "Passwords do not match";
    return;
  }

  try {
    const response = await register({
      email: email.value,
      password: password.value,
      mfa_enabled: mfaEnabled.value,
    });
    success.value = `Account created for ${response.email}`;
    if (response.mfa_enabled && response.mfa_otpauth_url) {
      mfaQrCodeDataUrl.value = await QRCode.toDataURL(response.mfa_otpauth_url, {
        margin: 1,
        width: 220,
      });
      showMfaSetup.value = true;
    }
  } catch (err) {
    error.value = err.message || "Registration failed";
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

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #334155;
  font-size: 0.95rem;
}

.mfa-card {
  margin-top: 1rem;
  border: 1px solid #bae6fd;
  background: #f0f9ff;
  padding: 0.9rem;
  border-radius: 12px;
}

.mfa-card h3 {
  margin: 0 0 0.4rem;
}

.qr {
  border-radius: 10px;
  background: #fff;
  padding: 0.35rem;
}

.hint {
  color: #334155;
  font-size: 0.9rem;
}

.success {
  color: #166534;
}

.error {
  color: #b91c1c;
}

.footer-link {
  margin-top: 0.6rem;
}
</style>
