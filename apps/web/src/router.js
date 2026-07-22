import { createRouter, createWebHistory } from "vue-router";
import LoginPage from "./views/LoginPage.vue";
import RegisterPage from "./views/RegisterPage.vue";
import HomePage from "./views/HomePage.vue";
import BoardPage from "./views/BoardPage.vue";

const routes = [
  { path: "/", redirect: "/home" },
  { path: "/login", component: LoginPage, meta: { guestOnly: true } },
  { path: "/register", component: RegisterPage, meta: { guestOnly: true } },
  { path: "/home", component: HomePage, meta: { requiresAuth: true } },
  {
    path: "/boards/:id",
    component: BoardPage,
    meta: { requiresAuth: true },
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = localStorage.getItem("auth_token");
  if (to.meta.requiresAuth && !token) {
    return "/login";
  }
  if (to.meta.guestOnly && token) {
    return "/home";
  }
  return true;
});

export default router;
