<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-section">
          <el-icon size="48" class="logo-icon">
            <Document />
          </el-icon>
          <h1 class="logo-title">ArborVista</h1>
          <p class="logo-subtitle">智能文档处理平台</p>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-button"
                :loading="isLogging"
                @click="handleLogin"
              >
                {{ isLogging ? "登录中..." : "登录" }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="用户名（3-20个字符）"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="密码（至少6个字符）"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="确认密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleRegister"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-button"
                :loading="isRegistering"
                @click="handleRegister"
              >
                {{ isRegistering ? "注册中..." : "注册" }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { Document, User, Lock } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import axios from "axios";
import { getApiBaseUrl } from "@/config/api";

export default {
  name: "LoginView",
  components: {
    Document,
  },
  data() {
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.registerForm.password) {
        callback(new Error("两次输入的密码不一致"));
      } else {
        callback();
      }
    };

    return {
      // 图标组件用于 prefix-icon 属性
      User,
      Lock,
      activeTab: "login",
      loginForm: {
        username: "",
        password: "",
      },
      registerForm: {
        username: "",
        password: "",
        confirmPassword: "",
      },
      loginRules: {
        username: [
          { required: true, message: "请输入用户名", trigger: "blur" },
        ],
        password: [{ required: true, message: "请输入密码", trigger: "blur" }],
      },
      registerRules: {
        username: [
          { required: true, message: "请输入用户名", trigger: "blur" },
          {
            min: 3,
            max: 20,
            message: "用户名长度在 3 到 20 个字符",
            trigger: "blur",
          },
        ],
        password: [
          { required: true, message: "请输入密码", trigger: "blur" },
          {
            min: 6,
            message: "密码长度至少 6 个字符",
            trigger: "blur",
          },
        ],
        confirmPassword: [
          { required: true, message: "请确认密码", trigger: "blur" },
          { validator: validateConfirmPassword, trigger: "blur" },
        ],
      },
      isLogging: false,
      isRegistering: false,
    };
  },
  methods: {
    async handleLogin() {
      try {
        await this.$refs.loginFormRef.validate();
        this.isLogging = true;

        const API_BASE_URL = getApiBaseUrl();
        const response = await axios.post(
          `${API_BASE_URL}/api/auth/login`,
          this.loginForm
        );

        if (response.data.success) {
          ElMessage.success("登录成功");
          // 保存用户信息到localStorage
          localStorage.setItem("user", JSON.stringify(response.data.user));
          localStorage.setItem("user_id", response.data.user.user_id);
          // 跳转到首页
          this.$router.push("/");
        } else {
          ElMessage.error(response.data.error || "登录失败");
        }
      } catch (error) {
        console.error("登录失败:", error);
        if (error.response && error.response.data) {
          ElMessage.error(error.response.data.error || "登录失败");
        } else {
          ElMessage.error("登录失败，请重试");
        }
      } finally {
        this.isLogging = false;
      }
    },
    async handleRegister() {
      try {
        await this.$refs.registerFormRef.validate();
        this.isRegistering = true;

        const API_BASE_URL = getApiBaseUrl();
        const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
          username: this.registerForm.username,
          password: this.registerForm.password,
        });

        if (response.data.success) {
          ElMessage.success("注册成功，已自动登录");
          // 保存用户信息到localStorage
          localStorage.setItem("user", JSON.stringify(response.data.user));
          localStorage.setItem("user_id", response.data.user.user_id);
          // 跳转到首页
          this.$router.push("/");
        } else {
          ElMessage.error(response.data.error || "注册失败");
        }
      } catch (error) {
        console.error("注册失败:", error);
        if (error.response && error.response.data) {
          ElMessage.error(error.response.data.error || "注册失败");
        } else {
          ElMessage.error("注册失败，请重试");
        }
      } finally {
        this.isRegistering = false;
      }
    },
  },
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    135deg,
    var(--bg-primary) 0%,
    var(--bg-secondary) 100%
  );
  padding: var(--space-lg);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-xl);
  backdrop-filter: blur(20px);
  padding: var(--space-3xl);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.logo-icon {
  color: var(--primary-color);
  filter: drop-shadow(0 4px 12px rgba(0, 122, 255, 0.3));
}

.logo-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -1px;
}

.logo-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.login-tabs {
  margin-top: var(--space-lg);
}

.login-form {
  margin-top: var(--space-lg);
}

.login-button {
  width: 100%;
  padding: var(--space-md);
  font-size: 16px;
  font-weight: 600;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  transition: var(--transition-normal);
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

:deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
}

:deep(.el-input__wrapper) {
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  transition: var(--transition-fast);
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--border-medium);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}
</style>
