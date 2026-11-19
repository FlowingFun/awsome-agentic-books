"""Build the static book collection from its pinned reading editions."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import NavigableString

from mage_text import apply, extract, page
from snapshot_mage import BASE, check_html, references

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'books/mage'
HAN = re.compile(r'[\u3400-\u9fff]')
SECTION_LABEL = re.compile(r'^(§\d+\.\d+ · )(.+)$')
SEARCH_TRANSLATIONS = {
    'clipboard.copied': '已复制到剪贴板', 'clipboard.copy': '复制到剪贴板',
    'search.result.more.one': '本页另有 1 条结果', 'search.result.more.other': '本页另有 # 条结果',
    'search.result.none': '未找到匹配结果', 'search.result.one': '找到 1 条结果',
    'search.result.other': '找到 # 条结果', 'search.result.placeholder': '输入关键词搜索原文',
    'search.result.term.missing': '未匹配', 'select.version': '选择版本',
}


def checksum(path, expected):
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError(f'Snapshot checksum mismatch: {path}')
    return body


def load_book():
    source = BOOK / 'source'
    manifest = json.loads((source / 'snapshot.json').read_text(encoding='utf-8'))
    files = manifest['files']
    raw = {name: checksum(source / name, digest) for name, digest in files.items()}
    checksum(source / 'LICENSE', manifest['license_sha256'])
    translated, articles, counts = {}, {}, {}
    for name, body in raw.items():
        if not name.endswith('.html'):
            continue
        check_html(name, body)
        translation = BOOK / 'zh' / Path(name).with_suffix('.json').name
        if not translation.exists():
            articles[name] = page(body)
            continue
        entries = json.loads(translation.read_text(encoding='utf-8'))
        source_units = extract(body)
        if not isinstance(entries, dict) or any(not isinstance(v, str) or not v.strip() for v in entries.values()):
            raise ValueError(f'Expected an object with nonempty translations in {translation}')
        counts[name] = (len(entries), len(source_units))
        try:
            articles[name] = apply(body, entries)
        except ValueError as error:
            raise ValueError(f'{translation}: {error}') from error
        if entries.keys() == source_units.keys():
            translated[name] = articles[name]
    for translation in (BOOK / 'zh').glob('*.json'):
        if translation.with_suffix('.html').name not in articles:
            raise ValueError(f'Translation has no source page: {translation}')
    return raw, articles, translated, counts


def replace_labels(node, labels):
    if node is None:
        return
    for text in list(node.find_all(string=True)):
        old = str(text).strip()
        if text.find_parent(['svg', 'script', 'style']):
            continue
        section = SECTION_LABEL.fullmatch(old)
        translated = labels.get(old)
        if translated is None and section and section[2] in labels:
            translated = section[1] + labels[section[2]]
        if translated is not None:
            text.replace_with(str(text).replace(old, translated, 1))
    for tag in [node, *node.find_all(True)]:
        if tag.find_parent('svg') or tag.name == 'svg':
            continue
        for attr in ('aria-label', 'title', 'placeholder'):
            value = tag.get(attr)
            if value in labels:
                tag[attr] = labels[value]
            elif value and ' — ' in value:
                prefix, rest = value.split(' — ', 1)
                if prefix in labels or rest in labels:
                    tag[attr] = f'{labels.get(prefix, prefix)} — {labels.get(rest, rest)}'


def archive_link(name, ref):
    if not ref or ref.startswith(('#', 'data:')):
        return ref
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc:
        return ref
    upstream = urljoin(urljoin(BASE, name), ref)
    if parts.path.endswith(('.pdf', '.epub')) or not upstream.startswith(BASE):
        return upstream
    return ref


def decorate(name, soup, complete, counts, labels):
    soup.html['lang'] = 'zh-CN' if complete else 'en'
    if not complete:
        soup.article['lang'] = 'en'
    for element in soup.select('.md-header, .md-sidebar, .md-top, .md-skip, .md-footer, .md-search'):
        replace_labels(element, labels)
    for node in soup.select('article .chapnav, article header.chap'):
        replace_labels(node, labels)
    if soup.title:
        title = soup.title.get_text().strip()
        soup.title.string = ' - '.join(labels.get(t, t) for t in title.split(' - '))
    for node in soup.find_all(True):
        for attr in ('href', 'src'):
            if node.get(attr):
                node[attr] = archive_link(name, node[attr])
    for node in soup.select('article img[alt]'):
        if node['alt'] in labels:
            node['alt'] = labels[node['alt']]
    search_input = soup.select_one('.md-search__input')
    if search_input:
        search_input['placeholder'] = search_input['aria-label'] = '搜索英文原文'
    config = soup.find(id='__config')
    if config:
        data = json.loads(config.get_text())
        data['translations'].update(SEARCH_TRANSLATIONS)
        config.string = json.dumps(data, ensure_ascii=False)

    note = soup.new_tag('p', attrs={'class': 'collection-note', 'lang': 'zh-CN'})
    library = soup.new_tag('a', href='../../index.html')
    library.string = '返回书库'
    note.append(library)
    if complete:
        status = '非官方简体中文译本'
    elif name in counts:
        read, total = counts[name]
        status = f'本页翻译中（{read}/{total} 段），未译部分为英文原文'
    else:
        status = '本页尚未翻译，以下为英文原文'
    note.append(NavigableString(' · ' + status + ' · '))
    original = soup.new_tag('a', href=urljoin(BASE, name))
    original.string = '英文原版'
    note.append(original)
    note.append(NavigableString(' · '))
    license_link = soup.new_tag('a', href='LICENSE.txt')
    license_link.string = 'MIT 许可'
    note.append(license_link)
    soup.article.insert(0, note)
    return soup


def fingerprint(soup):
    article = soup.article
    return (
        Counter(str(n) for n in article.select('svg, pre')),
        Counter((n.name, n.get('id')) for n in article.select('[id]')),
        Counter(n.get('src') for n in article.select('img')),
        Counter(n['href'] for n in article.select('[href]')),
        Counter(n.name for n in article.find_all(['figure', 'table', 'tr', 'td', 'th', 'caption', 'figcaption'])),
    )


def verify_links(output):
    errors = []
    anchors = {}
    preexisting = {}
    book_path = output / 'books/mage'
    files = sorted(output.rglob('*.html'))
    for file in files:
        soup = page(file.read_bytes())
        anchors[file] = {node['id'] for node in soup.select('[id]')} | {node['name'] for node in soup.select('a[name]')}
        if file.parent == book_path:
            old = BOOK / 'source' / file.name
            preexisting[file] = set(references(file.name, old.read_bytes()))
    known = set()
    for file in files:
        for ref in references(file.name, file.read_bytes()):
            parts = urlsplit(ref)
            if parts.scheme or parts.netloc:
                continue
            if parts.path.startswith('/'):
                errors.append(f'{file.name}: root-absolute {ref}')
                continue
            target = (file.parent / unquote(parts.path)).resolve() if parts.path else file
            if target.is_dir():
                target /= 'index.html'
            if not target.is_relative_to(output) or not target.is_file():
                errors.append(f'{file.name}: missing local resource {ref}')
            elif parts.fragment and target in anchors and unquote(parts.fragment) not in anchors[target]:
                issue = f'{file.name}: unresolved anchor {ref}'
                # Anchor IDs are compared against the snapshot as well, so an upstream
                # broken fragment is not evidence of a regression in the translation.
                if ref in preexisting.get(file, set()):
                    known.add(issue)
                else:
                    errors.append(issue)
    if errors:
        raise ValueError('\n'.join(errors))
    return len(known)


def build(output):
    raw, articles, translated, counts = load_book()
    labels = json.loads((BOOK / 'navigation.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'site', output, dirs_exist_ok=True)
    homepage = page((output / 'index.html').read_bytes())
    progress = f'已完成 {len(translated)} / {len(articles)} 页' if len(translated) < len(articles) else f'全书 {len(articles)} 页已翻译'
    homepage.find(id='mage-progress').string = progress
    (output / 'index.html').write_text(str(homepage), encoding='utf-8')
    (output / '.nojekyll').touch()
    book = output / 'books/mage'
    for name, body in raw.items():
        target = book / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name not in articles:
            target.write_bytes(body)
            continue
        soup = articles[name]
        before = fingerprint(page(body))
        after = fingerprint(soup)
        if before != after:
            changed = [tag for tag, x, y in zip(('svg/pre', 'id', 'img', 'href', 'table/figure'), before, after) if x != y]
            raise ValueError(f'{name}: translation changed protected elements: {changed}')
        if name in translated and not HAN.search(soup.article.get_text()):
            raise ValueError(f'{name}: completed page does not contain Chinese')
        target.write_text(str(decorate(name, soup, name in translated, counts, labels)), encoding='utf-8')
    shutil.copyfile(BOOK / 'source/LICENSE', book / 'LICENSE.txt')
    notices = BOOK / 'notices'
    if notices.exists():
        shutil.copytree(notices, book / 'notices', dirs_exist_ok=True)
    upstream_issues = verify_links(output)
    print(f'{progress}；{len(raw) - len(articles)} 个原始静态资源；'
          f'{upstream_issues} 个原书已有的无效锚点，未新增。')


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output', type=Path, default=ROOT / '_site')
    args = cli.parse_args()
    dest = args.output.resolve()
    if dest == ROOT or dest in ROOT.parents or dest.is_relative_to(BOOK) or dest.is_relative_to(ROOT / 'site'):
        cli.error('输出目录不能覆盖网站或译本源码')
    build(dest)
