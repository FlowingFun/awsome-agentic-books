"""Publish the Chinese reading edition of the MIT-licensed Cookbook notebook."""
from collections import Counter
from html import escape
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from markdown import markdown

from mage_text import page

BOOK = Path(__file__).resolve().parents[1] / 'books/macro-evals'
ORIGINAL = ('https://developers.openai.com/cookbook/examples/partners/'
            'macro_evals_for_agentic_systems/macro_evals_for_agentic_systems')
PIN = 'dfd760b4de0bd175b51ad05b9b5260c36dfea09c'
NOTEBOOK = (f'https://github.com/openai/openai-cookbook/blob/{PIN}/examples/partners/'
            'macro_evals_for_agentic_systems/macro_evals_for_agentic_systems.ipynb')
FIGURE = '../../../images/agentic-system-architecture.svg'
ALLOWED = {'a', 'img', 'blockquote', 'code', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
           'hr', 'br', 'li', 'ol', 'p', 'pre', 'strong', 'ul', 'table', 'tbody', 'td',
           'th', 'thead', 'tr'}


def render(text):
    return page(markdown(text, extensions=['fenced_code', 'tables']))


def unchanged(soup):
    return ([tag.name for tag in soup.select('h1,h2,h3,h4,h5,h6')],
            Counter(tag.get_text() for tag in soup.select('code')),
            Counter(tag['href'] for tag in soup.select('a[href]')),
            Counter(tag['src'] for tag in soup.select('img[src]')))


def build_macro_evals(output):
    source = BOOK / 'source'
    cells = json.loads((source / 'macro-evals.ipynb').read_text(encoding='utf-8'))['cells']
    translations = {}
    for path in sorted((BOOK / 'zh').glob('part-*.json')):
        part = json.loads(path.read_text(encoding='utf-8'))
        if translations.keys() & part.keys():
            raise ValueError('评估教程存在重复翻译单元')
        translations.update(part)
    if translations.keys() != {str(i) for i, cell in enumerate(cells) if cell['cell_type'] == 'markdown'}:
        raise ValueError('评估教程翻译未覆盖所有 Markdown 单元')

    sections, toc = [], []
    for i, cell in enumerate(cells):
        original = ''.join(cell['source'])
        if cell['cell_type'] == 'code':
            if cell.get('outputs'):
                raise ValueError('原 Notebook 新增了输出，需要核对阅读版')
            sections.append(f'<pre data-cell="{i}"><code>{escape(original)}</code></pre>')
            continue
        translated = translations[str(i)]
        if not isinstance(translated, str) or not translated.strip():
            raise ValueError(f'评估教程单元 {i} 译文为空')
        soup = render(translated)
        if unchanged(render(original)) != unchanged(soup):
            raise ValueError(f'评估教程单元 {i} 修改了原文的标题层级、代码、图像或链接')
        for tag in soup.find_all(True):
            if tag.name not in ALLOWED or any(key.startswith('on') for key in tag.attrs):
                raise ValueError(f'评估教程单元 {i} 含不受支持的标签或属性')
            if tag.name == 'a' and urlsplit(tag['href']).scheme != 'https':
                raise ValueError(f'评估教程单元 {i} 含非 HTTPS 链接')
            if tag.name == 'img':
                if tag['src'] != FIGURE:
                    raise ValueError(f'评估教程单元 {i} 含未知图像')
                tag['src'] = 'assets/agentic-system-architecture.svg'
                tag['style'] = 'max-width:100%;height:auto;background:#fff'
        for j, heading in enumerate(soup.select('h1,h2,h3')):
            heading['id'] = f'cell-{i}-{j}'
            if heading.name == 'h2':
                toc.append(f'<li><a href="#{heading["id"]}">{escape(heading.get_text())}</a></li>')
        sections.append(soup.decode_contents())

    target = output / 'reading/macro-evals'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / 'assets', target / 'assets', dirs_exist_ok=True)
    shutil.copyfile(source / 'LICENSE', target / 'LICENSE.txt')
    (target / 'index.html').write_text(f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>智能体系统的整体评估 · OpenAI Cookbook 中文译文</title>
<link rel="stylesheet" href="../../styles.css">
</head>
<body class="volume">
<div class="page">
<header class="masthead">
  <a class="original" href="../../zh.html">返回中文书库</a>
  <a class="original" href="{ORIGINAL}" hreflang="en">英文原文 ↗</a>
</header>
<div class="volume-grid">
<nav class="volume-toc" aria-label="教程目录"><h2>教程目录</h2><ol>{''.join(toc)}</ol></nav>
<main class="reading-page">
<p class="entry-author">OpenAI 与 Slalom 合作编写。此阅读版翻译了原 Notebook 的说明文字，保留原图与示例代码，不在网页上执行代码。需要运行示例时请到 <a href="{NOTEBOOK}" hreflang="en">英文 Notebook</a> 获取代码与配套材料。</p>
{''.join(sections)}
<footer class="volume-credit">来源：<a href="{ORIGINAL}" hreflang="en">OpenAI Cookbook 英文原文</a> · <a rel="license" href="LICENSE.txt">原版 MIT 许可证及版权声明</a>。</footer>
</main>
</div>
</div>
</body>
</html>
''', encoding='utf-8')
    print(f'OpenAI Cookbook：{len(translations)} 个正文单元已翻译，{len(cells) - len(translations)} 个代码单元原样保留。')
