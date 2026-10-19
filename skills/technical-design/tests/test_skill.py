"""Run: python3 -B -m unittest discover -s <skill>/tests -v."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from contract import load, validate, TYPES
from render import render, diagram, save
from check import check, advice


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = [], []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        if values.get('href', '').startswith('#'):
            self.links.append(values['href'][1:])


class TechnicalDesignTests(unittest.TestCase):
    def setUp(self):
        self.data = load(ROOT / 'assets' / 'example.json')
    def graph(self, kind):
        return next(v for v in self.data['diagrams'] if v['type'] == kind)
    def invalid(self):
        self.assertTrue(validate(self.data))

    def test_example_contract(self):
        self.assertEqual(validate(self.data), [])
    def test_nine_graph_types(self):
        self.assertEqual({v['type'] for v in self.data['diagrams']}, TYPES)
    def test_all_graphs_are_real_svg(self):
        for graph in self.data['diagrams']:
            output = diagram(graph)
            self.assertIn('<svg', output)
            self.assertIn('<path', output)
            start = output.index('<svg')
            end = output.index('</svg>', start) + 6
            parsed = ET.fromstring(output[start:end])
            self.assertTrue(parsed.findall('text'))
    def test_offline_no_javascript(self):
        page = render(self.data)
        self.assertNotIn('<script', page)
        self.assertNotIn('cdn.', page)
        self.assertNotIn('<img', page)
        self.assertIn('给定', page)
    def test_anchors(self):
        parser = Parser()
        parser.feed(render(self.data))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(set(parser.links).issubset(set(parser.ids)))
    def test_untrusted_content_escaped(self):
        self.data['title'] = '<script>alert(1)</script>'
        self.data['sections'][0]['blocks'][0]['text'] = '<img src=x onerror=alert(1)>'
        page = render(self.data)
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn('&lt;script&gt;', page)
    def test_unsafe_source_url(self):
        for url in ('javascript:alert(1)', 'https://u:p@example.test/', 'https://example.test/\nattack'):
            self.data['sources'][0]['url'] = url
            self.invalid()
    def test_quote_in_url_escaped(self):
        self.data['sources'][0]['url'] = 'https://example.test/?q="x"&y=1'
        self.assertIn('&quot;x&quot;&amp;y=1', render(self.data))
    def test_missing_sections(self):
        self.data['sections'] = self.data['sections'][:-1]
        self.invalid()
    def test_empty_design(self):
        self.data['designs'] = []
        self.invalid()
    def test_uncovered_requirement(self):
        self.data['requirements'].append({'id':'REQ-999','name':'额外需求','status':'建议','source_ids':[],'acceptance':['待讨论']})
        self.invalid()
    def test_dangling_req(self):
        self.data['designs'][0]['req_ids'] = ['REQ-999']
        self.invalid()
    def test_dangling_design(self):
        self.data['diagrams'][0]['design_ids'] = ['DES-999']
        self.invalid()
    def test_missing_tests(self):
        self.data['designs'][0]['tests'] = []
        self.invalid()
    def test_confirmed_without_source(self):
        self.data['designs'][0]['status'] = '已确认'
        self.invalid()
    def test_confirmed_doc_with_unresolved(self):
        self.data['status'] = '已确认'
        self.invalid()
    def test_graph_section_missing(self):
        self.data['diagrams'][0]['section_id'] = 'missing'
        self.invalid()
    def test_graph_edge_missing(self):
        self.graph('flow')['edges'][0]['to'] = 'missing'
        self.invalid()
    def test_graph_node_duplicate(self):
        self.graph('flow')['nodes'][1]['id'] = self.graph('flow')['nodes'][0]['id']
        self.invalid()
    def test_unknown_graph_type(self):
        self.data['diagrams'][0]['type'] = 'magic'
        self.invalid()
    def test_dependency_cycle_rejected(self):
        graph = self.graph('dependency')
        graph['edges'].append({'from':'integration','to':'contract','label':'错误回边','status':'建议','source_ids':[]})
        self.invalid()
    def test_swimlane_requires_group(self):
        del self.graph('swimlane')['nodes'][0]['group']
        self.invalid()
    def test_invalid_er_cardinality(self):
        self.graph('er')['relations'][0]['cardinality'] = 'many'
        self.invalid()
    def test_er_duplicate_field(self):
        fields = self.graph('er')['entities'][0]['fields']
        fields.append(copy.deepcopy(fields[0]))
        self.invalid()
    def test_sequence_invalid_kind(self):
        self.graph('sequence')['messages'][0]['kind'] = 'invalid'
        self.invalid()
    def test_sequence_self_message_supported(self):
        self.assertEqual(validate(self.data), [])
        self.assertIn('持久化', diagram(self.graph('sequence')))
    def test_three_mutual_diagrams_required(self):
        self.data['diagrams'] = self.data['diagrams'][:1]
        self.invalid()
    def test_writing_scan_nonmutating(self):
        self.data['sections'][0]['blocks'][0]['text'] = '上述系统进行验证,值得深思。'
        before = copy.deepcopy(self.data)
        self.assertTrue(advice(self.data))
        self.assertTrue(check(self.data)['passed'])
        self.assertEqual(before, self.data)
    def test_code_and_quotes_not_linted(self):
        data = {'type':'code','text':'中文,代码全链路闭环'}
        self.assertEqual(advice(data), [])
        self.assertEqual(advice({'original_request':'原文,不改','text':'“上述系统进行验证,引用” `代码,不改`'}), [])
    def test_fact_and_guarantee_preserved(self):
        value = 'P99 3 秒与 800 毫秒不能混同；幂等、事务、unknown 不升级为 exactly-once。'
        self.data['designs'][0]['failures'] = [value]
        self.assertIn(value, render(self.data))
    def test_duplicate_json_and_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            for value in ('{"a":1,"a":2}', '{"a":NaN}'):
                path.write_text(value, encoding='utf-8')
                with self.assertRaises(ValueError):
                    load(path)
    def test_nonoverwriting_and_force(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'user.html'
            path.write_text('已有内容', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                save(path, render(self.data))
            self.assertEqual(path.read_text(encoding='utf-8'), '已有内容')
            save(path, render(self.data), force=True)
            self.assertIn('技术方案', path.read_text(encoding='utf-8'))
    def test_cli_and_relocation(self):
        with tempfile.TemporaryDirectory(prefix='technical skill ') as directory:
            target = Path(directory)
            relocated = target / 'technical-design'
            shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns('_shots','__pycache__'))
            output = target / '示例 方案.html'
            args = [sys.executable,'-B',str(relocated/'scripts/render.py'),str(relocated/'assets/example.json'),'--output',str(output)]
            run = subprocess.run(args,cwd=str(target),capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'],'rendered')
            repeat = subprocess.run(args,cwd=str(target),capture_output=True,text=True)
            self.assertEqual(repeat.returncode,2)
    def test_checker_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            args = [sys.executable,'-B',str(ROOT/'scripts/check.py'),str(path)]
            self.data['designs'] = []
            path.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')
            run = subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(run.returncode,1)
            path.write_text('{broken',encoding='utf-8')
            run = subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(run.returncode,2)
    def test_skill_self_contained(self):
        text = (ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: technical-design\n'))
        self.assertNotIn('/Users/',text)
        for relative in ('references/design-contract.md','references/writing.md','references/diagrams.md','scripts/check.py','scripts/render.py','assets/example.json'):
            self.assertIn(relative,text)
            self.assertTrue((ROOT/relative).is_file())
    def test_state_model_matches_documented_results(self):
        graph = self.graph('state')
        self.assertEqual({n['label'] for n in graph['nodes']}, {'pending','accepted','cancelled','failed','unknown'})
        self.assertFalse(any(e['from']=='unknown' and e['to']=='pending' for e in graph['edges']))

    def test_long_sequence_text_stays_in_svg(self):
        graph = self.graph('sequence')
        graph['messages'].append({'from':'channel','to':'channel','label':'保持字段与条件的完整表达'*12,'kind':'note','status':'建议','source_ids':[]})
        output = diagram(graph)
        start = output.index('<svg')
        svg = ET.fromstring(output[start:output.index('</svg>',start)+6])
        width, height = [float(v) for v in svg.attrib['viewBox'].split()][2:]
        for element in svg.findall('text'):
            self.assertLess(float(element.attrib['x']),width)
            self.assertLess(float(element.attrib['y']),height)

    def test_rendered_example_matches_data(self):
        path = ROOT/'assets/团队待办技术方案示例.html'
        self.assertEqual(path.read_text(encoding='utf-8'),render(self.data))


if __name__ == '__main__':
    unittest.main()
