const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
  transpileDependencies: true,
  // 网络开发配置 - 支持外部访问
  devServer: {
    host: "0.0.0.0", // 允许外部访问
    port: 8008,
    // 添加代理配置 - 指向后端地址
    proxy: {
      "/api": {
        target: "http://127.0.0.1:6006",
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
