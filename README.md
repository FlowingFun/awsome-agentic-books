# Agentic Engineering Library

**English** · [简体中文](README.zh-CN.md)

A curated library of online books, guides, and engineering articles about building, operating, and evaluating AI agents. The site opens in English by default and has a Simplified Chinese edition.

## Read online

| | English | 简体中文 |
| --- | --- | --- |
| Library home | [English home](https://flowingfun.github.io/awsome-agentic-books/) | [中文首页](https://flowingfun.github.io/awsome-agentic-books/zh.html) |
| All articles | [English article directory](https://flowingfun.github.io/awsome-agentic-books/articles.html) | [中文文章目录](https://flowingfun.github.io/awsome-agentic-books/articles-zh.html) |

Start with the books, guides, and featured articles on the homepage, or browse the full article directory by topic. The catalogue links to original works and Simplified Chinese editions where available; some translations are hosted in the library.

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
| [`site/`](site/) | Bilingual homepages, article directories, and stylesheets. |
| [`books/`](books/) | Source material and translation files for hosted editions. |
| [`tools/build_site.py`](tools/build_site.py), [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | Static-site builder and GitHub Pages workflow. |

See [AGENTS.md](AGENTS.md) for editing and translation conventions.

## Attribution and deployment

Each work has its own license. See the corresponding reading page or source material for attribution and license notices.

The Pages workflow builds and deploys `_site/` on pushes to `main` and can also run manually from **Actions → Build and deploy GitHub Pages**. For a new setup, select **GitHub Actions** as the source in **Settings → Pages**. No deployment branch is needed.
