#!/usr/bin/env python3
"""Read-only structure checks and advisory prose scan. Python 3.9+ stdlib."""
import argparse
import json
from pathlib import Path
import re
import sys
from contract import load, validate

PATTERNS = {
    'half_punctuation': re.compile(r'[\u4e00-\u9fff][,;:]|[\u4e00-\u9fff]\.(?![0-9])'),
    'empty_commentary': re.compile(r'值得深思|至关重要|全方位赋能|全链路闭环'),
    'nominalized_action': re.compile(r'进行.{0,8}(验证|处理|配置|操作)|实现对.{0,8}的'),
    'vague_reference': re.compile(r'前者|后者|上述系统'),
}
PROTECTED = re.compile(r'`[^`]*`|https?://\S+|“[^”]*”|「[^」]*」')


def prose(value, path='$'):
    if isinstance(value, dict):
        if value.get('type') == 'code':
            return
        for key, child in value.items():
            if key in {'original_request','id','req_ids','design_ids','source_ids','url','from','to','kind','type','status','section_id','name','data_type','constraint'}:
                continue
            yield from prose(child, path+'.'+key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from prose(child, f'{path}[{i}]')
    elif isinstance(value, str):
        yield path, value


def advice(data):
    result = []
    for path, value in prose(data):
        clean = PROTECTED.sub(lambda m: ' '*len(m.group()), value)
        for key, pattern in PATTERNS.items():
            for match in pattern.finditer(clean):
                result.append({'path':path,'check':key,'snippet':match.group(),'note':'仅提示，结合原文和技术契约判断，不自动改稿'})
    return result


def check(data):
    errors = validate(data)
    return {'passed':not errors,'errors':errors,'writing_advice':advice(data),
            'limits':['不判断来源是否支持事实','不证明实现、性能、测试或业务语义正确','不替代实际渲染与打印检查']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        report = check(load(args.input))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'passed':False,'error':str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
