import { createRouter, createWebHistory } from "vue-router";
import { useWalletStore } from "../stores/wallet.js";

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

// 路由守卫：检查管理员权限
router.beforeEach((to, from, next) => {
  next();
});

export default router;
