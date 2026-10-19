"""Run with unittest discover; only temporary task directories are mutated."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pipeline import register, resolve, snapshot, HandoffError, strict_json


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='handoff test ')
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def write(self, name, content=None):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or json.dumps({'title':name,'status':'待评审'},ensure_ascii=False),encoding='utf-8')
        return path
    def pair(self):
        self.write('prd.json')
        self.write('technical-design.json')
        register(self.root,'demo','prd','prd.json','待评审','requirement-analysis')
        register(self.root,'demo','technical_design','technical-design.json','待评审','technical-design')
    def test_missing_both_asks(self):
        result=resolve(self.root)
        self.assertEqual(result['state'],'needs_input')
        self.assertEqual(result['missing'],['prd','technical_design'])
        self.assertIn('询问',result['next'])
    def test_only_prd_preserved(self):
        self.write('prd.json')
        result=resolve(self.root)
        self.assertEqual(result['missing'],['technical_design'])
        self.assertEqual(result['available'],{'prd':'prd.json'})
    def test_only_design_preserved(self):
        self.write('technical-design.json')
        self.assertEqual(resolve(self.root)['missing'],['prd'])
    def test_valid_handoff(self):
        self.pair()
        result=resolve(self.root)
        self.assertEqual(result['state'],'ready')
        self.assertEqual(result['version_link'],'verified')
        self.assertEqual(result['inputs']['prd']['document_status'],'待评审')
    def test_unique_names_without_manifest_not_version_verified(self):
        self.write('prd.json'); self.write('technical-design.json')
        self.assertEqual(resolve(self.root)['version_link'],'unverified')
    def test_multiple_prd_candidates(self):
        self.write('prd.json'); self.write('prd.md','真实 PRD')
        self.write('technical-design.json')
        result=resolve(self.root)
        self.assertEqual(result['state'],'needs_input')
        self.assertEqual(len(result['ambiguous']['prd']),2)
    def test_explicit_input_overrides_ambiguity(self):
        self.write('prd.json'); self.write('prd.md','真实 PRD')
        self.write('technical-design.json')
        self.assertEqual(resolve(self.root,prd='prd.json')['state'],'ready')
    def test_explicit_missing_no_fallback(self):
        self.pair()
        with self.assertRaises(HandoffError): resolve(self.root,prd='missing.json')
    def test_changed_prd_blocks(self):
        self.pair(); self.write('prd.json','{"title":"修改","status":"待评审"}')
        with self.assertRaises(HandoffError): resolve(self.root)
    def test_changed_design_blocks(self):
        self.pair(); self.write('technical-design.json','{"title":"修改设计","status":"待评审"}')
        with self.assertRaises(HandoffError): resolve(self.root)
    def test_updated_prd_invalidates_old_design_binding(self):
        self.pair(); self.write('prd.json','{"title":"新需求","status":"待评审"}')
        result=register(self.root,'demo','prd','prd.json','待评审','requirement-analysis')
        self.assertTrue(result['invalidated_design'])
        self.assertIn('technical_design',json.loads((self.root/'pipeline.json').read_text())['artifacts'])
        self.assertTrue((self.root/'technical-design.json').exists())
        with self.assertRaises(HandoffError): resolve(self.root)
        register(self.root,'demo','technical_design','technical-design.json','待评审','technical-design')
        self.assertEqual(resolve(self.root)['version_link'],'verified')
    def test_register_design_requires_prd(self):
        self.write('technical-design.json')
        with self.assertRaises(HandoffError): register(self.root,'demo','technical_design','technical-design.json','待评审','technical-design')
    def test_register_design_requires_unchanged_prd(self):
        self.write('prd.json'); self.write('technical-design.json')
        register(self.root,'demo','prd','prd.json','待评审','requirement-analysis')
        self.write('prd.json','{"title":"变化","status":"待评审"}')
        with self.assertRaises(HandoffError): register(self.root,'demo','technical_design','technical-design.json','待评审','technical-design')
    def test_forged_old_design_binding(self):
        self.pair(); manifest=json.loads((self.root/'pipeline.json').read_text())
        manifest['artifacts']['technical_design']['prd_sha256']='0'*64
        (self.root/'pipeline.json').write_text(json.dumps(manifest),encoding='utf-8')
        with self.assertRaises(HandoffError): resolve(self.root)
    def test_absolute_traversal_and_url_rejected(self):
        for path in ('../prd.json','/tmp/prd.json','https://example.test/prd','C:/docs/prd.json','a\\prd.json'):
            with self.subTest(path=path),self.assertRaises(HandoffError): snapshot(self.root,path)
    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            file=Path(outside)/'outside.md'; file.write_text('outside',encoding='utf-8')
            (self.root/'prd.md').symlink_to(file)
            with self.assertRaises(HandoffError): snapshot(self.root,'prd.md')
    def test_manifest_symlink_rejected(self):
        self.write('other.json','{}'); (self.root/'pipeline.json').symlink_to(self.root/'other.json')
        with self.assertRaises(HandoffError): resolve(self.root)
    def test_skill_example_rejected(self):
        self.write('skills/a/assets/example.json')
        with self.assertRaises(HandoffError): snapshot(self.root,'skills/a/assets/example.json')
    def test_no_cross_task_search(self):
        self.write('other-task/prd.json'); self.write('other-task/technical-design.json')
        self.assertEqual(resolve(self.root)['missing'],['prd','technical_design'])
    def test_nested_document_names(self):
        self.write('documents/prd.json'); self.write('docs/technical-design.json')
        self.assertEqual(resolve(self.root)['state'],'ready')
    def test_same_file_rejected(self):
        self.write('prd.json')
        with self.assertRaises(HandoffError): resolve(self.root,prd='prd.json',design='prd.json')
    def test_empty_file_rejected(self):
        (self.root/'prd.md').write_text('  ',encoding='utf-8')
        with self.assertRaises(HandoffError): snapshot(self.root,'prd.md')
    def test_duplicate_json_nan_rejected(self):
        for content in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(HandoffError): strict_json(content)
    def test_invalid_manifest_schema(self):
        self.write('pipeline.json','{"schema_version":false,"task":"demo","artifacts":{}}')
        with self.assertRaises(HandoffError): resolve(self.root)
    def test_state_not_upgraded(self):
        self.write('prd.json','{"title":"草稿","status":"探索草稿"}')
        with self.assertRaises(HandoffError): register(self.root,'demo','prd','prd.json','已确认','user')
    def test_task_name_change_rejected(self):
        self.pair()
        with self.assertRaises(HandoffError): register(self.root,'other','prd','prd.json','待评审','user')
    def test_invalid_producer(self):
        self.write('prd.json')
        with self.assertRaises(HandoffError): register(self.root,'demo','prd','prd.json','待评审','technical-design')
    def test_unchanged_prd_keeps_design(self):
        self.pair()
        result=register(self.root,'demo','prd','prd.json','待评审','requirement-analysis')
        self.assertFalse(result['invalidated_design'])
        self.assertEqual(resolve(self.root)['version_link'],'verified')
    def test_resolve_is_read_only(self):
        self.pair(); before=(self.root/'pipeline.json').read_bytes()
        resolve(self.root)
        self.assertEqual(before,(self.root/'pipeline.json').read_bytes())
    def test_no_absolute_machine_path_in_output(self):
        self.pair(); output=json.dumps(resolve(self.root))
        self.assertNotIn(str(self.root),output)
    def test_cli_return_codes(self):
        args=[sys.executable,'-B',str(ROOT/'scripts/pipeline.py'),'resolve','--task-dir',str(self.root)]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,1)
        self.pair(); run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0)
        self.write('prd.json','bad'); run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
    def test_portable_script_and_cli_registration(self):
        relocated=self.root/'skill-copy'
        shutil.copytree(ROOT,relocated,ignore=shutil.ignore_patterns('__pycache__'))
        self.write('prd.json')
        args=[sys.executable,'-B',str(relocated/'scripts/pipeline.py'),'register','--task-dir',str(self.root),'--task','demo','--role','prd','--file','prd.json','--status','待评审','--producer','user']
        run=subprocess.run(args,cwd=str(self.root),capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
    def test_real_upstream_artifacts(self):
        repo=ROOT.parents[1]
        shutil.copyfile(repo/'skills/requirement-analysis/assets/example.json',self.root/'prd.json')
        shutil.copyfile(repo/'skills/technical-design/assets/example.json',self.root/'technical-design.json')
        register(self.root,'sample','prd','prd.json','探索草稿','requirement-analysis')
        register(self.root,'sample','technical_design','technical-design.json','探索草稿','technical-design')
        self.assertEqual(resolve(self.root)['version_link'],'verified')
        self.assertIn('不等于批准',resolve(self.root)['note'])
    def test_upstream_docs_explicitly_handoff(self):
        repo=ROOT.parents[1]
        for name in ('requirement-analysis','technical-design'):
            text=(repo/'skills'/name/'SKILL.md').read_text(encoding='utf-8')
            self.assertIn('product-development/references/handoff.md',text)
            self.assertIn('pipeline.py register',text)
    def test_skill_missing_document_question(self):
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('是否要我先帮你完善 PRD 和技术方案',text)
        self.assertIn('提问后等待回复',text)
        self.assertIn('停止开发',text)
        self.assertIn('单独调用',text)
    def test_invalid_utf8_manifest_returns_structured_error(self):
        (self.root/'pipeline.json').write_bytes(b'\xff\xfe')
        args=[sys.executable,'-B',str(ROOT/'scripts/pipeline.py'),'resolve','--task-dir',str(self.root)]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertEqual(json.loads(run.stdout)['state'],'invalid')
        self.assertNotIn(str(self.root),run.stdout)

    def test_manifest_escape_rejected(self):
        self.pair()
        manifest=json.loads((self.root/'pipeline.json').read_text())
        manifest['artifacts']['prd']['path']='../outside.json'
        (self.root/'pipeline.json').write_text(json.dumps(manifest),encoding='utf-8')
        with self.assertRaises(HandoffError): resolve(self.root)

    def test_local_resources_and_frontmatter(self):
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: product-development\n'))
        for path in ('references/handoff.md','references/development.md','scripts/pipeline.py'):
            self.assertIn(path,text); self.assertTrue((ROOT/path).is_file())


if __name__=='__main__':
    unittest.main()
