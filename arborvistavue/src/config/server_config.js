/**
 * 服务器端口映射配置
 * 直接修改此文件中的变量即可，无需配置环境变量
 *
 * 注意：如果修改了此文件，请同步修改根目录下的 server_config.js（用于 vue.config.js）
 */

// 后端端口配置
export const BACKEND_PORT = 6006;
export const FRONTEND_PORT = 6008;

// 端口映射配置（本地端口 -> 服务器URL）
export const PORT_MAPPING = {
  6006: "https://u486956-b5fb-82b008e7.westb.seetacloud.com:8443",
  6008: "https://uu486956-b5fb-82b008e7.westb.seetacloud.com:8443",
};

/**
 * 根据本地端口获取服务器映射URL
 * @param {string|number} localPort - 本地端口号
 * @returns {string|null} 服务器URL，如果未配置则返回null
 */
export function getServerUrl(localPort) {
  return PORT_MAPPING[String(localPort)] || null;
}
