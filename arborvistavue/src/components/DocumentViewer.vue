<template>
  <div
    class="document-viewer"
    :class="{ fullscreen: isFullscreen }"
    v-if="visible"
  >
    <!-- 顶部工具栏 -->
    <div class="viewer-header" v-show="!isFullscreen">
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

        <!-- 文档内容 - 小文件直接渲染 -->
        <div
          v-else-if="documentContent && !isLargeDocument"
          class="markdown-content"
          v-html="renderedContent"
        ></div>

        <!-- 文档内容 - 大文件分块渲染 -->
        <div
          v-else-if="documentContent && isLargeDocument"
          class="markdown-content large-document-container"
        >
          <div v-if="isChunking" class="chunking-hint">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在处理大文件...</span>
          </div>
          <div
            v-else
            class="chunks-wrapper"
            :style="{ height: totalContentHeight + 'px' }"
          >
            <div
              v-for="chunkIndex in Array.from(visibleChunks)"
              :key="chunkIndex"
              :data-chunk-index="chunkIndex"
              class="chunk-item"
              :style="{
                position: 'absolute',
                top: getChunkTop(chunkIndex) + 'px',
                left: 0,
                right: 0,
              }"
              v-html="renderedChunks[chunkIndex]"
            ></div>
          </div>
        </div>

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
    <div class="viewer-footer" v-show="!isFullscreen">
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
  Loading,
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
    Loading,
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
      isFullscreen: false,
      scrollProgress: 0,
      currentPage: 1,
      totalPages: 1,
      md: null,
      // 虚拟滚动相关
      chunkSize: 200, // 每块渲染的行数
      visibleChunks: new Set(), // 当前可见的块
      renderedChunks: {}, // 已渲染的块缓存
      contentChunks: [], // 分块后的原始内容
      isChunking: false, // 是否正在分块
      scrollTimer: null, // 滚动防抖计时器
      chunkHeights: [], // 每个块的高度
      chunkTops: [], // 每个块的top位置（累积高度）
      avgLineHeight: 24, // 平均行高（用于估算）
    };
  },
  computed: {
    // 判断是否是大文件（超过3000行）
    isLargeDocument() {
      if (!this.documentContent) return false;
      const lines = this.documentContent.split("\n").length;
      return lines > 3000;
    },

    // 渲染内容 - 对于小文件直接渲染，大文件使用分块
    renderedContent() {
      if (!this.documentContent || !this.md) {
        return "";
      }

      // 小文件直接渲染
      if (!this.isLargeDocument) {
        return this.md.render(this.documentContent);
      }

      // 大文件返回空，使用分块渲染
      return "";
    },

    // 获取可见块的渲染内容（已废弃，改用chunk-item方式）
    visibleRenderedContent() {
      if (!this.isLargeDocument) return "";

      let html = "";
      const sortedChunks = Array.from(this.visibleChunks).sort((a, b) => a - b);

      for (const chunkIndex of sortedChunks) {
        if (this.renderedChunks[chunkIndex]) {
          html += this.renderedChunks[chunkIndex];
        }
      }

      return html;
    },

    // 计算总内容高度
    totalContentHeight() {
      if (this.chunkTops.length === 0 || this.chunkHeights.length === 0) {
        return 0;
      }
      const lastIndex = this.chunkHeights.length - 1;
      return this.chunkTops[lastIndex] + this.chunkHeights[lastIndex];
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
    documentContent(newVal) {
      if (newVal && this.isLargeDocument) {
        // 大文件需要分块处理
        this.prepareChunkedContent();
      }
    },
    renderedContent() {
      // 小文件直接渲染的处理
      this.$nextTick(() => {
        this.setupImageHandlers();
        this.updatePageInfo();
        // 小文件直接对整个文档进行MathJax渲染
        if (
          !this.isLargeDocument &&
          window.MathJax &&
          window.MathJax.typesetPromise
        ) {
          window.MathJax.typesetPromise().catch((err) => {
            console.warn("MathJax渲染失败:", err);
          });
        }
      });
    },
    visibleRenderedContent() {
      // 大文件分块渲染后的处理（已废弃，改为在renderChunk后调用）
      this.$nextTick(() => {
        this.setupImageHandlers();
        this.updatePageInfo();
      });
    },
  },
  mounted() {
    this.initMarkdownRenderer();
    this.addFullscreenListeners();
  },
  beforeUnmount() {
    this.removeScrollListener();
    this.removeFullscreenListeners();
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

    // 准备分块内容
    async prepareChunkedContent() {
      if (!this.documentContent || this.isChunking) return;

      this.isChunking = true;
      this.contentChunks = [];
      this.renderedChunks = {};
      this.visibleChunks = new Set();
      this.chunkHeights = [];
      this.chunkTops = [];

      try {
        // 按行分割内容
        const lines = this.documentContent.split("\n");

        // 智能分块：避免切断数学公式和代码块
        this.smartChunking(lines);

        // 预渲染前5块（首屏内容）
        await this.renderInitialChunks();
      } catch (error) {
        console.error("分块处理失败:", error);
      } finally {
        this.isChunking = false;
      }
    },

    // 智能分块：避免切断数学公式、代码块
    smartChunking(lines) {
      let currentChunk = [];
      let cumulativeTop = 0;
      let inCodeBlock = false;
      let inMathBlock = false;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // 检测代码块边界
        if (line.trim().startsWith("```")) {
          inCodeBlock = !inCodeBlock;
        }

        // 检测块级数学公式边界
        if (
          line.trim() === "$$" ||
          line.trim().startsWith("\\[") ||
          line.trim().startsWith("\\]")
        ) {
          inMathBlock = !inMathBlock;
        }

        // 检测行内是否有未闭合的数学公式
        const hasUnclosedInlineMath = this.hasUnclosedMath(line);

        currentChunk.push(line);

        // 判断是否可以切分
        const canSplit =
          currentChunk.length >= this.chunkSize &&
          !inCodeBlock &&
          !inMathBlock &&
          !hasUnclosedInlineMath &&
          line.trim() !== "" && // 不在空行切分
          !line.trim().startsWith("#") && // 不在标题行切分
          !line.trim().endsWith("\\"); // 不在行尾有续行符时切分

        if (canSplit || i === lines.length - 1) {
          // 保存当前块
          const chunkContent = currentChunk.join("\n");
          this.contentChunks.push(chunkContent);

          // 预估块高度
          const lineCount = currentChunk.length;
          const estimatedHeight = lineCount * this.avgLineHeight;
          this.chunkHeights.push(estimatedHeight);
          this.chunkTops.push(cumulativeTop);
          cumulativeTop += estimatedHeight;

          // 重置当前块
          currentChunk = [];
        }
      }

      // 处理最后可能剩余的内容
      if (currentChunk.length > 0) {
        const chunkContent = currentChunk.join("\n");
        this.contentChunks.push(chunkContent);

        const lineCount = currentChunk.length;
        const estimatedHeight = lineCount * this.avgLineHeight;
        this.chunkHeights.push(estimatedHeight);
        this.chunkTops.push(cumulativeTop);
      }
    },

    // 检测行内是否有未闭合的数学公式
    hasUnclosedMath(line) {
      // 检测 $...$ 形式的行内公式
      let dollarCount = 0;
      let escaped = false;

      for (let i = 0; i < line.length; i++) {
        if (line[i] === "\\" && !escaped) {
          escaped = true;
          continue;
        }

        if (line[i] === "$" && !escaped) {
          dollarCount++;
        }

        escaped = false;
      }

      // 如果$数量为奇数，说明有未闭合的公式
      return dollarCount % 2 !== 0;
    },

    // 渲染初始块
    async renderInitialChunks() {
      const initialChunksCount = Math.min(5, this.contentChunks.length);

      for (let i = 0; i < initialChunksCount; i++) {
        await this.renderChunk(i);
        this.visibleChunks.add(i);
      }

      // 强制更新视图并测量实际高度
      this.$forceUpdate();

      // 延迟测量以确保DOM已渲染，并对新块进行MathJax渲染
      await this.$nextTick();
      setTimeout(() => {
        this.measureRenderedChunks();
        this.typesetVisibleChunks();
      }, 100);
    },

    // 渲染单个块
    async renderChunk(chunkIndex) {
      if (
        chunkIndex < 0 ||
        chunkIndex >= this.contentChunks.length ||
        this.renderedChunks[chunkIndex]
      ) {
        return;
      }

      return new Promise((resolve) => {
        // 使用 requestIdleCallback 或 setTimeout 避免阻塞
        const renderFn = () => {
          try {
            const chunkContent = this.contentChunks[chunkIndex];
            this.renderedChunks[chunkIndex] = this.md.render(chunkContent);
          } catch (error) {
            console.error(`渲染块 ${chunkIndex} 失败:`, error);
            this.renderedChunks[chunkIndex] = `<p>渲染失败</p>`;
          }
          resolve();
        };

        if (window.requestIdleCallback) {
          window.requestIdleCallback(renderFn, { timeout: 100 });
        } else {
          setTimeout(renderFn, 0);
        }
      });
    },

    // 更新可见块
    async updateVisibleChunks() {
      if (
        !this.isLargeDocument ||
        this.isChunking ||
        this.chunkTops.length === 0
      )
        return;

      const contentRef = this.$refs.contentRef;
      if (!contentRef) return;

      const scrollTop = contentRef.scrollTop;
      const viewportHeight = contentRef.clientHeight;
      const viewportBottom = scrollTop + viewportHeight;

      // 使用二分查找找到第一个可见块
      let startChunk = 0;
      for (let i = 0; i < this.chunkTops.length; i++) {
        if (this.chunkTops[i] + this.chunkHeights[i] >= scrollTop) {
          startChunk = Math.max(0, i - 1); // 预加载上1块
          break;
        }
      }

      // 找到最后一个可见块
      let endChunk = this.contentChunks.length - 1;
      for (let i = startChunk; i < this.chunkTops.length; i++) {
        if (this.chunkTops[i] > viewportBottom) {
          endChunk = Math.min(this.contentChunks.length - 1, i + 1); // 预加载下1块
          break;
        }
      }

      // 收集需要渲染的新块
      const newVisibleChunks = new Set();
      const chunksToRender = [];

      for (let i = startChunk; i <= endChunk; i++) {
        newVisibleChunks.add(i);
        if (!this.renderedChunks[i]) {
          chunksToRender.push(i);
        }
      }

      // 更新可见块集合
      this.visibleChunks = newVisibleChunks;

      // 渲染新块
      if (chunksToRender.length > 0) {
        for (const chunkIndex of chunksToRender) {
          await this.renderChunk(chunkIndex);
        }
        this.$forceUpdate();

        // 渲染完成后测量新块的实际高度并进行MathJax渲染
        await this.$nextTick();
        setTimeout(() => {
          this.measureRenderedChunks();
          this.typesetVisibleChunks();
        }, 50);
      }
    },

    // 只对可见块进行MathJax渲染
    typesetVisibleChunks() {
      if (!window.MathJax || !window.MathJax.typesetPromise) return;

      if (!this.$refs.contentRef) return;

      // 获取所有可见的chunk元素
      const chunkElements =
        this.$refs.contentRef.querySelectorAll(".chunk-item");

      if (chunkElements.length === 0) return;

      // 只对这些元素进行MathJax渲染
      window.MathJax.typesetPromise(Array.from(chunkElements)).catch((err) => {
        console.warn("MathJax渲染失败:", err);
      });
    },

    // 获取块的top位置
    getChunkTop(chunkIndex) {
      return this.chunkTops[chunkIndex] || 0;
    },

    // 测量已渲染块的实际高度
    measureRenderedChunks() {
      if (!this.$refs.contentRef) return;

      const chunkElements =
        this.$refs.contentRef.querySelectorAll(".chunk-item");
      if (chunkElements.length === 0) return;

      let heightChanged = false;
      const measuredIndices = [];

      chunkElements.forEach((element) => {
        // 从data-chunk-index属性获取块索引
        const chunkIndex = parseInt(element.dataset.chunkIndex);

        if (
          !isNaN(chunkIndex) &&
          chunkIndex >= 0 &&
          chunkIndex < this.chunkHeights.length
        ) {
          const actualHeight = element.offsetHeight;
          const oldHeight = this.chunkHeights[chunkIndex];

          // 如果高度有显著变化（超过5%），更新高度
          if (
            actualHeight > 0 &&
            Math.abs(actualHeight - oldHeight) > oldHeight * 0.05
          ) {
            this.chunkHeights[chunkIndex] = actualHeight;
            heightChanged = true;
            measuredIndices.push(chunkIndex);
          }
        }
      });

      // 如果有高度变化，重新计算所有块的top位置
      if (heightChanged) {
        this.recalculateChunkTops();

        // 调整平均行高以改进后续估算
        if (measuredIndices.length > 0) {
          let totalHeight = 0;
          let totalLines = 0;
          measuredIndices.forEach((idx) => {
            totalHeight += this.chunkHeights[idx];
            totalLines += this.contentChunks[idx].split("\n").length;
          });
          if (totalLines > 0) {
            // 使用加权平均，保留一部分旧值
            this.avgLineHeight =
              this.avgLineHeight * 0.3 + (totalHeight / totalLines) * 0.7;
          }
        }
      }
    },

    // 重新计算所有块的top位置
    recalculateChunkTops() {
      let cumulativeTop = 0;
      for (let i = 0; i < this.chunkHeights.length; i++) {
        this.chunkTops[i] = cumulativeTop;
        cumulativeTop += this.chunkHeights[i];
      }
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

        // 大文件模式下更新可见块
        if (this.isLargeDocument) {
          // 使用防抖避免频繁调用
          if (this.scrollTimer) {
            clearTimeout(this.scrollTimer);
          }
          this.scrollTimer = setTimeout(() => {
            this.updateVisibleChunks();
          }, 100);
        }
      };
      this.$refs.contentRef?.addEventListener("scroll", this.scrollListener);
    },

    // 移除滚动监听
    removeScrollListener() {
      if (this.scrollTimer) {
        clearTimeout(this.scrollTimer);
        this.scrollTimer = null;
      }
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
        document.documentElement
          .requestFullscreen()
          .then(() => {
            this.isFullscreen = true;
          })
          .catch((err) => {
            console.error("进入全屏失败:", err);
          });
      } else {
        document
          .exitFullscreen()
          .then(() => {
            this.isFullscreen = false;
          })
          .catch((err) => {
            console.error("退出全屏失败:", err);
          });
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

    // 添加全屏状态监听器
    addFullscreenListeners() {
      this.handleFullscreenChange = () => {
        this.isFullscreen = !!document.fullscreenElement;
      };

      document.addEventListener(
        "fullscreenchange",
        this.handleFullscreenChange
      );
      document.addEventListener(
        "webkitfullscreenchange",
        this.handleFullscreenChange
      );
      document.addEventListener(
        "mozfullscreenchange",
        this.handleFullscreenChange
      );
      document.addEventListener(
        "MSFullscreenChange",
        this.handleFullscreenChange
      );
    },

    // 移除全屏状态监听器
    removeFullscreenListeners() {
      if (this.handleFullscreenChange) {
        document.removeEventListener(
          "fullscreenchange",
          this.handleFullscreenChange
        );
        document.removeEventListener(
          "webkitfullscreenchange",
          this.handleFullscreenChange
        );
        document.removeEventListener(
          "mozfullscreenchange",
          this.handleFullscreenChange
        );
        document.removeEventListener(
          "MSFullscreenChange",
          this.handleFullscreenChange
        );
      }
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

/* 全屏时的内容区域样式 */
.document-viewer.fullscreen .viewer-content {
  padding: var(--space-md);
  height: 100vh;
}

.document-content {
  max-width: 1200px;
  margin: 0 auto;
  transition: transform var(--transition-normal);
}

.loading-container {
  padding: var(--space-2xl);
}

.chunking-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  gap: var(--space-md);
  color: var(--text-secondary);
  font-size: 16px;
}

.chunking-hint .el-icon {
  font-size: 32px;
  color: var(--primary-color);
}

/* 大文件分块渲染容器 */
.large-document-container {
  position: relative;
}

.chunks-wrapper {
  position: relative;
  width: 100%;
}

.chunk-item {
  width: 100%;
  box-sizing: border-box;
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
