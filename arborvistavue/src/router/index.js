import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Library from "../views/Library.vue";
import Login from "../views/Login.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    name: "home",
    component: Home,
    meta: { requiresAuth: true },
  },
  {
    path: "/library",
    name: "library",
    component: Library,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const user_id = localStorage.getItem("user_id");
  const isAuthenticated = !!user_id;

  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      // 未登录，跳转到登录页
      next({ name: "login" });
    } else {
      next();
    }
  } else {
    // 如果已登录且访问登录页，跳转到首页
    if (to.name === "login" && isAuthenticated) {
      next({ name: "home" });
    } else {
      next();
    }
  }
});

export default router;
