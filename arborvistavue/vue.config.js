const { defineConfig } = require("@vue/cli-service");

// 从 server_config.js 读取端口配置
// 注意：这里使用 require 因为 vue.config.js 是 Node.js 环境
const serverConfig = require("./server_config.js");

const FRONTEND_PORT = serverConfig.FRONTEND_PORT;
const BACKEND_PORT = serverConfig.BACKEND_PORT;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

module.exports = defineConfig({
  transpileDependencies: true,
  // 网络开发配置 - 支持外部访问
  devServer: {
    host: "0.0.0.0", // 允许外部访问
    port: parseInt(FRONTEND_PORT),
    // 添加代理配置 - 指向后端地址
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false,
      },
    },
    // 允许外部访问
    allowedHosts: "all",
    // 禁用主机检查
    client: {
      webSocketURL: "auto://0.0.0.0:0/ws",
    },
  },
});
