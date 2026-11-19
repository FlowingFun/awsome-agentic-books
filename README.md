# awsome-agentic-books

一个收录智能体工程书籍的中文书库。第一本书是 James C. Davis 的《基于模型的智能体工程：一个软件工程案例研究》。

## 中文译本

第 1 版网页版共 70 页，已完成正文、附录、目录、图注和索引的逐段翻译。原图和图内文字、代码、公式、参考文献著录信息保留原样。构建时会核对原书资源、章内锚点和站内链接。

## 本地构建与预览

在仓库根目录运行（GitHub Actions 使用 Python 3.12）：

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 tools/build_site.py --output _site
python3 -m http.server 8000 --bind 127.0.0.1 --directory _site
```

打开 <http://127.0.0.1:8000/>，点击「进入阅读」，或直接访问 <http://127.0.0.1:8000/books/mage/index.html>。`_site/` 是生成目录，不提交到仓库。

## 文件说明

| 路径 | 用途 |
| --- | --- |
| `books/mage/source/` | [原书第 1 版网页版](https://davisjam.github.io/model-based-agentic-software-engineering/book/mage-book/index.html)快照；网页、资源和原版授权原样保留，哈希记录在 `snapshot.json`。 |
| `books/mage/zh/` | 按原书页名保存逐段译文，构建时回填到原有版式。 |
| `books/mage/navigation.json` | 书名、章节目录和阅读界面的中文用语。 |
| `site/index.html`、`site/styles.css` | 中文站点首页及样式。首页的 `mage-progress` 元素由构建更新。 |
| `tools/build_site.py` | 生成静态站点。 |
| `requirements.txt` | 本地及 CI 构建依赖。 |
| `.gitignore` | 忽略构建产物和本地 Python 环境文件。 |
| `.github/workflows/pages.yml` | 构建并部署 GitHub Pages 的工作流。 |

## 续译

运行 `python3 tools/mage_text.py books/mage/source/<页名>.html` 提取正文段落。把译文写入 `books/mage/zh/<页名>.json`，保留段落编号和成对的 `⟦编号⟧` / `⟦/编号⟧`，可按中文语序移动整组。代码、公式、SVG 原图不重绘，图注和表格文字照译。译文尚未覆盖的页面明确标为英文原文；原版自带搜索仍按英文索引检索，PDF 和 EPUB 仍链接到英文原版。

## 原书授权

原书采用 MIT 许可证。原版权声明及许可证全文保存在 [`books/mage/source/LICENSE`](books/mage/source/LICENSE)；分发原书或译本时一并保留。

## GitHub Pages 配置

首次发布时，在 GitHub 仓库的 **Settings → Pages → Build and deployment** 下，将 **Source** 设为 **GitHub Actions**。项目站点地址为 <https://flowingfun.github.io/awsome-agentic-books/>。

启用后，工作流会在推送到 `main` 时运行，也可在 **Actions → Build and deploy GitHub Pages → Run workflow** 中选择 `main` 手动触发。它将用官方 Pages Actions 上传并部署 `_site/`，无需提交构建产物或另建发布分支。
