import { createRouter, createWebHistory } from "vue-router";
import { AUTH_TOKEN_KEY } from "../services/api.js";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("../views/HomeView.vue"),
  },
  {
    path: "/auth",
    name: "Auth",
    component: () => import("../views/AuthView.vue"),
  },
  {
    path: "/vote",
    name: "Vote",
    meta: { requiresAuth: true },
    component: () => import("../views/VoteView.vue"),
  },
  {
    path: "/results",
    name: "Results",
    component: () => import("../views/ResultsView.vue"),
  },
  {
    path: "/admin",
    name: "Admin",
    component: () => import("../views/AdminView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !window.localStorage.getItem(AUTH_TOKEN_KEY)) {
    next({ name: "Auth", query: { redirect: to.fullPath } });
    return;
  }
  next();
});

export default router;
