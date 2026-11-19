# 智能体工程书库

[English](README.md) · **简体中文**

精选关于构建、运行和评估 AI 智能体的在线书籍、指南和技术文章。网站默认打开英文首页，可切换到简体中文。

## 在线阅读

| | English | 简体中文 |
| --- | --- | --- |
| 书库首页 | [英文首页](https://flowingfun.github.io/awsome-agentic-books/) | [中文首页](https://flowingfun.github.io/awsome-agentic-books/zh.html) |
| 全部文章 | [英文文章目录](https://flowingfun.github.io/awsome-agentic-books/articles.html) | [中文文章目录](https://flowingfun.github.io/awsome-agentic-books/articles-zh.html) |

首页展示书籍、指南和精选文章。全部文章按「智能体设计与上下文」「智能体循环与运行环境」「智能体评估」分组，提供原文链接，并在有中文版时给出入口。收录的外部书籍和指南在原站阅读。

## 站内中文译本

| 译本 | 内容 |
| --- | --- |
| [《基于模型的智能体工程》](https://flowingfun.github.io/awsome-agentic-books/books/mage/index.html) | James C. Davis 著，第 1 版网页版全文翻译。保留原图（含图中文字）、代码、公式和参考文献著录；原书搜索索引、PDF 和 EPUB 仍为英文。 |
| [《构建智能体系统》第一卷](https://flowingfun.github.io/awsome-agentic-books/books/building-an-agentic-system/introduction.html) | Gerred Dillon 著，第一卷全文翻译，保留原书目录结构、图表和代码。 |
| [《智能体系统的整体评估》](https://flowingfun.github.io/awsome-agentic-books/reading/macro-evals/index.html) | OpenAI Cookbook Notebook 的简体中文阅读版，翻译说明文字，保留原图和示例代码；网页不执行代码。 |

## 本地构建与预览

在仓库根目录运行（GitHub Actions 使用 Python 3.12）：

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 tools/build_site.py --output _site
python3 -m http.server 8000 --bind 127.0.0.1 --directory _site
```

打开[本地首页](http://127.0.0.1:8000/)，使用 **English / 中文** 切换语言。构建会核对译文覆盖、受保护的原书内容和站内链接。`_site/` 是生成目录，不提交到仓库。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| [`site/index.html`](site/index.html)、[`site/zh.html`](site/zh.html) | 中英文首页；`#mage-progress` 由构建填入。 |
| [`site/articles.html`](site/articles.html)、[`site/articles-zh.html`](site/articles-zh.html) | 按主题分组的中英文文章目录。 |
| [`site/library.css`](site/library.css)、[`site/styles.css`](site/styles.css) | 分别用于书库页面和共用阅读页。 |
| [`books/mage/`](books/mage/) | 原书网页快照、逐段译文和导航用语。 |
| [`books/building-an-agentic-system/`](books/building-an-agentic-system/)、[`books/macro-evals/`](books/macro-evals/) | 《构建智能体系统》第一卷和 Cookbook Notebook 的原始材料与译文。 |
| [`tools/build_site.py`](tools/build_site.py)、[`.github/workflows/pages.yml`](.github/workflows/pages.yml) | 静态站点构建脚本和 GitHub Pages 工作流。 |

编辑与翻译约定见 [AGENTS.md](AGENTS.md)。

## 授权与发布

MAGE 快照与 Cookbook Notebook 保留各自原版的 MIT 声明：[MAGE 许可](books/mage/source/LICENSE) · [Cookbook 许可](books/macro-evals/source/LICENSE)。《构建智能体系统》按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 标注来源，详见阅读页页脚。以上许可对应各自作品，不适用于所有外链材料。

推送到 `main` 会构建并发布 `_site/`，也可从 **Actions → Build and deploy GitHub Pages** 手动运行。首次配置时，在 **Settings → Pages** 中将发布来源选为 **GitHub Actions**，无需另建发布分支。
