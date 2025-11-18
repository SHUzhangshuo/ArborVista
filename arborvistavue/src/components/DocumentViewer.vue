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
          @click="openRAGDialog"
          circle
          size="large"
          class="action-btn"
          title="AI问答"
        >
          <el-icon><ChatDotRound /></el-icon>
        </el-button>
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

    <!-- 构建向量数据库对话框 -->
    <el-dialog
      v-model="showBuildDialog"
      title="构建向量数据库"
      width="500px"
      :close-on-click-modal="false"
      class="build-vector-store-dialog"
    >
      <div class="build-dialog-content">
        <div class="build-icon">
          <el-icon size="64"><Connection /></el-icon>
        </div>
        <div class="build-info">
          <h3>向量数据库不存在</h3>
          <p class="build-description">
            为了使用AI问答功能，需要先为当前文库构建向量数据库。构建过程将：
          </p>
          <ul class="build-features">
            <li>
              <el-icon><Check /></el-icon>
              分析所有论文内容
            </li>
            <li>
              <el-icon><Check /></el-icon>
              生成向量索引
            </li>
            <li>
              <el-icon><Check /></el-icon>
              支持智能问答检索
            </li>
          </ul>
          <div class="build-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>构建过程可能需要几分钟，请耐心等待</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showBuildDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="confirmBuildVectorStore"
            :loading="isBuildingVectorStore"
          >
            <el-icon><Connection /></el-icon>
            立即构建
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- RAG问答对话框 -->
    <el-dialog
      v-model="showRAGDialog"
      title="AI论文问答"
      width="80%"
      :close-on-click-modal="false"
      class="rag-dialog"
    >
      <div class="rag-container">
        <!-- 查询模式选择 -->
        <div class="rag-mode-selector">
          <el-button
            :type="ragQueryMode === 'single_paper' ? 'primary' : ''"
            @click="ragQueryMode = 'single_paper'"
            :disabled="isRAGLoading"
            size="small"
          >
            <el-icon><Document /></el-icon>
            当前论文
          </el-button>
          <el-button
            :type="ragQueryMode === 'all_papers' ? 'primary' : ''"
            @click="ragQueryMode = 'all_papers'"
            :disabled="isRAGLoading"
            size="small"
          >
            <el-icon><Collection /></el-icon>
            整个文档库
          </el-button>
        </div>

        <!-- 输入区域 -->
        <div class="rag-input-area">
          <el-input
            v-model="ragQuestion"
            type="textarea"
            :rows="3"
            :placeholder="
              ragQueryMode === 'single_paper'
                ? '请输入关于当前论文的问题，例如：这篇论文的主要贡献是什么？论文中提到了哪些关键技术？'
                : '请输入问题，可以从所有论文中检索，例如：哪些论文提到了transformer？agent最火的论文是哪个？'
            "
            :disabled="isRAGLoading"
          />
          <div class="rag-actions">
            <el-button
              type="primary"
              @click="submitRAGQuery"
              :loading="isRAGLoading"
              :disabled="!ragQuestion.trim()"
            >
              <el-icon><Search /></el-icon>
              提问
            </el-button>
            <el-button @click="clearRAGResult" :disabled="isRAGLoading">
              清空
            </el-button>
          </div>
        </div>

        <!-- 结果区域 -->
        <div v-if="ragResult" class="rag-result-area">
          <!-- 查询范围提示 -->
          <div class="rag-query-info">
            <el-tag
              :type="
                ragResult.query_scope === 'single_paper' ? 'info' : 'success'
              "
            >
              {{
                ragResult.query_scope === "single_paper"
                  ? "当前论文"
                  : "整个文档库"
              }}
            </el-tag>
            <span class="paper-count"
              >涉及 {{ ragResult.paper_count }} 篇论文</span
            >
          </div>

          <!-- 回答 -->
          <div class="rag-answer-section">
            <h3>AI回答</h3>
            <div
              class="rag-answer-content"
              v-html="formatRAGAnswer(ragResult.answer)"
            ></div>
          </div>

          <!-- 来源 -->
          <div
            v-if="ragResult.sources && ragResult.sources.length > 0"
            class="rag-sources-section"
          >
            <h3>参考来源 ({{ ragResult.sources.length }} 个片段)</h3>
            <div
              v-for="(source, index) in ragResult.sources"
              :key="index"
              class="rag-source-item"
            >
              <div class="source-header">
                <span class="source-index">{{ index + 1 }}</span>
                <span class="source-filename">{{ source.filename }}</span>
                <span v-if="source.library_name" class="source-library">
                  [{{ source.library_name }}]
                </span>
                <span class="source-chunk"
                  >片段 {{ source.chunk_index + 1 }}</span
                >
              </div>
              <div
                class="source-content"
                v-html="formatRAGContent(source.content_preview)"
              ></div>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="isRAGLoading" class="rag-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI正在思考中...</span>
        </div>

        <!-- 空状态 -->
        <div v-if="!ragResult && !isRAGLoading" class="rag-empty">
          <el-icon size="48"><ChatDotRound /></el-icon>
          <p>输入问题开始AI问答</p>
        </div>
      </div>
    </el-dialog>

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
  ChatDotRound,
  Search,
  Collection,
  Connection,
  Check,
  InfoFilled,
} from "@element-plus/icons-vue";
import MarkdownIt from "markdown-it";
import markdownItMathjax3 from "markdown-it-mathjax3";
import { ElMessage } from "element-plus";

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
    ChatDotRound,
    Search,
    Collection,
    Connection,
    Check,
    InfoFilled,
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
    libraryId: {
      type: String,
      default: "",
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
      // RAG相关
      showRAGDialog: false,
      ragQuestion: "",
      ragResult: null,
      isRAGLoading: false,
      ragQueryMode: "single_paper", // "single_paper" 或 "all_papers"
      // 构建向量数据库对话框
      showBuildDialog: false,
      isBuildingVectorStore: false,
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
        this.setupTableHandlers();
        this.updatePageInfo();
        // 小文件直接对整个文档进行MathJax渲染
        if (
          !this.isLargeDocument &&
          window.MathJax &&
          window.MathJax.typesetPromise
        ) {
          window.MathJax.typesetPromise()
            .then(() => {
              // MathJax渲染完成后，为公式添加交互功能
              this.setupFormulaHandlers();
            })
            .catch((err) => {
              console.warn("MathJax渲染失败:", err);
            });
        }
      });
    },
    visibleRenderedContent() {
      // 大文件分块渲染后的处理（已废弃，改为在renderChunk后调用）
      this.$nextTick(() => {
        this.setupImageHandlers();
        this.setupTableHandlers();
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
      } else {
        // 即使没有新块需要渲染，也要检查是否有新的公式和表格需要设置处理器
        // 因为 MathJax 可能在后续才完成渲染
        setTimeout(() => {
          this.setupFormulaHandlers();
          this.setupTableHandlers();
        }, 100);
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
      window.MathJax.typesetPromise(Array.from(chunkElements))
        .then(() => {
          // MathJax渲染完成后，为公式添加交互功能
          this.setupFormulaHandlers();
          // 同时设置表格处理器
          this.setupTableHandlers();
        })
        .catch((err) => {
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

    // 设置表格处理器（悬停效果和点击复制）
    setupTableHandlers() {
      if (!this.$refs.contentRef) return;

      // 查找所有表格元素
      const tables = this.$refs.contentRef.querySelectorAll(
        ".markdown-content table:not(.table-clickable)"
      );

      tables.forEach((table) => {
        // 标记已处理，避免重复添加
        table.classList.add("table-clickable");

        // 添加可点击样式
        table.style.cursor = "pointer";
        table.style.transition = "all 0.2s ease";

        // 添加点击事件来复制表格
        table.addEventListener("click", (e) => {
          e.stopPropagation();
          this.copyTableToClipboard(table);
        });
      });
    },

    // 设置公式处理器（悬停效果和点击复制）
    setupFormulaHandlers() {
      if (!this.$refs.contentRef) return;

      // 首先，为所有 script 标签添加原始 Markdown 格式
      this.attachOriginalMarkdownToFormulas();

      // 查找所有 MathJax 渲染的公式元素
      // MathJax 3 使用 mjx-container 类
      const formulaElements = this.$refs.contentRef.querySelectorAll(
        "mjx-container:not(.formula-clickable), .MathJax:not(.formula-clickable)"
      );

      formulaElements.forEach((element) => {
        // 标记已处理，避免重复添加
        element.classList.add("formula-clickable");

        // 添加可点击样式
        element.style.cursor = "pointer";
        element.style.transition = "all 0.2s ease";

        // 添加点击事件来复制公式
        element.addEventListener("click", (e) => {
          e.stopPropagation();
          this.copyFormulaToClipboard(element);
        });
      });
    },

    // 为公式 script 标签附加原始 Markdown 格式
    attachOriginalMarkdownToFormulas() {
      if (!this.$refs.contentRef || !this.documentContent) return;

      // 查找所有包含公式的 script 标签
      const scriptElements = this.$refs.contentRef.querySelectorAll(
        "script[type='math/tex'], script[type='math/tex; mode=display']"
      );

      scriptElements.forEach((scriptElement) => {
        // 如果已经有原始 Markdown 数据，跳过
        if (scriptElement.dataset.originalMarkdown) return;

        const latexContent = (
          scriptElement.textContent ||
          scriptElement.innerText ||
          ""
        ).trim();
        if (!latexContent) return;

        const isDisplayMode = scriptElement.type === "math/tex; mode=display";

        // 从原始文档内容中查找匹配的公式
        let markdownFormula = "";

        // 方法1: 尝试精确匹配 LaTeX 内容
        // 清理 LaTeX 内容中的空白字符用于匹配
        const normalizedLatex = latexContent.replace(/\s+/g, " ").trim();

        if (isDisplayMode) {
          // 块级公式：匹配 $$...$$ 或 \[...\]
          // 使用更灵活的匹配，允许空白字符差异
          const displayPatterns = [
            // 匹配 $$...$$ 格式
            new RegExp(
              `\\$\\$[\\s\\S]*?${this.escapeRegex(
                normalizedLatex
              )}[\\s\\S]*?\\$\\$`,
              "g"
            ),
            // 匹配 \[...\] 格式
            new RegExp(
              `\\\\\\[[\\s\\S]*?${this.escapeRegex(
                normalizedLatex
              )}[\\s\\S]*?\\\\\\]`,
              "g"
            ),
          ];

          for (const pattern of displayPatterns) {
            const matches = this.documentContent.match(pattern);
            if (matches && matches.length > 0) {
              // 选择最接近的匹配（通常第一个就是）
              markdownFormula = matches[0].trim();
              break;
            }
          }

          // 如果精确匹配失败，尝试匹配所有块级公式，然后通过内容相似度选择
          if (!markdownFormula) {
            const allDisplayFormulas = this.documentContent.match(
              /\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]/g
            );
            if (allDisplayFormulas) {
              // 找到内容最相似的公式
              for (const formula of allDisplayFormulas) {
                const formulaContent = formula
                  .replace(/^\$\$|^\$|^\$|\\\[|\\\]|\$\$$/g, "")
                  .trim()
                  .replace(/\s+/g, " ");
                if (
                  formulaContent.includes(normalizedLatex) ||
                  normalizedLatex.includes(formulaContent)
                ) {
                  markdownFormula = formula.trim();
                  break;
                }
              }
            }
          }
        } else {
          // 行内公式：匹配 $...$ 或 \(...\)
          // 先找到所有可能的行内公式，然后过滤掉块级公式
          const allInlineFormulas = this.documentContent.match(
            /\$[^$\n]+?\$|\\\([^)]+?\\\)/g
          );
          if (allInlineFormulas) {
            for (const formula of allInlineFormulas) {
              // 排除块级公式（以 $$ 开头和结尾的）
              if (formula.startsWith("$$") && formula.endsWith("$$")) continue;

              const formulaContent = formula
                .replace(/^\$|^\$|\\\(|\\\)|\$$/g, "")
                .trim()
                .replace(/\s+/g, " ");
              if (
                formulaContent.includes(normalizedLatex) ||
                normalizedLatex.includes(formulaContent)
              ) {
                markdownFormula = formula.trim();
                break;
              }
            }
          }

          // 如果还是没找到，尝试正则匹配
          if (!markdownFormula) {
            const inlinePatterns = [
              // 匹配 \(...\) 格式
              new RegExp(
                `\\\\\\([^)]*?${this.escapeRegex(
                  normalizedLatex
                )}[^)]*?\\\\\\)`,
                "g"
              ),
            ];

            for (const pattern of inlinePatterns) {
              const matches = this.documentContent.match(pattern);
              if (matches && matches.length > 0) {
                markdownFormula = matches[0].trim();
                break;
              }
            }
          }
        }

        // 如果还是找不到，使用 LaTeX 内容构造 Markdown 格式
        if (!markdownFormula) {
          markdownFormula = isDisplayMode
            ? `$$${latexContent}$$`
            : `$${latexContent}$`;
        }

        // 将原始 Markdown 格式存储到 data 属性
        scriptElement.dataset.originalMarkdown = markdownFormula;
      });
    },

    // 转义正则表达式特殊字符
    escapeRegex(str) {
      return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    },

    // 复制公式到剪贴板（复制原始 Markdown 格式）
    async copyFormulaToClipboard(formulaElement) {
      try {
        // 查找包含原始公式内容的 script 标签
        let scriptElement = null;

        // 方法1: 查找相邻的 script 标签
        let sibling = formulaElement.previousElementSibling;
        while (sibling && !scriptElement) {
          if (
            sibling.tagName === "SCRIPT" &&
            (sibling.type === "math/tex" ||
              sibling.type === "math/tex; mode=display")
          ) {
            scriptElement = sibling;
            break;
          }
          sibling = sibling.previousElementSibling;
        }

        // 如果前一个兄弟节点没找到，查找后一个兄弟节点
        if (!scriptElement) {
          sibling = formulaElement.nextElementSibling;
          while (sibling && !scriptElement) {
            if (
              sibling.tagName === "SCRIPT" &&
              (sibling.type === "math/tex" ||
                sibling.type === "math/tex; mode=display")
            ) {
              scriptElement = sibling;
              break;
            }
            sibling = sibling.nextElementSibling;
          }
        }

        // 方法2: 在元素内部查找 script 标签
        if (!scriptElement && formulaElement.querySelector) {
          scriptElement = formulaElement.querySelector(
            "script[type='math/tex'], script[type='math/tex; mode=display']"
          );
        }

        // 方法3: 从父元素查找
        if (!scriptElement) {
          let current = formulaElement.parentElement;
          let depth = 0;
          while (current && depth < 3 && !scriptElement) {
            scriptElement = current.querySelector
              ? current.querySelector(
                  "script[type='math/tex'], script[type='math/tex; mode=display']"
                )
              : null;
            if (scriptElement) break;
            current = current.parentElement;
            depth++;
          }
        }

        // 获取原始 Markdown 格式
        let markdownFormula = "";

        if (scriptElement && scriptElement.dataset.originalMarkdown) {
          // 优先使用已存储的原始 Markdown 格式
          markdownFormula = scriptElement.dataset.originalMarkdown;
        } else if (scriptElement) {
          // 如果没有存储，尝试从原始文档中查找
          const latexContent = (
            scriptElement.textContent ||
            scriptElement.innerText ||
            ""
          ).trim();
          const isDisplayMode = scriptElement.type === "math/tex; mode=display";

          if (latexContent && this.documentContent) {
            // 尝试从原始文档中匹配
            const escapedContent = latexContent.replace(
              /[.*+?^${}()|[\]\\]/g,
              "\\$&"
            );

            if (isDisplayMode) {
              const patterns = [
                new RegExp(`\\$\\$\\s*${escapedContent}\\s*\\$\\$`, "g"),
                new RegExp(`\\\\\\[\\s*${escapedContent}\\s*\\\\\\]`, "g"),
              ];

              for (const pattern of patterns) {
                const matches = this.documentContent.match(pattern);
                if (matches && matches.length > 0) {
                  markdownFormula = matches[0].trim();
                  break;
                }
              }
            } else {
              const patterns = [
                new RegExp(`\\$\\s*${escapedContent}\\s*\\$`, "g"),
                new RegExp(`\\\\\\(\\s*${escapedContent}\\s*\\\\\\)`, "g"),
              ];

              for (const pattern of patterns) {
                const matches = this.documentContent.match(pattern);
                if (matches && matches.length > 0) {
                  markdownFormula = matches[0].trim();
                  break;
                }
              }
            }

            // 如果还是找不到，构造 Markdown 格式
            if (!markdownFormula) {
              markdownFormula = isDisplayMode
                ? `$$${latexContent}$$`
                : `$${latexContent}$`;
            }
          }
        } else {
          // 如果找不到 script 标签，使用元素的文本内容作为后备
          const formulaContent =
            formulaElement.textContent || formulaElement.innerText || "";
          const trimmedContent = formulaContent.trim().replace(/\s+/g, " ");
          const isBlock =
            formulaElement.closest("p") === null ||
            formulaElement.parentElement?.tagName === "DIV";

          if (trimmedContent) {
            markdownFormula = isBlock
              ? `$$${trimmedContent}$$`
              : `$${trimmedContent}$`;
          }
        }

        // 复制到剪贴板
        if (markdownFormula) {
          await navigator.clipboard.writeText(markdownFormula);
          ElMessage.success({
            message: "公式已复制到剪贴板（Markdown格式）",
            duration: 2000,
          });
        } else {
          ElMessage.warning({
            message: "无法获取公式代码",
            duration: 2000,
          });
        }
      } catch (error) {
        console.error("复制公式失败:", error);
        // 降级方案：使用传统的复制方法
        try {
          const formulaContent =
            formulaElement.textContent || formulaElement.innerText || "";
          const trimmedContent = formulaContent.trim().replace(/\s+/g, " ");
          const isBlock =
            formulaElement.closest("p") === null ||
            formulaElement.parentElement?.tagName === "DIV";
          const markdownFormula = isBlock
            ? `$$${trimmedContent}$$`
            : `$${trimmedContent}$`;

          const textArea = document.createElement("textarea");
          textArea.value = markdownFormula;
          textArea.style.position = "fixed";
          textArea.style.opacity = "0";
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand("copy");
          document.body.removeChild(textArea);
          ElMessage.success({
            message: "公式已复制到剪贴板（Markdown格式）",
            duration: 2000,
          });
        } catch (fallbackError) {
          console.error("降级复制方案也失败:", fallbackError);
          ElMessage.error({
            message: "复制失败，请手动选择文本复制",
            duration: 2000,
          });
        }
      }
    },

    // 复制表格到剪贴板（复制为 Markdown 格式）
    async copyTableToClipboard(tableElement) {
      try {
        // 将 HTML 表格转换为 Markdown 格式
        const markdownTable = this.convertTableToMarkdown(tableElement);

        if (markdownTable) {
          await navigator.clipboard.writeText(markdownTable);
          ElMessage.success({
            message: "表格已复制到剪贴板（Markdown格式）",
            duration: 2000,
          });
        } else {
          ElMessage.warning({
            message: "无法转换表格",
            duration: 2000,
          });
        }
      } catch (error) {
        console.error("复制表格失败:", error);
        // 降级方案：使用传统的复制方法
        try {
          const markdownTable = this.convertTableToMarkdown(tableElement);
          const textArea = document.createElement("textarea");
          textArea.value = markdownTable;
          textArea.style.position = "fixed";
          textArea.style.opacity = "0";
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand("copy");
          document.body.removeChild(textArea);
          ElMessage.success({
            message: "表格已复制到剪贴板（Markdown格式）",
            duration: 2000,
          });
        } catch (fallbackError) {
          console.error("降级复制方案也失败:", fallbackError);
          ElMessage.error({
            message: "复制失败，请手动选择文本复制",
            duration: 2000,
          });
        }
      }
    },

    // 将 HTML 表格转换为 Markdown 格式
    convertTableToMarkdown(tableElement) {
      const rows = [];
      const thead = tableElement.querySelector("thead");
      const tbody = tableElement.querySelector("tbody") || tableElement;

      // 处理表头
      if (thead) {
        const headerRow = thead.querySelector("tr");
        if (headerRow) {
          const headerCells = Array.from(headerRow.querySelectorAll("th, td"));
          const headerTexts = headerCells.map((cell) =>
            this.getCellText(cell).trim()
          );
          rows.push(headerTexts);

          // 添加分隔行
          const separator = headerTexts.map(() => "---");
          rows.push(separator);
        }
      }

      // 处理表体
      const bodyRows = tbody.querySelectorAll("tr");
      bodyRows.forEach((row) => {
        const cells = Array.from(row.querySelectorAll("td, th"));
        const cellTexts = cells.map((cell) => this.getCellText(cell).trim());
        if (cellTexts.length > 0) {
          rows.push(cellTexts);
        }
      });

      // 如果没有表头，使用第一行作为表头
      if (!thead && rows.length > 0) {
        const firstRow = rows[0];
        const separator = firstRow.map(() => "---");
        rows.splice(1, 0, separator);
      }

      // 转换为 Markdown 格式
      return rows
        .map((row) => {
          // 确保所有行的列数一致（以第一行为准）
          const maxCols = rows[0] ? rows[0].length : row.length;
          const paddedRow = [...row];
          while (paddedRow.length < maxCols) {
            paddedRow.push("");
          }
          return "| " + paddedRow.join(" | ") + " |";
        })
        .join("\n");
    },

    // 获取单元格文本（处理嵌套元素和公式）
    getCellText(cell) {
      // 克隆单元格以避免修改原始 DOM
      const clone = cell.cloneNode(true);

      // 处理 MathJax 公式：尝试从 script 标签获取原始 LaTeX
      const scripts = clone.querySelectorAll(
        "script[type='math/tex'], script[type='math/tex; mode=display']"
      );
      scripts.forEach((script) => {
        const latexContent = (
          script.textContent ||
          script.innerText ||
          ""
        ).trim();
        if (latexContent) {
          let markdownFormula = "";

          // 方法1: 尝试从已存储的原始 Markdown 格式获取
          if (script.dataset && script.dataset.originalMarkdown) {
            markdownFormula = script.dataset.originalMarkdown;
          }
          // 方法2: 从原始文档中查找匹配的公式
          else if (this.documentContent) {
            const normalizedLatex = latexContent.replace(/\s+/g, " ").trim();
            const isDisplayMode = script.type === "math/tex; mode=display";

            if (isDisplayMode) {
              const patterns = [
                new RegExp(
                  `\\$\\$[\\s\\S]*?${this.escapeRegex(
                    normalizedLatex
                  )}[\\s\\S]*?\\$\\$`,
                  "g"
                ),
                new RegExp(
                  `\\\\\\[[\\s\\S]*?${this.escapeRegex(
                    normalizedLatex
                  )}[\\s\\S]*?\\\\\\]`,
                  "g"
                ),
              ];

              for (const pattern of patterns) {
                const matches = this.documentContent.match(pattern);
                if (matches && matches.length > 0) {
                  markdownFormula = matches[0].trim();
                  break;
                }
              }
            } else {
              const allInlineFormulas = this.documentContent.match(
                /\$[^$\n]+?\$|\\\([^)]+?\\\)/g
              );
              if (allInlineFormulas) {
                for (const formula of allInlineFormulas) {
                  if (formula.startsWith("$$") && formula.endsWith("$$"))
                    continue;
                  const formulaContent = formula
                    .replace(/^\$|^\$|\\\(|\\\)|\$$/g, "")
                    .trim()
                    .replace(/\s+/g, " ");
                  if (
                    formulaContent.includes(normalizedLatex) ||
                    normalizedLatex.includes(formulaContent)
                  ) {
                    markdownFormula = formula.trim();
                    break;
                  }
                }
              }
            }
          }

          // 如果还是找不到，使用 LaTeX 内容构造 Markdown 格式
          if (!markdownFormula) {
            const isDisplayMode = script.type === "math/tex; mode=display";
            markdownFormula = isDisplayMode
              ? `$$${latexContent}$$`
              : `$${latexContent}$`;
          }

          // 替换 script 标签内容为 Markdown 格式
          script.textContent = markdownFormula;
        }
      });

      // 移除 script 标签，保留文本内容
      const tempDiv = document.createElement("div");
      tempDiv.appendChild(clone);
      let text = tempDiv.innerHTML;

      // 清理 HTML 标签，保留文本
      text = text
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "") // 移除剩余的 script 标签
        .replace(/<[^>]+>/g, "") // 移除所有 HTML 标签
        .replace(/&nbsp;/g, " ") // 替换 &nbsp;
        .replace(/&amp;/g, "&") // 替换 &amp;
        .replace(/&lt;/g, "<") // 替换 &lt;
        .replace(/&gt;/g, ">") // 替换 &gt;
        .replace(/&quot;/g, '"') // 替换 &quot;
        .replace(/&#39;/g, "'") // 替换 &#39;
        .trim();

      return text || "";
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

    // RAG相关方法
    openRAGDialog() {
      if (!this.libraryId || !this.documentId) {
        ElMessage.warning("缺少文库ID或文档ID，无法使用AI问答功能");
        return;
      }
      this.showRAGDialog = true;
      this.ragQuestion = "";
      this.ragResult = null;
    },

    async submitRAGQuery() {
      if (!this.ragQuestion.trim()) {
        ElMessage.warning("请输入问题");
        return;
      }

      if (!this.libraryId) {
        ElMessage.error("缺少文库ID");
        return;
      }

      // 如果是单篇论文查询，需要文档ID
      if (this.ragQueryMode === "single_paper" && !this.documentId) {
        ElMessage.error("缺少文档ID，无法查询单篇论文");
        return;
      }

      this.isRAGLoading = true;
      this.ragResult = null;

      try {
        const axios = (await import("axios")).default;
        const API_BASE_URL =
          process.env.VUE_APP_API_URL ||
          (window.location.hostname === "localhost" ||
          window.location.hostname === "127.0.0.1"
            ? "http://127.0.0.1:5000"
            : `${window.location.protocol}//${window.location.hostname}:5000`);

        // 根据查询模式选择不同的API端点
        let url, payload;
        if (this.ragQueryMode === "single_paper") {
          // 单篇论文查询
          url = `${API_BASE_URL}/api/libraries/${this.libraryId}/files/${this.documentId}/rag`;
          payload = {
            question: this.ragQuestion.trim(),
            query_mode: "single_paper",
          };
        } else {
          // 整个文档库查询
          url = `${API_BASE_URL}/api/libraries/${this.libraryId}/rag`;
          payload = {
            question: this.ragQuestion.trim(),
            query_mode: "all_papers",
          };
        }

        const response = await axios.post(url, payload);

        if (response.data.success) {
          this.ragResult = {
            answer: response.data.answer,
            sources: response.data.sources || [],
            paper_count: response.data.paper_count || 0,
            query_scope: response.data.query_scope || this.ragQueryMode,
          };
          ElMessage.success("查询成功");
        } else {
          ElMessage.error(response.data.error || "查询失败");

          // 如果是向量数据库不存在，提供构建选项
          if (
            response.data.error &&
            response.data.error.includes("向量数据库不存在")
          ) {
            this.showBuildVectorStoreDialog();
          }
        }
      } catch (error) {
        console.error("RAG查询失败:", error);
        const errorMsg =
          error.response?.data?.error || error.message || "查询失败";
        ElMessage.error(errorMsg);

        // 如果是向量数据库不存在，提供构建选项
        if (
          error.response?.status === 404 &&
          (error.response?.data?.error?.includes("向量数据库不存在") ||
            error.response?.data?.error?.includes("未找到"))
        ) {
          this.showBuildVectorStoreDialog();
        } else if (error.response?.data?.hint) {
          ElMessage.info(error.response.data.hint);
        }
      } finally {
        this.isRAGLoading = false;
      }
    },

    // 显示构建向量数据库对话框
    showBuildVectorStoreDialog() {
      this.showBuildDialog = true;
    },

    // 确认构建向量数据库
    async confirmBuildVectorStore() {
      if (!this.libraryId) {
        ElMessage.error("缺少文库ID");
        return;
      }

      this.isBuildingVectorStore = true;

      try {
        const axios = (await import("axios")).default;
        const API_BASE_URL =
          process.env.VUE_APP_API_URL ||
          (window.location.hostname === "localhost" ||
          window.location.hostname === "127.0.0.1"
            ? "http://127.0.0.1:5000"
            : `${window.location.protocol}//${window.location.hostname}:5000`);

        const response = await axios.post(
          `${API_BASE_URL}/api/libraries/${this.libraryId}/build_vector_store`,
          {}
        );

        if (response.data.success) {
          this.showBuildDialog = false;
          ElMessage.success(
            `向量数据库构建成功！共处理 ${
              response.data.paper_count || 0
            } 篇论文`
          );
          // 构建成功后，可以自动重新查询
          if (this.ragQuestion.trim()) {
            // 延迟一下再查询，确保数据库已完全加载
            setTimeout(() => {
              this.submitRAGQuery();
            }, 500);
          }
        } else {
          ElMessage.error(response.data.error || "构建失败");
        }
      } catch (error) {
        console.error("构建向量数据库失败:", error);
        const errorMsg =
          error.response?.data?.error || error.message || "构建失败";
        ElMessage.error(errorMsg);
      } finally {
        this.isBuildingVectorStore = false;
      }
    },

    clearRAGResult() {
      this.ragQuestion = "";
      this.ragResult = null;
    },

    formatRAGAnswer(answer) {
      if (!answer) return "";
      // 简单的文本格式化，将换行转换为<br>
      return answer
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>")
        .replace(/^(.+)$/, "<p>$1</p>");
    },

    formatRAGContent(content) {
      if (!content) return "";
      // 简单的文本格式化
      return content.replace(/\n/g, "<br>").replace(/^(.+)$/, "<p>$1</p>");
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

/* 表格交互样式 */
.markdown-content :deep(table.table-clickable) {
  position: relative;
  transition: all 0.2s ease;
}

.markdown-content :deep(table.table-clickable:hover) {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
  transform: scale(1.01);
}

.markdown-content :deep(table.table-clickable:active) {
  transform: scale(0.99);
}

/* 为表格添加提示工具 */
.markdown-content :deep(table.table-clickable::before) {
  content: "点击复制表格";
  position: absolute;
  top: -32px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 1000;
}

.markdown-content :deep(table.table-clickable:hover::before) {
  opacity: 1;
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

/* 数学公式交互样式 */
.markdown-content :deep(mjx-container.formula-clickable),
.markdown-content :deep(.MathJax.formula-clickable) {
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 4px;
  padding: 2px 4px;
  margin: 0 2px;
}

.markdown-content :deep(mjx-container.formula-clickable:hover),
.markdown-content :deep(.MathJax.formula-clickable:hover) {
  background-color: rgba(64, 158, 255, 0.1);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
  transform: scale(1.02);
}

.markdown-content :deep(mjx-container.formula-clickable:active),
.markdown-content :deep(.MathJax.formula-clickable:active) {
  transform: scale(0.98);
  background-color: rgba(64, 158, 255, 0.15);
}

/* 为公式添加提示工具 */
.markdown-content :deep(mjx-container.formula-clickable::after),
.markdown-content :deep(.MathJax.formula-clickable::after) {
  content: "点击复制";
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-4px);
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  z-index: 1000;
  margin-bottom: 4px;
}

.markdown-content :deep(mjx-container.formula-clickable:hover::after),
.markdown-content :deep(.MathJax.formula-clickable:hover::after) {
  opacity: 1;
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

/* RAG对话框样式 */
.rag-dialog {
  max-width: 90vw;
}

.rag-container {
  min-height: 400px;
}

.rag-input-area {
  margin-bottom: var(--space-xl);
}

.rag-actions {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-md);
  justify-content: flex-end;
}

.rag-result-area {
  margin-top: var(--space-xl);
  max-height: 60vh;
  overflow-y: auto;
}

.rag-answer-section {
  margin-bottom: var(--space-2xl);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--primary-color);
}

.rag-answer-section h3 {
  margin: 0 0 var(--space-md) 0;
  color: var(--primary-color);
  font-size: 18px;
  font-weight: 600;
}

.rag-answer-content {
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 15px;
}

.rag-answer-content p {
  margin-bottom: var(--space-md);
}

.rag-sources-section {
  margin-top: var(--space-2xl);
}

.rag-sources-section h3 {
  margin: 0 0 var(--space-md) 0;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
}

.rag-source-item {
  margin-bottom: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  transition: var(--transition-fast);
}

.rag-source-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.source-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  font-size: 14px;
  color: var(--text-secondary);
}

.source-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.source-filename {
  font-weight: 600;
  color: var(--text-primary);
}

.source-library {
  color: var(--primary-color);
  font-size: 12px;
}

.source-chunk {
  margin-left: auto;
  font-size: 12px;
}

.source-content {
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  max-height: 200px;
  overflow-y: auto;
}

.source-content p {
  margin: 0;
}

.rag-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
  gap: var(--space-md);
}

.rag-loading .el-icon {
  font-size: 32px;
}

.rag-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
  gap: var(--space-md);
}

.rag-empty p {
  margin: 0;
  font-size: 16px;
}

/* 查询模式选择器样式 - 模仿底部工具栏按钮 */
.rag-mode-selector {
  margin-bottom: var(--space-xl);
  display: flex;
  gap: var(--space-md);
}

.rag-query-info {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.paper-count {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 构建向量数据库对话框样式 */
.build-vector-store-dialog :deep(.el-dialog__body) {
  padding: var(--space-2xl) var(--space-xl);
}

.build-dialog-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.build-icon {
  margin-bottom: var(--space-lg);
  color: var(--primary-color);
}

.build-info {
  width: 100%;
}

.build-info h3 {
  margin: 0 0 var(--space-md) 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.build-description {
  margin: 0 0 var(--space-lg) 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.build-features {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-lg) 0;
  text-align: left;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.build-features li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
  font-size: 14px;
  color: var(--text-primary);
}

.build-features li .el-icon {
  color: var(--primary-color);
  font-size: 18px;
}

.build-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: rgba(0, 122, 255, 0.1);
  border-radius: var(--radius-md);
  color: var(--primary-color);
  font-size: 14px;
}

.build-tip .el-icon {
  font-size: 18px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
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
