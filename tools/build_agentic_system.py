"""Build the Chinese reading editions of the Agentic Systems series."""
from collections import Counter
import json
from pathlib import Path
from posixpath import dirname, join, normpath, relpath
import re
import shutil
from urllib.parse import urljoin, urlsplit

from mage_text import apply, extract, page

BOOK = Path(__file__).resolve().parents[1] / 'books/building-an-agentic-system'
UPSTREAM = 'https://gerred.github.io/building-an-agentic-system/'
UPSTREAM_MARKDOWN = ('https://github.com/gerred/building-an-agentic-system/blob/'
                     'eec7f0226fb0d0019c67dc6f209a80b61720117e/src/')
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
PARTS = {'Part I: Foundations': '第一部分：基础', 'Part II: Implementation': '第二部分：实现',
         'Part III: Practical Application': '第三部分：实际应用'}
VOLUME_TWO_TITLES = {
    'second-edition/index': '导论',
    'second-edition/part-i-foundations/chapter-1-from-local-to-collaborative': '第 1 章：从本地到协作',
    'second-edition/part-i-foundations/chapter-2-amp-architecture-overview': '第 2 章：AI 系统的面向服务架构',
    'second-edition/part-i-foundations/chapter-3-authentication-and-identity': '第 3 章：开发者工具的身份验证与身份管理',
    'second-edition/part-ii-core-systems/chapter-4-thread-management-at-scale': '第 4 章：大规模会话线程管理',
    'second-edition/part-ii-core-systems/chapter-5-real-time-synchronization': '第 5 章：实时同步',
    'second-edition/part-ii-core-systems/chapter-6-tool-system-evolution': '第 6 章：工具系统架构的演进',
    'second-edition/part-iii-collaboration/chapter-7-sharing-and-permissions': '第 7 章：共享与权限模式',
    'second-edition/part-iii-collaboration/chapter-8-team-workflows': '第 8 章：团队工作流模式',
    'second-edition/part-iii-collaboration/chapter-9-enterprise-integration': '第 9 章：企业集成模式',
    'second-edition/part-iv-advanced-patterns/chapter-10-multi-agent-orchestration': '第 10 章：多智能体编排模式',
    'second-edition/part-iv-advanced-patterns/chapter-11-performance-at-scale': '第 11 章：大规模系统的性能模式',
    'second-edition/part-iv-advanced-patterns/chapter-12-observability-and-monitoring': '第 12 章：可观测性与监控模式',
    'second-edition/part-v-implementation/chapter-13-building-your-own-amp': '第 13 章：构建自己的协作式 AI 助手',
    'second-edition/part-v-implementation/chapter-14-migration-strategies': '第 14 章：迁移策略模式',
    'second-edition/part-v-implementation/chapter-15-case-studies': '第 15 章：实施案例',
    'second-edition/part-vi-future/chapter-16-emerging-patterns': '第 16 章：新兴架构模式',
    'second-edition/part-vi-future/chapter-17-collaborative-ai-ecosystem': '第 17 章：协作式 AI 生态系统模式',
    'second-edition/appendices/appendix-a-api-reference': '附录 A：架构模式参考',
    'second-edition/appendices/appendix-b-deployment-guide': '附录 B：部署模式指南',
    'second-edition/appendices/appendix-c-performance-tuning': '附录 C：性能优化策略',
}
VOLUME_TWO_PARTS = {
    'Part I: Foundations': '第一部分：基础',
    'Part II: Core Systems': '第二部分：核心系统',
    'Part III: Collaboration Features': '第三部分：协作功能',
    'Part IV: Advanced Patterns': '第四部分：进阶模式',
    'Part V: Practical Implementation': '第五部分：实践与实现',
    'Part VI: Future Directions': '第六部分：未来方向',
    'Appendices': '附录',
}
MARKDOWN_SECTIONS = ('second-edition/part-v-implementation/',
                     'second-edition/part-vi-future/', 'second-edition/appendices/')
LICENSE = 'https://creativecommons.org/licenses/by/4.0/'


def toc(summary, titles, parts, prefix=''):
    groups = [(None, [])]
    for line in summary.splitlines():
        if line.startswith('## '):
            groups.append((parts[line.removeprefix('## ')], []))
        match = re.fullmatch(r'- \[.*?\]\(([\w/-]+)\.md\)', line)
        if match:
            slug = 'index' if match[1] == 'README' else match[1]
            groups[-1][1].append(prefix + slug)
    slugs = [slug for _, group in groups for slug in group]
    if len(slugs) != len(set(slugs)) or set(slugs) != titles.keys():
        raise ValueError(f'目录与章节映射不一致：{prefix or "第一卷"}')
    return groups


def contents(groups, current, titles, ordered):
    fragment = page('<div></div>')
    position = 1
    for label, group in groups:
        if label is not None:
            heading = fragment.new_tag('p', attrs={'class': 'volume-part'})
            heading.string = label
            fragment.div.append(heading)
        listing = fragment.new_tag('ol', start=str(position)) if ordered else fragment.new_tag('ul')
        for slug in group:
            row = fragment.new_tag('li')
            link = fragment.new_tag('a', href=relpath(slug + '.html', dirname(current) or '.'))
            if slug == current:
                link['aria-current'] = 'page'
            link.string = titles[slug]
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


def verify_source_links(main, chapter, chapters):
    for node in main.select('[href], [src]'):
        for attr in ('href', 'src'):
            if not node.has_attr(attr):
                continue
            ref = node[attr]
            parts = urlsplit(ref)
            if parts.scheme in {'http', 'https', 'mailto'} or ref.startswith('#'):
                continue
            local_path = normpath(join(dirname(chapter), parts.path))
            if not parts.scheme and not parts.netloc and local_path in chapters:
                continue
            raise ValueError(f'未处理的原书资源或链接：{ref}')


def build_agentic_system(output):
    target = output / 'books/building-an-agentic-system'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BOOK / 'source/assets', target / 'assets', dirs_exist_ok=True)
    shutil.copyfile(BOOK / 'diagrams.js', target / 'diagrams.js')
    summary = (BOOK / 'source/SUMMARY.md').read_text(encoding='utf-8')
    volume_one = summary.split('# Book 1:', 1)[1].split('# Book 2:', 1)[0]
    build_volume(target, toc(volume_one, TITLES, PARTS), TITLES, volume='第一卷', title='构建智能体系统',
                 status='本站将第一卷正文译为简体中文并重新排版；')
    volume_two = (BOOK / 'source/second-edition/SUMMARY.md').read_text(encoding='utf-8')
    groups = toc(volume_two, VOLUME_TWO_TITLES, VOLUME_TWO_PARTS, 'second-edition/')
    build_volume(target, groups, VOLUME_TWO_TITLES, volume='第二卷', title='扩展智能体系统',
                 status='本站将第二卷的导论、17 章正文和 3 篇附录译为简体中文并重新排版。',
                 ordered_toc=False)


def build_volume(target, groups, titles, *, volume, title, status, ordered_toc=True):
    slugs = [slug for _, group in groups for slug in group]
    chapter_files = {slug + '.html' for slug in slugs}
    for index, slug in enumerate(slugs):
        name = slug + '.html'
        original = (BOOK / 'source' / name).read_bytes()
        translation = json.loads((BOOK / 'zh' / (slug + '.json')).read_text(encoding='utf-8'))
        if translation.keys() != extract(original, 'main').keys() or not all(
                isinstance(text, str) and text.strip() for text in translation.values()):
            raise ValueError(f'章节译文缺失或段号不匹配：{name}')
        source_main = page(original).main
        main = apply(original, translation, 'main').main
        if protected(source_main) != protected(main) or [x['id'] for x in source_main.select('[id]')] != [
                x['id'] for x in main.select('[id]')]:
            raise ValueError(f'译文修改了原书代码、图像、公式或锚点：{name}')
        verify_source_links(main, name, chapter_files)
        start = dirname(name) or '.'
        site_path = join('books/building-an-agentic-system', start)
        library = relpath('zh.html', site_path)
        styles = relpath('styles.css', site_path)
        reader = relpath('reader.js', site_path)
        prev = slugs[index - 1] if index else None
        following = slugs[index + 1] if index + 1 < len(slugs) else None
        previous_link = f'<a rel="prev" href="{relpath(prev + ".html", start)}">← {titles[prev]}</a>' if prev else ''
        following_link = ''
        if following:
            following_link = f'<a rel="next" href="{relpath(following + ".html", start)}">{titles[following]} →</a>'
        original_url = (urljoin(UPSTREAM_MARKDOWN, slug + '.md') if slug.startswith(MARKDOWN_SECTIONS)
                        else urljoin(UPSTREAM, name))
        diagram_scripts = ''
        if main.select_one('pre.mermaid'):
            mermaid = relpath('assets/mermaid.min.js', start)
            diagrams = relpath('diagrams.js', start)
            diagram_scripts = f'<script defer src="{mermaid}"></script>\n<script defer src="{diagrams}"></script>'
        html = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titles[slug]} · {title}</title>
<link rel="stylesheet" href="{styles}?v=paper">
<script defer src="{reader}"></script>
{diagram_scripts}
</head>
<body class="volume">
<div class="page">
<header class="masthead">
  <div><p>{title} · {volume}</p><a class="original" href="{library}">返回中文书库</a></div>
  <a class="original" href="{original_url}" hreflang="en">本章英文原文 ↗</a>
</header>
<div class="volume-grid">
<nav class="volume-toc" aria-label="{volume}目录">
  <details open>
    <summary>{volume}目录</summary>
    {contents(groups, slug, titles, ordered_toc)}
  </details>
</nav>
<main id="chapter" class="reading-page">
{main.decode_contents()}
<nav class="volume-pagination" aria-label="相邻章节">{previous_link}{following_link}</nav>
<footer class="volume-credit">原著：Gerred Dillon · <a href="{UPSTREAM}" hreflang="en">Building an Agentic System</a> · <a rel="license" href="{LICENSE}">CC BY 4.0</a>。{status}原始代码与图表保留，不代表作者背书。</footer>
</main>
</div>
</div>
</body>
</html>
'''
        chapter = target / name
        chapter.parent.mkdir(parents=True, exist_ok=True)
        chapter.write_text(html, encoding='utf-8')
    print(f'《{title}》{volume}：{len(slugs)} 页译文、目录、原图与代码已校验。')
