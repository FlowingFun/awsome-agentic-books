"""Build the Chinese web edition of Building an Agentic System, volume one."""
from collections import Counter
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin, urlsplit

from mage_text import apply, extract, page

BOOK = Path(__file__).resolve().parents[1] / 'books/building-an-agentic-system'
UPSTREAM = 'https://gerred.github.io/building-an-agentic-system/'
TITLES = {
    'introduction': '导论',
    'overview-and-philosophy': '概览与设计理念',
    'core-architecture': '核心架构',
    'system-architecture-diagram': '系统架构模式',
    'system-prompts-and-model-settings': '系统提示词与配置',
    'initialization-process': '初始化模式',
    'ink-yoga-reactive-ui': '用 Ink 和 Yoga 构建响应式界面',
    'execution-flow-in-detail': '执行流程',
    'the-permission-system': '权限系统',
    'parallel-tool-execution': '并行执行',
    'feature-flag-integration': '功能管理',
    'real-world-examples': '实际应用中的模式',
    'lessons-learned-and-implementation-challenges': '经验教训',
}
PARTS = {'I: Foundations': '第一部分：基础', 'II: Implementation': '第二部分：实现',
         'III: Practical Application': '第三部分：实际应用'}
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'


def toc():
    raw = (BOOK / 'source/SUMMARY.md').read_text(encoding='utf-8')
    volume = raw.split('# Book 1:', 1)[1].split('# Book 2:', 1)[0]
    groups = [(None, [])]
    for line in volume.splitlines():
        if line.startswith('## Part '):
            groups.append((PARTS[line.removeprefix('## Part ')], []))
        match = re.fullmatch(r'- \[.*?\]\(([a-z0-9-]+)\.md\)', line)
        if match:
            groups[-1][1].append(match[1])
    slugs = [slug for _, group in groups for slug in group]
    if len(slugs) != len(set(slugs)) or set(slugs) != TITLES.keys():
        raise ValueError('第一卷目录与章节映射不一致')
    return groups, slugs


def contents(groups, current):
    fragment = page('<div></div>')
    position = 1
    for label, group in groups:
        if label is not None:
            heading = fragment.new_tag('p', attrs={'class': 'volume-part'})
            heading.string = label
            fragment.div.append(heading)
        listing = fragment.new_tag('ol', start=str(position))
        for slug in group:
            row = fragment.new_tag('li')
            link = fragment.new_tag('a', href=slug + '.html')
            if slug == current:
                link['aria-current'] = 'page'
            link.string = TITLES[slug]
            row.append(link)
            listing.append(row)
        fragment.div.append(listing)
        position += len(group)
    return fragment.div.decode_contents()


def protected(main):
    # Keep block order, but allow inline code to move within translated prose.
    blocks = [str(item) for item in main.select('pre, img, svg, math')]
    inline = Counter(str(item) for item in main.select('code') if not item.find_parent('pre'))
    return blocks, inline


def verify_source_links(main, chapters):
    for node in main.select('[href], [src]'):
        for attr in ('href', 'src'):
            if not node.has_attr(attr):
                continue
            ref = node[attr]
            parts = urlsplit(ref)
            if parts.scheme in {'http', 'https', 'mailto'} or ref.startswith('#'):
                continue
            if not parts.scheme and not parts.netloc and parts.path.removeprefix('./') in chapters:
                continue
            raise ValueError(f'未处理的原书资源或链接：{ref}')


def build_agentic_system(output):
    groups, slugs = toc()
    source = BOOK / 'source'
    target = output / 'books/building-an-agentic-system'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / 'assets', target / 'assets', dirs_exist_ok=True)
    chapter_files = {slug + '.html' for slug in slugs}
    for index, slug in enumerate(slugs):
        name = slug + '.html'
        original = (source / name).read_bytes()
        translation = json.loads((BOOK / 'zh' / (slug + '.json')).read_text(encoding='utf-8'))
        if translation.keys() != extract(original, 'main').keys() or not all(
                isinstance(text, str) and text.strip() for text in translation.values()):
            raise ValueError(f'章节译文缺失或段号不匹配：{name}')
        source_main = page(original).main
        main = apply(original, translation, 'main').main
        if protected(source_main) != protected(main) or [x['id'] for x in source_main.select('[id]')] != [
                x['id'] for x in main.select('[id]')]:
            raise ValueError(f'译文修改了原书代码、图像、公式或锚点：{name}')
        verify_source_links(main, chapter_files)
        prev = slugs[index - 1] if index else None
        following = slugs[index + 1] if index + 1 < len(slugs) else None
        previous_link = f'<a rel="prev" href="{prev}.html">← {TITLES[prev]}</a>' if prev else ''
        following_link = f'<a rel="next" href="{following}.html">{TITLES[following]} →</a>' if following else ''
        diagram_scripts = '''<script defer src="assets/mermaid.min.js"></script>
<script defer src="diagrams.js"></script>''' if main.select_one('pre.mermaid') else ''
        html = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLES[slug]} · 构建智能体系统</title>
<link rel="stylesheet" href="../../styles.css">
{diagram_scripts}
</head>
<body class="volume">
<div class="page">
<header class="masthead">
  <div><p>构建智能体系统 · 第一卷</p><a class="original" href="../../zh.html">返回中文书库</a></div>
  <a class="original" href="{urljoin(UPSTREAM, name)}" hreflang="en">本章英文原文 ↗</a>
</header>
<div class="volume-grid">
<nav class="volume-toc" aria-label="第一卷目录">
  <h2>第一卷目录</h2>
  {contents(groups, slug)}
</nav>
<main id="chapter" class="reading-page">
{main.decode_contents()}
<nav class="volume-pagination" aria-label="相邻章节">{previous_link}{following_link}</nav>
<footer class="volume-credit">原著：Gerred Dillon · <a href="{UPSTREAM}" hreflang="en">Building an Agentic System</a> · <a rel="license" href="{LICENSE}">CC BY 4.0</a>。本站将第一卷正文译为简体中文并重新排版；原始代码与图表保留，不代表作者背书。</footer>
</main>
</div>
</div>
</body>
</html>
'''
        (target / name).write_text(html, encoding='utf-8')
    shutil.copyfile(BOOK / 'diagrams.js', target / 'diagrams.js')
    print(f'《构建智能体系统》第一卷：{len(slugs)} 章译文、目录、原图与代码已校验。')
