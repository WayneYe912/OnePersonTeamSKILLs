#!/usr/bin/env python3
"""Register and resolve task-local PRD/design handoffs. Python 3.9+ stdlib."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

ROLES = ('prd', 'technical_design', 'test_cases')
STATES = {'探索草稿', '待评审', '已确认'}
PRODUCERS = {'prd': {'requirement-analysis', 'user'}, 'technical_design': {'technical-design', 'user'},
             'test_cases': {'test-case-design', 'user'}}
HASH = re.compile(r'[a-f0-9]{64}\Z')
NAMES = {'prd': ('prd.json', 'prd.md', 'prd.html', 'requirements.json'),
         'technical_design': ('technical-design.json', 'technical-design.md', 'technical-design.html', 'design.json')}


class HandoffError(ValueError):
    pass


def strict_json(content):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise HandoffError('JSON 存在重复键：' + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise HandoffError('JSON 不接受非有限数值')
    try:
        return json.loads(content, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, TypeError) as exc:
        raise HandoffError('无法读取有效 JSON：' + str(exc)) from exc


def task_root(value):
    root = Path(value).resolve()
    if not root.is_dir():
        raise HandoffError('任务目录不存在或不是目录')
    return root


def local_path(root, value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise HandoffError('文档路径必须是任务内的相对路径')
    logical = PurePosixPath(value)
    if logical.is_absolute() or '..' in logical.parts or value == '.':
        raise HandoffError('不允许绝对路径或上级目录路径')
    if '.git' in logical.parts or ('skills' in logical.parts and 'assets' in logical.parts):
        raise HandoffError('不允许使用 Git 内部文件或技能样例作前置')
    full = root.joinpath(*logical.parts)
    try:
        resolved = full.resolve()
        resolved.relative_to(root)
    except (ValueError, OSError, RuntimeError) as exc:
        raise HandoffError('文档路径越出任务目录') from exc
    return full


def snapshot(root, value):
    path = local_path(root, value)
    if not path.is_file():
        raise HandoffError('前置文档不存在或不是文件：' + value)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise HandoffError('前置文档无法读取：' + value) from exc
    if not content.strip():
        raise HandoffError('前置文档为空：' + value)
    doc_state = None
    if path.suffix.lower() == '.json':
        try:
            data = strict_json(content.decode('utf-8-sig'))
        except UnicodeError as exc:
            raise HandoffError('JSON 文档不是 UTF-8：' + value) from exc
        if not isinstance(data, dict) or not data:
            raise HandoffError('JSON 前置文档必须是非空对象：' + value)
        doc_state = data.get('status')
        if doc_state is not None and (not isinstance(doc_state, str) or doc_state not in STATES):
            raise HandoffError('JSON 文档状态错误：' + value)
    return {'path': PurePosixPath(value).as_posix(), 'sha256': hashlib.sha256(content).hexdigest(),
            'document_status': doc_state}


def load_manifest(root):
    path = root / 'pipeline.json'
    if not path.exists() and not path.is_symlink():
        return None
    local_path(root, 'pipeline.json')
    if path.is_symlink() or not path.is_file():
        raise HandoffError('任务清单必须是目录内的普通文件')
    try:
        content = path.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError) as exc:
        raise HandoffError('任务清单不可读或不是有效 UTF-8') from exc
    data = strict_json(content)
    if not isinstance(data, dict) or set(data) != {'schema_version', 'task', 'artifacts'}:
        raise HandoffError('任务清单根字段错误')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise HandoffError('不支持的清单版本')
    if not isinstance(data['task'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', data['task']):
        raise HandoffError('task 必须为简短语义任务名')
    artifacts = data['artifacts']
    if not isinstance(artifacts, dict) or set(artifacts) - set(ROLES):
        raise HandoffError('未知或无效 artifact 角色')
    for role, record in artifacts.items():
        fields = {'path', 'sha256', 'producer', 'status'} | ({'prd_sha256'} if role != 'prd' else set())
        if not isinstance(record, dict) or set(record) != fields:
            raise HandoffError('文档登记字段错误：' + role)
        local_path(root, record['path'])
        if not isinstance(record['sha256'], str) or not HASH.fullmatch(record['sha256']):
            raise HandoffError('摘要格式错误：' + role)
        if not isinstance(record['status'], str) or record['status'] not in STATES:
            raise HandoffError('登记状态错误：' + role)
        if not isinstance(record['producer'], str) or record['producer'] not in PRODUCERS[role]:
            raise HandoffError('生成者与文档角色不匹配：' + role)
        if role != 'prd' and (not isinstance(record['prd_sha256'], str) or not HASH.fullmatch(record['prd_sha256'])):
            raise HandoffError('前置 PRD 绑定摘要格式错误：' + role)
    return data


def checked_record(root, record):
    actual = snapshot(root, record['path'])
    if actual['sha256'] != record['sha256']:
        raise HandoffError('文档内容已变化，需要重新确认与登记：' + record['path'])
    if actual['document_status'] and actual['document_status'] != record['status']:
        raise HandoffError('登记状态与文档状态不一致：' + record['path'])
    return actual


def register(root, task, role, file, status, producer):
    root = task_root(root)
    if role not in ROLES or status not in STATES or producer not in PRODUCERS[role]:
        raise HandoffError('角色、状态或生成者错误')
    if not isinstance(task, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task):
        raise HandoffError('task 必须为简短语义任务名')
    data = load_manifest(root) or {'schema_version': 1, 'task': task, 'artifacts': {}}
    if data['task'] != task:
        raise HandoffError('已有清单属于另一任务')
    actual = snapshot(root, file)
    if actual['document_status'] and actual['document_status'] != status:
        raise HandoffError('不能改变原文确认状态')
    if actual['path'] == 'pipeline.json':
        raise HandoffError('清单本身不能作为前置文档')
    record = {key: actual[key] for key in ('path', 'sha256')}
    record.update(status=status, producer=producer)
    invalidated = False
    if role != 'prd':
        prd = data['artifacts'].get('prd')
        if not prd:
            raise HandoffError('登记下游文档前必须登记 PRD')
        checked_record(root, prd)
        if local_path(root, prd['path']).resolve() == local_path(root, file).resolve():
            raise HandoffError('下游文档与 PRD 不能是同一文件')
        record['prd_sha256'] = prd['sha256']
        if role == 'test_cases':
            if local_path(root, file).suffix.lower() != '.json':
                raise HandoffError('测试用例登记需使用权威 JSON')
            payload = strict_json(local_path(root, file).read_text(encoding='utf-8-sig'))
            declared_prd = payload.get('prd') if isinstance(payload, dict) else None
            if not isinstance(declared_prd, dict) or declared_prd.get('sha256') != prd['sha256'] or declared_prd.get('path') != prd['path'] or declared_prd.get('status') != prd['status']:
                raise HandoffError('测试用例内声明的 PRD 与清单不一致')
    else:
        old = data['artifacts'].get('prd')
        if not old or old['sha256'] != record['sha256'] or old['path'] != record['path']:
            invalidated = 'technical_design' in data['artifacts']
            # Preserve downstream old bindings; consumers reject stale PRD hashes.
    data['artifacts'][role] = record
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=str(root), delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        os.replace(tmp, root / 'pipeline.json')
    finally:
        if tmp and tmp.exists():
            tmp.unlink()
    return {'state': 'registered', 'manifest': 'pipeline.json', 'role': role, 'path': record['path'],
            'invalidated_design': invalidated, 'note': '登记不等于业务确认或开发批准'}


def resolve(root, prd=None, design=None, only_prd=False):
    root = task_root(root)
    data = load_manifest(root)
    records = data['artifacts'] if data else {}
    inputs, missing, ambiguous = {}, [], {}
    if only_prd and design is not None:
        raise HandoffError('only-prd 模式不接受技术方案参数')
    requested = (('prd', prd),) if only_prd else (('prd', prd), ('technical_design', design))
    for role, explicit in requested:
        record = records.get(role)
        if explicit is not None:
            actual = snapshot(root, explicit)
            if record and actual['path'] == record['path']:
                checked_record(root, record)
            inputs[role] = actual
        elif record:
            inputs[role] = checked_record(root, record)
        else:
            candidates = []
            for folder in ('', 'docs/', 'documents/'):
                for name in NAMES[role]:
                    value = folder + name
                    candidate = root / value
                    if candidate.exists() or candidate.is_symlink():
                        candidates.append(value)
            if len(candidates) > 1:
                ambiguous[role] = candidates
            elif candidates:
                inputs[role] = snapshot(root, candidates[0])
            else:
                missing.append(role)
    if missing or ambiguous:
        return {'state': 'needs_input', 'missing': missing, 'ambiguous': ambiguous,
                'available': {k: v['path'] for k, v in inputs.items()},
                'next': '询问是否完善缺少的 PRD 或使用已有 PRD；未回答不生成用例' if only_prd else '询问是否完善缺少的文档或使用已有文档；未回答不开发'}
    if only_prd:
        return {'state': 'ready', 'inputs': inputs, 'note': '仅 PRD 文件核验通过；完整读取并核对后才能设计用例，未执行产品测试'}
    if local_path(root, inputs['prd']['path']).resolve() == local_path(root, inputs['technical_design']['path']).resolve():
        raise HandoffError('PRD 与技术方案不能是同一文件')
    selected_design = records.get('technical_design')
    bound = False
    if selected_design and selected_design['path'] == inputs['technical_design']['path']:
        checked_record(root, selected_design)
        if selected_design['prd_sha256'] != inputs['prd']['sha256']:
            raise HandoffError('技术方案绑定的 PRD 版本已失效')
        bound = True
    if 'test_cases' in records:
        suite = records['test_cases']
        actual = checked_record(root, suite)
        if suite['prd_sha256'] != inputs['prd']['sha256']:
            raise HandoffError('测试用例绑定的 PRD 版本已失效')
        payload = strict_json(local_path(root, suite['path']).read_text(encoding='utf-8-sig'))
        declared = payload.get('prd') if isinstance(payload, dict) else None
        if not isinstance(declared, dict) or declared.get('sha256') != inputs['prd']['sha256'] or declared.get('path') != inputs['prd']['path']:
            raise HandoffError('测试用例与当前 PRD 不一致')
        inputs['test_cases'] = actual
    return {'state': 'ready', 'inputs': inputs, 'version_link': 'verified' if bound else 'unverified',
            'note': '完整读取并核对业务、设计和实施范围后才能开发；文件门禁不等于批准'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    reg = sub.add_parser('register', help='登记本任务真实生成的文档，不生成内容')
    reg.add_argument('--task-dir', required=True)
    reg.add_argument('--task', required=True)
    reg.add_argument('--role', required=True, choices=ROLES)
    reg.add_argument('--file', required=True)
    reg.add_argument('--status', required=True, choices=sorted(STATES))
    reg.add_argument('--producer', required=True)
    res = sub.add_parser('resolve', help='只读定位前置文档与校验版本')
    res.add_argument('--task-dir', required=True)
    res.add_argument('--prd')
    res.add_argument('--design')
    res.add_argument('--only-prd', action='store_true', help='只定位 PRD，供测试用例设计使用，不要求技术方案')
    args = parser.parse_args()
    try:
        if args.command == 'register':
            result = register(args.task_dir, args.task, args.role, args.file, args.status, args.producer)
        else:
            result = resolve(args.task_dir, args.prd, args.design, args.only_prd)
    except HandoffError as exc:
        print(json.dumps({'state': 'invalid', 'error': str(exc)}, ensure_ascii=False))
        return 2
    except UnicodeError:
        print(json.dumps({'state': 'invalid', 'error': '任务文档不是有效 UTF-8'}, ensure_ascii=False))
        return 2
    except OSError:
        print(json.dumps({'state': 'invalid', 'error': '任务文件读写失败，请检查目标目录和权限'}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['state'] == 'needs_input' else 0


if __name__ == '__main__':
    sys.exit(main())
