<template>
  <div class="home">
    <!-- 英雄区域 -->
    <section class="hero">
      <!-- 背景装饰元素 -->
      <div class="hero-bg-elements">
        <div class="floating-shape shape-1"></div>
        <div class="floating-shape shape-2"></div>
        <div class="floating-shape shape-3"></div>
        <div class="floating-shape shape-4"></div>
        <div class="floating-shape shape-5"></div>
      </div>

      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-icon">🚀</span>
          <span class="badge-text">AI驱动</span>
        </div>

        <h1 class="hero-title">
          <span class="title-line">智能论文阅读</span>
          <span class="title-line">从这里开始</span>
        </h1>

        <p class="hero-subtitle">
          上传您的PDF、图片等文档，览树将自动解析并转换为易读的Markdown格式，
          让学术阅读变得更加高效和愉悦
        </p>

        <div class="hero-features">
          <div class="feature-tag">
            <span class="tag-icon">📚</span>
            <span>多格式支持</span>
          </div>
          <div class="feature-tag">
            <span class="tag-icon">⚡</span>
            <span>快速处理</span>
          </div>
          <div class="feature-tag">
            <span class="tag-icon">🔒</span>
            <span>隐私安全</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 文件上传区域 -->
    <section class="upload-section">
      <div class="upload-container">
        <!-- 配置选择区域 -->
        <div class="config-section">
          <h3 class="config-title">处理配置</h3>
          <div class="config-grid">
            <div class="config-item">
              <label for="method">解析方法</label>
              <el-select
                v-model="selectedConfig.method"
                placeholder="请选择解析方法"
                class="config-select"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="method in configOptions.methods"
                  :key="method"
                  :label="getMethodLabel(method)"
                  :value="method"
                />
              </el-select>
            </div>

            <div class="config-item">
              <label for="language">文档语言</label>
              <el-select
                v-model="selectedConfig.language"
                placeholder="请选择文档语言"
                class="config-select"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="lang in configOptions.languages"
                  :key="lang"
                  :label="getLanguageLabel(lang)"
                  :value="lang"
                />
              </el-select>
            </div>
          </div>
        </div>

        <div
          class="upload-area"
          :class="{ dragover: isDragOver, uploading: isUploading }"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @click="triggerFileInput"
        >
          <div class="upload-icon">
            <svg
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 16L12 8M12 8L15 11M12 8L9 11"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M3 15V16C3 18.8284 3 20.2426 3.87868 21.1213C4.75736 22 6.17157 22 9 22H15C17.8284 22 19.2426 22 20.1213 21.1213C21 20.2426 21 18.8284 21 16V15"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <h3 class="upload-title">拖拽文件到这里，或点击上传</h3>
          <p class="upload-subtitle">支持 PDF、PNG、JPG、JPEG 等格式</p>
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            @change="handleFileSelect"
            style="display: none"
          />
        </div>
      </div>
    </section>

    <!-- 功能特性 -->
    <section class="features">
      <h2 class="features-title">为什么选择览树？</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🚀</div>
          <h3>智能解析</h3>
          <p>基于先进的AI技术，自动识别文档内容，提取文字、表格、公式等</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📱</div>
          <h3>多格式支持</h3>
          <p>支持PDF、图片等多种格式，满足不同文档类型的需求</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🎨</div>
          <h3>优雅阅读</h3>
          <p>转换为Markdown格式，提供清晰、美观的阅读体验</p>
        </div>
      </div>
    </section>

    <!-- 上传进度提示 -->
    <div v-if="isUploading" class="upload-progress">
      <div class="progress-content">
        <div class="progress-spinner"></div>
        <p>正在处理您的文档，请稍候...</p>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="uploadSuccess" class="success-message">
      <div class="success-content">
        <div class="success-icon">✅</div>
        <p>{{ successMessage }}</p>
        <button @click="goToLibrary" class="success-button">查看文档</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { API_ENDPOINTS } from "../config/api.js";

export default {
  name: "HomePage",
  data() {
    return {
      isDragOver: false,
      isUploading: false,
      uploadSuccess: false,
      successMessage: "",
      configOptions: {
        methods: ["auto", "txt", "ocr"],
        languages: [
          "ch",
          "ch_server",
          "ch_lite",
          "en",
          "korean",
          "japan",
          "chinese_cht",
          "ta",
          "te",
          "ka",
          "latin",
          "arabic",
          "east_slavic",
          "cyrillic",
          "devanagari",
        ],
        defaults: {
          method: "auto",
          language: "ch",
        },
      },
      selectedConfig: {
        method: "auto",
        language: "ch",
      },
    };
  },
  methods: {
    // 配置标签转换方法
    getMethodLabel(method) {
      const labels = {
        auto: "自动选择",
        txt: "文本提取",
        ocr: "OCR识别",
      };
      return labels[method] || method;
    },

    getLanguageLabel(lang) {
      const labels = {
        ch: "中文",
        ch_server: "中文服务器",
        ch_lite: "中文轻量",
        en: "英文",
        korean: "韩文",
        japan: "日文",
        chinese_cht: "繁体中文",
        ta: "泰米尔语",
        te: "泰卢固语",
        ka: "格鲁吉亚语",
        latin: "拉丁语",
        arabic: "阿拉伯语",
        east_slavic: "东斯拉夫语",
        cyrillic: "西里尔语",
        devanagari: "天城文",
      };
      return labels[lang] || lang;
    },

    handleDragOver(e) {
      e.preventDefault();
      this.isDragOver = true;
    },
    handleDragLeave(e) {
      e.preventDefault();
      this.isDragOver = false;
    },
    handleDrop(e) {
      e.preventDefault();
      this.isDragOver = false;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.uploadFile(files[0]);
      }
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleFileSelect(e) {
      const file = e.target.files[0];
      if (file) {
        this.uploadFile(file);
      }
    },
    async uploadFile(file) {
      this.isUploading = true;
      this.uploadSuccess = false;

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("method", this.selectedConfig.method);
        formData.append("backend", "pipeline");
        formData.append("language", this.selectedConfig.language);

        const response = await axios.post(API_ENDPOINTS.UPLOAD, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });

        if (response.data.success) {
          this.successMessage = '文档 "' + file.name + '" 处理成功！';
          this.uploadSuccess = true;
          // 3秒后自动跳转
          setTimeout(() => {
            this.goToLibrary();
          }, 3000);
        }
      } catch (error) {
        console.error("上传失败:", error);
        alert("上传失败，请重试");
      } finally {
        this.isUploading = false;
      }
    },
    goToLibrary() {
      this.$router.push("/library");
    },
  },
};
</script>

<style scoped>
.home {
  min-height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* 英雄区域 */
.hero {
  text-align: center;
  padding: 1.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  color: white;
  margin: -2rem 0 2rem 0;
  position: relative;
  overflow: hidden;
  border-radius: 0 0 20px 20px;
  width: 100%;
  max-width: 1200px;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
}

/* 背景装饰元素 */
.hero-bg-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 60%;
  right: 15%;
  animation-delay: 1s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  bottom: 30%;
  left: 20%;
  animation-delay: 2s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  top: 30%;
  right: 30%;
  animation-delay: 3s;
}

.shape-5 {
  width: 40px;
  height: 40px;
  bottom: 20%;
  right: 10%;
  animation-delay: 4s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.6;
  }
}

.hero-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0;
  position: relative;
  z-index: 2;
}

/* AI驱动徽章 */
.hero-badge {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 50px;
  padding: 0.6rem 1.25rem;
  margin-bottom: 1.5rem;
  animation: slideInDown 0.8s ease-out;
}

.badge-icon {
  font-size: 1.2rem;
  margin-right: 0.5rem;
  animation: bounce 2s infinite;
}

.badge-text {
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  line-height: 1.2;
  animation: slideInUp 0.8s ease-out 0.2s both;
}

.title-line {
  display: block;
  background: linear-gradient(45deg, #ffffff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.title-line:last-child {
  background: linear-gradient(45deg, #f0f8ff, #ffffff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  opacity: 0.95;
  line-height: 1.6;
  margin-bottom: 2rem;
  animation: slideInUp 0.8s ease-out 0.4s both;
}

/* 特性标签 */
.hero-features {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  animation: slideInUp 0.8s ease-out 0.6s both;
}

.feature-tag {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 25px;
  padding: 0.6rem 1rem;
  transition: all 0.3s ease;
  cursor: pointer;
}

.feature-tag:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.tag-icon {
  font-size: 1.1rem;
  margin-right: 0.5rem;
}

/* 动画效果 */
@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

/* 上传区域 */
.upload-section {
  margin-bottom: 4rem;
  width: 100%;
}

.upload-container {
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

/* 配置选择区域 */
.config-section {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  padding: 2.5rem;
  border-radius: 20px;
  margin-bottom: 2rem;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.config-section:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.15),
    0 8px 12px -4px rgba(0, 0, 0, 0.1);
}

.config-section::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #f5576c);
  border-radius: 20px 20px 0 0;
}

.config-section::after {
  content: "";
  position: absolute;
  top: 20px;
  right: 20px;
  width: 60px;
  height: 60px;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.1),
    rgba(118, 75, 162, 0.1)
  );
  border-radius: 50%;
  opacity: 0.6;
  z-index: 0;
}

/* 配置项装饰 */
.config-item::before {
  content: "";
  position: absolute;
  top: -10px;
  left: -10px;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  opacity: 0.3;
  z-index: -1;
}

.config-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 2rem;
  color: #1f2937;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  position: relative;
}

.config-title::after {
  content: "";
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 2px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2.5rem;
  max-width: 800px;
  margin: 0 auto;
}

.config-item {
  display: flex;
  flex-direction: column;
  position: relative;
}

.config-item label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  padding-left: 1rem;
}

.config-item label::before {
  content: "⚙️";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.8rem;
}

/* Element Plus 下拉框美化样式 */
.config-select {
  /* 自定义下拉框样式 */
}

.config-select :deep(.el-input__wrapper) {
  padding: 1rem 1.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  color: #1f2937;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
  appearance: none;
  padding-right: 3rem;
}

.config-select :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
  background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.config-select :deep(.el-input__wrapper.is-focus) {
  outline: none;
  border-color: #667eea;
  background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1),
    0 8px 25px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.config-select :deep(.el-input__inner) {
  color: #1f2937;
  font-weight: 500;
}

.config-select :deep(.el-input__suffix) {
  color: #6b7280;
  transition: all 0.3s ease;
}

.config-select :deep(.el-input__suffix:hover) {
  color: #667eea;
  transform: scale(1.1);
}

/* 下拉选项美化 */
.config-select :deep(.el-select-dropdown) {
  border-radius: 12px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.config-select :deep(.el-select-dropdown__item) {
  padding: 0.75rem 1rem;
  color: #606266;
  font-weight: 400;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f0f0f0;
}

.config-select :deep(.el-select-dropdown__item:hover) {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f4fd 100%);
  color: #409eff;
  font-weight: 500;
}

.config-select :deep(.el-select-dropdown__item.is-selected) {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  color: white;
  font-weight: 500;
}

/* 选择框悬停效果 */
.config-item:hover label {
  color: #667eea;
  transform: translateX(4px);
  transition: all 0.3s ease;
}

.config-item:hover label::before {
  animation: spin 0.6s ease-in-out;
}

.config-item:hover::before {
  transform: scale(1.5);
  opacity: 0.6;
  transition: all 0.3s ease;
}

/* 配置项悬停时的整体效果 */
.config-item:hover {
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

@keyframes spin {
  0% {
    transform: translateY(-50%) rotate(0deg);
  }
  100% {
    transform: translateY(-50%) rotate(360deg);
  }
}

/* 配置区域加载动画 */
.config-section {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 配置项逐个出现动画 */
.config-item:nth-child(1) {
  animation: slideInLeft 0.6s ease-out 0.1s both;
}

.config-item:nth-child(2) {
  animation: slideInRight 0.6s ease-out 0.2s both;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.upload-area {
  border: 3px dashed #d1d5db;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.upload-area:hover {
  border-color: #007aff;
  background-color: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

.upload-area.dragover {
  border-color: #007aff;
  background-color: #f0f8ff;
  transform: scale(1.02);
}

.upload-area.uploading {
  border-color: #10b981;
  background-color: #f0fdf4;
}

.upload-icon {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.upload-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.upload-subtitle {
  color: #6b7280;
  font-size: 1rem;
}

/* 功能特性 */
.features {
  text-align: center;
  margin-bottom: 4rem;
  width: 100%;
}

.features-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 3rem;
  color: #1f2937;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

.feature-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1f2937;
}

.feature-card p {
  color: #6b7280;
  line-height: 1.6;
}

/* 上传进度 */
.upload-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.progress-content {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.progress-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #007aff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 成功提示 */
.success-message {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.success-content {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.success-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.success-button {
  background: #007aff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 1rem;
  transition: background-color 0.3s ease;
}

.success-button:hover {
  background: #0056b3;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home {
    padding: 0 0.5rem;
  }

  .hero {
    padding: 1.2rem 0.5rem;
    margin: -2rem 0 2rem 0;
    width: 100%;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-content {
    padding: 0;
  }

  .hero-title {
    font-size: 2.2rem;
  }

  .hero-subtitle {
    font-size: 1.1rem;
    padding: 0 1rem;
  }

  .hero-features {
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .feature-tag {
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
  }

  .floating-shape {
    display: none;
  }

  .upload-area {
    padding: 2rem 1rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    padding: 0 1rem;
  }

  .features-title {
    font-size: 2rem;
    padding: 0 1rem;
  }

  /* 移动端配置区域优化 */
  .config-section {
    padding: 2rem 1.5rem;
    margin: 0 0 2rem 0;
  }

  .config-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
    max-width: 100%;
  }

  .config-title {
    font-size: 1.25rem;
  }

  .config-select :deep(.el-input__wrapper) {
    padding: 0.875rem 1rem;
    font-size: 0.95rem;
    padding-right: 2.5rem;
  }
}

/* 平板端优化 */
@media (min-width: 769px) and (max-width: 1024px) {
  .home {
    padding: 0 1.5rem;
  }

  .hero {
    padding: 1.5rem 1.5rem;
    margin: -2rem 0 2rem 0;
    width: 100%;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-content {
    padding: 0;
  }

  .config-section {
    padding: 2.5rem;
    margin: 0 0 2rem 0;
  }

  .config-grid {
    gap: 2.5rem;
  }

  .features-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 2rem;
  }
}

/* 大屏幕优化 */
@media (min-width: 1025px) {
  .home {
    padding: 0 2rem;
  }

  .hero {
    padding: 1.5rem 2rem;
    margin: -2rem 0 2rem 0;
    width: 100%;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-content {
    padding: 0;
  }

  .config-section {
    padding: 3rem;
    margin: 0 0 2rem 0;
  }

  .config-grid {
    gap: 3rem;
  }

  .features-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 2.5rem;
  }
}

/* 超大屏幕优化 */
@media (min-width: 1400px) {
  .home {
    max-width: 1400px;
    padding: 0 3rem;
  }

  .hero {
    padding: 1.5rem 3rem;
    margin: -2rem 0 2rem 0;
    width: 100%;
    max-width: 1400px;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-content {
    padding: 0;
  }

  .config-section {
    padding: 4rem;
  }

  .features-grid {
    gap: 3rem;
  }
}
</style>
