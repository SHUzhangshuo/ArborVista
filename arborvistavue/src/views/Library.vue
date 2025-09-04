<template>
  <div class="library">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">我的文库</h1>
      <p class="page-subtitle">管理您已处理的学术文档</p>
    </div>

    <!-- 文档列表 -->
    <div v-if="!selectedFile" class="documents-section">
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="files.length === 0" class="empty-state">
        <div class="empty-icon">📚</div>
        <h3>暂无文档</h3>
        <p>您还没有上传任何文档，去首页上传一个试试吧！</p>
        <router-link to="/" class="upload-link">上传文档</router-link>
      </div>

      <div v-else class="documents-grid">
        <div
          v-for="file in files"
          :key="file.id"
          class="document-card"
          @click="selectFile(file)"
        >
          <div class="document-icon">📄</div>
          <div class="document-info">
            <h3 class="document-title">{{ getDocumentTitle(file) }}</h3>
            <p class="document-date">{{ formatDate(file.created_at) }}</p>
          </div>
          <div class="document-actions">
            <button
              @click.stop="selectFile(file)"
              class="action-button read-button"
            >
              <span class="button-icon">📖</span>
              <span class="button-text">阅读</span>
            </button>
            <button
              @click.stop="showDeleteConfirmFromList(file)"
              class="action-button delete-button"
            >
              <span class="button-icon">🗑️</span>
              <span class="button-text">删除</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 文档阅读器 -->
    <div v-else class="reader-section">
      <div class="reader-header">
        <button @click="backToLibrary" class="back-button">← 返回文库</button>
        <h2 class="reader-title">{{ getDocumentTitle(selectedFile) }}</h2>
        <div class="reader-actions">
          <button @click="showDeleteConfirm" class="delete-button">
            <span class="delete-icon">🗑️</span>
            <span class="delete-text">删除文档</span>
          </button>
        </div>
      </div>

      <div class="reader-content">
        <div v-if="contentLoading" class="content-loading">
          <div class="loading-spinner"></div>
          <p>加载文档内容...</p>
        </div>

        <div v-else class="markdown-container">
          <!-- 测试按钮 -->
          <div class="test-section" v-if="!renderedContent">
            <h3>样式测试</h3>
            <p>点击下面的按钮来测试Markdown样式是否生效：</p>
            <button @click="testStyles" class="test-button">测试样式</button>
            <div
              v-if="testContent"
              class="test-content markdown-body"
              v-html="testContent"
            ></div>
          </div>

          <div
            class="markdown-content markdown-body"
            v-html="renderedContent"
          ></div>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteModal" class="delete-modal">
      <div class="delete-modal-content">
        <div class="delete-modal-header">
          <div class="delete-modal-icon">⚠️</div>
          <h3 class="delete-modal-title">确认删除</h3>
        </div>
        <div class="delete-modal-body">
          <p>
            您确定要删除文档
            <strong>"{{ getDocumentTitle(fileToDelete) }}"</strong> 吗？
          </p>
          <p class="delete-warning">此操作不可恢复，文档将被永久删除。</p>
        </div>
        <div class="delete-modal-actions">
          <button @click="cancelDelete" class="cancel-button">取消</button>
          <button @click="confirmDelete" class="confirm-delete-button">
            <span class="confirm-icon">🗑️</span>
            确认删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import {
  API_ENDPOINTS,
  getFileContentUrl,
  getFileDeleteUrl,
  getImageUrl,
} from "../config/api.js";

export default {
  name: "LibraryPage",
  data() {
    return {
      files: [],
      selectedFile: null,
      loading: false,
      contentLoading: false,
      renderedContent: "",
      testContent: "",
      showDeleteModal: false,
      fileToDelete: null,
    };
  },
  async mounted() {
    await this.loadFiles();
  },
  methods: {
    async loadFiles() {
      this.loading = true;
      try {
        const response = await axios.get(API_ENDPOINTS.FILES);
        this.files = response.data.files;

        // 为每个文件提取标题
        for (const file of this.files) {
          if (!file.title) {
            await this.loadFileTitle(file);
          }
        }
      } catch (error) {
        console.error("加载文件列表失败:", error);
        alert("加载文件列表失败");
      } finally {
        this.loading = false;
      }
    },

    async selectFile(file) {
      this.selectedFile = file;
      this.contentLoading = true;

      try {
        const response = await axios.get(getFileContentUrl(file.id));

        // 处理markdown内容中的图片URL
        let content = response.data.content;
        // 将相对路径的图片URL转换为绝对URL
        content = content.replace(
          /!\[([^\]]*)\]\(images\/([^)]+)\)/g,
          (match, alt, imagePath) => {
            const imageUrl = getImageUrl(file.id, imagePath);
            return `![${alt}](${imageUrl})`;
          }
        );

        // 渲染markdown内容
        this.renderedContent = this.$md.render(content);
      } catch (error) {
        console.error("加载文档内容失败:", error);
        this.renderedContent = "<p>加载文档内容失败</p>";
      } finally {
        this.contentLoading = false;
      }
    },

    showDeleteConfirm() {
      this.fileToDelete = this.selectedFile;
      this.showDeleteModal = true;
    },

    showDeleteConfirmFromList(file) {
      this.fileToDelete = file;
      this.showDeleteModal = true;
    },

    cancelDelete() {
      this.showDeleteModal = false;
      this.fileToDelete = null;
    },

    async confirmDelete() {
      if (!this.fileToDelete) return;

      const fileId = this.fileToDelete.id;
      this.showDeleteModal = false;
      this.fileToDelete = null;

      try {
        await axios.delete(getFileDeleteUrl(fileId));

        // 如果删除的是当前选中的文件，返回文库
        if (this.selectedFile && this.selectedFile.id === fileId) {
          this.backToLibrary();
        }

        // 重新加载文件列表
        await this.loadFiles();

        // 显示成功提示
        this.showSuccessMessage("文档删除成功");
      } catch (error) {
        console.error("删除文档失败:", error);
        this.showErrorMessage("删除文档失败");
      }
    },

    showSuccessMessage(message) {
      // 创建临时成功提示
      const successDiv = document.createElement("div");
      successDiv.className = "temp-success-message";
      successDiv.innerHTML = `
        <div class="temp-success-content">
          <span class="temp-success-icon">✅</span>
          <span class="temp-success-text">${message}</span>
        </div>
      `;
      document.body.appendChild(successDiv);

      // 3秒后自动移除
      setTimeout(() => {
        if (successDiv.parentNode) {
          successDiv.parentNode.removeChild(successDiv);
        }
      }, 3000);
    },

    showErrorMessage(message) {
      // 创建临时错误提示
      const errorDiv = document.createElement("div");
      errorDiv.className = "temp-error-message";
      errorDiv.innerHTML = `
        <div class="temp-error-content">
          <span class="temp-error-icon">❌</span>
          <span class="temp-error-text">${message}</span>
        </div>
      `;
      document.body.appendChild(errorDiv);

      // 5秒后自动移除
      setTimeout(() => {
        if (errorDiv.parentNode) {
          errorDiv.parentNode.removeChild(errorDiv);
        }
      }, 5000);
    },

    async deleteFile(fileId) {
      if (!confirm("确定要删除这个文档吗？此操作不可恢复。")) {
        return;
      }

      try {
        await axios.delete(getFileDeleteUrl(fileId));

        // 如果删除的是当前选中的文件，返回文库
        if (this.selectedFile && this.selectedFile.id === fileId) {
          this.backToLibrary();
        }

        // 重新加载文件列表
        await this.loadFiles();

        alert("文档删除成功");
      } catch (error) {
        console.error("删除文档失败:", error);
        alert("删除文档失败");
      }
    },

    backToLibrary() {
      this.selectedFile = null;
      this.renderedContent = "";
    },

    formatDate(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    },

    getDocumentTitle(file) {
      // 如果文件为null或undefined，返回默认值
      if (!file) {
        return "未命名文档";
      }

      // 如果文件有标题属性，直接返回
      if (file.title) {
        return file.title;
      }

      // 如果没有标题，尝试从文件名中提取
      if (file.filename) {
        // 移除文件扩展名
        const nameWithoutExt = file.filename.replace(/\.[^/.]+$/, "");
        // 如果文件名看起来像UUID，返回默认标题
        if (
          /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i.test(
            nameWithoutExt
          )
        ) {
          return "未命名文档";
        }
        return nameWithoutExt;
      }

      return "未命名文档";
    },

    extractFirstTitle(content) {
      if (!content) return null;

      // 查找第一个标题（以#开头的行）
      const titleMatch = content.match(/^#{1,6}\s+(.+)$/m);
      if (titleMatch) {
        return titleMatch[1].trim();
      }

      // 如果没有找到标题，尝试查找第一个非空行
      const lines = content.split("\n").filter((line) => line.trim());
      if (lines.length > 0) {
        const firstLine = lines[0].trim();
        // 如果第一行看起来像标题（长度适中，不包含特殊字符）
        if (
          firstLine.length > 3 &&
          firstLine.length < 100 &&
          !firstLine.includes("```")
        ) {
          return firstLine;
        }
      }

      return null;
    },

    async loadFileTitle(file) {
      try {
        const response = await axios.get(getFileContentUrl(file.id));

        const firstTitle = this.extractFirstTitle(response.data.content);
        if (firstTitle) {
          file.title = firstTitle;
        }
      } catch (error) {
        console.error(`加载文件 ${file.id} 标题失败:`, error);
        // 如果加载失败，不设置标题，保持原有逻辑
      }
    },

    testStyles() {
      const testMarkdown = `
# 标题1 - 测试样式
## 标题2 - 二级标题
### 标题3 - 三级标题

这是一个**粗体文本**和*斜体文本*的测试。

> 这是一个引用块，用来测试引用样式。

- 列表项目1
- 列表项目2
  - 嵌套列表
  - 更多嵌套

1. 有序列表1
2. 有序列表2

\`\`\`javascript
// 代码块测试
function hello() {
  console.log("Hello World!");
}
\`\`\`

| 表格标题1 | 表格标题2 |
|-----------|-----------|
| 单元格1   | 单元格2   |
| 单元格3   | 单元格4   |

[链接文本](https://example.com)

---

*斜体* **粗体** ***粗斜体***

- [x] 已完成任务
- [ ] 未完成任务
      `;

      this.testContent = this.$md.render(testMarkdown);
    },
  },
};
</script>

<style scoped>
/* 全局图片居中样式 */
:deep(img) {
  display: block !important;
  margin: 20px auto !important;
  text-align: center !important;
}

.library {
  min-height: 100vh;
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1.1rem;
  color: #7f8c8d;
  margin: 0;
}

/* 文档列表 */
.documents-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
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

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  margin: 2rem 0;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: #7f8c8d;
  margin-bottom: 2rem;
}

.upload-link {
  display: inline-block;
  background: #3498db;
  color: white;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.3s;
}

.upload-link:hover {
  background: #2980b9;
}

/* 文档网格 */
.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.document-card {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.document-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #3498db;
}

.document-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.document-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.document-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.document-date {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.document-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: auto;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex: 1;
  position: relative;
  overflow: hidden;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}

.action-button::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.action-button:hover::before {
  left: 100%;
}

.read-button {
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
}

.read-button:hover {
  background: linear-gradient(135deg, #2980b9 0%, #1f5f8b 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
}

.delete-button {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
}

.delete-button:hover {
  background: linear-gradient(135deg, #c0392b 0%, #a93226 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
}

.button-icon {
  font-size: 1rem;
  transition: transform 0.3s ease;
}

.action-button:hover .button-icon {
  transform: scale(1.1);
}

.button-text {
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 阅读器 */
.reader-section {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 1rem;
}

.reader-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e1e8ed;
}

.back-button {
  background: #95a5a6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.back-button:hover {
  background: #7f8c8d;
}

.reader-title {
  color: #2c3e50;
  margin: 0;
  flex: 1;
  text-align: center;
}

.reader-actions {
  display: flex;
  gap: 1rem;
}

/* 删除按钮样式 */
.delete-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
  position: relative;
  overflow: hidden;
}

.delete-button::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.delete-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
  background: linear-gradient(135deg, #ff5252 0%, #d32f2f 100%);
}

.delete-button:hover::before {
  left: 100%;
}

.delete-button:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.delete-icon {
  font-size: 1rem;
  animation: shake 2s infinite;
}

.delete-text {
  font-weight: 600;
  letter-spacing: 0.5px;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  10%,
  30%,
  50%,
  70%,
  90% {
    transform: translateX(-2px);
  }
  20%,
  40%,
  60%,
  80% {
    transform: translateX(2px);
  }
}

/* 删除确认弹窗样式 */
.delete-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
  animation: fadeIn 0.3s ease-out;
}

.delete-modal-content {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideInUp 0.3s ease-out;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.delete-modal-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.delete-modal-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: pulse 2s infinite;
}

.delete-modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.delete-modal-body {
  text-align: center;
  margin-bottom: 2rem;
}

.delete-modal-body p {
  color: #5a6c7d;
  line-height: 1.6;
  margin: 0.5rem 0;
}

.delete-warning {
  color: #e74c3c !important;
  font-weight: 600;
  font-size: 0.9rem;
}

.delete-modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.cancel-button {
  background: #95a5a6;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(149, 165, 166, 0.3);
}

.cancel-button:hover {
  background: #7f8c8d;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(149, 165, 166, 0.4);
}

.confirm-delete-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
}

.confirm-delete-button:hover {
  background: linear-gradient(135deg, #c0392b 0%, #a93226 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
}

.confirm-icon {
  font-size: 1rem;
}

/* 临时提示消息样式 */
.temp-success-message,
.temp-error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1001;
  animation: slideInRight 0.3s ease-out;
}

.temp-success-content,
.temp-error-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  font-weight: 600;
}

.temp-success-content {
  background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
  color: white;
}

.temp-error-content {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
}

.temp-success-icon,
.temp-error-icon {
  font-size: 1.2rem;
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
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

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.content-loading {
  text-align: center;
  padding: 3rem;
}

.markdown-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
}

/* Markdown 样式 */
.markdown-container :deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial,
    sans-serif;
  line-height: 1.8;
  color: #2c3e50;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 标题样式 */
.markdown-container :deep(.markdown-body h1),
.markdown-container :deep(.markdown-body h2),
.markdown-container :deep(.markdown-body h3),
.markdown-container :deep(.markdown-body h4),
.markdown-container :deep(.markdown-body h5),
.markdown-container :deep(.markdown-body h6) {
  color: #1a202c;
  font-weight: 700;
  line-height: 1.3;
  margin: 2rem 0 1rem 0;
  position: relative;
}

.markdown-container :deep(.markdown-body h1) {
  font-size: 2.5rem;
  border-bottom: 3px solid #667eea;
  padding-bottom: 0.5rem;
  margin-bottom: 2rem;
}

.markdown-container :deep(.markdown-body h2) {
  font-size: 2rem;
  border-left: 4px solid #764ba2;
  padding-left: 1rem;
}

.markdown-container :deep(.markdown-body h3) {
  font-size: 1.5rem;
  color: #4a5568;
}

.markdown-container :deep(.markdown-body h4) {
  font-size: 1.25rem;
  color: #718096;
}

/* 段落样式 */
.markdown-container :deep(.markdown-body p) {
  margin: 1.5rem 0;
  text-align: justify;
  text-justify: inter-word;
  hyphens: auto;
}

/* 强调文本样式 */
.markdown-container :deep(.markdown-body strong) {
  color: #2d3748;
  font-weight: 700;
  background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}

.markdown-container :deep(.markdown-body em) {
  color: #805ad5;
  font-style: italic;
  font-weight: 500;
}

/* 链接样式 */
.markdown-container :deep(.markdown-body a) {
  color: #3182ce;
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
  position: relative;
}

.markdown-container :deep(.markdown-body a:hover) {
  color: #2c5282;
  border-bottom-color: #3182ce;
  transform: translateY(-1px);
}

/* 列表样式 */
.markdown-container :deep(.markdown-body ul),
.markdown-container :deep(.markdown-body ol) {
  margin: 1.5rem 0;
  padding-left: 2rem;
}

.markdown-container :deep(.markdown-body li) {
  margin: 0.5rem 0;
  line-height: 1.6;
}

.markdown-container :deep(.markdown-body ul li) {
  position: relative;
}

.markdown-container :deep(.markdown-body ul li::before) {
  content: "•";
  color: #667eea;
  font-weight: bold;
  position: absolute;
  left: -1.5rem;
}

/* 引用样式 */
.markdown-container :deep(.markdown-body blockquote) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 1.5rem 2rem;
  margin: 2rem 0;
  border-radius: 12px;
  border-left: 6px solid #e53e3e;
  box-shadow: 0 4px 16px rgba(240, 147, 251, 0.3);
}

.markdown-container :deep(.markdown-body blockquote p) {
  margin: 0;
  font-style: italic;
  font-size: 1.1rem;
}

/* 代码样式 */
.markdown-container :deep(.markdown-body code) {
  background: #2d3748;
  color: #e2e8f0;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: "Fira Code", "Monaco", "Consolas", "Liberation Mono",
    "Courier New", monospace;
  font-size: 0.9em;
}

.markdown-container :deep(.markdown-body pre) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  overflow-x: auto;
  margin: 2rem 0;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.markdown-container :deep(.markdown-body pre code) {
  background: transparent;
  color: white;
  padding: 0;
}

/* 水平分割线样式 */
.markdown-container :deep(.markdown-body hr) {
  border: none;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #f5576c);
  margin: 3rem 0;
  border-radius: 2px;
}

/* 全局表格样式 - 确保覆盖所有HTML表格 */
:deep(table) {
  border-collapse: collapse !important;
  margin: 24px 0 !important;
  width: 100% !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
  background: white !important;
  border: 1px solid #e8eaed !important;
}

:deep(table th) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  font-weight: 600 !important;
  padding: 18px 16px !important;
  text-align: left !important;
  vertical-align: middle !important;
  border: none !important;
  font-size: 15px !important;
  letter-spacing: 0.3px !important;
  position: relative !important;
}

:deep(table th:after) {
  content: "" !important;
  position: absolute !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 2px !important;
  background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1) !important;
}

:deep(table td) {
  padding: 16px !important;
  text-align: left !important;
  vertical-align: middle !important;
  border: none !important;
  border-bottom: 1px solid #f1f3f4 !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  color: #3c4043 !important;
}

:deep(table tr:last-child td) {
  border-bottom: none !important;
}

:deep(table tr:nth-child(even)) {
  background-color: #fafbfc !important;
}

:deep(table tr:hover) {
  background-color: #f8f9fa !important;
  transform: translateY(-2px) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
}

:deep(table tr:hover td) {
  background-color: #f8f9fa !important;
}

/* 表格样式 */
.markdown-container :deep(.markdown-body) table {
  border-collapse: collapse;
  margin: 24px 0;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  background: white;
  border: 1px solid #e8eaed;
}

.markdown-container :deep(.markdown-body) table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  padding: 18px 16px;
  text-align: left;
  vertical-align: middle;
  border: none;
  font-size: 15px;
  letter-spacing: 0.3px;
  position: relative;
}

.markdown-container :deep(.markdown-body) table th:after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
}

.markdown-container :deep(.markdown-body) table td {
  padding: 16px;
  text-align: left;
  vertical-align: middle;
  border: none;
  border-bottom: 1px solid #f1f3f4;
  font-size: 14px;
  line-height: 1.6;
  color: #3c4043;
}

.markdown-container :deep(.markdown-body) table tr:last-child td {
  border-bottom: none;
}

.markdown-container :deep(.markdown-body) table tr:nth-child(even) {
  background-color: #fafbfc;
}

.markdown-container :deep(.markdown-body) table tr:hover {
  background-color: #f8f9fa;
  transform: translateY(-2px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.markdown-container :deep(.markdown-body) table tr:hover td {
  background-color: #f8f9fa;
}

/* 表格响应式设计 */
@media (max-width: 768px) {
  .markdown-container :deep(.markdown-body) table {
    font-size: 13px;
    margin: 16px 0;
  }

  .markdown-container :deep(.markdown-body) table th,
  .markdown-container :deep(.markdown-body) table td {
    padding: 12px 10px;
  }
}

/* 额外的表格样式确保正确显示 */
.markdown-container :deep(.markdown-body) table,
:deep(table) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial,
    sans-serif;
  border-spacing: 0;
  word-break: break-word;
}

.markdown-container :deep(.markdown-body) table th,
.markdown-container :deep(.markdown-body) table td,
:deep(table th),
:deep(table td) {
  box-sizing: border-box;
}

/* 确保表格内容不换行 */
.markdown-container :deep(.markdown-body) table td,
:deep(table td) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 数学公式样式 */
.markdown-container :deep(.math) {
  text-align: center;
  margin: 16px 0;
}

.markdown-container :deep(.math-inline) {
  display: inline;
}

/* 任务列表样式 */
.markdown-container :deep(.markdown-body .task-list-item) {
  list-style-type: none;
}

.markdown-container
  :deep(.markdown-body .task-list-item input[type="checkbox"]) {
  margin: 0 0.2em 0.25em -1.4em;
  vertical-align: middle;
}

/* 引用样式 */
.markdown-container :deep(.markdown-body blockquote) {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
  background-color: #f6f8fa;
  border-radius: 0 6px 6px 0;
}

/* 列表样式 */
.markdown-container :deep(.markdown-body ul),
.markdown-container :deep(.markdown-body ol) {
  padding-left: 2em;
  margin-bottom: 16px;
}

.markdown-container :deep(.markdown-body li) {
  margin-bottom: 0.25em;
}

.markdown-container :deep(.markdown-body li > ul),
.markdown-container :deep(.markdown-body li > ol) {
  margin-top: 0.25em;
  margin-bottom: 0;
}

/* 图片样式 */
.markdown-container :deep(.markdown-body) img {
  max-width: 100% !important;
  height: auto !important;
  display: block !important;
  margin: 20px auto !important;
  text-align: center !important;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

/* 确保所有图片都适应容器 */
:deep(img) {
  max-width: 100% !important;
  height: auto !important;
  display: block !important;
  margin: 20px auto !important;
  text-align: center !important;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.markdown-container :deep(.markdown-body) img:hover,
:deep(img:hover) {
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 链接样式 */
.markdown-container :deep(.markdown-body a) {
  color: #0366d6;
  text-decoration: none;
}

.markdown-container :deep(.markdown-body a:hover) {
  text-decoration: underline;
}

/* 分割线样式 */
.markdown-container :deep(.markdown-body hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}

/* 表情符号样式 */
.markdown-container :deep(.markdown-body .emoji) {
  height: 1.2em;
  width: 1.2em;
  margin: 0 0.05em 0 0.1em;
  vertical-align: -0.1em;
}

/* 目录样式 */
.markdown-container :deep(.markdown-body .toc) {
  background-color: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 24px;
}

.markdown-container :deep(.markdown-body .toc h2) {
  margin-top: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.markdown-container :deep(.markdown-body .toc ul) {
  list-style-type: none;
  padding-left: 0;
}

.markdown-container :deep(.markdown-body .toc li) {
  margin-bottom: 0.5em;
}

.markdown-container :deep(.markdown-body .toc a) {
  color: #0366d6;
  text-decoration: none;
}

.markdown-container :deep(.markdown-body .toc a:hover) {
  text-decoration: underline;
}

/* 测试区域样式 */
.test-section {
  text-align: center;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.test-section h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.test-section p {
  color: #7f8c8d;
  margin-bottom: 1.5rem;
}

.test-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1.5rem;
}

.test-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.test-content {
  text-align: left;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }

  .documents-grid {
    grid-template-columns: 1fr;
  }

  .reader-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .markdown-container {
    padding: 1rem;
  }
}
</style>
