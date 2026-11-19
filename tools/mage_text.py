"""Extract or apply prose translations without replacing the book's markup."""
import argparse
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup, Comment, NavigableString

BLOCKS = {'p', 'li', 'dt', 'dd', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th', 'td',
          'figcaption', 'caption', 'div', 'blockquote', 'summary', 'a', 'span', 'aside'}
PROTECTED = {'code', 'pre', 'script', 'style', 'svg', 'math', 'kbd', 'samp'}
MARKER = re.compile(r'⟦(/?\d+)⟧')
LATIN = re.compile(r'[a-zA-Z]')
SPACE = re.compile(r'\s+')


def page(raw):
    return BeautifulSoup(raw, 'html.parser')


def units(article):
    """Yield direct prose blocks; inline nodes are numbered, nested blocks are independent."""
    def visit(container):
        group = []
        for child in list(container.children):
            if child.name not in PROTECTED and getattr(child, 'name', None) and (
                    child.name in BLOCKS or child.find(BLOCKS - {'a', 'span'})) and (
                    child.name not in {'a', 'span'} or child.find(BLOCKS - {'a', 'span'})):
                yield group
                group = []
                yield from visit(child)
            else:
                group.append(child)
        yield group

    for group in visit(article):
        slots = {}
        expected = []
        def encode(nodes):
            chunks = []
            for node in nodes:
                if isinstance(node, Comment):
                    continue
                if isinstance(node, NavigableString):
                    chunks.append(str(node))
                    continue
                is_opaque = node.name in PROTECTED or not node.contents
                key = str(len(slots) + 1)
                slots[key] = (node, is_opaque)
                expected.append(key)
                chunks.append(f'⟦{key}⟧')
                if not is_opaque:
                    chunks.append(encode(node.children))
                    expected.append('/' + key)
                    chunks.append(f'⟦/{key}⟧')
            return ''.join(chunks)
        source = SPACE.sub(' ', encode(group)).strip()
        if LATIN.search(source):
            yield source, group, slots, expected


def extract(raw, selector='article'):
    soup = page(raw)
    return {str(i): source for i, (source, *_) in enumerate(units(soup.select_one(selector)), 1)}


def apply(raw, entries, selector='article'):
    soup = page(raw)
    groups = list(units(soup.select_one(selector)))
    for key, text in entries.items():
        if not key.isdecimal() or not 1 <= int(key) <= len(groups):
            raise ValueError(f'Unknown unit: {key}')
        source, original, slots, expected = groups[int(key) - 1]
        if sorted(MARKER.findall(text)) != sorted(expected):
            raise ValueError(f'Unmatched formatting markers in unit {key}: {text}')
        anchor = Comment('translation')
        original[0].insert_before(anchor)
        def add(node):
            if stack:
                stack[-1][1].append(node)
            else:
                anchor.insert_before(node)
        stack = []
        cursor = 0
        for match in MARKER.finditer(text):
            if match.start() > cursor:
                add(NavigableString(text[cursor:match.start()]))
            mark = match[1]
            if mark.startswith('/'):
                if not stack or stack[-1][0] != mark[1:]:
                    raise ValueError(f'Formatting markers out of order in unit {key}')
                stack.pop()
            else:
                tag, opaque = slots[mark]
                if not opaque:
                    tag.clear()
                add(tag)
                if not opaque:
                    stack.append((mark, tag))
            cursor = match.end()
        if cursor < len(text):
            add(NavigableString(text[cursor:]))
        for node in original:
            if node.parent is anchor.parent and not any(node is tag for tag, _ in slots.values()):
                node.extract()
        anchor.extract()
    return soup


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('html', type=Path)
    args = cli.parse_args()
    print(json.dumps(extract(args.html.read_bytes()), ensure_ascii=False, indent=2))
