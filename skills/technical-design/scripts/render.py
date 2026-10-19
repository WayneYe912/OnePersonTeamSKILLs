#!/usr/bin/env python3
"""Offline technical design HTML and nine deterministic diagram types."""
import argparse
import html
import json
import os
from pathlib import Path
import sys
import tempfile
import unicodedata
from contract import load, validate


def esc(value):
    return html.escape(str(value), quote=True)


def badge(state):
    css = {'已确认': 'confirmed', '建议': 'proposal', '待确认': 'pending'}[state]
    return f'<span class="badge {css}">{esc(state)}</span>'


def refs(item):
    return ' '.join(f'<a href="#source-{esc(sid)}">[{esc(sid)}]</a>' for sid in item['source_ids'])


def wrap(value, size=30):
    lines, word, length = [], '', 0
    for ch in value:
        count = 2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if ch == '\n' or length + count > size:
            lines.append(word)
            word, length = '', 0
            if ch == '\n':
                continue
        word += ch
        length += count
    if word or not lines:
        lines.append(word)
    return lines


def text(value, x, y, size=30, step=22):
    return ''.join(f'<text x="{x}" y="{y+i*step}">{esc(line)}</text>' for i, line in enumerate(wrap(value, size)))


def svg_start(graph, width, height):
    marker = 'arrow-' + graph['id']
    return (f'<svg role="img" aria-label="{esc(graph["title"])}" viewBox="0 0 {width} {height}" style="width:{width}px;max-width:none">'
            f'<title>{esc(graph["title"])}</title><defs><marker id="{esc(marker)}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#285e80"/></marker></defs>')


def box(label, x, y, width, height, kind='process'):
    if kind == 'store':
        shape = f'<path d="M{x} {y+12}Q{x+width/2} {y-8} {x+width} {y+12}V{y+height-12}Q{x+width/2} {y+height+8} {x} {y+height-12}Z"/>'
    elif kind == 'decision':
        shape = f'<path d="M{x+14} {y}H{x+width-14}L{x+width} {y+height/2}L{x+width-14} {y+height}H{x+14}L{x} {y+height/2}Z"/>'
    else:
        radius = height / 2 if kind == 'state' else 3 if kind == 'task' else 8
        shape = f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}"/>'
    return f'<g fill="#f0f6fa" stroke="#718fa4">{shape}</g>' + text(label, x+18, y+27, max(10, int((width-36)/8)))


def relation_rows(graph, nodes, edges, er=False):
    byid = {n['id']: n for n in nodes}
    rows, y = [], 20
    for i, edge in enumerate(edges):
        label = edge['label'] + (' [' + edge['cardinality'] + ']' if er else '') + '（' + edge['status'] + '）'
        height = max(106, 30 + 22*len(wrap(label, 30)), 36+22*max(len(wrap(byid[edge[k]]['label'], 22)) for k in ('from', 'to')))
        rows.append((i, edge, y, height, label))
        y += height + 24
    parts = [svg_start(graph, 880, y+10)]
    for i, edge, y, height, label in rows:
        left, right = byid[edge['from']], byid[edge['to']]
        parts.append(box(left['label'], 18, y, 220, height, left.get('kind', 'process')))
        parts.append(box(right['label'], 638, y, 220, height, right.get('kind', 'process')))
        ey = y + height - 20
        dashed = '' if edge['status'] == '已确认' else ' stroke-dasharray="6 4"'
        parts.append(f'<path d="M242 {ey}H633" fill="none" stroke="#285e80" stroke-width="2"{dashed} marker-end="url(#arrow-{esc(graph["id"])})"/>')
        parts.append(text(str(i+1)+'. '+label, 266, y+25, 40))
    parts.append('</svg>')
    return ''.join(parts)


def sequence(graph):
    people = graph['participants']
    positions = {p['id']: 130 + i*280 for i, p in enumerate(people)}
    width = max(560, len(people)*280+200)
    top = 40 + 24*max(len(wrap(p['label'], 22)) for p in people)
    rows, y = [], top+42
    for i, message in enumerate(graph['messages']):
        sx, tx = positions[message['from']], positions[message['to']]
        label = f'{i+1}. {message["kind"]}：{message["label"]}（{message["status"]}）'
        cap = 28 if sx == tx else max(24, int(abs(tx-sx)/8)-4)
        block_height = 22*len(wrap(label, cap))
        rows.append((message, y, label, cap, block_height))
        y += block_height + (72 if sx == tx else 48)
    parts = [svg_start(graph, width, y+30)]
    for p in people:
        x = positions[p['id']]
        parts.append(box(p['label'], x-110, 12, 220, top-12))
        parts.append(f'<path d="M{x} {top}V{y}" stroke="#8296a5" stroke-dasharray="5 6"/>')
    for msg, my, label, cap, block_height in rows:
        sx, tx = positions[msg['from']], positions[msg['to']]
        ey = my + block_height + 4
        parts.append(text(label, min(sx,tx)+12, my, cap))
        if sx == tx:
            parts.append(f'<path d="M{sx} {ey}h90v28h-90" stroke="#285e80" fill="none" marker-end="url(#arrow-{esc(graph["id"])})"/>')
        else:
            dashed = ' stroke-dasharray="6 4"' if msg['kind'] == 'response' else ''
            parts.append(f'<path d="M{sx} {ey}H{tx}" stroke="#285e80" fill="none" stroke-width="2"{dashed} marker-end="url(#arrow-{esc(graph["id"])})"/>')
    parts.append('</svg>')
    return ''.join(parts)


def topology(graph):
    nodes, edges = graph['nodes'], graph['edges']
    index = {node['id']: i for i, node in enumerate(nodes)}
    byid = {node['id']: node for node in nodes}
    positions, y = {}, 20
    for node in nodes:
        label = node['label'] + '（' + node['status'] + '）'
        if node.get('group'):
            label += '\n' + node['group']
        height = max(84, 35+22*len(wrap(label, 32)))
        positions[node['id']] = (y, height, label)
        y += height + 116
    extra = [edge for edge in edges if index[edge['to']] != index[edge['from']]+1]
    width = max(570, 430+210*len(extra))
    parts = [svg_start(graph, width, y-70)]
    lane_i = 0
    for edge in edges:
        sy, sh, _ = positions[edge['from']]
        ty, th, _ = positions[edge['to']]
        label = edge['label']+'（'+edge['status']+'）'
        dashed = '' if edge['status'] == '已确认' else ' stroke-dasharray="6 4"'
        if index[edge['to']] == index[edge['from']]+1:
            ey = sy+sh
            parts.append(f'<path d="M170 {ey}V{ty-3}" stroke="#285e80" fill="none"{dashed} marker-end="url(#arrow-{esc(graph["id"])})"/>')
            parts.append(text(label, 188, ey+26, 40))
        else:
            lane = 370+lane_i*210
            lane_i += 1
            start, end = sy+sh/2, ty+th/2
            parts.append(f'<path d="M330 {start}H{lane}V{end}H333" stroke="#285e80" fill="none"{dashed} marker-end="url(#arrow-{esc(graph["id"])})"/>')
            parts.append(text(label, lane+12, min(start,end)+45, 22))
    for node in nodes:
        ny, nh, label = positions[node['id']]
        parts.append(box(label, 10, ny, 320, nh, node['kind']))
    parts.append('</svg>')
    return ''.join(parts)


def swimlane(graph):
    groups = list(dict.fromkeys(n['group'] for n in graph['nodes']))
    xmap = {g: 20+i*300 for i,g in enumerate(groups)}
    positions, rows, y = {}, [], 68
    for node in graph['nodes']:
        label = node['label']+'（'+node['status']+'）'
        height = max(76, 35+22*len(wrap(label, 28)))
        positions[node['id']] = (xmap[node['group']], y, height)
        rows.append((node,label,y,height))
        y += height+110
    width = len(groups)*300+20
    parts = [svg_start(graph,width,y)]
    for group in groups:
        x = xmap[group]
        parts.append(f'<rect x="{x}" y="0" width="280" height="{y-10}" fill="#f8fafc" stroke="#d7e0e7"/>')
        parts.append(text(group,x+12,28,28))
    for edge in graph['edges']:
        sx,sy,sh = positions[edge['from']]
        tx,ty,th = positions[edge['to']]
        line_y = sy+sh+48
        if sx==tx:
            parts.append(f'<path d="M{sx+140} {sy+sh}V{ty-3}" fill="none" stroke="#285e80" marker-end="url(#arrow-{esc(graph["id"])})"/>')
            parts.append(text(edge['label']+'（'+edge['status']+'）',sx+146,sy+sh+25,28))
        else:
            parts.append(f'<path d="M{sx+140} {sy+sh}V{line_y}H{tx+140}V{ty-3}" fill="none" stroke="#285e80" marker-end="url(#arrow-{esc(graph["id"])})"/>')
            parts.append(text(edge['label']+'（'+edge['status']+'）',min(sx,tx)+148,line_y-14,max(24,int(abs(sx-tx)/8))))
    for node,label,ny,nh in rows:
        parts.append(box(label,xmap[node['group']]+12,ny,256,nh,node['kind']))
    parts.append('</svg>')
    return ''.join(parts)


def diagram(graph):
    names = {'architecture':'架构图','flow':'流程图','sequence':'时序图','er':'实体关系图','state':'状态图','dataflow':'数据流图','deployment':'部署图','dependency':'研发依赖图','swimlane':'泳道图'}
    parts = [f'<figure id="{esc(graph["id"])}"><h3>{esc(graph["title"])}</h3><p>{names[graph["type"]]} · {badge(graph["status"])} {refs(graph)}</p>']
    if graph['type'] == 'sequence':
        parts.append('<dl class="nodes">')
        for p in graph['participants']:
            parts.append(f'<dt>{esc(p["label"])} {badge(p["status"])}</dt><dd>{esc(p["detail"])} {refs(p)}</dd>')
        parts.append('</dl><div class="diagram-scroll" tabindex="0" aria-label="时序图，窄屏可横向滚动">'+sequence(graph)+'</div>')
    elif graph['type'] == 'er':
        for entity in graph['entities']:
            parts.append(f'<article class="entity"><h4>{esc(entity["label"])} {badge(entity["status"])}</h4>{refs(entity)}<dl>')
            for field in entity['fields']:
                parts.append(f'<dt><code>{esc(field["name"])}</code></dt><dd>{esc(field["data_type"])}；{esc(field["constraint"])}</dd>')
            parts.append('</dl></article>')
        parts.append('<div class="diagram-scroll" tabindex="0" aria-label="实体关系与基数，可横向滚动">'+relation_rows(graph, graph['entities'], graph['relations'], True)+'</div>')
    else:
        if graph['type'] == 'swimlane':
            groups = list(dict.fromkeys(n['group'] for n in graph['nodes']))
            for group in groups:
                parts.append(f'<section class="lane"><h4>{esc(group)}</h4><dl>')
                for node in graph['nodes']:
                    if node['group'] == group:
                        parts.append(f'<dt>{esc(node["label"])} {badge(node["status"])}</dt><dd>{esc(node["detail"])} {refs(node)}</dd>')
                parts.append('</dl></section>')
        else:
            parts.append('<dl class="nodes">')
            for node in graph['nodes']:
                group = ' · '+esc(node['group']) if node.get('group') else ''
                parts.append(f'<dt>{esc(node["label"])}{group} {badge(node["status"])}</dt><dd>{esc(node["detail"])} {refs(node)}</dd>')
            parts.append('</dl>')
        chart = swimlane(graph) if graph['type']=='swimlane' else topology(graph)
        parts.append('<p class="muted">节点按职责或状态组织，箭头标签给出动作和条件；窄屏可在图内横向滚动。</p><div class="diagram-scroll" tabindex="0" aria-label="研发图，可横向滚动">'+chart+'</div>')
    parts.append('<figcaption>'+esc(graph['caption'])+'<br>需求：'+', '.join(f'<a href="#{esc(v)}">{esc(v)}</a>' for v in graph['req_ids'])+'；设计：'+', '.join(f'<a href="#{esc(v)}">{esc(v)}</a>' for v in graph['design_ids'])+'</figcaption></figure>')
    return ''.join(parts)


CSS = """
:root{font-family:'PingFang SC','Microsoft YaHei',system-ui,sans-serif;background:#f3f6f9;color:#273643;font-size:16px;line-height:1.75;color-scheme:light}*{box-sizing:border-box}body{margin:0}main{max-width:1120px;margin:auto;padding:24px 18px 60px;background:white}h1{font-size:30px;line-height:1.35}h2{font-size:24px;line-height:1.4;margin-top:34px;border-bottom:1px solid #d7e0e7;padding-bottom:10px}h3{font-size:20px;line-height:1.5}h4{font-size:18px;line-height:1.5}p,li,dd{overflow-wrap:anywhere}a{color:#236088;text-underline-offset:3px}a:focus-visible,.diagram-scroll:focus-visible{outline:3px solid #2a6b97;outline-offset:3px}.badge{display:inline-block;padding:0 6px;border:1px solid;border-radius:3px;font-size:14px;white-space:nowrap}.confirmed{color:#235f8c;background:#eef5fb}.proposal{color:#815219;background:#fff7e8}.pending{color:#95463b;background:#fff0ee}.muted{font-size:14px;color:#546471}nav{padding:12px 16px;background:#f0f4f7;margin:22px 0}nav a{display:inline-block;padding:7px 10px}.original{white-space:pre-wrap;border:1px solid #d7e0e7;padding:12px 16px}.design,.requirement{border-top:2px solid #d7e0e7;padding:8px 0 18px;margin-top:20px}dl{margin:12px 0}dt{font-weight:600;margin-top:10px}dd{margin-left:0}.nodes dd{margin-bottom:8px}figure{border:1px solid #d7e0e7;border-radius:6px;margin:20px 0;padding:14px}figure h3{margin:0 0 10px}figcaption{font-size:14px;color:#4f6070;margin-top:14px}.diagram-scroll{max-width:100%;overflow-x:auto;margin:14px 0;padding:0 0 10px}svg{display:block}svg text{font-family:'PingFang SC','Microsoft YaHei',system-ui,sans-serif;font-size:14px;fill:#273643}.entity,.lane{border:1px solid #93a9ba;padding:12px 16px;margin:12px 0}.entity h4,.lane h4{margin:0 0 10px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f9;padding:14px;font-size:14px}code{font-family:ui-monospace,monospace;font-size:14px}.source{padding:12px 0;border-top:1px solid #d7e0e7}@media(min-width:768px){main{padding:36px 42px 60px}h1{font-size:36px}.entity dl{display:grid;grid-template-columns:230px minmax(0,1fr);gap:8px 14px}.entity dt{margin:0}}@media print{body{background:#fff}main{max-width:none;padding:0}nav{display:none}h2,h3{break-after:avoid}.diagram-scroll{overflow:visible}svg{width:100%!important;max-width:100%!important}.entity{break-inside:avoid}figure{break-inside:auto}a{color:inherit}@page{size:A4;margin:18mm}}
"""


def render(data):
    errors = validate(data)
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=False))
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
             f'<title>{esc(data["title"])}</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 fill=%27%23235f8c%27/%3E%3Cpath d=%27M8 8h16v16H8z%27 stroke=%27white%27 fill=%27none%27/%3E%3C/svg%3E"><style>{CSS}</style></head><body><main>',
             f'<header id="overview"><h1>{esc(data["title"])}</h1><p>文档状态：{esc(data["status"])}</p><p class="muted">蓝色为已确认，棕色为建议，红色为待确认。示意不等于已实现，确认不等于测试已执行。</p><div class="original">{esc(data["original_request"])}</div><p>{esc(data["summary"])}</p></header>',
             '<nav aria-label="目录"><a href="#traceability">需求与设计映射</a>'+''.join(f'<a href="#{esc(s["id"])}">{esc(s["title"])}</a>' for s in data['sections'])+'<a href="#sources">来源</a></nav>',
             '<section id="traceability"><h2>需求与设计映射</h2>']
    for req in data['requirements']:
        mapped = [d for d in data['designs'] if req['id'] in d['req_ids']]
        parts.append(f'<article class="requirement" id="{esc(req["id"])}"><h3>{esc(req["id"])} {esc(req["name"])}</h3>{badge(req["status"])} {refs(req)}<ul>'+''.join('<li>'+esc(t)+'</li>' for t in req['acceptance'])+'</ul><p>关联设计：'+', '.join(f'<a href="#{esc(d["id"])}">{esc(d["id"])}</a>' for d in mapped)+'</p></article>')
    for d in data['designs']:
        parts.append(f'<article class="design" id="{esc(d["id"])}"><h3>{esc(d["id"])} {esc(d["name"])}</h3>{badge(d["status"])} {refs(d)}<p>{esc(d["responsibility"])}</p><p>实施变更：{esc(d["changes"])}</p>')
        for key, label in [('inputs','输入'),('outputs','输出'),('failures','失败与恢复'),('tests','验证标准')]:
            parts.append(f'<h4>{label}</h4><ul>'+''.join('<li>'+esc(v)+'</li>' for v in d[key])+'</ul>')
        parts.append('</article>')
    parts.append('</section>')
    for section in data['sections']:
        parts.append(f'<section id="{esc(section["id"])}"><h2>{esc(section["title"])}</h2>')
        for block in section['blocks']:
            if block['type'] == 'paragraph':
                parts.append(f'<p>{badge(block["status"])} {esc(block["text"])} {refs(block)}</p>')
            elif block['type'] == 'code':
                parts.append(f'<p>{esc(block["language"])} {badge(block["status"])} {refs(block)}；仅展示，不执行</p><pre><code>{esc(block["text"])}</code></pre>')
            else:
                parts.append('<ul>'+''.join(f'<li>{badge(item["status"])} {esc(item["text"])} {refs(item)}</li>' for item in block['items'])+'</ul>')
        parts.extend(diagram(graph) for graph in data['diagrams'] if graph['section_id'] == section['id'])
        parts.append('</section>')
    parts.append('<section id="sources"><h2>信息来源</h2>')
    for source in data['sources']:
        parts.append(f'<article class="source" id="source-{esc(source["id"])}"><strong>{esc(source["id"])} {esc(source["title"])}</strong><p>{esc(source["note"])}</p>')
        if source.get('url'):
            parts.append(f'<a href="{esc(source["url"])}" rel="noopener noreferrer">{esc(source["url"])}</a>')
        parts.append('</article>')
    parts.append('</section><footer><p class="muted">未完成的业务、接口、容量及环境确认仍须评审；本方案不构成实现、生产变更或上线授权。</p></footer></main></body></html>')
    return ''.join(parts)


def save(path, content, force=False):
    path = Path(path)
    if path.suffix.lower() != '.html':
        raise ValueError('输出必须是 .html 文件')
    if not force:
        with path.open('x', encoding='utf-8', newline='') as stream:
            stream.write(content)
        return
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=str(path.parent), delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(content)
        os.replace(tmp, path)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('输入输出不能相同')
        save(args.output, render(load(args.input)), args.force)
    except (ValueError, OSError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'status':'rendered','output':str(args.output.resolve()),'note':'仍需语义与视觉核验'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
