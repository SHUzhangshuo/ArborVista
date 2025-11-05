<template>
  <div class="library-container">
    <!-- 文库选择器 -->
    <div class="library-selector">
      <div class="selector-content">
        <div class="selector-left">
          <el-icon class="selector-icon"><Folder /></el-icon>
          <span class="selector-label">当前文库：</span>
          <el-select
            v-model="selectedLibrary"
            placeholder="选择文库"
            @change="onLibraryChange"
            class="library-select"
            size="large"
          >
            <el-option
              v-for="library in libraries"
              :key="library.id"
              :label="library.name"
              :value="library.id"
            />
          </el-select>
        </div>
        <div class="selector-right">
          <span class="file-count">{{ filteredFiles.length }} 个文档</span>
          <el-button
            @click="buildVectorStore"
            :loading="isBuildingVectorStore"
            :disabled="!selectedLibrary || filteredFiles.length === 0"
            size="large"
            type="primary"
          >
            <el-icon><Connection /></el-icon>
            {{
              vectorStoreStatus === "exists"
                ? "重建向量数据库"
                : "构建向量数据库"
            }}
          </el-button>
          <el-button @click="loadFiles" :loading="isLoading" size="large">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <div class="search-content">
        <div class="search-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索文档..."
            @input="handleSearch"
            class="search-input"
            size="large"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="search-right">
          <el-select
            v-model="sortBy"
            @change="filterFiles"
            class="sort-select"
            size="large"
          >
            <el-option label="按时间排序" value="time" />
            <el-option label="按名称排序" value="name" />
            <el-option label="按大小排序" value="size" />
          </el-select>
          <el-button-group class="view-toggle">
            <el-button
              :type="viewMode === 'grid' ? 'primary' : ''"
              @click="viewMode = 'grid'"
              size="large"
            >
              <el-icon><Grid /></el-icon>
            </el-button>
            <el-button
              :type="viewMode === 'list' ? 'primary' : ''"
              @click="viewMode = 'list'"
              size="large"
            >
              <el-icon><List /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="documents-section">
      <div v-if="isLoading" class="loading-state">
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="filteredFiles.length === 0" class="empty-state">
        <div class="empty-content">
          <el-icon class="empty-icon" size="64">
            <Document />
          </el-icon>
          <h3 class="empty-title">暂无文档</h3>
          <p class="empty-subtitle">
            {{ searchQuery ? "没有找到匹配的文档" : "该文库中还没有文档" }}
          </p>
          <el-button
            v-if="!searchQuery"
            @click="$router.push('/')"
            type="primary"
            size="large"
          >
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </div>
      </div>

      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="grid-view">
        <div class="documents-grid">
          <div
            v-for="file in paginatedFiles"
            :key="file.id"
            class="document-card"
            @click="selectFile(file)"
          >
            <div class="card-header">
              <div class="file-icon">
                <el-icon size="32">
                  <Document />
                </el-icon>
              </div>
              <div class="file-actions">
                <el-button
                  @click.stop="selectFile(file)"
                  type="primary"
                  size="small"
                  circle
                >
                  <el-icon><View /></el-icon>
                </el-button>
                <el-button
                  @click.stop="deleteFile(file)"
                  type="danger"
                  size="small"
                  circle
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="card-content">
              <h3 class="file-title" :title="file.name">{{ file.name }}</h3>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <span class="file-date">{{ formatDate(file.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 列表视图 -->
      <div v-else class="list-view">
        <div class="documents-table">
          <div
            v-for="file in paginatedFiles"
            :key="file.id"
            class="document-row"
            @click="selectFile(file)"
          >
            <div class="row-icon">
              <el-icon size="24">
                <Document />
              </el-icon>
            </div>
            <div class="row-content">
              <h3 class="file-title">{{ file.name }}</h3>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <span class="file-date">{{ formatDate(file.created_at) }}</span>
              </div>
            </div>
            <div class="row-actions">
              <el-button
                @click.stop="selectFile(file)"
                type="primary"
                size="small"
              >
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button
                @click.stop="deleteFile(file)"
                type="danger"
                size="small"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="filteredFiles.length > pageSize" class="pagination-section">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="filteredFiles.length"
          @current-change="handlePageChange"
          layout="prev, pager, next"
          class="pagination"
        />
      </div>
    </div>

    <!-- 文档查看器 -->
    <DocumentViewer
      :visible="showPreviewDialog"
      :document-id="selectedFile?.id || ''"
      :document-name="selectedFile?.name || ''"
      :file-size="selectedFile?.size || 0"
      :created-at="selectedFile?.created_at || ''"
      :document-content="documentContent"
      :is-loading="isLoadingContent"
      :library-id="selectedLibrary"
      @close="handlePreviewClose"
      @preview-image="handleImagePreview"
      @download-document="handleDownloadDocument"
    />

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showImageDialog"
      :title="currentImageName"
      width="auto"
      class="image-dialog"
    >
      <img
        :src="currentImageUrl"
        :alt="currentImageName"
        class="preview-image"
      />
    </el-dialog>
  </div>
</template>

<script>
import {
  Refresh,
  Folder,
  Search,
  Grid,
  List,
  Document,
  Connection,
  View,
  Upload,
  Delete,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import {
  getLibraries,
  getFiles,
  getLibraryFileContent,
  deleteFile,
} from "@/config/api";
import DocumentViewer from "@/components/DocumentViewer.vue";

export default {
  name: "LibraryView",
  components: {
    Refresh,
    Folder,
    Search,
    Grid,
    List,
    Document,
    Connection,
    View,
    Upload,
    Delete,
    DocumentViewer,
  },
  data() {
    return {
      // 文库数据
      libraries: [],
      selectedLibrary: "default",

      // 文件数据
      files: [],
      filteredFiles: [],
      selectedFile: null,

      // 搜索和排序
      searchQuery: "",
      sortBy: "time",

      // 视图模式
      viewMode: "grid",

      // 分页
      currentPage: 1,
      pageSize: 12,

      // 加载状态
      isLoading: false,
      isLoadingContent: false,

      // 预览对话框
      showPreviewDialog: false,
      documentContent: "",

      // 图片预览
      showImageDialog: false,
      currentImageUrl: "",
      currentImageName: "",

      // 向量数据库状态
      isBuildingVectorStore: false,
      vectorStoreStatus: "unknown", // "unknown" | "exists" | "not_exists"
    };
  },
  computed: {
    paginatedFiles() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.filteredFiles.slice(start, end);
    },
    selectedLibraryName() {
      if (!Array.isArray(this.libraries)) {
        return "未知文库";
      }
      const library = this.libraries.find(
        (lib) => lib.id === this.selectedLibrary
      );
      return library ? library.name : "未知文库";
    },
  },
  created() {
    // 组件创建时的初始化
  },
  mounted() {
    this.loadLibraries();
    this.loadFiles();
  },
  methods: {
    // 加载文库列表
    async loadLibraries() {
      try {
        const response = await getLibraries();
        this.libraries = Array.isArray(response.data.data)
          ? response.data.data
          : [];
        if (this.libraries.length === 0) {
          this.libraries = [{ id: "default", name: "默认文库" }];
        }

        // 确保selectedLibrary在libraries中存在
        if (!this.libraries.find((lib) => lib.id === this.selectedLibrary)) {
          this.selectedLibrary = this.libraries[0]?.id || "default";
        }
      } catch (error) {
        console.error("加载文库失败:", error);
        this.libraries = [{ id: "default", name: "默认文库" }];
        this.selectedLibrary = "default";
      }
    },

    // 加载文件列表
    async loadFiles() {
      if (!this.selectedLibrary) return;

      this.isLoading = true;
      try {
        const response = await getFiles(this.selectedLibrary);
        this.files = Array.isArray(response.data.data)
          ? response.data.data
          : [];
        this.filterFiles();
        this.checkVectorStoreStatus();
      } catch (error) {
        console.error("加载文件失败:", error);
        ElMessage.error("加载文件失败");
        this.files = [];
      } finally {
        this.isLoading = false;
      }
    },

    // 筛选文件
    filterFiles() {
      let filtered = Array.isArray(this.files) ? [...this.files] : [];

      // 搜索筛选
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter((file) =>
          file.name.toLowerCase().includes(query)
        );
      }

      // 排序
      filtered.sort((a, b) => {
        switch (this.sortBy) {
          case "name":
            return a.name.localeCompare(b.name);
          case "size":
            return (b.size || 0) - (a.size || 0);
          case "time":
          default:
            return new Date(b.created_at) - new Date(a.created_at);
        }
      });

      this.filteredFiles = filtered;
      this.currentPage = 1;
    },

    // 搜索处理
    handleSearch() {
      this.filterFiles();
    },

    // 文库选择变化
    onLibraryChange() {
      this.selectedFile = null;
      this.currentPage = 1;
      this.loadFiles();
    },

    // 选择文件
    async selectFile(file) {
      this.selectedFile = file;
      this.showPreviewDialog = true;
      await this.loadDocumentContent(file);
    },

    // 加载文档内容
    async loadDocumentContent(file) {
      this.isLoadingContent = true;
      this.documentContent = "";

      try {
        const response = await getLibraryFileContent(
          this.selectedLibrary,
          file.id
        );
        this.documentContent = response.data.content || "";
      } catch (error) {
        console.error("加载文档内容失败:", error);
        ElMessage.error("加载文档内容失败");
      } finally {
        this.isLoadingContent = false;
      }
    },

    // 处理图片预览
    handleImagePreview({ url, name }) {
      this.currentImageUrl = url;
      this.currentImageName = name;
      this.showImageDialog = true;
    },

    // 处理文档下载
    handleDownloadDocument() {
      if (this.selectedFile) {
        // 这里可以实现文档下载逻辑
        ElMessage.info("文档下载功能开发中...");
      }
    },

    // 删除文件
    async deleteFile(file) {
      try {
        await this.$confirm(
          `确定要删除文档 "${file.name}" 吗？此操作不可撤销。`,
          "确认删除",
          {
            confirmButtonText: "删除",
            cancelButtonText: "取消",
            type: "warning",
            confirmButtonClass: "el-button--danger",
          }
        );

        // 调用后端删除API
        await deleteFile(this.selectedLibrary, file.id);

        // 从列表中移除
        const index = this.files.findIndex((f) => f.id === file.id);
        if (index > -1) {
          this.files.splice(index, 1);
          this.filterFiles();
        }

        ElMessage.success("文档删除成功");
      } catch (error) {
        if (error !== "cancel") {
          console.error("删除文档失败:", error);
          ElMessage.error("删除文档失败，请重试");
        }
      }
    },

    // 关闭预览对话框
    handlePreviewClose() {
      this.selectedFile = null;
      this.documentContent = "";
      this.showPreviewDialog = false;
    },

    // 检查向量数据库状态
    async checkVectorStoreStatus() {
      if (!this.selectedLibrary) {
        this.vectorStoreStatus = "unknown";
        return;
      }

      try {
        const axios = (await import("axios")).default;
        const API_BASE_URL =
          process.env.VUE_APP_API_URL ||
          (window.location.hostname === "localhost" ||
          window.location.hostname === "127.0.0.1"
            ? "http://127.0.0.1:5000"
            : `${window.location.protocol}//${window.location.hostname}:5000`);

        // 尝试加载向量数据库来检查是否存在
        const response = await axios.get(
          `${API_BASE_URL}/api/libraries/${this.selectedLibrary}/vector_store_status`
        );

        if (response.data.exists) {
          this.vectorStoreStatus = "exists";
        } else {
          this.vectorStoreStatus = "not_exists";
        }
      } catch (error) {
        // 如果API不存在或返回404，说明向量数据库不存在
        if (error.response?.status === 404) {
          this.vectorStoreStatus = "not_exists";
        } else {
          this.vectorStoreStatus = "unknown";
        }
      }
    },

    // 构建向量数据库
    async buildVectorStore() {
      if (!this.selectedLibrary) {
        ElMessage.warning("请先选择文库");
        return;
      }

      if (this.filteredFiles.length === 0) {
        ElMessage.warning("文库中没有文档，无法构建向量数据库");
        return;
      }

      try {
        await this.$confirm(
          this.vectorStoreStatus === "exists"
            ? "重建向量数据库将覆盖现有数据，是否继续？"
            : `将为文库 "${this.selectedLibrary}" 构建向量数据库，包含 ${this.filteredFiles.length} 篇论文。构建过程可能需要几分钟，是否继续？`,
          "构建向量数据库",
          {
            confirmButtonText: "确认构建",
            cancelButtonText: "取消",
            type: "info",
          }
        );

        this.isBuildingVectorStore = true;

        const axios = (await import("axios")).default;
        const API_BASE_URL =
          process.env.VUE_APP_API_URL ||
          (window.location.hostname === "localhost" ||
          window.location.hostname === "127.0.0.1"
            ? "http://127.0.0.1:5000"
            : `${window.location.protocol}//${window.location.hostname}:5000`);

        const response = await axios.post(
          `${API_BASE_URL}/api/libraries/${this.selectedLibrary}/build_vector_store`,
          {}
        );

        if (response.data.success) {
          ElMessage.success(
            `向量数据库构建成功！共处理 ${
              response.data.paper_count || this.filteredFiles.length
            } 篇论文`
          );
          this.vectorStoreStatus = "exists";
        } else {
          ElMessage.error(response.data.error || "构建失败");
        }
      } catch (error) {
        if (error !== "cancel") {
          console.error("构建向量数据库失败:", error);
          const errorMsg =
            error.response?.data?.error || error.message || "构建失败";
          ElMessage.error(errorMsg);
        }
      } finally {
        this.isBuildingVectorStore = false;
      }
    },

    // 分页变化
    handlePageChange(page) {
      this.currentPage = page;
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
.library-container {
  min-height: 100vh;
  background: var(--bg-primary);
  padding: var(--space-lg);
}

/* 文库选择器 */
.library-selector {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  margin-bottom: var(--space-xl);
  backdrop-filter: blur(20px);
}

.selector-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
}

.selector-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.selector-icon {
  color: var(--primary-color);
  font-size: 20px;
}

.selector-label {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.library-select {
  width: 200px;
}

.selector-right {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.selector-right .el-button {
  margin-left: var(--space-md);
}

.file-count {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 搜索区域 */
.search-section {
  margin-bottom: var(--space-xl);
}

.search-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  max-width: 1200px;
  margin: 0 auto;
}

.search-left {
  flex: 1;
  max-width: 400px;
}

.search-input {
  width: 100%;
}

.search-right {
  display: flex;
  align-items: center;
  gap: 60px;
}

.sort-select {
  width: 150px;
}

.view-toggle {
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-left: 40px;
}

.view-toggle .el-button {
  margin: 0;
  border-radius: 0;
}

.view-toggle .el-button:first-child {
  border-top-left-radius: var(--radius-md);
  border-bottom-left-radius: var(--radius-md);
}

.view-toggle .el-button:last-child {
  border-top-right-radius: var(--radius-md);
  border-bottom-right-radius: var(--radius-md);
}

/* 文档区域 */
.documents-section {
  max-width: 1200px;
  margin: 0 auto;
}

.loading-state {
  padding: var(--space-2xl);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-content {
  text-align: center;
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: var(--space-lg);
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.empty-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0 0 var(--space-lg) 0;
}

/* 网格视图 */
.grid-view {
  margin-bottom: var(--space-xl);
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-lg);
}

.document-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  cursor: pointer;
  transition: var(--transition-normal);
  backdrop-filter: blur(20px);
}

.document-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-light);
}

.file-icon {
  color: var(--primary-color);
}

.file-actions {
  opacity: 0;
  transition: var(--transition-fast);
}

.document-card:hover .file-actions {
  opacity: 1;
}

.card-content {
  padding: var(--space-lg);
}

.file-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: var(--text-secondary);
}

/* 列表视图 */
.list-view {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  backdrop-filter: blur(20px);
}

.documents-table {
  padding: var(--space-sm);
}

.document-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-fast);
  margin-bottom: var(--space-xs);
}

.document-row:hover {
  background: var(--bg-secondary);
}

.document-row:last-child {
  margin-bottom: 0;
}

.row-icon {
  color: var(--primary-color);
  flex-shrink: 0;
}

.row-content {
  flex: 1;
  min-width: 0;
}

.row-content .file-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 var(--space-xs) 0;
}

.row-content .file-meta {
  font-size: 14px;
  color: var(--text-secondary);
}

.row-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: var(--transition-fast);
}

.document-row:hover .row-actions {
  opacity: 1;
}

/* 分页 */
.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: var(--space-xl);
}

.pagination {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

/* 图片预览对话框 */
.image-dialog {
  border-radius: var(--radius-xl);
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .library-container {
    padding: var(--space-md);
  }

  .selector-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .library-select {
    width: 100%;
  }

  .search-content {
    flex-direction: column;
    align-items: stretch;
  }

  .search-left {
    max-width: none;
  }

  .search-right {
    justify-content: space-between;
    gap: 40px;
  }

  .view-toggle {
    margin-left: 30px;
  }

  .documents-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .selector-content {
    padding: var(--space-md);
  }

  .search-content {
    gap: var(--space-md);
  }

  .search-right {
    flex-direction: column;
    gap: var(--space-md);
  }

  .sort-select {
    width: 100%;
  }

  .view-toggle {
    width: 100%;
  }

  .view-toggle .el-button {
    flex: 1;
  }
}
</style>
