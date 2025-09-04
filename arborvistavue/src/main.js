import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import MarkdownIt from "markdown-it";

// Element Plus 引入
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";

import taskLists from "markdown-it-task-lists";
import mathjax3 from "markdown-it-mathjax3";
import toc from "markdown-it-table-of-contents";
import anchor from "markdown-it-anchor";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

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

const app = createApp(App);

// 添加到全局属性
app.config.globalProperties.$md = md;

// 使用 Element Plus
app.use(ElementPlus);

app.use(router);
app.mount("#app");
