// API 配置文件
import axios from "axios";

// 获取当前页面的主机地址，支持网络访问
export const getApiBaseUrl = () => {
  // 优先使用环境变量
  if (process.env.VUE_APP_API_URL) {
    return process.env.VUE_APP_API_URL;
  }

  // 获取当前页面的主机地址
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;

  // 如果是本地开发环境，使用127.0.0.1
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://127.0.0.1:5000";
  }

  // 如果是网络访问，使用当前主机地址
  return `${protocol}//${hostname}:5000`;
};

const API_BASE_URL = getApiBaseUrl();

// 配置axios拦截器，自动添加用户ID到请求头
axios.interceptors.request.use(
  (config) => {
    const user_id = localStorage.getItem("user_id");
    if (user_id) {
      config.headers["X-User-ID"] = user_id;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器，处理401未授权
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // 清除本地存储的用户信息
      localStorage.removeItem("user");
      localStorage.removeItem("user_id");
      // 跳转到登录页
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const API_ENDPOINTS = {
  UPLOAD: `${API_BASE_URL}/api/upload`, // 统一上传接口，支持单个或多个文件
  FILES: `${API_BASE_URL}/api/files`,
  HEALTH: `${API_BASE_URL}/api/health`,
  CONFIG_OPTIONS: `${API_BASE_URL}/api/config/options`,
  LIBRARIES: `${API_BASE_URL}/api/libraries`,
};

// 基础API函数
export const getFileContentUrl = (fileId) =>
  `${API_BASE_URL}/api/files/${fileId}/content`;
export const getFileDeleteUrl = (fileId) =>
  `${API_BASE_URL}/api/files/${fileId}`;
export const getImageUrl = (fileId, imagePath) =>
  `${API_BASE_URL}/api/files/${fileId}/images/${imagePath}`;

// 文库相关API
export const getLibraryFilesUrl = (libraryId) =>
  `${API_BASE_URL}/api/libraries/${libraryId}/files`;
export const getLibraryFileContentUrl = (libraryId, fileId) =>
  `${API_BASE_URL}/api/libraries/${libraryId}/files/${fileId}/content`;
export const getLibraryFileProcessUrl = (libraryId, fileId) =>
  `${API_BASE_URL}/api/libraries/${libraryId}/files/${fileId}/process`;
export const getLibraryImageUrl = (libraryId, fileId, imagePath) =>
  `${API_BASE_URL}/api/libraries/${libraryId}/files/${fileId}/images/${imagePath}`;

// 文库管理API函数
export const getLibraries = async () => {
  try {
    const response = await axios.get(API_ENDPOINTS.LIBRARIES);
    return response;
  } catch (error) {
    console.error("获取文库列表失败:", error);
    throw error;
  }
};

export const createLibrary = async (libraryData) => {
  try {
    const response = await axios.post(API_ENDPOINTS.LIBRARIES, libraryData);
    return response;
  } catch (error) {
    console.error("创建文库失败:", error);
    throw error;
  }
};

// 文件管理API函数
export const getFiles = async (libraryId) => {
  try {
    const response = await axios.get(getLibraryFilesUrl(libraryId));
    return response;
  } catch (error) {
    console.error("获取文件列表失败:", error);
    throw error;
  }
};

export const getLibraryFileContent = async (libraryId, fileId) => {
  try {
    const response = await axios.get(
      getLibraryFileContentUrl(libraryId, fileId)
    );
    return response;
  } catch (error) {
    console.error("获取文件内容失败:", error);
    throw error;
  }
};

// 文件上传API函数
export const uploadFiles = async (formData) => {
  try {
    const response = await axios.post(API_ENDPOINTS.UPLOAD, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response;
  } catch (error) {
    console.error("文件上传失败:", error);
    throw error;
  }
};

// 删除文件API函数
export const deleteFile = async (libraryId, fileId) => {
  try {
    const response = await axios.delete(
      `${API_BASE_URL}/api/libraries/${libraryId}/files/${fileId}`
    );
    return response;
  } catch (error) {
    console.error("删除文件失败:", error);
    throw error;
  }
};
