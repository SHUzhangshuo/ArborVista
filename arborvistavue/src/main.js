import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import MarkdownIt from "markdown-it";

// Element Plus 引入
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";

// Element Plus 图标
import * as ElementPlusIconsVue from "@element-plus/icons-vue";

// Element Plus 中文语言包
import zhCn from "element-plus/dist/locale/zh-cn.mjs";

// Markdown 相关插件
import taskLists from "markdown-it-task-lists";
import mathjax3 from "markdown-it-mathjax3";
import toc from "markdown-it-table-of-contents";
import anchor from "markdown-it-anchor";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

// 引入自定义 Markdown 样式
import "./assets/markdown.css";

// 创建 MarkdownIt 实例
const md = new MarkdownIt({
  html: true, // 允许 HTML 标签
  breaks: true, // 转换换行符为 <br>
  linkify: true, // 自动转换 URL 为链接
  typographer: true, // 启用一些语言中性的替换 + 引号美化
  tables: true, // 确保表格支持启用
  quotes: ["「", "」", "『", "』"], // 中文引号美化
  langPrefix: "hljs language-", // 代码高亮类名前缀
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) {
        // 忽略高亮错误，使用默认处理
      }
    }
    return ""; // 使用默认的转义
  },
});

// 逐个添加插件，避免链式调用出错
try {
  md.use(taskLists, { enabled: true });
  console.log("✅ taskLists plugin loaded");
} catch (e) {
  console.warn("❌ taskLists plugin failed:", e);
}

try {
  md.use(mathjax3);
  console.log("✅ mathjax3 plugin loaded");
} catch (e) {
  console.warn("❌ mathjax3 plugin failed:", e);
}

try {
  md.use(anchor, {
    permalink: true,
    permalinkBefore: true,
    permalinkSymbol: "§",
  });
  console.log("✅ anchor plugin loaded");
} catch (e) {
  console.warn("❌ anchor plugin failed:", e);
}

try {
  md.use(toc, {
    includeLevel: [1, 2, 3],
    containerHeaderHtml: "<h2>目录</h2>",
  });
  console.log("✅ toc plugin loaded");
} catch (e) {
  console.warn("❌ toc plugin failed:", e);
}

// 创建 Vue 应用
const app = createApp(App);

// 添加 MarkdownIt 到全局属性
app.config.globalProperties.$md = md;

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// 使用 Element Plus
app.use(ElementPlus, {
  locale: zhCn, // 设置中文语言包
  size: "default", // 设置组件默认尺寸
  zIndex: 3000, // 设置弹层初始 z-index
});

// 使用路由
app.use(router);

// 挂载应用
app.mount("#app");

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error("Vue Error:", err);
  console.error("Component:", vm);
  console.error("Info:", info);
};

// 全局警告处理
app.config.warnHandler = (msg, vm, trace) => {
  console.warn("Vue Warning:", msg);
  console.warn("Component:", vm);
  console.warn("Trace:", trace);
};
