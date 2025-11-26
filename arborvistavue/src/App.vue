<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-container">
        <!-- Logo区域 -->
        <div class="logo-section">
          <div class="logo-icon">
            <el-icon size="28">
              <Document />
            </el-icon>
          </div>
          <div class="logo-text">
            <h1 class="logo-title">ArborVista</h1>
            <span class="logo-subtitle">智能文档处理平台</span>
          </div>
        </div>

        <!-- 导航菜单 -->
        <nav class="nav-menu">
          <router-link
            to="/"
            class="nav-item"
            :class="{ active: $route.path === '/' }"
          >
            <el-icon><House /></el-icon>
            <span>首页</span>
          </router-link>
          <router-link
            to="/library"
            class="nav-item"
            :class="{ active: $route.path === '/library' }"
          >
            <el-icon><Collection /></el-icon>
            <span>文档库</span>
          </router-link>
        </nav>

        <!-- 用户信息区域 -->
        <div class="user-section">
          <el-dropdown @command="handleUserCommand" trigger="click">
            <div class="user-avatar">
              <el-icon><User /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <span class="user-info-text">{{ currentUsername }}</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <span style="display: flex; align-items: center; gap: 8px">
                    <el-icon><Close /></el-icon>
                    退出登录
                  </span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="app-main">
      <router-view v-slot="{ Component, route }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <!-- 底部信息 -->
    <footer class="app-footer">
      <div class="footer-container">
        <div class="footer-left">
          <p>&copy; 2025 ArborVista. 智能文档处理平台</p>
        </div>
        <div class="footer-right">
          <a href="#" class="footer-link">帮助中心</a>
          <a href="#" class="footer-link">隐私政策</a>
          <a href="#" class="footer-link">服务条款</a>
        </div>
      </div>
    </footer>

    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>
  </div>
</template>

<script>
import {
  Document,
  House,
  Collection,
  User,
  Close,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import axios from "axios";
import { getApiBaseUrl } from "@/config/api";

export default {
  name: "App",
  components: {
    Document,
    House,
    Collection,
    User,
    Close,
  },
  data() {
    return {
      currentUsername: "",
    };
  },
  mounted() {
    this.loadUserInfo();
  },
  methods: {
    loadUserInfo() {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          this.currentUsername = user.username || "用户";
        } catch (e) {
          console.error("解析用户信息失败:", e);
        }
      }
    },
    async handleUserCommand(command) {
      if (command === "logout") {
        try {
          await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
          });

          // 调用登出API
          const API_BASE_URL = getApiBaseUrl();
          try {
            await axios.post(`${API_BASE_URL}/api/auth/logout`);
          } catch (e) {
            console.error("登出API调用失败:", e);
          }

          // 清除本地存储
          localStorage.removeItem("user");
          localStorage.removeItem("user_id");
          this.currentUsername = "";

          ElMessage.success("已退出登录");
          // 跳转到登录页
          this.$router.push("/login");
        } catch (e) {
          // 用户取消
        }
      }
    },
  },
};
</script>

<style>
/* CSS变量定义 - Apple风格设计系统 */
:root {
  /* 主色调 - Apple蓝色系 */
  --primary-color: #007aff;
  --primary-light: #5ac8fa;
  --primary-dark: #0051d5;

  /* 中性色 */
  --text-primary: #1d1d1f;
  --text-secondary: #86868b;
  --text-tertiary: #c7c7cc;
  --text-inverse: #ffffff;

  /* 背景色 */
  --bg-primary: #ffffff;
  --bg-secondary: #f2f2f7;
  --bg-tertiary: #e5e5ea;
  --bg-dark: #1c1c1e;
  --bg-card: rgba(255, 255, 255, 0.8);
  --bg-glass: rgba(255, 255, 255, 0.1);

  /* 边框和分割线 */
  --border-light: #e5e5ea;
  --border-medium: #c7c7cc;
  --border-dark: #8e8e93;

  /* 阴影 */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.15);
  --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.2);

  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;

  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  --space-3xl: 64px;

  /* 字体 */
  --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
    "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas,
    "Courier New", monospace;

  /* 动画 */
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-family);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  overflow-x: hidden;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

/* 头部样式 - Apple风格 */
.app-header {
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  height: 72px;
  position: sticky;
  top: 0;
  z-index: 1000;
  transition: var(--transition-normal);
}

.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-lg);
}

.logo-section {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-light)
  );
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-inverse);
  box-shadow: var(--shadow-md);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.logo-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 400;
}

.nav-menu {
  display: flex;
  gap: var(--space-sm);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 15px;
  transition: var(--transition-fast);
  position: relative;
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-secondary);
}

.nav-item.active {
  color: var(--primary-color);
  background: rgba(0, 122, 255, 0.1);
}

.nav-item.active::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 2px;
  background: var(--primary-color);
  border-radius: 1px;
}

.user-section {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: var(--bg-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  cursor: pointer;
  transition: var(--transition-fast);
  border: 1px solid var(--border-light);
}

.user-avatar:hover {
  background: var(--bg-tertiary);
  transform: scale(1.05);
}

/* 主内容区域 */
.app-main {
  flex: 1;
  padding: 0;
  background: var(--bg-primary);
  position: relative;
  z-index: 1;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.4s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 底部样式 */
.app-footer {
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-light);
  height: 72px;
  margin-top: auto;
}

.footer-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-lg);
  color: var(--text-secondary);
}

.footer-left p {
  margin: 0;
  font-size: 14px;
}

.footer-right {
  display: flex;
  gap: var(--space-lg);
}

.footer-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: var(--transition-fast);
}

.footer-link:hover {
  color: var(--primary-color);
}

/* 背景装饰 */
.background-decoration {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    rgba(0, 122, 255, 0.05),
    rgba(90, 200, 250, 0.05)
  );
  animation: float 20s infinite ease-in-out;
}

.orb-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 200px;
  height: 200px;
  top: 60%;
  right: 10%;
  animation-delay: -7s;
}

.orb-3 {
  width: 150px;
  height: 150px;
  bottom: 20%;
  left: 50%;
  animation-delay: -14s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  33% {
    transform: translateY(-30px) rotate(120deg);
  }
  66% {
    transform: translateY(30px) rotate(240deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-container {
    padding: 0 var(--space-md);
  }

  .logo-title {
    font-size: 20px;
  }

  .logo-subtitle {
    display: none;
  }

  .nav-item span {
    display: none;
  }

  .footer-container {
    flex-direction: column;
    gap: var(--space-sm);
    text-align: center;
  }

  .orb-1,
  .orb-2,
  .orb-3 {
    display: none;
  }
}

/* 文档查看器激活时隐藏App导航栏 */
body.document-viewer-active .app-header {
  display: none !important;
}

body.document-viewer-active .app-footer {
  display: none !important;
}

/* Element Plus 组件样式覆盖 - Apple风格 */
.el-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--border-light) !important;
  background: var(--bg-card) !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: var(--shadow-md) !important;
  transition: var(--transition-normal) !important;
}

.el-card:hover {
  box-shadow: var(--shadow-lg) !important;
  transform: translateY(-2px) !important;
}

.el-button {
  border-radius: var(--radius-md) !important;
  font-weight: 500 !important;
  transition: var(--transition-normal) !important;
  border: none !important;
}

.el-button--primary {
  background: var(--primary-color) !important;
  color: var(--text-inverse) !important;
}

.el-button--primary:hover {
  background: var(--primary-dark) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow-md) !important;
}

.el-input__wrapper {
  border-radius: var(--radius-md) !important;
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-light) !important;
  transition: var(--transition-fast) !important;
}

.el-input__wrapper:hover {
  border-color: var(--border-medium) !important;
}

.el-input__wrapper.is-focus {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1) !important;
}

.el-select .el-input__wrapper {
  background: var(--bg-secondary) !important;
}

.el-upload {
  border-radius: var(--radius-lg) !important;
}

.el-upload-dragger {
  border-radius: var(--radius-lg) !important;
  background: var(--bg-secondary) !important;
  border: 2px dashed var(--border-medium) !important;
  transition: var(--transition-normal) !important;
}

.el-upload-dragger:hover {
  border-color: var(--primary-color) !important;
  background: rgba(0, 122, 255, 0.05) !important;
}

.el-dialog {
  border-radius: var(--radius-xl) !important;
  border: 1px solid var(--border-light) !important;
  box-shadow: var(--shadow-xl) !important;
}

.el-dialog__header {
  padding: var(--space-lg) var(--space-lg) var(--space-md) !important;
  border-bottom: 1px solid var(--border-light) !important;
}

.el-dialog__body {
  padding: var(--space-lg) !important;
}

.el-table {
  border-radius: var(--radius-lg) !important;
  overflow: hidden !important;
}

.el-table th {
  background: var(--bg-secondary) !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
}

.el-table td {
  border-bottom: 1px solid var(--border-light) !important;
}

.el-pagination {
  justify-content: center !important;
}

.el-pagination .el-pager li {
  border-radius: var(--radius-sm) !important;
  margin: 0 var(--space-xs) !important;
}

.el-pagination .el-pager li.is-active {
  background: var(--primary-color) !important;
  color: var(--text-inverse) !important;
}
</style>
