#!/usr/bin/env python3
"""Validate canonical records and generate the website and GitHub catalogue.

Only the marked catalogue block of README.md and tags/*.md are generated and
committed. dist/ is disposable build output. Python 3.11+, no dependencies.
"""
from __future__ import annotations

import argparse
from datetime import date
import html
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- catalogue:start -->'
END = '<!-- catalogue:end -->'
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
REQUIRED = {'id', 'title', 'url', 'venue', 'year', 'tags', 'primaryTopic', 'notes'}
OPTIONAL = {'kind', 'authors', 'equalContributors', 'resources', 'publicationHistory', 'historySource', 'provenance'}
PROVENANCE = {'addedAt', 'checkedAt', 'source', 'authorSource', 'publicationSource', 'descriptionSource', 'workshopSources'}


class ValidationError(ValueError):
    """A canonical source file or generated document needs correction."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def keys(value: object, required: set[str], optional: set[str], where: str) -> None:
    require(isinstance(value, dict), f'{where}: must be an object')
    missing = required - value.keys()
    extra = value.keys() - required - optional
    require(not missing, f'{where}: missing fields: {", ".join(sorted(missing))}')
    require(not extra, f'{where}: unknown fields: {", ".join(sorted(extra))}')


def string(value: object, where: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), f'{where}: must be a nonempty string')
    require(value == value.strip(), f'{where}: remove surrounding whitespace')
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), f'{where}: control characters are not allowed')


def iso_date(value: object, where: str) -> None:
    string(value, where)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f'{where}: use an ISO date, YYYY-MM-DD') from error
    require(parsed.isoformat() == value, f'{where}: use an ISO date, YYYY-MM-DD')


def url(value: object, where: str) -> None:
    string(value, where)
    require(not any(c.isspace() or c in '<>"\\' for c in value), f'{where}: URL contains unsafe characters')
    try:
        parsed = urlsplit(value)
        require(parsed.scheme == 'https' and bool(parsed.hostname), f'{where}: use an absolute HTTPS URL')
        require(parsed.username is None and parsed.password is None, f'{where}: URL credentials are not allowed')
        parsed.port  # Also reject malformed or out-of-range ports.
    except ValueError as error:
        raise ValidationError(f'{where}: invalid HTTPS URL') from error


def canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip('/'), parsed.query, ''))


def read_json(path: Path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'{path}: duplicate JSON key: {key}')
            result[key] = value
        return result
    try:
        return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_keys)
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f'{path}: {error}') from error


def validate_paper(paper: object, topic_ids: set[str], filename: str) -> None:
    keys(paper, REQUIRED, OPTIONAL, filename)
    for field in ('id', 'title', 'venue', 'primaryTopic'):
        string(paper[field], f'{filename}.{field}')
    require(bool(SLUG.fullmatch(paper['id'])), f'{filename}.id: use a lowercase hyphenated slug')
    require(filename == paper['id'] + '.json', f'{filename}: filename must match the paper id')
    url(paper['url'], f'{filename}.url')
    require(type(paper['year']) is int and 1900 <= paper['year'] <= 2100, f'{filename}.year: expected an integer from 1900 to 2100')
    tags = paper['tags']
    require(isinstance(tags, list) and bool(tags), f'{filename}.tags: must be a nonempty list')
    for tag in tags:
        string(tag, f'{filename}.tags')
        require(tag in topic_ids, f'{filename}.tags: unknown topic: {tag}')
    require(len(set(tags)) == len(tags), f'{filename}.tags: duplicate topics')
    require(paper['primaryTopic'] in tags, f'{filename}.primaryTopic: must be in tags')
    keys(paper['notes'], set(tags), set(), f'{filename}.notes')
    for tag, note in paper['notes'].items():
        string(note, f'{filename}.notes.{tag}')
    for field in ('kind', 'publicationHistory'):
        if field in paper:
            string(paper[field], f'{filename}.{field}')
    if 'historySource' in paper:
        url(paper['historySource'], f'{filename}.historySource')
        require('publicationHistory' in paper, f'{filename}.historySource: include publicationHistory')
    if 'authors' in paper:
        require(isinstance(paper['authors'], list) and bool(paper['authors']), f'{filename}.authors: must be a nonempty list')
        for name in paper['authors']:
            string(name, f'{filename}.authors')
    if 'equalContributors' in paper:
        count = paper['equalContributors']
        require(type(count) is int and 2 <= count <= len(paper.get('authors', [])), f'{filename}.equalContributors: must be 2 through the number of authors')
    if 'resources' in paper:
        require(isinstance(paper['resources'], list) and bool(paper['resources']), f'{filename}.resources: must be a nonempty list')
        seen_labels, seen_urls = set(), set()
        for resource in paper['resources']:
            keys(resource, {'label', 'url'}, set(), f'{filename}.resources')
            string(resource['label'], f'{filename}.resources.label')
            url(resource['url'], f'{filename}.resources.url')
            label, resource_url = resource['label'].casefold(), canonical_url(resource['url'])
            require(label not in seen_labels, f'{filename}.resources: duplicate label')
            require(resource_url not in seen_urls, f'{filename}.resources: duplicate URL')
            seen_labels.add(label)
            seen_urls.add(resource_url)
    if 'provenance' in paper:
        provenance = paper['provenance']
        keys(provenance, set(), PROVENANCE, f'{filename}.provenance')
        require(bool(provenance), f'{filename}.provenance: omit empty metadata')
        for field, value in provenance.items():
            where = f'{filename}.provenance.{field}'
            if field in {'addedAt', 'checkedAt'}:
                iso_date(value, where)
            elif field == 'source':
                string(value, where)
            elif field == 'workshopSources':
                require(isinstance(value, list) and bool(value), f'{where}: must be a nonempty list')
                for link in value:
                    url(link, where)
            else:
                url(value, where)


def load_collection(root: Path = ROOT) -> tuple[list[dict], list[dict], dict]:
    topics = read_json(root / 'data/topics.json')
    require(isinstance(topics, list) and bool(topics), 'topics.json: must be a nonempty list')
    topic_ids, topic_labels = set(), set()
    for topic in topics:
        keys(topic, {'id', 'label', 'description'}, set(), 'topics.json')
        for field, value in topic.items():
            string(value, f'topics.json.{field}')
        require(bool(SLUG.fullmatch(topic['id'])), 'topics.json.id: use a lowercase hyphenated slug')
        require(topic['id'] not in topic_ids, f'topics.json: duplicate id: {topic["id"]}')
        require(topic['label'].casefold() not in topic_labels, f'topics.json: duplicate label: {topic["label"]}')
        topic_ids.add(topic['id'])
        topic_labels.add(topic['label'].casefold())
    collection = read_json(root / 'data/collection.json')
    keys(collection, {'updatedAt'}, set(), 'collection.json')
    iso_date(collection['updatedAt'], 'collection.json.updatedAt')
    files = sorted((root / 'data/papers').glob('*.json'))
    require(bool(files), 'data/papers/: no paper records found')
    papers, seen = [], {field: set() for field in ('id', 'title', 'url')}
    for path in files:
        paper = read_json(path)
        validate_paper(paper, topic_ids, path.name)
        for field in seen:
            normalized = canonical_url(paper[field]) if field == 'url' else ' '.join(paper[field].casefold().split())
            require(normalized not in seen[field], f'{path.name}: duplicate {field}: {paper[field]}')
            seen[field].add(normalized)
        papers.append(paper)
    return sorted(papers, key=lambda p: (-p['year'], p['title'].casefold(), p['id'])), topics, collection


def markdown(value: str) -> str:
    """Render plain text safely in Markdown table cells and link labels."""
    escaped = html.escape(value, quote=False)
    for character in '\\`*_[]|':
        escaped = escaped.replace(character, '\\' + character)
    return escaped


def markdown_link(label: str, target: str) -> str:
    return f'[{markdown(label)}](<{target}>)'


def render_catalogue(papers: list[dict], topics: list[dict]) -> str:
    rows = ['## Browse by topic', '', f'**{len(papers)} papers · {len(topics)} topics.** A paper can appear in several topics.', '', '| Topic | Focus | Papers |', '| --- | --- | ---: |']
    for topic in topics:
        count = sum(topic['id'] in paper['tags'] for paper in papers)
        rows.append(f'| {markdown_link(topic["label"], "tags/" + topic["id"] + ".md")} | {markdown(topic["description"])} | {count} |')
    return '\n'.join(rows)


def render_tag(topic: dict, papers: list[dict]) -> str:
    selected = [paper for paper in papers if topic['id'] in paper['tags']]
    lines = [f'# {topic["label"]}', '', topic['description'], '', '[← All topics](../README.md#browse-by-topic)', '', '<!-- Generated by scripts/build.py from data/papers/. Do not edit directly. -->', '', f'{len(selected)} {"paper" if len(selected) == 1 else "papers"}, newest first.', '', '| Paper | Venue | Why it is included |', '| --- | --- | --- |']
    for paper in selected:
        identity = markdown_link(paper['title'], paper['url'])
        if paper.get('resources'):
            identity += '<br>' + ' · '.join(markdown_link(resource['label'], resource['url']) for resource in paper['resources'])
        lines.append(f'| {identity} | {markdown(paper["venue"])} | {markdown(paper["notes"][topic["id"]])} |')
    lines.extend(['', 'A paper may also appear on other topic pages. [Suggest a paper](https://github.com/Social-Atoms/awesome-social-sim/issues/new?template=paper-suggestion.yml) or [contribute a record](../CONTRIBUTING.md).', ''])
    return '\n'.join(lines)


def replace_catalogue(readme: str, content: str) -> str:
    require(readme.count(START) == 1 and readme.count(END) == 1, 'README.md: expected exactly one catalogue:start and catalogue:end marker')
    before, rest = readme.split(START)
    require(END in rest, 'README.md: catalogue:end must follow catalogue:start')
    _, after = rest.split(END)
    return before + START + '\n\n' + content + '\n\n' + END + after


def render_page(papers: list[dict], topics: list[dict], collection: dict, root: Path = ROOT) -> str:
    escape = html.escape
    labels = {topic['id']: topic['label'] for topic in topics}
    rows = []
    for paper in papers:
        tags = ''.join(f'<a class="paper-topic" href="?topic={escape(tag)}" data-topic="{escape(tag)}">{escape(labels[tag])}</a>' for tag in paper['tags'])
        notes = ''.join(f'<li data-note-topic="{escape(tag)}"><strong>{escape(labels[tag])}</strong><p>{escape(paper["notes"][tag])}</p></li>' for tag in paper['tags'])
        extras = f'<details class="more-notes"><summary>Notes across topics</summary><ul>{notes}</ul></details>' if len(set(paper['notes'].values())) > 1 else ''
        kind = f'<span class="paper-kind">{escape(paper["kind"])}</span>' if paper.get('kind') else ''
        details_parts = []
        if paper.get('authors'):
            author_text = ', '.join(escape(name) + ('<sup>*</sup>' if i < paper.get('equalContributors', 0) else '') for i, name in enumerate(paper['authors']))
            details_parts.append(f'<p class="paper-authors">{author_text}</p>')
            if paper.get('equalContributors'):
                details_parts.append('<p class="contribution-note">* Equal contribution.</p>')
        if paper.get('publicationHistory'):
            history_source = f' <a href="{escape(paper["historySource"])}" target="_blank" rel="noopener noreferrer">Publication history ↗</a>' if paper.get('historySource') else ''
            details_parts.append(f'<p>{escape(paper["publicationHistory"])}{history_source}</p>')
        details = '<details class="paper-details"><summary>Authors &amp; publication details</summary><div>' + ''.join(details_parts) + '</div></details>' if details_parts else ''
        resources = ''
        if paper.get('resources'):
            resources = '<nav class="paper-resources" aria-label="Resources for ' + escape(paper['title']) + '">' + ''.join(f'<a href="{escape(resource["url"])}" target="_blank" rel="noopener noreferrer">{escape(resource["label"])}<span aria-hidden="true">↗</span></a>' for resource in paper['resources']) + '</nav>'
        rows.append(f'<article class="paper" id="{escape(paper["id"])}"><div class="paper-identity"><h3><a href="{escape(paper["url"])}" target="_blank" rel="noopener noreferrer">{escape(paper["title"])}</a></h3><p class="publication">{escape(paper["venue"])}{kind}</p>{resources}{details}</div><p class="paper-note">{escape(paper["notes"][paper["primaryTopic"]])}</p><div class="paper-topics">{tags}</div>{extras}</article>')
    links = f'<li><a class="topic-link" href="./" data-topic="" aria-current="true"><span>All papers</span><span class="topic-count">{len(papers)}</span></a></li>'
    for topic in topics:
        count = sum(topic['id'] in paper['tags'] for paper in papers)
        links += f'<li><a class="topic-link" href="?topic={topic["id"]}" data-topic="{topic["id"]}" aria-current="false"><span>{escape(topic["label"])}</span><span class="topic-count">{count}</span></a></li>'
    payload = json.dumps({'papers': papers, 'topics': topics}, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    years = sorted({paper['year'] for paper in papers}, reverse=True)
    updated = date.fromisoformat(collection['updatedAt'])
    months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    replacements = {
        '__FAVICON__': 'data:image/svg+xml,' + quote((root / 'site/static/assets/social-atoms.svg').read_text(encoding='utf-8'), safe=''),
        '__PAPER_ROWS__': '\n'.join(rows), '__TOPIC_LINKS__': links, '__COLLECTION_DATA__': payload,
        '__PAPER_COUNT__': str(len(papers)), '__TOPIC_COUNT__': str(len(topics)),
        '__YEAR_RANGE__': f'{min(years)}–{max(years)}',
        '__YEAR_OPTIONS__': ''.join(f'<option>{year}</option>' for year in years),
        '__UPDATED_AT__': f'{updated.day} {months[updated.month - 1]} {updated.year}',
    }
    page = (root / 'site/index.template.html').read_text(encoding='utf-8')
    markers = set(re.findall(r'__[A-Z_]+__', page))
    require(markers == replacements.keys(), f'site/index.template.html: unexpected or missing template markers: {sorted(markers ^ replacements.keys())}')
    # A single substitution avoids interpreting marker-like text from paper data.
    return re.sub(r'__[A-Z_]+__', lambda match: replacements[match.group()], page)


def build(root: Path = ROOT, check: bool = False) -> None:
    papers, topics, collection = load_collection(root)
    page = render_page(papers, topics, collection, root)
    readme = root / 'README.md'
    documents = {readme: replace_catalogue(readme.read_text(encoding='utf-8'), render_catalogue(papers, topics))}
    for topic in topics:
        documents[root / 'tags' / (topic['id'] + '.md')] = render_tag(topic, papers)
    extra_tags = set((root / 'tags').glob('*.md')) - documents.keys()
    require(not extra_tags, 'Remove obsolete generated topic pages: ' + ', '.join(str(path.relative_to(root)) for path in sorted(extra_tags)))
    stale = [str(path.relative_to(root)) for path, content in documents.items() if not path.exists() or path.read_text(encoding='utf-8') != content]
    if check:
        require(not stale, 'Generated files are stale: ' + ', '.join(stale) + '. Run python3 scripts/build.py and commit the changes.')
        print(f'Validated {len(papers)} papers and {len(topics)} topics; generated catalogue is up to date.')
        return
    for path, content in documents.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    output = root / 'dist'
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(root / 'site/static', output)
    (output / 'index.html').write_text(page, encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Built {len(papers)} papers and {len(topics)} topics → dist/, tags/, README catalogue.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate data and generated Markdown without modifying files.')
    args = parser.parse_args()
    try:
        build(check=args.check)
    except (ValidationError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
