"""Regression checks for case contracts and PRD-only handoff. Stdlib only."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT.parents[1]/'skills/product-development/scripts'))
from cases import load,validate,render,summary,save,TYPES
from pipeline import register,resolve,HandoffError


class CaseTests(unittest.TestCase):
    def setUp(self):
        self.data=load(ROOT/'assets/example-cases.json')
    def test_example_valid(self): self.assertEqual(validate(self.data),[])
    def test_summary_from_details(self):
        stats=summary(self.data); self.assertEqual(stats['cases'],len(self.data['cases'])); self.assertEqual(stats['conditions'],5)
    def test_default_unexecuted(self):
        self.assertTrue(all(c['execution_status']=='未执行' for c in self.data['cases']))
    def test_claimed_pass_rejected(self):
        self.data['cases'][0]['execution_status']='通过'; self.assertTrue(validate(self.data))
    def test_missing_step_expected(self):
        del self.data['cases'][0]['steps'][0]['expected']; self.assertTrue(validate(self.data))
    def test_empty_assertion(self):
        self.data['cases'][0]['assertions']=[]; self.assertTrue(validate(self.data))
    def test_duplicate_id(self):
        self.data['cases'][1]['id']=self.data['cases'][0]['id']; self.assertTrue(validate(self.data))
    def test_unknown_type(self):
        self.data['cases'][0]['type']='invented'; self.assertTrue(validate(self.data))
    def test_unknown_reference(self):
        self.data['cases'][0]['condition_ids']=['AC-999']; self.assertTrue(validate(self.data))
    def test_condition_mismatch(self):
        self.data['cases'][0]['condition_ids']=['AC-005']; self.assertTrue(validate(self.data))
    def test_unconfirmed_rule_not_upgraded(self):
        self.data['conditions'][0]['status']='待确认'; self.assertTrue(validate(self.data))
    def test_unmapped_condition_requires_gap(self):
        self.data['conditions'].append({'id':'AC-999','req_id':'REQ-001','text':'新条件','status':'待确认','source':'用户待定'})
        self.assertTrue(validate(self.data))
        self.data['coverage_gaps'].append({'condition_id':'AC-999','reason':'缺标准','needed_input':'确认规则'})
        self.assertEqual(validate(self.data),[])
    def test_all_type_applicability(self):
        self.assertEqual({n['type'] for n in self.data['type_notes']},set(TYPES))
        self.data['type_notes'].pop(); self.assertTrue(validate(self.data))
    def test_inapplicable_type_cannot_have_cases(self):
        self.data['type_notes'][0]['applicability']='不适用'; self.assertTrue(validate(self.data))
    def test_confirmation_not_faked(self):
        self.data['requirements'][0]['status']='建议'; self.assertTrue(validate(self.data))
    def test_safe_path_and_hash(self):
        self.data['prd']['path']='../outside.json'; self.assertTrue(validate(self.data))
        self.data['prd']['path']='prd.json'; self.data['prd']['sha256']='placeholder'; self.assertTrue(validate(self.data))
    def test_markdown_escaping(self):
        self.data['title']='<script>alert(1)</script> [label](https://example.test)'
        output=render(self.data); self.assertNotIn('<script>',output); self.assertIn('&lt;script&gt;',output); self.assertIn('\\[label\\]',output)
    def test_rendered_fields_complete(self):
        output=render(self.data)
        for word in ('操作：','预期：','结果断言','优先级','覆盖缺口','类型适用说明','未执行'): self.assertIn(word,output)
        self.assertIn('TC\\-001',output)
    def test_original_boundaries_unchanged(self):
        self.assertIn('恰等于 D',render(self.data)); self.assertIn('不允许晚于截止时间',render(self.data))
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'case.md'; p.write_text('已有',encoding='utf-8')
            with self.assertRaises(FileExistsError): save(p,render(self.data))
            self.assertEqual(p.read_text(encoding='utf-8'),'已有'); save(p,render(self.data),True)
    def test_duplicate_json_nan(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json'
            for text in ('{"a":1,"a":2}','{"a":NaN}'):
                p.write_text(text,encoding='utf-8')
                with self.assertRaises(ValueError): load(p)
    def test_prd_only_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=resolve(tmp,only_prd=True); self.assertEqual(result['missing'],['prd']); self.assertIn('询问',result['next'])
    def test_prd_only_ready_and_no_design_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shutil.copyfile(ROOT/'assets/example-prd.json',root/'prd.json')
            register(root,'test','prd','prd.json','已确认','requirement-analysis')
            result=resolve(root,only_prd=True); self.assertEqual(result['state'],'ready'); self.assertEqual(set(result['inputs']),{'prd'})
    def test_prd_only_no_cross_task_or_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'other').mkdir(); shutil.copyfile(ROOT/'assets/example-prd.json',root/'other/prd.json')
            self.assertEqual(resolve(root,only_prd=True)['state'],'needs_input')
    def test_prd_only_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'prd.md').write_text('a',encoding='utf-8'); (root/'prd.html').write_text('b',encoding='utf-8')
            self.assertIn('prd',resolve(root,only_prd=True)['ambiguous'])
    def test_case_binding_and_development_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shutil.copyfile(ROOT/'assets/example-prd.json',root/'prd.json'); shutil.copyfile(ROOT/'assets/example-cases.json',root/'test-cases.json')
            (root/'technical-design.json').write_text('{"title":"design","status":"待评审"}',encoding='utf-8')
            register(root,'test','prd','prd.json','已确认','requirement-analysis')
            register(root,'test','technical_design','technical-design.json','待评审','technical-design')
            register(root,'test','test_cases','test-cases.json','待评审','test-case-design')
            self.assertIn('test_cases',resolve(root)['inputs'])
            (root/'prd.json').write_text('{"title":"new","status":"已确认"}',encoding='utf-8')
            register(root,'test','prd','prd.json','已确认','requirement-analysis')
            self.assertEqual(resolve(root,only_prd=True)['state'],'ready')
            register(root,'test','technical_design','technical-design.json','待评审','technical-design')
            with self.assertRaises(HandoffError): resolve(root)
    def test_wrong_prd_declared_in_suite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shutil.copyfile(ROOT/'assets/example-prd.json',root/'prd.json')
            register(root,'test','prd','prd.json','已确认','user')
            self.data['prd']['sha256']='0'*64; (root/'test-cases.json').write_text(json.dumps(self.data),encoding='utf-8')
            with self.assertRaises(HandoffError): register(root,'test','test_cases','test-cases.json','待评审','test-case-design')
    def test_sample_hash_actual(self):
        digest=hashlib.sha256((ROOT/'assets/example-prd.json').read_bytes()).hexdigest(); self.assertEqual(digest,self.data['prd']['sha256'])
    def test_cli_codes_and_render(self):
        with tempfile.TemporaryDirectory(prefix='cases test ') as tmp:
            out=Path(tmp)/'用例.md'; args=[sys.executable,'-B',str(ROOT/'scripts/cases.py'),'render',str(ROOT/'assets/example-cases.json'),'--output',str(out)]
            run=subprocess.run(args,cwd=tmp,capture_output=True,text=True); self.assertEqual(run.returncode,0,run.stdout); self.assertTrue(out.exists())
            run=subprocess.run(args,cwd=tmp,capture_output=True,text=True); self.assertEqual(run.returncode,2)
    def test_changed_suite_blocks_development_but_not_prd_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            shutil.copyfile(ROOT/'assets/example-prd.json',root/'prd.json')
            shutil.copyfile(ROOT/'assets/example-cases.json',root/'test-cases.json')
            (root/'technical-design.json').write_text('{"title":"design","status":"待评审"}',encoding='utf-8')
            register(root,'test','prd','prd.json','已确认','user')
            register(root,'test','technical_design','technical-design.json','待评审','user')
            register(root,'test','test_cases','test-cases.json','待评审','test-case-design')
            (root/'test-cases.json').write_text('{"title":"changed","status":"待评审"}',encoding='utf-8')
            with self.assertRaises(HandoffError): resolve(root)
            self.assertEqual(resolve(root,only_prd=True)['state'],'ready')

    def test_only_prd_cli_and_missing_input_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=[sys.executable,'-B',str(ROOT.parents[1]/'skills/product-development/scripts/pipeline.py'),'resolve','--only-prd','--task-dir',tmp]
            run=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(run.returncode,1)
            self.assertEqual(json.loads(run.stdout)['missing'],['prd'])
            shutil.copyfile(ROOT/'assets/example-prd.json',Path(tmp)/'prd.json')
            run=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(run.returncode,0)
            self.assertNotIn('technical_design',json.loads(run.stdout)['inputs'])

    def test_cases_script_runs_after_relocation(self):
        with tempfile.TemporaryDirectory(prefix='portable cases ') as tmp:
            target=Path(tmp)/'test-case-design'
            shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('__pycache__'))
            args=[sys.executable,'-B',str(target/'scripts/cases.py'),'check',str(target/'assets/example-cases.json')]
            run=subprocess.run(args,cwd=tmp,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_generated_example_matches_renderer(self):
        self.assertEqual((ROOT/'assets/测试用例示例.md').read_text(encoding='utf-8'),render(self.data))

    def test_every_declared_type_can_be_validated(self):
        for kind in TYPES:
            with self.subTest(kind=kind):
                data=copy.deepcopy(self.data)
                case=copy.deepcopy(data['cases'][0]); case['type']=kind
                data['cases']=[case]
                data['coverage_gaps']=[{'condition_id':ac['id'],'reason':'本测试只验证图种契约','needed_input':'补其余条件'} for ac in data['conditions'] if ac['id']!='AC-001']
                data['type_notes']=[{'type':t,'applicability':'适用' if t==kind else '不适用','reason':'仅用于结构测试'} for t in TYPES]
                self.assertEqual(validate(data),[])

    def test_wrong_prd_confirmation_in_suite_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shutil.copyfile(ROOT/'assets/example-prd.json',root/'prd.json')
            register(root,'test','prd','prd.json','已确认','user')
            self.data['prd']['status']='探索草稿'
            (root/'test-cases.json').write_text(json.dumps(self.data),encoding='utf-8')
            with self.assertRaises(HandoffError): register(root,'test','test_cases','test-cases.json','待评审','test-case-design')

    def test_missing_prd_question_and_self_contained(self):
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8'); self.assertIn('是否要我先帮你完善 PRD',text); self.assertIn('提问后等待',text); self.assertIn('用户拒绝',text)
        self.assertTrue(text.startswith('---\nname: test-case-design\n'))
        for p in ('references/test-design.md','references/case-contract.md','scripts/cases.py'): self.assertIn(p,text); self.assertTrue((ROOT/p).is_file())


if __name__=='__main__': unittest.main()
