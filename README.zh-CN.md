# 智能体工程书库

[English](README.md) · **简体中文**

精选关于构建、运行和评估 AI 智能体的在线书籍、指南和技术文章。网站默认打开英文首页，可切换到简体中文。

## 在线阅读

| | English | 简体中文 |
| --- | --- | --- |
| 书库首页 | [英文首页](https://flowingfun.github.io/awsome-agentic-books/) | [中文首页](https://flowingfun.github.io/awsome-agentic-books/zh.html) |
| 全部文章 | [英文文章目录](https://flowingfun.github.io/awsome-agentic-books/articles.html) | [中文文章目录](https://flowingfun.github.io/awsome-agentic-books/articles-zh.html) |

可以从首页浏览书籍、指南和精选文章，也可以在完整文章目录中按主题查找。书库提供原文入口，有简体中文版时也会标注，部分译本可在站内阅读。

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
| [`site/`](site/) | 中英文首页、文章目录和样式表。 |
| [`books/`](books/) | 站内译本的原始材料和翻译文件。 |
| [`tools/build_site.py`](tools/build_site.py)、[`.github/workflows/pages.yml`](.github/workflows/pages.yml) | 静态站点构建脚本和 GitHub Pages 工作流。 |

编辑与翻译约定见 [AGENTS.md](AGENTS.md)。

## 授权与发布

各作品适用各自的许可。作者署名及许可声明见对应的阅读页或原始材料。

推送到 `main` 会构建并发布 `_site/`，也可从 **Actions → Build and deploy GitHub Pages** 手动运行。首次配置时，在 **Settings → Pages** 中将发布来源选为 **GitHub Actions**，无需另建发布分支。
