#!/usr/bin/env python3
"""Read-only case validation and safe Markdown rendering; Python 3.9+ stdlib."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

TYPES = ('functional','boundary','negative','permission','security','api','state','compatibility','accessibility','performance','reliability','regression','acceptance')
LEVELS = {'unit','integration','system','acceptance'}
METHODS = {'scenario','equivalence','boundary_value','decision_table','state_transition','pairwise','error_guessing'}
STATES = {'已确认','建议','待确认'}
DOC_STATES = {'探索草稿','待评审','已确认'}


def load(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value: raise ValueError('JSON 重复键')
            value[key] = item
        return value
    def finite(value):
        raise ValueError('不接受非有限数值')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique, parse_constant=finite)


def validate(data):
    errors = []
    def err(path, message): errors.append({'path':path,'message':message})
    def obj(value,path):
        if not isinstance(value,dict): err(path,'必须是对象'); return {}
        return value
    def text(value,path):
        if not isinstance(value,str) or not value.strip(): err(path,'必须是非空字符串'); return ''
        return value
    def array(value,path,empty=False):
        if not isinstance(value,list) or (not empty and not value): err(path,'必须为'+('' if empty else '非空')+'数组'); return []
        return value
    def enum(value,allowed,path):
        if not isinstance(value,str) or value not in allowed: err(path,'值不在允许枚举内')
    def records(value,path,prefix):
        items=[obj(item,f'{path}[{i}]') for i,item in enumerate(array(value,path))]; byid={}
        for i,item in enumerate(items):
            identifier=text(item.get('id'),f'{path}[{i}].id')
            if not re.fullmatch(prefix+r'-[0-9]{3,}',identifier): err(f'{path}[{i}].id','编号格式错误')
            if identifier in byid: err(f'{path}[{i}].id','编号重复')
            byid[identifier]=item
        return items,byid
    def strings(value,path):
        values=array(value,path)
        for i,v in enumerate(values): text(v,f'{path}[{i}]')
        return values
    root=obj(data,'$')
    text(root.get('title'),'title'); enum(root.get('status'),DOC_STATES,'status')
    prd=obj(root.get('prd'),'prd'); path=text(prd.get('path'),'prd.path')
    if not path or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or ':' in path or '\\' in path or '\x00' in path:
        err('prd.path','必须是安全的任务内相对路径')
    digest=text(prd.get('sha256'),'prd.sha256')
    if not re.fullmatch(r'[a-f0-9]{64}',digest): err('prd.sha256','必须为实际 SHA-256 格式')
    enum(prd.get('status'),DOC_STATES,'prd.status')
    requirements,reqs=records(root.get('requirements'),'requirements','REQ')
    conditions,acs=records(root.get('conditions'),'conditions','AC')
    for i,req in enumerate(requirements):
        p=f'requirements[{i}]'
        for key in ('title','source'): text(req.get(key),p+'.'+key)
        enum(req.get('status'),STATES,p+'.status')
    condition_reqs=set()
    for i,ac in enumerate(conditions):
        p=f'conditions[{i}]'
        for key in ('text','source'): text(ac.get(key),p+'.'+key)
        enum(ac.get('status'),STATES,p+'.status')
        rid=ac.get('req_id')
        if not isinstance(rid,str) or rid not in reqs: err(p+'.req_id','条件引用不存在的需求')
        else:
            condition_reqs.add(rid)
            if reqs[rid].get('status')=='待确认' and ac.get('status')!='待确认': err(p+'.status','条件不能升级未确认需求')
            if ac.get('status')=='已确认' and reqs[rid].get('status')!='已确认': err(p+'.status','条件确认状态强于需求')
    if set(reqs)-condition_reqs: err('conditions','有需求未拆测试条件')
    cases,case_ids=records(root.get('cases'),'cases','TC')
    mapped=set()
    for i,case in enumerate(cases):
        p=f'cases[{i}]'
        for key in ('title','priority_reason','cleanup','automation_reason'): text(case.get(key),p+'.'+key)
        for key,allowed in [('type',TYPES),('level',LEVELS),('method',METHODS),('priority',{'P0','P1','P2'}),('definition_status',STATES),('automation',{'可自动化','需人工','待评估'})]: enum(case.get(key),allowed,p+'.'+key)
        if case.get('execution_status')!='未执行': err(p+'.execution_status','生成阶段只能未执行')
        rid_values=strings(case.get('req_ids'),p+'.req_ids')
        cid_values=strings(case.get('condition_ids'),p+'.condition_ids')
        states=[]
        for rid in rid_values:
            if not isinstance(rid,str) or rid not in reqs: err(p+'.req_ids','需求引用不存在')
            else: states.append(reqs[rid].get('status'))
        for cid in cid_values:
            if not isinstance(cid,str) or cid not in acs: err(p+'.condition_ids','条件引用不存在')
            else:
                mapped.add(cid); states.append(acs[cid].get('status'))
                if acs[cid].get('req_id') not in rid_values: err(p+'.condition_ids','条件不属于该用例的需求')
        if '待确认' in states and case.get('definition_status')!='待确认': err(p+'.definition_status','用例不能升级未确认依据')
        if case.get('definition_status')=='已确认' and any(s!='已确认' for s in states): err(p+'.definition_status','用例已确认但依据未确认')
        for key in ('preconditions','data','assertions'): strings(case.get(key),p+'.'+key)
        for j,step in enumerate(array(case.get('steps'),p+'.steps')):
            step=obj(step,f'{p}.steps[{j}]')
            for key in ('action','expected'): text(step.get(key),f'{p}.steps[{j}].{key}')
    gaps=set()
    gap_items=array(root.get('coverage_gaps'),'coverage_gaps',True)
    for i,gap in enumerate(gap_items):
        p=f'coverage_gaps[{i}]'; gap=obj(gap,p)
        for key in ('reason','needed_input'): text(gap.get(key),p+'.'+key)
        cid=gap.get('condition_id')
        if not isinstance(cid,str) or cid not in acs: err(p+'.condition_id','缺口条件不存在')
        else: gaps.add(cid)
    if set(acs)-mapped-gaps: err('coverage_gaps','测试条件既无用例也无缺口说明')
    notes={}
    for i,item in enumerate(array(root.get('type_notes'),'type_notes')):
        p=f'type_notes[{i}]'; item=obj(item,p)
        enum(item.get('type'),TYPES,p+'.type'); enum(item.get('applicability'),{'适用','不适用','待确认'},p+'.applicability'); text(item.get('reason'),p+'.reason')
        kind=item.get('type')
        if isinstance(kind,str):
            if kind in notes: err(p+'.type','类型说明重复')
            notes[kind]=item
    if set(TYPES)-set(notes): err('type_notes','未说明所有内置类型的适用性')
    for kind,note in notes.items():
        selected=[c for c in cases if c.get('type')==kind]
        if note.get('applicability')=='适用' and not selected: err('type_notes','适用类型没有用例：'+kind)
        if note.get('applicability')=='不适用' and selected: err('type_notes','不适用类型含用例：'+kind)
        if note.get('applicability')=='待确认' and any(c.get('definition_status')!='待确认' for c in selected): err('type_notes','类型待确认，用例却未标待确认：'+kind)
    if root.get('status')=='已确认':
        if prd.get('status')!='已确认' or gap_items or any(r.get('status')!='已确认' for r in requirements+conditions) or any(c.get('definition_status')!='已确认' for c in cases): err('status','已确认套件仍有未确认内容或缺口')
    return errors


def summary(data):
    cases=data['cases']; conditions=data['conditions']
    executable={cid for c in cases if c['definition_status']=='已确认' for cid in c['condition_ids']}
    mapped={cid for c in cases for cid in c['condition_ids']}
    return {'cases':len(cases),'types':dict(Counter(c['type'] for c in cases)),
            'conditions':len(conditions),'mapped_conditions':len(mapped),
            'confirmed_definition_conditions':len(executable),
            'gaps':len(data['coverage_gaps']), 'execution':'未执行；映射数量不代表充分性或通过率'}


def md(value):
    value=str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return re.sub(r'([\\`*_{}\[\]()#+.!|~-])',r'\\\1',value).replace('\n','\n\n')


def render(data):
    errors=validate(data)
    if errors: raise ValueError(json.dumps(errors,ensure_ascii=False))
    counts=summary(data)
    parts=['# '+md(data['title']), '文档状态：'+md(data['status'])+'。所有用例未执行。',
           '## PRD 依据', '路径：'+md(data['prd']['path']), 'SHA256：'+md(data['prd']['sha256']),
           '原文状态：'+md(data['prd']['status']), '## 覆盖口径',
           f"用例 {counts['cases']} 条，测试条件 {counts['conditions']} 条，映射 {counts['mapped_conditions']} 条，已确认定义映射 {counts['confirmed_definition_conditions']} 条，缺口 {counts['gaps']} 条。映射不等于充分性或执行通过。",
           '## 类型适用说明']
    parts += ['- '+md(n['type'])+'：'+md(n['applicability'])+'。'+md(n['reason']) for n in data['type_notes']]
    parts.append('## 需求与测试条件')
    for req in data['requirements']:
        parts += ['### '+md(req['id']+' '+req['title']), '状态：'+md(req['status'])+'；依据：'+md(req['source'])]
        parts += ['- '+md(ac['id'])+' ['+md(ac['status'])+'] '+md(ac['text'])+'；来源：'+md(ac['source']) for ac in data['conditions'] if ac['req_id']==req['id']]
    parts.append('## 测试用例')
    for case in data['cases']:
        parts += ['### '+md(case['id']+' '+case['title']), '类型：'+md(case['type'])+'；层级：'+md(case['level'])+'；方法：'+md(case['method']),
                  '定义状态：'+md(case['definition_status'])+'；执行状态：未执行',
                  '优先级：'+md(case['priority'])+'。'+md(case['priority_reason']),
                  '需求：'+md(', '.join(case['req_ids']))+'；测试条件：'+md(', '.join(case['condition_ids']))]
        for key,label in [('preconditions','前提'),('data','测试数据')]:
            parts.append('#### '+label); parts += ['- '+md(v) for v in case[key]]
        parts.append('#### 操作与预期')
        for i,step in enumerate(case['steps'],1):
            parts.append(f'{i}. 操作：'+md(step['action'])+'\n\n   预期：'+md(step['expected']))
        parts.append('#### 结果断言'); parts += ['- '+md(v) for v in case['assertions']]
        parts += ['清理：'+md(case['cleanup']), '自动化：'+md(case['automation'])+'。'+md(case['automation_reason'])]
    parts.append('## 覆盖缺口')
    parts += ['- '+md(g['condition_id'])+'：'+md(g['reason'])+'；需要：'+md(g['needed_input']) for g in data['coverage_gaps']]
    if not data['coverage_gaps']: parts.append('登记的测试条件无未映射缺口；不保证需求穷尽或测试充分。')
    parts.append('仅完成用例设计和结构校验；本文件没有执行产品测试，不代表实现正确或上线批准。')
    return '\n\n'.join(parts)+'\n'


def save(path,content,force=False):
    path=Path(path)
    if path.suffix.lower()!='.md': raise ValueError('输出必须为 .md')
    if not force:
        with path.open('x',encoding='utf-8',newline='') as stream: stream.write(content)
        return
    temp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',dir=str(path.parent),delete=False) as stream:
            temp=Path(stream.name); stream.write(content)
        os.replace(temp,path)
    finally:
        if temp and temp.exists(): temp.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    c=sub.add_parser('check'); c.add_argument('input',type=Path)
    r=sub.add_parser('render'); r.add_argument('input',type=Path); r.add_argument('--output',required=True,type=Path); r.add_argument('--force',action='store_true')
    args=parser.parse_args()
    try:
        data=load(args.input); errors=validate(data)
        if args.command=='check':
            print(json.dumps({'passed':not errors,'errors':errors,'summary':summary(data) if not errors else None,'limits':['结构校验不判断 PRD 语义等价或实际文件摘要一致','未执行产品测试']},ensure_ascii=False,indent=2))
            return 1 if errors else 0
        if args.input.resolve()==args.output.resolve(): raise ValueError('输入输出不能相同')
        save(args.output,render(data),args.force)
    except (ValueError,UnicodeError) as exc:
        print(json.dumps({'passed':False,'error':str(exc)},ensure_ascii=False)); return 2
    except OSError:
        print(json.dumps({'passed':False,'error':'输入或输出文件读写失败'},ensure_ascii=False)); return 2
    print(json.dumps({'rendered':True,'output_name':args.output.name,'execution':'未执行'},ensure_ascii=False)); return 0


if __name__=='__main__':
    sys.exit(main())
