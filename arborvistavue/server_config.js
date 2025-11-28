/**
 * 服务器端口映射配置（Node.js 环境使用，用于 vue.config.js）
 * 直接修改此文件中的变量即可，无需配置环境变量
 *
 * 注意：如果修改了此文件，请同步修改 src/config/server_config.js（用于前端代码）
 */

// 后端端口配置
const BACKEND_PORT = 6006;
const FRONTEND_PORT = 6008;

// 端口映射配置（本地端口 -> 服务器URL）
const PORT_MAPPING = {
  6006: "https://u486956-b5fb-82b008e7.westb.seetacloud.com:8443",
  6008: "https://uu486956-b5fb-82b008e7.westb.seetacloud.com:8443",
};

module.exports = {
  BACKEND_PORT,
  FRONTEND_PORT,
  PORT_MAPPING,
  getServerUrl: (localPort) => PORT_MAPPING[String(localPort)] || null,
};
