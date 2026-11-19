"""Capture the MAGE web edition and the local resources it actually uses."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urljoin, urlsplit
import subprocess
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup

BASE = 'https://davisjam.github.io/model-based-agentic-software-engineering/book/mage-book/'
LICENSE = 'https://raw.githubusercontent.com/davisjam/model-based-agentic-software-engineering/864cabcb296d285a9389c94630b54126d8a51bd7/LICENSE'
CSS_URL = re.compile(r'url\(\s*[\"\']?([^\)\"\'\s]+)[\"\']?\s*\)')


def download(url):
    with TemporaryDirectory() as directory:
        path = Path(directory) / 'response'
        # curl can truncate a file on retry; stdout would concatenate partial responses.
        content_type = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--location',
                                                '--compressed', '--retry', '2', '--retry-max-time', '150',
                                                '--connect-timeout', '15', '--max-time', '90', '--output',
                                                str(path), '--write-out', '%{content_type}', url])
        return path.read_bytes(), content_type.decode('ascii')


def check_html(path, body):
    html = body.lower()
    if any(html.count(marker) != 1 for marker in (b'<!doctype html>', b'<article ', b'</article>')):
        raise ValueError(f'Expected one complete HTML page for {path}')


def references(path, body):
    if path.endswith('.css'):
        return CSS_URL.findall(body.decode('utf-8'))
    if not path.endswith('.html'):
        return []
    soup = BeautifulSoup(body, 'html.parser')
    links = []
    for node in soup.find_all(True):
        for key in ('href', 'src', 'data-src', 'poster'):
            if node.get(key):
                links.append(node[key])
        if node.get('style'):
            links.extend(CSS_URL.findall(node['style']))
        if node.get('srcset'):
            links.extend(part.split()[0] for part in node['srcset'].split(',') if part.split())
    config = soup.find(id='__config')
    if config:
        search = json.loads(config.get_text()).get('search')
        if search:
            links.extend([search, 'search/search_index.json'])
    return links


def capture(destination):
    origin = urlsplit(BASE)
    pending = {'index.html'}
    records = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        def retrieve(path):
            if (destination / path).is_file():
                return (destination / path).read_bytes(), 'text/html' if path.endswith('.html') else ''
            try:
                body, content_type = download(urljoin(BASE, path))
            except subprocess.CalledProcessError as error:
                raise RuntimeError(f'Download failed for {path}') from error
            if path.endswith('.html') and 'text/html' not in content_type:
                raise ValueError(f'Unexpected content for {path}: {content_type}')
            file = destination / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(body)
            return body, content_type

        while pending:
            batch = sorted(pending)
            pending.clear()
            for path, (body, _) in zip(batch, pool.map(retrieve, batch)):
                if path.endswith('.html'):
                    check_html(path, body)
                records[path] = hashlib.sha256(body).hexdigest()
                for ref in references(path, body):
                    if ref.startswith(('#', 'data:', 'mailto:')):
                        continue
                    link = urlsplit(urljoin(urljoin(BASE, path), ref))
                    if (link.scheme, link.netloc) != (origin.scheme, origin.netloc) or not link.path.startswith(origin.path):
                        continue
                    target = unquote(link.path.removeprefix(origin.path)) or 'index.html'
                    if any(p in ('..', '.') for p in PurePosixPath(target).parts) or target.startswith('/'):
                        raise ValueError(f'Unsafe snapshot path: {target}')
                    if target.endswith(('.pdf', '.epub')) or target in records or target in batch:
                        continue
                    pending.add(target)
    license_text, _ = download(LICENSE)
    (destination / 'LICENSE').write_bytes(license_text)
    manifest = {'reading_edition': BASE + 'index.html', 'license_url': LICENSE,
                'license_sha256': hashlib.sha256(license_text).hexdigest(),
                'files': dict(sorted(records.items()))}
    (destination / 'snapshot.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Captured {sum(f.endswith(".html") for f in records)} HTML pages and '
          f'{sum(not f.endswith(".html") for f in records)} assets.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if (args.destination / 'snapshot.json').exists():
        parser.error('Choose a new destination; this command does not overwrite completed snapshots.')
    capture(args.destination)
