<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <h1>ArborVista</h1>
        </div>
        <nav class="nav">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/library" class="nav-link">我的文库</router-link>
        </nav>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- 底部信息 -->
    <footer class="footer">
      <div class="footer-content">
        <p>&copy; 2025 览树 - 让论文阅读更简单</p>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: "App",
};
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, sans-serif;
  background-color: #f5f5f7;
  color: #1d1d1f;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏样式 */
.header {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.8rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo h1 {
  font-size: 1.6rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav {
  display: flex;
  gap: 2rem;
}

.nav-link {
  text-decoration: none;
  color: #1d1d1f;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: #007aff;
}

.nav-link.router-link-active {
  color: #007aff;
  background-color: rgba(0, 122, 255, 0.1);
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

/* 底部样式 */
.footer {
  background-color: #f5f5f7;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
  color: #86868b;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .nav {
    gap: 1rem;
  }

  .main-content {
    padding: 1rem;
  }
}
</style>
