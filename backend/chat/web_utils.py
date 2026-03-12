import re
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings


URL_PATTERN = re.compile(r'https?://[^\s]+')
SEARCH_URL = 'https://html.duckduckgo.com/html/'
WIKIPEDIA_SEARCH_URL = 'https://en.wikipedia.org/w/api.php'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) ChatBotX/1.0'


def extract_urls(text):
    return list(dict.fromkeys(URL_PATTERN.findall(text or '')))


def sanitize_history(history):
    sanitized = []
    for item in history or []:
        role = item.get('role')
        content = (item.get('content') or '').strip()
        if role in {'user', 'assistant'} and content:
            sanitized.append({'role': role, 'content': content})
    return sanitized


def summarize_history(history, recent_messages, max_chars):
    if recent_messages < 0:
        recent_messages = 0

    recent_history = history[-recent_messages:] if recent_messages else []
    older_history = history[:-recent_messages] if recent_messages else history

    if not older_history:
        return '', recent_history

    lines = []
    total_chars = 0
    for item in older_history:
        role = 'User' if item['role'] == 'user' else 'Assistant'
        content = ' '.join(item['content'].split())
        snippet = content[:180]
        if len(content) > 180:
            snippet += '...'
        line = f'- {role}: {snippet}'
        next_total = total_chars + len(line) + 1
        if next_total > max_chars:
            break
        lines.append(line)
        total_chars = next_total

    if not lines:
        return '', recent_history

    summary = 'Summary of earlier conversation:\n' + '\n'.join(lines)
    return summary, recent_history


def build_system_prompt(web_context=''):
    base_prompt = settings.DEFAULT_SYSTEM_PROMPT
    if not web_context:
        return base_prompt

    return (
        f'{base_prompt}\n\n'
        'Additional web context is provided below. Use it only as supporting '
        'evidence, cite the relevant source URL in plain text when useful, and '
        'say when the sources are incomplete.\n\n'
        f'{web_context}'
    )


def _normalize_search_result_url(url):
    parsed = urlparse(url)
    if 'duckduckgo.com' in parsed.netloc and parsed.path.startswith('/l/'):
        target = parse_qs(parsed.query).get('uddg', [])
        if target:
            return unquote(target[0])
    return url


def _search_duckduckgo(query):
    try:
        response = requests.get(
            SEARCH_URL,
            params={'q': query},
            timeout=settings.WEB_REQUEST_TIMEOUT_SECONDS,
            headers={'User-Agent': USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    urls = []
    for anchor in soup.select('a.result__a, a[href]'):
        href = anchor.get('href', '').strip()
        if not href:
            continue
        normalized = _normalize_search_result_url(href)
        if not normalized.startswith('http'):
            continue
        if normalized in urls:
            continue
        urls.append(normalized)
        if len(urls) >= settings.WEB_SEARCH_MAX_RESULTS:
            break
    return urls


def _search_wikipedia(query):
    try:
        response = requests.get(
            WIKIPEDIA_SEARCH_URL,
            params={
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'utf8': 1,
            },
            timeout=settings.WEB_REQUEST_TIMEOUT_SECONDS,
            headers={'User-Agent': USER_AGENT},
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    urls = []
    for item in data.get('query', {}).get('search', []):
        title = item.get('title', '').strip().replace(' ', '_')
        if not title:
            continue
        url = f'https://en.wikipedia.org/wiki/{title}'
        if url not in urls:
            urls.append(url)
        if len(urls) >= settings.WEB_SEARCH_MAX_RESULTS:
            break
    return urls


def search_web(query):
    urls = _search_duckduckgo(query)
    if urls:
        return urls
    return _search_wikipedia(query)


def fetch_web_context(urls):
    context_blocks = []
    used_urls = []
    total_chars = 0

    for url in urls[: settings.WEB_CONTEXT_MAX_URLS]:
        try:
            response = requests.get(
                url,
                timeout=settings.WEB_REQUEST_TIMEOUT_SECONDS,
                headers={'User-Agent': USER_AGENT},
            )
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()

            title = (soup.title.string or '').strip() if soup.title else ''
            text_parts = []
            for node in soup.find_all(['h1', 'h2', 'h3', 'p', 'li']):
                text = ' '.join(node.get_text(' ', strip=True).split())
                if text:
                    text_parts.append(text)

            page_text = '\n'.join(text_parts)
            if not page_text:
                continue

            remaining_chars = settings.WEB_CONTEXT_MAX_CHARS - total_chars
            if remaining_chars <= 0:
                break

            snippet = page_text[:remaining_chars]
            block = f'Source: {url}\nTitle: {title or "Untitled"}\nContent:\n{snippet}'
            context_blocks.append(block)
            used_urls.append(url)
            total_chars += len(snippet)
        except requests.RequestException:
            continue

    return '\n\n'.join(context_blocks), used_urls