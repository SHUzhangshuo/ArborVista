const { defineConfig } = require("@vue/cli-service");
module.exports = defineConfig({
  transpileDependencies: true,
  // 允许外部访问配置
  devServer: {
    host: "localhost", // 只允许本地访问
    port: 8080,
    allowedHosts: "localhost", // 只允许localhost主机
    client: {
      webSocketURL: "auto://localhost:0/ws", // WebSocket配置
    },
  },
});
