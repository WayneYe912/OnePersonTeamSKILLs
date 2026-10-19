"""Run from any directory: python3 -B -m unittest discover -s <skill>/tests -v."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render import load, render, save, validate
from check import check, writing_findings


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.tags = [], [], []
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'href' in attrs:
            self.hrefs.append(attrs['href'])


class RequirementSkillTests(unittest.TestCase):
    def setUp(self):
        self.data = load(ROOT / 'assets' / 'example.json')

    def test_example_contract(self):
        self.assertEqual(validate(self.data), [])

    def test_full_render(self):
        page = render(self.data)
        for expected in ('REQ-001', '给定', '当', '则', '低保真示意', '信息来源', '取消并记录原因'):
            self.assertIn(expected, page)
        self.assertIn('<svg', page)
        self.assertNotIn('<script', page)
        self.assertNotIn('cdn.', page)

    def test_anchors_and_links(self):
        parser = DocumentParser()
        parser.feed(render(self.data))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        for link in parser.hrefs:
            if link.startswith('#'):
                self.assertIn(link[1:], parser.ids)

    def test_escape_untrusted_input(self):
        self.data['title'] = '<script>alert("x")</script>'
        self.data['sections'][0]['blocks'][0]['text'] = '<img src=x onerror=alert(1)>'
        page = render(self.data)
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('&lt;img', page)

    def test_unsafe_url_rejected(self):
        for url in ('javascript:alert(1)', 'data:text/html,x', 'https://x.test/\nattack', 'https://name:pass@x.test/'):
            data = copy.deepcopy(self.data)
            data['sources'][0]['url'] = url
            self.assertTrue(validate(data), url)

    def test_valid_url_escaped(self):
        self.data['sources'][0]['url'] = 'https://example.test/?q="x"&next=1'
        self.assertIn('&quot;x&quot;&amp;next=1', render(self.data))

    def test_missing_essential_section(self):
        self.data['sections'] = self.data['sections'][:-1]
        self.assertTrue(validate(self.data))

    def test_empty_requirement_rejected(self):
        self.data['requirements'] = []
        self.assertTrue(validate(self.data))

    def test_duplicate_requirement_id(self):
        self.data['requirements'][1]['id'] = self.data['requirements'][0]['id']
        self.assertTrue(validate(self.data))

    def test_dangling_visual_reference(self):
        self.data['visuals'][0]['req_ids'] = ['REQ-999']
        self.assertTrue(validate(self.data))

    def test_dangling_edge(self):
        self.data['visuals'][0]['edges'][0]['to'] = 'unknown'
        self.assertTrue(validate(self.data))

    def test_isolated_node(self):
        self.data['visuals'][0]['nodes'].append({'id': 'isolated', 'label': '孤立', 'status': '建议', 'source_ids': []})
        self.assertTrue(validate(self.data))

    def test_self_loop(self):
        self.data['visuals'][0]['edges'][0]['to'] = 'set'
        self.assertTrue(validate(self.data))

    def test_unknown_confirmation_state(self):
        self.data['requirements'][0]['status'] = '已开发'
        self.assertTrue(validate(self.data))

    def test_confirmed_without_source(self):
        self.data['requirements'][0]['status'] = '已确认'
        self.assertTrue(validate(self.data))

    def test_confirmed_document_with_unresolved_items(self):
        self.data['status'] = '已确认'
        self.assertTrue(validate(self.data))

    def test_missing_acceptance_result(self):
        self.data['requirements'][0]['acceptance'][0]['then'] = ''
        self.assertTrue(validate(self.data))

    def test_priority_status_required(self):
        del self.data['requirements'][0]['priority_status']
        self.assertTrue(validate(self.data))

    def test_unknown_source(self):
        self.data['requirements'][0]['source_ids'] = ['SRC-999']
        self.assertTrue(validate(self.data))

    def test_no_single_image_fake_completion(self):
        self.data['visuals'] = self.data['visuals'][:1]
        self.assertTrue(validate(self.data))

    def test_writing_advice_does_not_mutate(self):
        self.data['sections'][0]['blocks'][0]['text'] = '该功能值得关注,通过全面赋能实现效率的提升。'
        before = copy.deepcopy(self.data)
        self.assertTrue(writing_findings(self.data))
        self.assertEqual(self.data, before)
        self.assertTrue(check(self.data)['passed'])

    def test_protected_text_not_linted(self):
        self.data = {'original_request': '原话值得关注,不修改', 'text': '“引用值得关注,不修改” `中文,代码` https://x.test/路径,资料'}
        self.assertEqual(writing_findings(self.data), [])

    def test_exact_fact_and_term_preservation(self):
        self.data['requirements'][0]['rules'] = ['P99 从 3 秒降到 800 毫秒；幂等、回滚与可访问性保持原词。可能延迟，不得升级为准时送达。']
        page = render(self.data)
        self.assertIn(self.data['requirements'][0]['rules'][0], page)

    def test_no_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'report.html'
            target.write_text('用户已有内容', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                save(target, render(self.data))
            self.assertEqual(target.read_text(encoding='utf-8'), '用户已有内容')
            save(target, render(self.data), force=True)
            self.assertIn('需求分析', target.read_text(encoding='utf-8'))

    def test_duplicate_keys_and_nonfinite_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'data.json'
            for text in ('{"title":"a","title":"b"}', '{"value":NaN}'):
                target.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    load(target)

    def test_cli_from_unrelated_directory_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='skill test ') as directory:
            output = Path(directory) / '需求 示例.html'
            args = [sys.executable, '-B', str(ROOT / 'scripts' / 'render.py'),
                    str(ROOT / 'assets' / 'example.json'), '--output', str(output)]
            result = subprocess.run(args, cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'rendered')
            self.assertTrue(output.exists())
            second = subprocess.run(args, cwd=directory, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)

    def test_checker_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'data.json'
            self.data['requirements'] = []
            target.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
            args = [sys.executable, '-B', str(ROOT / 'scripts' / 'check.py'), str(target)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)['passed'])
            target.write_text('{broken', encoding='utf-8')
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)

    def test_skill_runs_after_relocation(self):
        import shutil
        with tempfile.TemporaryDirectory(prefix='portable skill ') as directory:
            relocated = Path(directory) / 'skills' / 'requirement-analysis'
            shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns('_shots', '__pycache__'))
            output = Path(directory) / 'relocated.html'
            result = subprocess.run([sys.executable, '-B', str(relocated / 'scripts' / 'render.py'),
                                     str(relocated / 'assets' / 'example.json'), '--output', str(output)],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('REQ-003', output.read_text(encoding='utf-8'))

    def test_checked_in_example_matches_renderer(self):
        target = ROOT / 'assets' / '团队待办需求分析示例.html'
        self.assertEqual(target.read_text(encoding='utf-8'), render(self.data))

    def test_frontmatter_and_local_resources(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: requirement-analysis\n'))
        self.assertNotIn('/Users/', text)
        self.assertNotRegex(text, r'https?://')
        for relative in ('references/document-contract.md', 'references/writing.md',
                         'references/visuals.md', 'scripts/render.py', 'scripts/check.py', 'assets/example.json'):
            self.assertIn(relative, text)
            self.assertTrue((ROOT / relative).is_file())


if __name__ == '__main__':
    unittest.main()
