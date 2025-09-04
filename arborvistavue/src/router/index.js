import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Library from "../views/Library.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: Home,
  },
  {
    path: "/library",
    name: "library",
    component: Library,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
