"""Regression coverage for catalogue integrity and safe, portable rendering."""
from copy import deepcopy
from contextlib import redirect_stdout
from html.parser import HTMLParser
import importlib.util
from io import StringIO
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import parse_qs, urljoin, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_build', ROOT / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
TOPICS = [
    {'id': 'evaluation', 'label': 'Evaluation', 'description': 'Human-grounded checks.'},
    {'id': 'multi-agent', 'label': 'Multi-agent interaction', 'description': 'Agents interact.'},
]
PAPER = {
    'id': 'example-paper', 'title': 'Example Paper', 'url': 'https://example.org/paper',
    'venue': 'Example 2025', 'year': 2025, 'tags': ['evaluation', 'multi-agent'],
    'primaryTopic': 'evaluation', 'notes': {'evaluation': 'Checks fidelity.', 'multi-agent': 'Studies interaction.'},
}


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.paper_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'script', 'img'} and 'src' in attrs:
            self.urls.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') in {'stylesheet', 'preload'}:
            self.urls.append(attrs['href'])
        if tag == 'article' and attrs.get('class') == 'paper':
            self.paper_count += 1


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data/papers').mkdir(parents=True)
        shutil.copytree(ROOT / 'site', self.root / 'site')
        self.save('data/topics.json', TOPICS)
        self.save('data/collection.json', {'updatedAt': '2026-09-21'})
        self.save_paper(PAPER)
        self.readme_before = '# Hand-written introduction\n\n' + builder.START + '\nold\n' + builder.END + '\n\nHand-written footer.\n'
        (self.root / 'README.md').write_text(self.readme_before, encoding='utf-8')

    def save(self, path, data):
        (self.root / path).write_text(json.dumps(data, ensure_ascii=False) + '\n', encoding='utf-8')

    def save_paper(self, paper):
        self.save('data/papers/' + paper['id'] + '.json', paper)

    def run_build(self, check=False):
        with redirect_stdout(StringIO()):
            builder.build(self.root, check=check)

    def test_invalid_records_are_rejected(self):
        mutations = [
            ('missing title', lambda p: p.pop('title')),
            ('unknown field', lambda p: p.update(yeer=2025)),
            ('wrong year type', lambda p: p.update(year=True)),
            ('blank title', lambda p: p.update(title=' ')),
            ('invalid id', lambda p: p.update(id='../escape')),
            ('unknown tag', lambda p: p.update(tags=['unknown'])),
            ('duplicate tag', lambda p: p.update(tags=['evaluation', 'evaluation'])),
            ('missing note', lambda p: p['notes'].pop('multi-agent')),
            ('extra note', lambda p: p['notes'].update(other='Extra.')),
            ('primary not in tags', lambda p: p.update(primaryTopic='other')),
            ('unsafe scheme', lambda p: p.update(url='javascript:alert(1)')),
            ('URL credentials', lambda p: p.update(url='https://name:secret@example.org')),
            ('malformed port', lambda p: p.update(url='https://example.org:bad/paper')),
            ('URL whitespace', lambda p: p.update(url='https://example.org/a b')),
            ('URL backslash', lambda p: p.update(url='https://example.org/\\paper')),
            ('unsafe nested URL', lambda p: p.update(resources=[{'label': 'Code', 'url': 'data:text/html,test'}])),
            ('resource typo', lambda p: p.update(resources=[{'label': 'Code', 'url': 'https://example.org/code', 'urll': 'typo'}])),
            ('duplicate resources', lambda p: p.update(resources=[{'label': 'Code', 'url': 'https://example.org/code'}, {'label': 'Code', 'url': 'https://example.org/other'}])),
            ('equal without authors', lambda p: p.update(equalContributors=2)),
            ('equal beyond author list', lambda p: p.update(authors=['A', 'B'], equalContributors=3)),
            ('equal boolean', lambda p: p.update(authors=['A', 'B'], equalContributors=True)),
            ('provenance typo', lambda p: p.update(provenance={'sorce': 'typo'})),
            ('provenance unsafe URL', lambda p: p.update(provenance={'authorSource': 'http://example.org'})),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                paper = deepcopy(PAPER)
                mutate(paper)
                with self.assertRaises(builder.ValidationError):
                    builder.validate_paper(paper, {'evaluation', 'multi-agent'}, 'example-paper.json')

    def test_filename_must_match_id(self):
        with self.assertRaisesRegex(builder.ValidationError, 'filename must match'):
            builder.validate_paper(PAPER, {'evaluation', 'multi-agent'}, 'different.json')

    def test_duplicate_title_and_url_are_rejected(self):
        for field, value in [('title', 'EXAMPLE   PAPER'), ('url', 'https://EXAMPLE.org/paper/#anchor')]:
            with self.subTest(field=field):
                second = deepcopy(PAPER)
                second.update(id='second-paper', title='Another Paper', url='https://example.org/another')
                second[field] = value
                self.save_paper(second)
                with self.assertRaisesRegex(builder.ValidationError, 'duplicate ' + field):
                    builder.load_collection(self.root)

    def test_duplicate_json_keys_are_rejected(self):
        (self.root / 'data/collection.json').write_text('{"updatedAt":"2026-09-21","updatedAt":"2026-09-22"}')
        with self.assertRaisesRegex(builder.ValidationError, 'duplicate JSON key'):
            builder.load_collection(self.root)

    def test_invalid_topic_and_collection_metadata_are_rejected(self):
        for value in [{'updatedAt': '20260921'}, {'updatedAt': '2026-02-31'}, {'updatedAt': '2026-09-21', 'paperCount': 1}]:
            self.save('data/collection.json', value)
            with self.assertRaises(builder.ValidationError):
                builder.load_collection(self.root)
        self.save('data/collection.json', {'updatedAt': '2026-09-21'})
        self.save('data/topics.json', TOPICS + [TOPICS[0]])
        with self.assertRaisesRegex(builder.ValidationError, 'duplicate id'):
            builder.load_collection(self.root)

    def test_html_and_embedded_json_are_safe(self):
        paper = deepcopy(PAPER)
        paper['title'] = '<img src=x onerror=alert(1)> & "quotes"'
        paper['notes']['evaluation'] = '</script><script>alert(1)</script> __PAPER_COUNT__'
        paper['authors'] = ['<b>Author</b>']
        paper['publicationHistory'] = '<strong>Published</strong>'
        self.save_paper(paper)
        self.run_build()
        page = (self.root / 'dist/index.html').read_text()
        self.assertIn('&lt;img src=x onerror=alert(1)&gt; &amp; &quot;quotes&quot;', page)
        self.assertIn('&lt;b&gt;Author&lt;/b&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('__PAPER_COUNT__', page)  # Data cannot become a template directive.
        payload = re.search(r'<script id="collection-data" type="application/json">(.*?)</script>', page, re.S).group(1)
        self.assertNotIn('<', payload)
        self.assertEqual(json.loads(payload)['papers'][0]['notes'], paper['notes'])

    def test_markdown_table_escapes_plain_text(self):
        paper = deepcopy(PAPER)
        paper['title'] = '[Link] | <script> *title*'
        paper['notes']['evaluation'] = 'Text | with `code` & <img>'
        tag = builder.render_tag(TOPICS[0], [paper])
        self.assertIn('\\[Link\\] \\| &lt;script&gt; \\*title\\*', tag)
        self.assertIn('Text \\| with \\`code\\` &amp; &lt;img&gt;', tag)

    def test_generated_counts_and_footer_match_canonical_data(self):
        second = deepcopy(PAPER)
        second.update(id='second-paper', title='Another Paper', url='https://example.org/another', tags=['evaluation'], primaryTopic='evaluation', notes={'evaluation': 'Different.'})
        self.save_paper(second)
        self.run_build()
        readme = (self.root / 'README.md').read_text()
        self.assertIn('**2 papers · 2 topics.**', readme)
        # Table cells are padded so the pipes align, which awesome-lint requires;
        # compare on the squeezed text so the assertion is about content, not spacing.
        squeezed = re.sub(r' {2,}', ' ', readme)
        self.assertIn('| Human-grounded checks. | 2 |', squeezed)
        self.assertIn('| Agents interact. | 1 |', squeezed)
        self.assertIn('2 papers, newest first.', (self.root / 'tags/evaluation.md').read_text())
        self.assertIn('1 paper, newest first.', (self.root / 'tags/multi-agent.md').read_text())
        page = (self.root / 'dist/index.html').read_text()
        parser = Assets()
        parser.feed(page)
        self.assertEqual(parser.paper_count, 2)
        self.assertIn('Collection updated · 21 Sep 2026', page)

    def test_topic_pages_list_newest_year_first(self):
        for paper_id, title, year in [
            ('older-paper', 'Older Paper', 2023),
            ('newer-paper', 'Newer Paper', 2026),
        ]:
            paper = deepcopy(PAPER)
            paper.update(id=paper_id, title=title, year=year, venue=f'Example {year}', url=f'https://example.org/{paper_id}')
            self.save_paper(paper)
        self.run_build()
        for topic in ('evaluation', 'multi-agent'):
            page = (self.root / 'tags' / f'{topic}.md').read_text()
            self.assertLess(page.index('Newer Paper'), page.index('Example Paper'))
            self.assertLess(page.index('Example Paper'), page.index('Older Paper'))

    def test_readme_outside_markers_is_preserved(self):
        self.run_build()
        readme = (self.root / 'README.md').read_text()
        self.assertEqual(readme.split(builder.START)[0], self.readme_before.split(builder.START)[0])
        self.assertEqual(readme.split(builder.END)[1], self.readme_before.split(builder.END)[1])
        with self.assertRaises(builder.ValidationError):
            builder.replace_catalogue('no markers', 'new content')
        with self.assertRaises(builder.ValidationError):
            builder.replace_catalogue(builder.END + builder.START, 'new content')

    def test_check_detects_stale_files_without_writing(self):
        self.run_build()
        self.run_build(check=True)
        paper = deepcopy(PAPER)
        paper['notes']['evaluation'] = 'Updated research note.'
        self.save_paper(paper)
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        with self.assertRaisesRegex(builder.ValidationError, 'Generated files are stale'):
            self.run_build(check=True)
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)

    def test_build_is_deterministic_and_dist_is_recreated(self):
        self.run_build()
        generated = [self.root / 'README.md', *sorted((self.root / 'tags').glob('*.md')), *sorted(path for path in (self.root / 'dist').rglob('*') if path.is_file())]
        before = {path.relative_to(self.root): path.read_bytes() for path in generated}
        (self.root / 'dist/stale-file.txt').write_text('obsolete')
        self.run_build()
        after = {path.relative_to(self.root): path.read_bytes() for path in generated}
        self.assertEqual(before, after)
        self.assertFalse((self.root / 'dist/stale-file.txt').exists())
        self.assertTrue((self.root / 'dist/.nojekyll').exists())

    def test_assets_work_at_github_pages_repository_path(self):
        self.run_build()
        parser = Assets()
        parser.feed((self.root / 'dist/index.html').read_text())
        self.assertGreaterEqual(len(parser.urls), 5)
        for asset in parser.urls:
            with self.subTest(asset=asset):
                self.assertFalse(asset.startswith('/'))
                self.assertFalse(urlsplit(asset).scheme)
                self.assertTrue((self.root / 'dist' / asset).is_file())
                self.assertTrue(urljoin('https://social-atoms.github.io/awesome-social-sim/', asset).startswith('https://social-atoms.github.io/awesome-social-sim/'))

    def test_repository_records_validate(self):
        papers, topics, _ = builder.load_collection(ROOT)
        self.assertTrue(papers)
        ids = {paper['id'] for paper in papers}
        self.assertIn('simulating-society-requires-simulating-thought', ids)
        self.assertIn('hugagent-a-human-simulation-benchmark-for-individual-level-reasoning', ids)
        self.assertEqual(len(ids), len(papers))
        self.assertTrue(all(paper['primaryTopic'] in {topic['id'] for topic in topics} for paper in papers))
        positions = [paper for paper in papers if paper.get('kind') == 'Position paper']
        self.assertTrue(positions)
        self.assertTrue(all(paper['tags'] == ['position-survey'] for paper in positions))
        self.assertTrue(all(not paper['venue'].startswith('arXiv preprint') for paper in papers))
        for paper in papers:
            source = paper['url']
            if 'aclanthology.org/' not in source:
                continue
            if '.findings-' in source:
                self.assertIn('Findings', paper['venue'])
            elif any(part in source for part in ('.acl-long.', '.naacl-long.', '.emnlp-main.')):
                self.assertIn('Main', paper['venue'])

    def test_field_map_links_match_catalogue_topics(self):
        _, topics, _ = builder.load_collection(ROOT)
        topic_names = {topic['id']: topic['label'] for topic in topics}
        svg_ids = []
        for filename in ('field-map.svg', 'field-map-mobile.svg'):
            with self.subTest(layout=filename):
                root = ET.parse(ROOT / 'site/static/assets' / filename).getroot()
                # An image role would hide the map's interactive descendants.
                self.assertEqual(root.get('role'), 'group')
                links = [node for node in root.iter('{http://www.w3.org/2000/svg}a') if node.get('data-topic')]
                self.assertCountEqual([link.get('data-topic') for link in links], topic_names)
                for link in links:
                    topic = link.get('data-topic')
                    target = urlsplit(link.get('href'))
                    self.assertEqual(target.scheme, 'https')
                    self.assertEqual(target.netloc, 'awesome.social-atoms.org')
                    self.assertEqual(parse_qs(target.query), {'topic': [topic]})
                    self.assertEqual(target.fragment, 'papers')
                    self.assertIn(topic_names[topic], link.get('aria-label', ''))
                    self.assertEqual(link.get('tabindex'), '0')
                    for text in link.findall('{http://www.w3.org/2000/svg}text'):
                        self.assertIn(''.join(text.itertext()), link.get('aria-label', ''))
                svg_ids.extend(node.get('id') for node in root.iter() if node.get('id'))
        self.assertEqual(len(svg_ids), len(set(svg_ids)), 'Both maps are embedded in the same page.')


if __name__ == '__main__':
    unittest.main()
