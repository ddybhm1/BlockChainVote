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
    redirect: (to) => ({
      name: "Home",
      query: {
        ...to.query,
        login: "1",
        redirect: typeof to.query.redirect === "string" ? to.query.redirect : "/dashboard",
      },
    }),
  },
  {
    path: "/dashboard",
    alias: "/vote",
    name: "Dashboard",
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
  const hasToken = Boolean(window.localStorage.getItem(AUTH_TOKEN_KEY));

  if (to.name === "Home" && hasToken && to.query.preview !== "1") {
    next({ name: "Dashboard" });
    return;
  }

  if (to.meta.requiresAuth && !hasToken) {
    next({ name: "Home", query: { login: "1", redirect: to.fullPath } });
    return;
  }
  next();
});

export default router;
