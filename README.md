# Agentic Engineering Library

**English** · [简体中文](README.zh-CN.md)

A curated library of online books, guides, and engineering articles about building, operating, and evaluating AI agents. The site opens in English by default and has a Simplified Chinese edition.

## Read online

| | English | 简体中文 |
| --- | --- | --- |
| Library home | [English home](https://flowingfun.github.io/awsome-agentic-books/) | [中文首页](https://flowingfun.github.io/awsome-agentic-books/zh.html) |
| All articles | [English article directory](https://flowingfun.github.io/awsome-agentic-books/articles.html) | [中文文章目录](https://flowingfun.github.io/awsome-agentic-books/articles-zh.html) |

The homepage has books, guides, and a short featured reading list. The full article directory is grouped by topic: agent design and context; agent loops and harnesses; and evaluation. It links to original articles and, where available, Chinese editions. External books and guides are read on their original sites.

## Chinese editions hosted here

| Edition | What is included |
| --- | --- |
| [Model-Based Agentic Engineering](https://flowingfun.github.io/awsome-agentic-books/books/mage/index.html) | James C. Davis’s complete first web edition in Simplified Chinese. The original images (including embedded text), code, equations, and bibliographic records are unchanged. The original search index, PDF, and EPUB remain in English. |
| [Building an Agentic System, Volume 1](https://flowingfun.github.io/awsome-agentic-books/books/building-an-agentic-system/introduction.html) | Gerred Dillon’s complete first volume in Simplified Chinese, with the original chapter structure, diagrams, and code preserved. |
| [Macro Evals for Agentic Systems](https://flowingfun.github.io/awsome-agentic-books/reading/macro-evals/index.html) | A Simplified Chinese reading edition of the OpenAI Cookbook notebook. It translates the explanatory text and preserves the original figures and code; the examples do not execute on the site. |

## Build and preview locally

From the repository root (GitHub Actions uses Python 3.12):

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 tools/build_site.py --output _site
python3 -m http.server 8000 --bind 127.0.0.1 --directory _site
```

Open [the local homepage](http://127.0.0.1:8000/) and use **English / 中文** to switch languages. The build checks translation coverage, protected content, and local links. `_site/` is generated and should not be committed.

## Repository map

| Path | Purpose |
| --- | --- |
| [`site/index.html`](site/index.html), [`site/zh.html`](site/zh.html) | English and Chinese homepages. The build fills in `#mage-progress`. |
| [`site/articles.html`](site/articles.html), [`site/articles-zh.html`](site/articles-zh.html) | Complete article directories grouped by topic. |
| [`site/library.css`](site/library.css), [`site/styles.css`](site/styles.css) | Library pages and shared reading-page styles, respectively. |
| [`books/mage/`](books/mage/) | Original web snapshot, translations, and navigation labels. |
| [`books/building-an-agentic-system/`](books/building-an-agentic-system/), [`books/macro-evals/`](books/macro-evals/) | Source material and translations for the first volume and the Cookbook notebook. |
| [`tools/build_site.py`](tools/build_site.py), [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | Static-site builder and GitHub Pages workflow. |

See [AGENTS.md](AGENTS.md) for editing and translation conventions.

## Attribution and deployment

The MAGE snapshot and the Cookbook notebook retain their upstream MIT notices: [MAGE license](books/mage/source/LICENSE) · [Cookbook license](books/macro-evals/source/LICENSE). *Building an Agentic System* is attributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see the reading-page footers. These are work-specific notices, not a blanket license for all linked material.

The Pages workflow builds and deploys `_site/` on pushes to `main` and can also run manually from **Actions → Build and deploy GitHub Pages**. For a new setup, select **GitHub Actions** as the source in **Settings → Pages**. No deployment branch is needed.
