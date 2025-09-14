<template>
  <div class="home-container">
    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-container">
        <div class="hero-content">
          <div class="hero-text">
            <h1 class="hero-title">
              <span class="title-icon">
                <el-icon size="48">
                  <Document />
                </el-icon>
              </span>
              ArborVista
            </h1>
            <p class="hero-subtitle">智能文档处理平台，让文档管理更简单高效</p>
            <div class="hero-features">
              <div
                v-for="feature in heroFeatures"
                :key="feature"
                class="feature-item"
              >
                <el-icon class="feature-icon"><Check /></el-icon>
                <span>{{ feature }}</span>
              </div>
            </div>
            <div class="hero-actions">
              <el-button type="primary" size="large" class="cta-button">
                <el-icon><Upload /></el-icon>
                开始处理文档
              </el-button>
            </div>
          </div>
          <div class="hero-visual">
            <div class="visual-card">
              <div class="card-header">
                <div class="card-dots">
                  <span class="dot red"></span>
                  <span class="dot yellow"></span>
                  <span class="dot green"></span>
                </div>
                <span class="card-title">文档处理预览</span>
              </div>
              <div class="card-content">
                <div class="file-preview">
                  <el-icon size="32"><Document /></el-icon>
                  <span>PDF文档.pdf</span>
                </div>
                <div class="processing-steps">
                  <div class="step completed">
                    <el-icon><Check /></el-icon>
                    <span>OCR识别</span>
                  </div>
                  <div class="step completed">
                    <el-icon><Check /></el-icon>
                    <span>公式提取</span>
                  </div>
                  <div class="step processing">
                    <el-icon><Loading /></el-icon>
                    <span>表格识别</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 配置区域 -->
    <section class="config-section">
      <div class="section-container">
        <div class="section-header">
          <h2 class="section-title">处理配置</h2>
          <p class="section-subtitle">自定义文档处理参数，获得最佳处理效果</p>
        </div>

        <div class="config-grid">
          <!-- 文库选择 -->
          <div class="config-card">
            <div class="card-header">
              <el-icon class="card-icon"><Collection /></el-icon>
              <h3 class="card-title">选择文库</h3>
            </div>
            <div class="card-content">
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
              <el-button
                @click="showCreateLibraryDialog = true"
                class="create-library-btn"
                size="large"
              >
                <el-icon><Plus /></el-icon>
                创建新文库
              </el-button>
            </div>
          </div>

          <!-- 处理选项 -->
          <div class="config-card">
            <div class="card-header">
              <el-icon class="card-icon"><Setting /></el-icon>
              <h3 class="card-title">处理选项</h3>
            </div>
            <div class="card-content">
              <div class="option-group">
                <el-switch v-model="isOcr" active-text="OCR识别" size="large" />
                <el-switch
                  v-model="enableFormula"
                  active-text="公式识别"
                  size="large"
                />
                <el-switch
                  v-model="enableTable"
                  active-text="表格识别"
                  size="large"
                />
              </div>
            </div>
          </div>

          <!-- 语言设置 -->
          <div class="config-card">
            <div class="card-header">
              <el-icon class="card-icon"><Collection /></el-icon>
              <h3 class="card-title">语言设置</h3>
            </div>
            <div class="card-content">
              <el-select
                v-model="language"
                placeholder="选择语言"
                class="language-select"
                size="large"
              >
                <el-option
                  v-for="lang in languageOptions"
                  :key="lang.value"
                  :label="lang.label"
                  :value="lang.value"
                />
              </el-select>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 文件上传区域 -->
    <section class="upload-section">
      <div class="section-container">
        <div class="section-header">
          <h2 class="section-title">上传文档</h2>
          <p class="section-subtitle">支持PDF、PNG、JPG格式，拖拽或点击上传</p>
        </div>

        <el-upload
          ref="uploadRef"
          :file-list="fileList"
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :before-upload="beforeUpload"
          drag
          multiple
          class="upload-dragger"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、PNG、JPG 格式，最大 100MB
            </div>
          </template>
        </el-upload>

        <div v-if="fileList.length > 0" class="file-list">
          <div class="file-list-header">
            <div class="file-count-info">
              <el-icon class="count-icon"><Document /></el-icon>
              <h3>已选择文件 ({{ fileList.length }})</h3>
            </div>
            <el-button
              @click="clearFiles"
              type="danger"
              size="small"
              class="clear-btn"
            >
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
          <div class="file-items">
            <div
              v-for="(file, index) in fileList"
              :key="index"
              class="file-item"
            >
              <div class="file-item-left">
                <div class="file-icon-container">
                  <el-icon class="file-icon"><Document /></el-icon>
                </div>
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
              </div>
              <el-button
                @click="removeFile(index)"
                type="danger"
                size="small"
                circle
                class="remove-btn"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <div class="upload-actions">
          <el-button
            @click="startProcessing"
            type="primary"
            size="large"
            :loading="isProcessing"
            :disabled="fileList.length === 0"
            class="process-button"
          >
            <el-icon v-if="!isProcessing"><Setting /></el-icon>
            {{
              isProcessing
                ? "处理中..."
                : `开始处理 (${fileList.length} 个文件)`
            }}
          </el-button>
        </div>
      </div>
    </section>

    <!-- 创建文库对话框 -->
    <el-dialog
      v-model="showCreateLibraryDialog"
      title="创建新文库"
      width="500px"
      :before-close="handleCreateLibraryClose"
      class="create-library-dialog"
    >
      <el-form
        ref="libraryFormRef"
        :model="newLibrary"
        :rules="libraryRules"
        label-width="80px"
      >
        <el-form-item label="文库名称" prop="name">
          <el-input
            v-model="newLibrary.name"
            placeholder="请输入文库名称"
            size="large"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="newLibrary.description"
            type="textarea"
            :rows="3"
            placeholder="请输入文库描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateLibraryDialog = false" size="large">
            取消
          </el-button>
          <el-button
            type="primary"
            @click="createLibrary"
            :loading="isCreatingLibrary"
            size="large"
          >
            创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import {
  Document,
  Check,
  Upload,
  UploadFilled,
  Collection,
  Plus,
  Setting,
  Close,
  Loading,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { uploadFiles, getLibraries, createLibrary } from "@/config/api";

export default {
  name: "HomeView",
  components: {
    Document,
    Check,
    Upload,
    UploadFilled,
    Collection,
    Plus,
    Setting,
    Close,
    Loading,
  },
  data() {
    return {
      // 英雄区域数据
      heroFeatures: [
        "智能OCR识别",
        "数学公式提取",
        "表格结构识别",
        "多格式支持",
        "批量处理",
        "云端存储",
      ],

      // 文库数据
      libraries: [],
      selectedLibrary: "",
      showCreateLibraryDialog: false,
      newLibrary: {
        name: "",
        description: "",
      },
      libraryRules: {
        name: [
          { required: true, message: "请输入文库名称", trigger: "blur" },
          {
            min: 2,
            max: 20,
            message: "文库名称长度在 2 到 20 个字符",
            trigger: "blur",
          },
        ],
      },
      isCreatingLibrary: false,

      // 处理配置
      isOcr: true,
      enableFormula: true,
      enableTable: true,
      language: "ch",

      // 语言选项
      languageOptions: [
        { value: "ch", label: "中文" },
        { value: "en", label: "English" },
        { value: "ja", label: "日本語" },
        { value: "ko", label: "한국어" },
      ],

      // 文件上传
      fileList: [],
      isProcessing: false,
    };
  },
  computed: {
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
  mounted() {
    this.loadLibraries();
  },
  methods: {
    // 加载文库列表
    async loadLibraries() {
      try {
        const response = await getLibraries();
        console.log("文库API响应:", response);
        this.libraries = Array.isArray(response.data.data)
          ? response.data.data
          : [];
        console.log("解析后的文库列表:", this.libraries);

        if (this.libraries.length === 0) {
          this.libraries = [{ id: "default", name: "默认文库" }];
        }

        // 设置默认选中的文库
        if (!this.selectedLibrary && this.libraries.length > 0) {
          this.selectedLibrary = this.libraries[0].id;
        }
      } catch (error) {
        console.error("加载文库失败:", error);
        this.libraries = [{ id: "default", name: "默认文库" }];
        this.selectedLibrary = "default";
      }
    },

    // 文库选择变化
    onLibraryChange() {
      console.log("选择文库:", this.selectedLibrary);
    },

    // 创建文库
    async createLibrary() {
      try {
        await this.$refs.libraryFormRef.validate();
        this.isCreatingLibrary = true;

        await createLibrary({
          name: this.newLibrary.name,
          description: this.newLibrary.description,
        });

        ElMessage.success("文库创建成功");
        this.showCreateLibraryDialog = false;
        this.newLibrary = { name: "", description: "" };
        this.loadLibraries();
      } catch (error) {
        console.error("创建文库失败:", error);
        ElMessage.error("创建文库失败");
      } finally {
        this.isCreatingLibrary = false;
      }
    },

    // 关闭创建文库对话框
    handleCreateLibraryClose(done) {
      this.newLibrary = { name: "", description: "" };
      this.$refs.libraryFormRef.resetFields();
      done();
    },

    // 文件变化处理
    handleFileChange(file, fileList) {
      this.fileList = fileList;
    },

    // 文件移除处理
    handleFileRemove(file, fileList) {
      this.fileList = fileList;
    },

    // 上传前检查
    beforeUpload(file) {
      const allowedTypes = ["application/pdf", "image/png", "image/jpeg"];
      const isAllowed = allowedTypes.includes(file.type);
      if (!isAllowed) {
        ElMessage.error("只支持 PDF、PNG、JPG 格式的文件");
        return false;
      }
      return true;
    },

    // 移除文件
    removeFile(index) {
      this.fileList.splice(index, 1);
    },

    // 清空文件
    clearFiles() {
      this.fileList = [];
    },

    // 格式化文件大小
    formatFileSize(size) {
      if (size < 1024) return size + " B";
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
      return (size / (1024 * 1024)).toFixed(1) + " MB";
    },

    // 开始处理
    async startProcessing() {
      if (this.fileList.length === 0) {
        ElMessage.warning("请先选择文件");
        return;
      }

      if (!this.selectedLibrary) {
        ElMessage.warning("请先选择文库");
        return;
      }

      this.isProcessing = true;

      try {
        const formData = new FormData();
        this.fileList.forEach((file) => {
          formData.append("files", file.raw);
        });

        formData.append("library_id", this.selectedLibrary);
        formData.append("is_ocr", this.isOcr);
        formData.append("enable_formula", this.enableFormula);
        formData.append("enable_table", this.enableTable);
        formData.append("language", this.language);

        const response = await uploadFiles(formData);

        if (response.data.success) {
          ElMessage.success(response.data.message);
          this.fileList = [];
          this.$refs.uploadRef.clearFiles();
        } else {
          ElMessage.error(response.data.error || "处理失败");
        }
      } catch (error) {
        console.error("处理失败:", error);
        ElMessage.error("处理失败，请重试");
      } finally {
        this.isProcessing = false;
      }
    },
  },
};
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: var(--bg-primary);
}

/* 英雄区域 */
.hero-section {
  padding: var(--space-3xl) 0;
  background: linear-gradient(
    135deg,
    var(--bg-primary) 0%,
    var(--bg-secondary) 100%
  );
  position: relative;
  overflow: hidden;
}

.hero-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-lg);
}

.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3xl);
  align-items: center;
}

.hero-text {
  max-width: 600px;
}

.hero-title {
  font-size: 64px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-lg) 0;
  line-height: 1.1;
  letter-spacing: -2px;
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.title-icon {
  color: var(--primary-color);
  filter: drop-shadow(0 4px 12px rgba(0, 122, 255, 0.3));
}

.hero-subtitle {
  font-size: 24px;
  color: var(--text-secondary);
  margin: 0 0 var(--space-xl) 0;
  line-height: 1.4;
  font-weight: 400;
}

.hero-features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  transition: var(--transition-fast);
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.feature-icon {
  color: var(--primary-color);
  font-size: 16px;
}

.hero-actions {
  margin-top: var(--space-xl);
}

.cta-button {
  padding: var(--space-md) var(--space-xl);
  font-size: 18px;
  font-weight: 600;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  transition: var(--transition-normal);
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}

/* 英雄区域视觉元素 */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.visual-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(20px);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-light);
}

.card-dots {
  display: flex;
  gap: var(--space-xs);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red {
  background: #ff5f57;
}

.dot.yellow {
  background: #ffbd2e;
}

.dot.green {
  background: #28ca42;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.card-content {
  padding: var(--space-lg);
}

.file-preview {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.processing-steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  font-size: 14px;
  transition: var(--transition-fast);
}

.step.completed {
  background: rgba(40, 202, 66, 0.1);
  color: #28ca42;
}

.step.processing {
  background: rgba(0, 122, 255, 0.1);
  color: var(--primary-color);
}

/* 配置区域 */
.config-section {
  padding: var(--space-3xl) 0;
  background: var(--bg-primary);
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-lg);
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-3xl);
}

.section-title {
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  letter-spacing: -1px;
}

.section-subtitle {
  font-size: 20px;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 400;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-lg);
}

.config-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: var(--transition-normal);
  backdrop-filter: blur(20px);
}

.config-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-light);
}

.card-icon {
  color: var(--primary-color);
  font-size: 20px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-content {
  padding: var(--space-lg);
}

.library-select,
.language-select,
.model-select {
  width: 100%;
  margin-bottom: var(--space-md);
}

.create-library-btn {
  width: 100%;
  border-radius: var(--radius-md);
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

/* 上传区域 */
.upload-section {
  padding: var(--space-3xl) 0;
  background: var(--bg-secondary);
}

.upload-dragger {
  width: 100%;
  margin-bottom: var(--space-xl);
  border: none !important;
  background: transparent !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  position: relative;
  overflow: visible;
}

.upload-dragger:hover {
  background: transparent !important;
  transform: none;
  box-shadow: none !important;
}

.upload-dragger:active {
  transform: none;
  box-shadow: none !important;
}

/* 美化上传图标 */
.upload-dragger .el-icon--upload {
  font-size: 48px !important;
  color: var(--primary-color) !important;
  margin-bottom: 16px !important;
  filter: drop-shadow(0 2px 8px rgba(0, 122, 255, 0.2));
  transition: all 0.3s ease;
}

.upload-dragger:hover .el-icon--upload {
  transform: scale(1.1);
  filter: drop-shadow(0 4px 12px rgba(0, 122, 255, 0.3));
}

/* 美化上传文字 */
.upload-dragger .el-upload__text {
  font-size: 16px !important;
  font-weight: 500 !important;
  color: var(--text-primary) !important;
  margin-bottom: 8px !important;
  transition: color 0.3s ease;
}

.upload-dragger:hover .el-upload__text {
  color: var(--primary-color) !important;
}

.upload-dragger .el-upload__text em {
  color: var(--primary-color) !important;
  font-style: normal !important;
  font-weight: 600 !important;
}

/* 美化提示文字 */
.upload-dragger .el-upload__tip {
  font-size: 14px !important;
  color: var(--text-secondary) !important;
  margin-top: 8px !important;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.upload-dragger:hover .el-upload__tip {
  opacity: 1;
}

.file-list {
  margin-top: var(--space-lg);
  background: transparent;
  border: none;
  border-radius: 0;
  overflow: visible;
  box-shadow: none;
}

.file-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) 0;
  background: transparent;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: var(--space-md);
}

.file-count-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.count-icon {
  color: var(--primary-color);
  font-size: 20px;
}

.file-list-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.clear-btn {
  border-radius: var(--radius-md);
  font-weight: 500;
}

.file-items {
  padding: var(--space-md);
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  background: transparent;
  border-radius: 0;
  margin-bottom: var(--space-sm);
  transition: var(--transition-fast);
  border: none;
  border-bottom: 1px solid #f3f4f6;
}

.file-item:hover {
  background: #f9fafb;
  transform: none;
  box-shadow: none;
}

.file-item:last-child {
  margin-bottom: 0;
}

.file-item-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
}

.file-icon-container {
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-icon {
  color: var(--primary-color);
  font-size: 16px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.file-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.file-size {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.remove-btn {
  opacity: 0.7;
  transition: var(--transition-fast);
}

.remove-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.upload-actions {
  text-align: center;
  margin-top: var(--space-xl);
}

.process-button {
  padding: 16px 32px;
  font-size: 18px;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(
    135deg,
    var(--primary-color),
    var(--primary-light)
  ) !important;
  border: none !important;
  position: relative;
  overflow: hidden;
  min-width: 200px;
}

.process-button::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  transition: left 0.6s ease;
}

.process-button:hover:not(:disabled)::before {
  left: 100%;
}

.process-button:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 122, 255, 0.4);
}

.process-button:active:not(:disabled) {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3);
}

.process-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

/* 对话框样式 */
.create-library-dialog {
  border-radius: var(--radius-xl);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-content {
    grid-template-columns: 1fr;
    gap: var(--space-xl);
    text-align: center;
  }

  .hero-title {
    font-size: 48px;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .hero-subtitle {
    font-size: 20px;
  }

  .hero-features {
    grid-template-columns: 1fr;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }

  .section-title {
    font-size: 36px;
  }

  .section-subtitle {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .hero-container,
  .section-container {
    padding: 0 var(--space-md);
  }

  .hero-title {
    font-size: 36px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .section-title {
    font-size: 28px;
  }

  .upload-content {
    padding: var(--space-xl);
  }

  .upload-title {
    font-size: 18px;
  }

  .upload-subtitle {
    font-size: 14px;
  }
}
</style>
