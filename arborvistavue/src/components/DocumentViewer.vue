<template>
  <div class="document-viewer" v-if="visible">
    <!-- 顶部工具栏 -->
    <div class="viewer-header">
      <div class="header-left">
        <el-button @click="closeViewer" circle size="large" class="close-btn">
          <el-icon><Close /></el-icon>
        </el-button>
        <div class="document-info">
          <h2 class="document-title">{{ documentName }}</h2>
          <span class="document-meta"
            >{{ formatFileSize(fileSize) }} • {{ formatDate(createdAt) }}</span
          >
        </div>
      </div>
      <div class="header-center">
        <el-button-group class="zoom-controls">
          <el-button @click="zoomOut" :disabled="zoomLevel <= 0.5" size="small">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button @click="resetZoom" size="small">
            {{ Math.round(zoomLevel * 100) }}%
          </el-button>
          <el-button @click="zoomIn" :disabled="zoomLevel >= 3" size="small">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
        </el-button-group>
      </div>
      <div class="header-right">
        <el-button
          @click="toggleReadingMode"
          circle
          size="large"
          class="action-btn"
        >
          <el-icon><Reading /></el-icon>
        </el-button>
        <el-button
          @click="toggleFullscreen"
          circle
          size="large"
          class="action-btn"
        >
          <el-icon><FullScreen /></el-icon>
        </el-button>
        <el-button
          @click="downloadDocument"
          circle
          size="large"
          class="action-btn"
        >
          <el-icon><Download /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 文档内容区域 -->
    <div class="viewer-content" ref="contentRef">
      <div
        class="document-content"
        :style="{
          transform: `scale(${zoomLevel})`,
          transformOrigin: 'top center',
        }"
      >
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-container">
          <el-skeleton :rows="15" animated />
        </div>

        <!-- 文档内容 -->
        <div
          v-else-if="documentContent"
          class="markdown-content"
          v-html="renderedContent"
        ></div>

        <!-- 空状态 -->
        <div v-else class="empty-content">
          <el-icon class="empty-icon" size="64">
            <Document />
          </el-icon>
          <h3>无法加载文档内容</h3>
          <p>请检查文档是否存在或网络连接是否正常</p>
        </div>
      </div>
    </div>

    <!-- 底部工具栏 -->
    <div class="viewer-footer">
      <div class="footer-left">
        <el-button @click="scrollToTop" size="small">
          <el-icon><Top /></el-icon>
          回到顶部
        </el-button>
        <el-button @click="toggleReadingMode" size="small">
          <el-icon><Reading /></el-icon>
          {{ isReadingMode ? "退出阅读模式" : "阅读模式" }}
        </el-button>
      </div>
      <div class="footer-center">
        <el-slider
          v-model="scrollProgress"
          :min="0"
          :max="100"
          @change="handleScrollChange"
          class="progress-slider"
        />
      </div>
      <div class="footer-right">
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import {
  Close,
  ZoomIn,
  ZoomOut,
  FullScreen,
  Download,
  Top,
  Reading,
  Document,
} from "@element-plus/icons-vue";
import MarkdownIt from "markdown-it";
import markdownItMathjax3 from "markdown-it-mathjax3";

export default {
  name: "DocumentViewer",
  components: {
    Close,
    ZoomIn,
    ZoomOut,
    FullScreen,
    Download,
    Top,
    Reading,
    Document,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    documentId: {
      type: String,
      default: "",
    },
    documentName: {
      type: String,
      default: "",
    },
    fileSize: {
      type: Number,
      default: 0,
    },
    createdAt: {
      type: String,
      default: "",
    },
    documentContent: {
      type: String,
      default: "",
    },
    isLoading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      zoomLevel: 1,
      isReadingMode: false,
      scrollProgress: 0,
      currentPage: 1,
      totalPages: 1,
      md: null,
    };
  },
  computed: {
    renderedContent() {
      if (!this.documentContent || !this.md) {
        return "";
      }
      return this.md.render(this.documentContent);
    },
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.initViewer();
        // 隐藏App的导航栏
        document.body.classList.add("document-viewer-active");
      } else {
        this.removeScrollListener();
        // 显示App的导航栏
        document.body.classList.remove("document-viewer-active");
      }
    },
    renderedContent() {
      this.$nextTick(() => {
        this.setupImageHandlers();
        this.updatePageInfo();
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise();
        }
      });
    },
  },
  mounted() {
    this.initMarkdownRenderer();
  },
  beforeUnmount() {
    this.removeScrollListener();
    // 确保清理body类
    document.body.classList.remove("document-viewer-active");
  },
  methods: {
    // 初始化Markdown渲染器
    initMarkdownRenderer() {
      this.md = new MarkdownIt({
        html: true,
        linkify: true,
        typographer: true,
      });

      this.md.use(markdownItMathjax3, {
        tex: {
          inlineMath: [
            ["$", "$"],
            ["\\(", "\\)"],
          ],
          displayMath: [
            ["$$", "$$"],
            ["\\[", "\\]"],
          ],
          processEscapes: true,
          processEnvironments: true,
        },
        options: {
          ignoreHtmlClass: "tex2jax_ignore",
          processHtmlClass: "tex2jax_process",
        },
      });
    },

    // 初始化查看器
    initViewer() {
      this.zoomLevel = 1;
      this.scrollProgress = 0;
      this.currentPage = 1;
      this.isReadingMode = false;

      // 延迟设置滚动监听器，确保DOM已渲染
      this.$nextTick(() => {
        this.setupScrollListener();
      });
    },

    // 设置图片处理器
    setupImageHandlers() {
      const images = this.$refs.contentRef?.querySelectorAll(
        ".markdown-content img"
      );
      if (images) {
        images.forEach((img) => {
          img.style.cursor = "pointer";
          img.addEventListener("click", (e) => {
            e.preventDefault();
            this.previewImage(img.src, img.alt || "图片");
          });
        });
      }
    },

    // 预览图片
    previewImage(url, name) {
      this.$emit("preview-image", { url, name });
    },

    // 设置滚动监听
    setupScrollListener() {
      this.scrollListener = () => {
        this.updateScrollProgress();
        this.updatePageInfo();
      };
      this.$refs.contentRef?.addEventListener("scroll", this.scrollListener);
    },

    // 移除滚动监听
    removeScrollListener() {
      if (this.scrollListener && this.$refs.contentRef) {
        this.$refs.contentRef.removeEventListener(
          "scroll",
          this.scrollListener
        );
      }
    },

    // 更新滚动进度
    updateScrollProgress() {
      if (!this.$refs.contentRef) return;

      const scrollTop = this.$refs.contentRef.scrollTop;
      const scrollHeight =
        this.$refs.contentRef.scrollHeight - this.$refs.contentRef.clientHeight;

      if (scrollHeight > 0) {
        this.scrollProgress = Math.round((scrollTop / scrollHeight) * 100);
      }
    },

    // 更新页面信息
    updatePageInfo() {
      if (!this.$refs.contentRef) return;

      const contentHeight = this.$refs.contentRef.scrollHeight;
      const viewportHeight = this.$refs.contentRef.clientHeight;
      this.totalPages = Math.max(1, Math.ceil(contentHeight / viewportHeight));

      // 计算当前页面
      const scrollTop = this.$refs.contentRef.scrollTop;
      this.currentPage = Math.min(
        this.totalPages,
        Math.max(1, Math.ceil(scrollTop / viewportHeight) + 1)
      );
    },

    // 处理滚动变化
    handleScrollChange(value) {
      if (!this.$refs.contentRef) return;

      const scrollHeight =
        this.$refs.contentRef.scrollHeight - this.$refs.contentRef.clientHeight;
      const targetScrollTop = (value / 100) * scrollHeight;

      this.$refs.contentRef.scrollTo({
        top: targetScrollTop,
        behavior: "smooth",
      });
    },

    // 放大
    zoomIn() {
      this.zoomLevel = Math.min(3, this.zoomLevel + 0.1);
    },

    // 缩小
    zoomOut() {
      this.zoomLevel = Math.max(0.5, this.zoomLevel - 0.1);
    },

    // 重置缩放
    resetZoom() {
      this.zoomLevel = 1;
    },

    // 切换全屏
    toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    },

    // 下载文档
    downloadDocument() {
      this.$emit("download-document");
    },

    // 回到顶部
    scrollToTop() {
      if (this.$refs.contentRef) {
        this.$refs.contentRef.scrollTo({
          top: 0,
          behavior: "smooth",
        });
      }
    },

    // 切换阅读模式
    toggleReadingMode() {
      this.isReadingMode = !this.isReadingMode;
      document.body.classList.toggle("reading-mode", this.isReadingMode);
    },

    // 关闭查看器
    closeViewer() {
      this.$emit("close");
      document.body.classList.remove("reading-mode");
    },

    // 格式化文件大小
    formatFileSize(size) {
      if (!size) return "未知";
      if (size < 1024) return size + " B";
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
      return (size / (1024 * 1024)).toFixed(1) + " MB";
    },

    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return "未知";
      const date = new Date(dateString);
      return date.toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    },
  },
};
</script>

<style scoped>
.document-viewer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: var(--bg-primary);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部工具栏 */
.viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(20px);
  z-index: 1000;
  position: sticky;
  top: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
  min-width: 0;
}

.close-btn {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-light) !important;
  color: var(--text-primary) !important;
}

.close-btn:hover {
  background: var(--bg-tertiary) !important;
  transform: scale(1.05);
}

.document-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 0;
}

.document-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-meta {
  font-size: 14px;
  color: var(--text-secondary);
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.zoom-controls {
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex: 1;
  justify-content: flex-end;
}

.action-btn {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-light) !important;
  color: var(--text-primary) !important;
}

.action-btn:hover {
  background: var(--bg-tertiary) !important;
  transform: scale(1.05);
}

/* 文档内容区域 */
.viewer-content {
  flex: 1;
  overflow: auto;
  padding: var(--space-xl);
  background: var(--bg-primary);
}

.document-content {
  max-width: 1200px;
  margin: 0 auto;
  transition: transform var(--transition-normal);
}

.loading-container {
  padding: var(--space-2xl);
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: var(--space-lg);
}

.empty-content h3 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.empty-content p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

/* Markdown内容样式 */
.markdown-content {
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 16px;
  font-family: var(--font-family);
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  color: var(--text-primary);
  margin-top: var(--space-2xl);
  margin-bottom: var(--space-lg);
  font-weight: 600;
  line-height: 1.3;
}

.markdown-content :deep(h1) {
  font-size: 32px;
  border-bottom: 2px solid var(--border-light);
  padding-bottom: var(--space-md);
}

.markdown-content :deep(h2) {
  font-size: 28px;
}

.markdown-content :deep(h3) {
  font-size: 24px;
}

.markdown-content :deep(h4) {
  font-size: 20px;
}

.markdown-content :deep(h5) {
  font-size: 18px;
}

.markdown-content :deep(h6) {
  font-size: 16px;
}

.markdown-content :deep(p) {
  margin-bottom: var(--space-lg);
  text-align: justify;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  transition: var(--transition-normal);
  margin: var(--space-xl) auto;
  display: block;
  text-align: center;
}

.markdown-content :deep(img:hover) {
  transform: scale(1.02);
  box-shadow: var(--shadow-xl);
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: var(--space-xl) 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  background: var(--bg-card);
}

.markdown-content :deep(table th),
.markdown-content :deep(table td) {
  border: 1px solid var(--border-light);
  padding: var(--space-md);
  text-align: left;
}

.markdown-content :deep(table th) {
  background: var(--bg-secondary);
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-content :deep(table tr:nth-child(even)) {
  background: var(--bg-secondary);
}

.markdown-content :deep(code) {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--primary-color);
}

.markdown-content :deep(pre) {
  background: var(--bg-secondary);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-lg) 0;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: var(--text-primary);
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--primary-color);
  padding-left: var(--space-lg);
  margin: var(--space-lg) 0;
  color: var(--text-secondary);
  font-style: italic;
  background: var(--bg-secondary);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: var(--space-lg) 0;
  padding-left: var(--space-xl);
}

.markdown-content :deep(li) {
  margin-bottom: var(--space-sm);
}

.markdown-content :deep(a) {
  color: var(--primary-color);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: var(--transition-fast);
}

.markdown-content :deep(a:hover) {
  border-bottom-color: var(--primary-color);
}

/* 底部工具栏 */
.viewer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-card);
  border-top: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(20px);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.footer-center {
  flex: 1;
  max-width: 300px;
  margin: 0 var(--space-lg);
}

.progress-slider {
  width: 100%;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.page-info {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 阅读模式 */
:global(.reading-mode) {
  background: #f8f9fa !important;
}

:global(.reading-mode .viewer-content) {
  background: #f8f9fa !important;
}

:global(.reading-mode .document-content) {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-2xl);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .viewer-header {
    padding: var(--space-sm) var(--space-md);
    flex-wrap: wrap;
    gap: var(--space-sm);
  }

  .header-left {
    gap: var(--space-sm);
    flex: 1 1 100%;
    order: 1;
  }

  .header-center {
    order: 3;
    flex: 1 1 100%;
    justify-content: center;
  }

  .header-right {
    gap: var(--space-sm);
    order: 2;
    flex: 0 0 auto;
  }

  .document-title {
    font-size: 16px;
  }

  .document-meta {
    font-size: 12px;
  }

  .viewer-content {
    padding: var(--space-md);
  }

  .markdown-content {
    font-size: 14px;
  }

  .markdown-content :deep(h1) {
    font-size: 24px;
  }

  .markdown-content :deep(h2) {
    font-size: 20px;
  }

  .markdown-content :deep(h3) {
    font-size: 18px;
  }

  .footer-center {
    display: none;
  }

  .viewer-footer {
    padding: var(--space-sm) var(--space-md);
  }
}
</style>
