#!/usr/bin/env python3
"""Strict design contract validation; Python 3.9+, standard library only."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

STATES = {'已确认', '建议', '待确认'}
TYPES = {'architecture', 'flow', 'sequence', 'er', 'state', 'dataflow', 'deployment', 'dependency', 'swimlane'}
SECTIONS = {'context', 'decisions', 'architecture', 'interfaces', 'data', 'reliability', 'security', 'capacity', 'testing', 'rollout', 'implementation', 'risks'}
ID = re.compile(r'[A-Za-z][A-Za-z0-9-]*\Z')
REQ = re.compile(r'REQ-[0-9]{3,}\Z')
DES = re.compile(r'DES-[0-9]{3,}\Z')


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('JSON 重复键：' + key)
            result[key] = value
        return result
    def reject(value):
        raise ValueError('不接受非标准 JSON 数值：' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique, parse_constant=reject)


def safe_url(url):
    if not isinstance(url, str) or re.search(r'[\s\x00-\x1f\x7f]', url):
        return False
    try:
        parsed = urlsplit(url)
        return bool(parsed.scheme in {'http', 'https'} and parsed.hostname and not parsed.username and not parsed.password)
    except ValueError:
        return False


def validate(data):
    errors = []
    def err(path, msg):
        errors.append({'path': path, 'message': msg})
    def obj(value, path):
        if not isinstance(value, dict):
            err(path, '必须是对象')
            return {}
        return value
    def text(value, path):
        if not isinstance(value, str) or not value.strip():
            err(path, '必须为非空字符串')
            return ''
        return value
    def array(value, path, nonempty=True):
        if not isinstance(value, list) or (nonempty and not value):
            err(path, '必须为' + ('非空' if nonempty else '') + '数组')
            return []
        return value
    def records(value, path, pattern=ID, nonempty=True):
        items = [obj(v, f'{path}[{i}]') for i, v in enumerate(array(value, path, nonempty))]
        ids = set()
        for i, item in enumerate(items):
            identifier = text(item.get('id'), f'{path}[{i}].id')
            if identifier and not pattern.fullmatch(identifier):
                err(f'{path}[{i}].id', '编号格式错误')
            if identifier in ids:
                err(f'{path}[{i}].id', '编号重复')
            ids.add(identifier)
        return items, ids
    root = obj(data, '$')
    for key in ('title', 'original_request', 'summary'):
        text(root.get(key), key)
    if root.get('status') not in {'探索草稿', '待评审', '已确认'}:
        err('status', '文档状态错误')
    sources, source_ids = records(root.get('sources'), 'sources')
    for i, source in enumerate(sources):
        for key in ('title', 'note'):
            text(source.get(key), f'sources[{i}].{key}')
        if 'url' in source and not safe_url(source['url']):
            err(f'sources[{i}].url', '来源链接只允许安全 HTTP(S) URL')
    def refs(item, key, allowed, path, nonempty=True):
        values = array(item.get(key), path + '.' + key, nonempty)
        for value in values:
            if not isinstance(value, str) or value not in allowed:
                err(path + '.' + key, '引用不存在或不是字符串')
        return [v for v in values if isinstance(v, str)]
    def evidence(item, path):
        state = item.get('status')
        if state not in STATES:
            err(path + '.status', '确认状态错误')
        source_refs = refs(item, 'source_ids', source_ids, path, False)
        if state == '已确认' and not source_refs:
            err(path + '.source_ids', '已确认内容必须有来源')
        if root.get('status') == '已确认' and state != '已确认':
            err(path + '.status', '已确认文档仍有未确认内容')
    def strings(item, key, path):
        for i, value in enumerate(array(item.get(key), path + '.' + key)):
            text(value, f'{path}.{key}[{i}]')
    requirements, req_ids = records(root.get('requirements'), 'requirements', REQ)
    for i, req in enumerate(requirements):
        path = f'requirements[{i}]'
        evidence(req, path)
        text(req.get('name'), path + '.name')
        strings(req, 'acceptance', path)
    designs, des_ids = records(root.get('designs'), 'designs', DES)
    covered = set()
    for i, design in enumerate(designs):
        path = f'designs[{i}]'
        evidence(design, path)
        for key in ('name', 'responsibility', 'changes'):
            text(design.get(key), path + '.' + key)
        covered.update(refs(design, 'req_ids', req_ids, path))
        for key in ('inputs', 'outputs', 'failures', 'tests'):
            strings(design, key, path)
    for missing in req_ids - covered:
        err('designs', '需求未映射到设计：' + missing)
    sections, section_ids = records(root.get('sections'), 'sections')
    for missing in SECTIONS - section_ids:
        err('sections', '缺少方案章节：' + missing)
    for i, section in enumerate(sections):
        path = f'sections[{i}]'
        text(section.get('title'), path + '.title')
        for j, block in enumerate(array(section.get('blocks'), path + '.blocks')):
            bpath = f'{path}.blocks[{j}]'
            block = obj(block, bpath)
            if block.get('type') in {'paragraph', 'code'}:
                evidence(block, bpath)
                text(block.get('text'), bpath + '.text')
                if block.get('type') == 'code':
                    text(block.get('language'), bpath + '.language')
            elif block.get('type') == 'list':
                for k, item in enumerate(array(block.get('items'), bpath + '.items')):
                    ipath = f'{bpath}.items[{k}]'
                    item = obj(item, ipath)
                    evidence(item, ipath)
                    text(item.get('text'), ipath + '.text')
            else:
                err(bpath + '.type', '内容块类型不支持')
    diagrams, diagram_ids = records(root.get('diagrams'), 'diagrams')
    kinds = {v.get('type') for v in diagrams if isinstance(v.get('type'), str)}
    if len(diagrams) < 3 or len(kinds) < 2 or 'architecture' not in kinds:
        err('diagrams', '默认至少三个图、两种类型，包含 architecture')
    for i, graph in enumerate(diagrams):
        path = f'diagrams[{i}]'
        evidence(graph, path)
        for key in ('title', 'caption'):
            text(graph.get(key), path + '.' + key)
        refs(graph, 'req_ids', req_ids, path)
        refs(graph, 'design_ids', des_ids, path)
        if graph.get('section_id') not in section_ids:
            err(path + '.section_id', '图指向不存在章节')
        kind = graph.get('type')
        if kind not in TYPES:
            err(path + '.type', '未知图种')
            continue
        node_key = 'participants' if kind == 'sequence' else 'entities' if kind == 'er' else 'nodes'
        edge_key = 'messages' if kind == 'sequence' else 'relations' if kind == 'er' else 'edges'
        nodes, node_ids = records(graph.get(node_key), path + '.' + node_key)
        if len(nodes) < 2:
            err(path + '.' + node_key, '至少两个实体或参与者')
        for j, node in enumerate(nodes):
            npath = f'{path}.{node_key}[{j}]'
            evidence(node, npath)
            text(node.get('label'), npath + '.label')
            if kind == 'er':
                field_names = set()
                for k, field in enumerate(array(node.get('fields'), npath + '.fields')):
                    fpath = f'{npath}.fields[{k}]'
                    field = obj(field, fpath)
                    for key in ('name', 'data_type', 'constraint'):
                        text(field.get(key), fpath + '.' + key)
                    name = field.get('name')
                    if isinstance(name, str):
                        if name in field_names:
                            err(fpath, '字段名重复')
                        field_names.add(name)
            else:
                text(node.get('detail'), npath + '.detail')
                if kind != 'sequence' and node.get('kind') not in {'actor', 'process', 'store', 'decision', 'state', 'task', 'service'}:
                    err(npath + '.kind', '节点形状类型错误')
                if 'group' in node or kind == 'swimlane':
                    text(node.get('group'), npath + '.group')
        edges = array(graph.get(edge_key), path + '.' + edge_key)
        adjacency = {value: set() for value in node_ids}
        touched = set()
        for j, edge in enumerate(edges):
            epath = f'{path}.{edge_key}[{j}]'
            edge = obj(edge, epath)
            evidence(edge, epath)
            text(edge.get('label'), epath + '.label')
            ends = []
            for key in ('from', 'to'):
                value = edge.get(key)
                if not isinstance(value, str) or value not in node_ids:
                    err(epath + '.' + key, '关系端点不存在')
                else:
                    ends.append(value)
                    touched.add(value)
            if len(ends) == 2:
                if ends[0] == ends[1] and kind != 'sequence':
                    err(epath, '关系自环须用单独步骤说明')
                adjacency[ends[0]].add(ends[1])
            if kind == 'sequence' and edge.get('kind') not in {'request', 'response', 'event', 'note'}:
                err(epath + '.kind', '消息类型错误')
            if kind == 'er' and edge.get('cardinality') not in {'1:1', '1:N', 'N:1', 'N:M'}:
                err(epath + '.cardinality', '关系基数错误')
        if node_ids - touched:
            err(path + '.' + node_key, '图存在孤立节点')
        if kind == 'dependency':
            visiting, visited = set(), set()
            def cycle(node):
                if node in visiting:
                    return True
                if node in visited:
                    return False
                visiting.add(node)
                if any(cycle(child) for child in adjacency[node]):
                    return True
                visiting.remove(node)
                visited.add(node)
                return False
            if any(cycle(node) for node in adjacency):
                err(path, '研发依赖不能成环')
    all_ids = ['overview', 'traceability', 'sources'] + list(req_ids) + list(des_ids) + list(section_ids) + list(diagram_ids) + ['source-' + v for v in source_ids]
    if len(all_ids) != len(set(all_ids)):
        err('id', '页面锚点编号冲突')
    return errors
