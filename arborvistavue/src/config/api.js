// API 配置文件
const API_BASE_URL = process.env.VUE_APP_API_URL || "http://localhost:5000";

export const API_ENDPOINTS = {
  UPLOAD: `${API_BASE_URL}/api/upload`,
  FILES: `${API_BASE_URL}/api/files`,
  HEALTH: `${API_BASE_URL}/api/health`,
  CONFIG_OPTIONS: `${API_BASE_URL}/api/config/options`,
};

export const getFileContentUrl = (fileId) =>
  `${API_BASE_URL}/api/files/${fileId}/content`;
export const getFileDeleteUrl = (fileId) =>
  `${API_BASE_URL}/api/files/${fileId}`;
export const getImageUrl = (fileId, imagePath) =>
  `${API_BASE_URL}/api/files/${fileId}/images/${imagePath}`;
