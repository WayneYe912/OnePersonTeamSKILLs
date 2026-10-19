#!/usr/bin/env python3
"""Read-only structural validation and advisory Chinese writing checks."""
import argparse
import json
from pathlib import Path
import re
import sys
from render import load, validate

PATTERNS = {
    'half_punctuation': re.compile(r'[\u4e00-\u9fff][,;:]|[\u4e00-\u9fff]\.(?![0-9])'),
    'empty_commentary': re.compile(r'值得深思|值得关注|不禁让人思考|引人深思|发人深省|至关重要'),
    'nominalized_action': re.compile(r'进行.{0,8}(操作|配置|处理|验证)|实现.{0,8}的(提升|保存|优化)'),
    'abstract_jargon': re.compile(r'全方位赋能|全面赋能|增长势能|协作势能|底层逻辑'),
    'vague_reference': re.compile(r'前者|后者|上述系统'),
    'contrast_formula': re.compile(r'不是[^。\n]{1,30}(而是|，是)|你以为[^。\n]{1,30}其实|看似[^。\n]{1,30}实则'),
    'dash': re.compile(r'——'),
}
PROTECTED = re.compile(r'```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`]*`|https?://\S+|“[^”]*”|「[^」]*」')


def strings(data, path='$'):
    if isinstance(data, dict):
        for key, value in data.items():
            # Metadata, original quotations and program identifiers are not prose.
            if key in {'original_request', 'url', 'id', 'source_ids', 'req_ids', 'from', 'to', 'status', 'priority', 'priority_status', 'type'}:
                continue
            yield from strings(value, path + '.' + key)
    elif isinstance(data, list):
        for i, value in enumerate(data):
            yield from strings(value, f'{path}[{i}]')
    elif isinstance(data, str):
        yield path, data


def writing_findings(data):
    findings = []
    for path, value in strings(data):
        text = PROTECTED.sub(lambda m: ' ' * len(m.group()), value)
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({'path': path, 'check': name, 'snippet': match.group(),
                                 'note': '仅提示，核对上下文与受保护内容后再修改'})
        for segment in re.split(r'[，、；：。！？,;:.!?\n]', text):
            if len(re.findall(r'[\u4e00-\u9fff]', segment)) >= 28:
                findings.append({'path': path, 'check': 'long_without_pause',
                                 'snippet': segment[:80], 'note': '先检查自然停顿，不为口语化拆严谨长句'})
        sentences = [s.strip() for s in re.split(r'[。！？\n]', text) if s.strip()]
        for previous, current in zip(sentences, sentences[1:]):
            if previous == current:
                findings.append({'path': path, 'check': 'exact_repetition', 'snippet': current,
                                 'note': '核对是否真有重复，不能删除独立规则'})
    return findings


def check(data):
    errors = validate(data)
    return {'passed': not errors, 'errors': errors,
            'writing_advice': writing_findings(data),
            'limits': ['结构检查不核验来源是否支持事实', '表达检查是启发式提示，不自动改稿',
                       '尚未验证业务语义等价、验收充分性和实际视觉布局']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        report = check(load(args.input))
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
