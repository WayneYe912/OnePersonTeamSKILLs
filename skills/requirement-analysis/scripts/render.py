#!/usr/bin/env python3
"""Validate analysis data and render an offline document. Python 3.9+, stdlib only."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import textwrap
import unicodedata
from urllib.parse import urlsplit

STATES = {"已确认", "建议", "待确认"}
SECTIONS = ("users", "scope", "solution", "rules", "data", "quality", "rollout", "risks", "questions")
IDENT = re.compile(r"[A-Za-z][A-Za-z0-9-]*\Z")
REQ = re.compile(r"REQ-[0-9]{3,}\Z")


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON 重复键：" + key)
            result[key] = value
        return result
    def finite(value):
        raise ValueError("不接受非标准 JSON 数值：" + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique, parse_constant=finite)


def validate(data):
    errors = []
    def fail(path, message):
        errors.append({"path": path, "message": message})
    def obj(value, path):
        if not isinstance(value, dict):
            fail(path, "必须为对象")
            return {}
        return value
    def string(value, path):
        if not isinstance(value, str) or not value.strip():
            fail(path, "必须为非空字符串")
            return ""
        return value
    def array(value, path, nonempty=True):
        if not isinstance(value, list) or (nonempty and not value):
            fail(path, "必须为" + ("非空" if nonempty else "") + "数组")
            return []
        return value
    def ids(items, path, pattern=IDENT):
        seen = set()
        for i, item in enumerate(items):
            item = obj(item, f"{path}[{i}]")
            value = string(item.get("id"), f"{path}[{i}].id")
            if value and not pattern.fullmatch(value):
                fail(f"{path}[{i}].id", "编号格式不正确")
            if value in seen:
                fail(f"{path}[{i}].id", "编号重复")
            seen.add(value)
        return seen
    root = obj(data, "$")
    for key in ("title", "original_request", "summary"):
        string(root.get(key), key)
    if root.get("status") not in {"探索草稿", "待评审", "已确认"}:
        fail("status", "文档状态不正确")
    sources = array(root.get("sources"), "sources")
    source_ids = ids(sources, "sources")
    for i, source in enumerate(sources):
        source = obj(source, f"sources[{i}]")
        for key in ("title", "note"):
            string(source.get(key), f"sources[{i}].{key}")
        if "url" in source:
            url = string(source["url"], f"sources[{i}].url")
            try:
                parts = urlsplit(url)
                valid = (parts.scheme in {"https", "http"} and parts.hostname
                         and not parts.username and not parts.password
                         and not re.search(r"[\s\x00-\x1f\x7f]", url))
            except ValueError:
                valid = False
            if not valid:
                fail(f"sources[{i}].url", "必须是安全的 HTTP(S) 来源链接")
    def evidence(item, path):
        state = item.get("status")
        if state not in STATES:
            fail(path + ".status", "状态必须是已确认、建议或待确认")
        refs = array(item.get("source_ids"), path + ".source_ids", False)
        for ref in refs:
            if not isinstance(ref, str) or ref not in source_ids:
                fail(path + ".source_ids", "引用不存在的来源")
        if state == "已确认" and not refs:
            fail(path + ".source_ids", "已确认内容必须标明来源")
        if root.get("status") == "已确认" and state != "已确认":
            fail(path + ".status", "已确认文档不能包含未确认内容")
    sections = array(root.get("sections"), "sections")
    section_ids = ids(sections, "sections")
    for missing in set(SECTIONS) - section_ids:
        fail("sections", "缺少章节：" + missing)
    for i, section in enumerate(sections):
        section = obj(section, f"sections[{i}]")
        string(section.get("title"), f"sections[{i}].title")
        for j, block in enumerate(array(section.get("blocks"), f"sections[{i}].blocks")):
            path = f"sections[{i}].blocks[{j}]"
            block = obj(block, path)
            if block.get("type") == "paragraph":
                string(block.get("text"), path + ".text")
                evidence(block, path)
            elif block.get("type") == "list":
                for k, item in enumerate(array(block.get("items"), path + ".items")):
                    ipath = f"{path}.items[{k}]"
                    item = obj(item, ipath)
                    string(item.get("text"), ipath + ".text")
                    evidence(item, ipath)
            else:
                fail(path + ".type", "只支持 paragraph 或 list")
    requirements = array(root.get("requirements"), "requirements")
    req_ids = ids(requirements, "requirements", REQ)
    for i, item in enumerate(requirements):
        path = f"requirements[{i}]"
        item = obj(item, path)
        evidence(item, path)
        for key in ("name", "priority_reason", "actor", "precondition", "trigger", "response"):
            string(item.get(key), path + "." + key)
        if item.get("priority") not in {"P0", "P1", "P2"}:
            fail(path + ".priority", "优先级只支持 P0、P1、P2")
        if item.get("priority_status") not in STATES:
            fail(path + ".priority_status", "必须说明优先级确认状态")
        if item.get("priority_status") == "已确认" and not item.get("source_ids"):
            fail(path + ".priority_status", "已确认优先级必须有来源")
        if root.get("status") == "已确认" and item.get("priority_status") != "已确认":
            fail(path + ".priority_status", "文档仍有未确认的优先级")
        for key in ("rules", "exceptions"):
            for j, value in enumerate(array(item.get(key), path + "." + key)):
                string(value, f"{path}.{key}[{j}]")
        for j, case in enumerate(array(item.get("acceptance"), path + ".acceptance")):
            cpath = f"{path}.acceptance[{j}]"
            case = obj(case, cpath)
            for key in ("given", "when", "then"):
                string(case.get(key), cpath + "." + key)
    visuals = array(root.get("visuals"), "visuals")
    visual_ids = ids(visuals, "visuals")
    if len(visuals) < 2:
        fail("visuals", "默认图文契约需要至少两个互补图")
    for i, visual in enumerate(visuals):
        path = f"visuals[{i}]"
        visual = obj(visual, path)
        for key in ("title", "caption"):
            string(visual.get(key), path + "." + key)
        evidence(visual, path)
        for rid in array(visual.get("req_ids"), path + ".req_ids"):
            if not isinstance(rid, str) or rid not in req_ids:
                fail(path + ".req_ids", "图引用不存在的需求")
        if visual.get("type") == "flow":
            nodes = array(visual.get("nodes"), path + ".nodes")
            node_ids = ids(nodes, path + ".nodes")
            if len(nodes) < 2:
                fail(path + ".nodes", "流程至少需要两个节点")
            for j, node in enumerate(nodes):
                node = obj(node, f"{path}.nodes[{j}]")
                string(node.get("label"), f"{path}.nodes[{j}].label")
                evidence(node, f"{path}.nodes[{j}]")
            connected = set()
            for j, edge in enumerate(array(visual.get("edges"), path + ".edges")):
                epath = f"{path}.edges[{j}]"
                edge = obj(edge, epath)
                string(edge.get("label"), epath + ".label")
                evidence(edge, epath)
                for key in ("from", "to"):
                    value = edge.get(key)
                    if not isinstance(value, str) or value not in node_ids:
                        fail(epath + "." + key, "连线端点不存在")
                    elif value == edge.get("from") == edge.get("to"):
                        fail(epath, "自环请用单独的状态说明表达")
                    else:
                        connected.add(value)
            if node_ids - connected:
                fail(path + ".nodes", "存在没有连线的孤立节点")
        elif visual.get("type") == "wireframe":
            string(visual.get("screen_title"), path + ".screen_title")
            for j, field in enumerate(array(visual.get("fields"), path + ".fields")):
                field = obj(field, f"{path}.fields[{j}]")
                for key in ("label", "value", "note"):
                    string(field.get(key), f"{path}.fields[{j}].{key}")
            for j, action in enumerate(array(visual.get("actions"), path + ".actions")):
                string(action, f"{path}.actions[{j}]")
        else:
            fail(path + ".type", "只支持 flow 或 wireframe")
    global_ids = ["overview", "requirements", "sources"]
    for value in section_ids | visual_ids | req_ids:
        if value in global_ids:
            fail("id", "章节、需求或图编号与页面锚点冲突：" + value)
        global_ids.append(value)
    if len(section_ids | visual_ids | req_ids) != len(section_ids) + len(visual_ids) + len(req_ids):
        fail("id", "章节、需求与图编号不能相同")
    return errors


def esc(value):
    return html.escape(str(value), quote=True)


def badge(state):
    cls = {"已确认": "confirmed", "建议": "proposal", "待确认": "pending"}.get(state, "pending")
    return f'<span class="badge {cls}">{esc(state)}</span>'


def citations(item):
    return ' '.join(f'<a class="ref" href="#source-{esc(sid)}">[{esc(sid)}]</a>'
                    for sid in item.get("source_ids", []))


def tagged(item):
    return f'{badge(item["status"])} {esc(item["text"])} {citations(item)}'


def wrap(value, capacity):
    lines, current, used = [], "", 0
    for ch in value:
        weight = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if ch == '\n' or used + weight > capacity:
            lines.append(current)
            current, used = "", 0
            if ch == '\n':
                continue
        current += ch
        used += weight
    if current or not lines:
        lines.append(current)
    return lines


def svg_lines(value, x, y, capacity, step=24):
    return ''.join(f'<text x="{x}" y="{y + i * step}">{esc(line)}</text>'
                   for i, line in enumerate(wrap(value, capacity)))


def flow(visual):
    nodes, edges = visual["nodes"], visual["edges"]
    geom, y = {}, 32
    positions = {node['id']: i for i, node in enumerate(nodes)}
    routed = [edge for edge in edges if positions[edge['to']] != positions[edge['from']] + 1]
    for node in nodes:
        height = max(86, 52 + 24 * len(wrap(node["label"], 28)))
        geom[node["id"]] = (y, height)
        y += height + 100
    lane_width = 208
    width, height = max(480, 360 + lane_width * len(routed)), y - 50
    marker = "arrow-" + visual["id"]
    parts = [f'<svg class="flow" role="img" aria-labelledby="title-{esc(visual["id"])}" viewBox="0 0 {width} {height}" style="width:{width}px;max-width:none">',
             f'<title id="title-{esc(visual["id"])}">{esc(visual["title"])}</title>',
             f'<defs><marker id="{esc(marker)}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#345c7d"/></marker></defs>']
    routed_index = 0
    for edge in edges:
        start, sh = geom[edge["from"]]
        end, eh = geom[edge["to"]]
        dashed = ' stroke-dasharray="6 5"' if edge["status"] != "已确认" else ''
        label = edge["label"] + "（" + edge["status"] + "）"
        if positions[edge['to']] == positions[edge['from']] + 1:
            sy, ey = start + sh, end
            parts.append(f'<path d="M162 {sy}V{ey-3}" fill="none" stroke="#345c7d" stroke-width="2"{dashed} marker-end="url(#{esc(marker)})"/>')
            ly = sy + 25
            parts.append(svg_lines(label, 178, ly, 24))
            continue
        sy, ey, lane = start + sh / 2, end + eh / 2, 342 + routed_index * lane_width
        routed_index += 1
        parts.append(f'<path d="M302 {sy}H{lane}V{ey}H306" fill="none" stroke="#345c7d" stroke-width="2"{dashed} marker-end="url(#{esc(marker)})"/>')
        lines = wrap(label, 22)
        ly = (sy + ey) / 2 - 12 * (len(lines) - 1)
        parts.append(f'<rect x="{lane + 8}" y="{ly - 20}" width="{lane_width - 16}" height="{len(lines)*24+8}" fill="#fff"/>')
        parts.append(svg_lines(label, lane + 12, ly, 22))
    for node in nodes:
        ny, nh = geom[node["id"]]
        fill = {"已确认": "#eef5fb", "建议": "#fff7e8", "待确认": "#fff0ee"}[node["status"]]
        parts.append(f'<rect x="22" y="{ny}" width="280" height="{nh}" rx="8" fill="{fill}" stroke="#8796a3"/>')
        parts.append(svg_lines(node["label"], 38, ny + 29, 28))
        parts.append(f'<text x="38" y="{ny + nh - 15}" class="state">{esc(node["status"])}</text>')
    parts.append('</svg>')
    return '<div class="diagram-scroll" tabindex="0" aria-label="流程图，可横向滚动">' + ''.join(parts) + '</div>'


def diagram(visual):
    result = f'<figure id="{esc(visual["id"])}"><h3>{esc(visual["title"])}</h3>{badge(visual["status"])} {citations(visual)}'
    if visual["type"] == "flow":
        result += flow(visual)
    else:
        result += '<div class="wireframe"><p class="muted">低保真示意，无交互；显示值仅作示例</p>'
        result += f'<h4>{esc(visual["screen_title"])}</h4>'
        for field in visual["fields"]:
            result += f'<div class="field"><strong>{esc(field["label"])}</strong><div class="field-value">{esc(field["value"])}</div><p class="muted">{esc(field["note"])}</p></div>'
        result += '<div class="actions">' + ''.join(f'<span>{esc(action)}</span>' for action in visual["actions"]) + '</div></div>'
    result += '<figcaption>' + esc(visual["caption"]) + ' 关联：' + ', '.join(
        f'<a href="#{esc(rid)}">{esc(rid)}</a>' for rid in visual["req_ids"]) + '</figcaption></figure>'
    return result


CSS = """
:root{color-scheme:light;font-family:'PingFang SC','Microsoft YaHei',system-ui,sans-serif;color:#263445;background:#f4f7fa;font-size:16px;line-height:1.75}
*{box-sizing:border-box}body{margin:0}main{max-width:1080px;margin:0 auto;background:#fff;padding:24px 18px 60px}h1{font-size:30px;line-height:1.35;margin:8px 0 18px}h2{font-size:24px;line-height:1.4;border-bottom:1px solid #dce3eb;padding-bottom:12px;margin-top:42px}h3{font-size:20px;line-height:1.5}h4{font-size:18px}p,li,dd{overflow-wrap:anywhere}p{margin:12px 0}a{color:#1f5f94;text-decoration:underline;text-underline-offset:3px}a:focus-visible,.diagram-scroll:focus-visible{outline:3px solid #2870a5;outline-offset:3px}nav{background:#eef3f7;padding:14px 18px;margin:26px 0}nav ul{display:flex;gap:8px 24px;flex-wrap:wrap;list-style:none;padding:0;margin:0}nav a{display:inline-block;padding:8px 0}.muted{color:#5b6571;font-size:14px}.badge{display:inline-block;padding:1px 7px;font-size:14px;border:1px solid;border-radius:4px;white-space:nowrap}.confirmed{color:#235f8c;background:#eef5fb}.proposal{color:#875716;background:#fff7e8}.pending{color:#98493e;background:#fff0ee}.ref{font-size:14px}.original{border:1px solid #dce3eb;padding:14px 18px;margin:16px 0;white-space:pre-wrap}.requirement{border-top:2px solid #dce3eb;margin:26px 0;padding:8px 0 22px}dl{display:grid;grid-template-columns:1fr;gap:0;margin:16px 0}dt{font-weight:600;margin-top:10px}dd{margin:0}.acceptance{background:#f4f7fa;padding:12px 16px;margin:10px 0}.acceptance p{margin:5px 0}figure{margin:24px 0;border:1px solid #dce3eb;padding:14px;border-radius:8px}figure h3{margin:0 0 10px}figcaption{font-size:14px;margin-top:16px;color:#4b5866}.diagram-scroll{overflow-x:auto;width:100%;margin-top:20px;padding-bottom:12px}.flow{display:block;max-height:none}.flow text{font-family:'PingFang SC','Microsoft YaHei',system-ui,sans-serif;font-size:16px;fill:#263445}.flow .state{font-size:14px;fill:#566270}.wireframe{border:2px solid #8796a3;max-width:620px;margin:20px auto;padding:18px}.field{margin:18px 0}.field-value{border:1px solid #aeb9c6;padding:10px 12px;background:#f8fafc;margin-top:6px;overflow-wrap:anywhere}.actions{display:flex;gap:12px;flex-wrap:wrap}.actions span{border:1px solid #345c7d;color:#345c7d;padding:8px 16px}.source{border-top:1px solid #dce3eb;padding:12px 0}.source p{margin:5px 0}
@media(min-width:768px){main{padding:40px 56px 72px}h1{font-size:36px}dl{grid-template-columns:110px minmax(0,1fr);gap:10px 16px}dt{margin:0}}
@media print{body{background:#fff}main{max-width:none;padding:0}nav{display:none}h2,h3{break-after:avoid}a{color:inherit}figure{break-inside:avoid}.diagram-scroll{overflow:visible}.flow{width:100%!important;max-width:100%!important}p,li{orphans:3;widows:3}@page{size:A4;margin:18mm}}
"""


def render(data):
    problems = validate(data)
    if problems:
        raise ValueError(json.dumps(problems, ensure_ascii=False))
    nav = [('overview', '需求概览')] + [(s['id'], s['title']) for s in data['sections'][:3]]
    nav += [('requirements', '功能与验收')] + [(s['id'], s['title']) for s in data['sections'][3:]] + [('sources', '信息来源')]
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f'<title>{esc(data["title"])}</title>',
             '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%276%27 fill=%27%23235f8c%27/%3E%3Cpath d=%27M9 9h14M9 16h14M9 23h9%27 stroke=%27white%27 stroke-width=%272%27/%3E%3C/svg%3E">',
             '<style>' + CSS + '</style></head><body><main>',
             f'<header id="overview"><h1>{esc(data["title"])}</h1><p>文档状态：{esc(data["status"])}</p>',
             '<p class="muted">蓝色为已确认，棕色为建议，红色为待确认。建议与示意不代表已批准方案。</p>',
             f'<div class="original"><strong>原始需求</strong><br>{esc(data["original_request"])}</div><p>{esc(data["summary"])}</p></header>',
             '<nav aria-label="文档目录"><ul>' + ''.join(f'<li><a href="#{esc(key)}">{esc(title)}</a></li>' for key, title in nav) + '</ul></nav>']
    def requirements():
        parts.append('<section id="requirements"><h2>功能与验收</h2>')
        for req in data['requirements']:
            parts.append(f'<article class="requirement" id="{esc(req["id"])}"><h3>{esc(req["id"])} {esc(req["name"])}</h3>{badge(req["status"])} {citations(req)}')
            parts.append(f'<p>优先级：{esc(req["priority"])} {badge(req["priority_status"])}<br>{esc(req["priority_reason"])}</p><dl>')
            for key, label in [('actor', '使用角色'), ('precondition', '前提'), ('trigger', '触发操作'), ('response', '系统响应')]:
                parts.append(f'<dt>{label}</dt><dd>{esc(req[key])}</dd>')
            parts.append('</dl>')
            for key, label in [('rules', '业务规则'), ('exceptions', '异常与恢复')]:
                parts.append(f'<h4>{label}</h4><ul>' + ''.join(f'<li>{esc(t)}</li>' for t in req[key]) + '</ul>')
            parts.append('<h4>验收标准</h4>')
            for case in req['acceptance']:
                parts.append('<div class="acceptance">' + ''.join(f'<p><strong>{label}</strong> {esc(case[key])}</p>' for key, label in [('given', '给定'), ('when', '当'), ('then', '则')]) + '</div>')
            parts.append('</article>')
        parts.append('</section>')
    inserted = False
    for section in data['sections']:
        parts.append(f'<section id="{esc(section["id"])}"><h2>{esc(section["title"])}</h2>')
        for block in section['blocks']:
            if block['type'] == 'paragraph':
                parts.append('<p>' + tagged(block) + '</p>')
            else:
                parts.append('<ul>' + ''.join('<li>' + tagged(item) + '</li>' for item in block['items']) + '</ul>')
        if section['id'] == 'solution':
            parts.extend(diagram(v) for v in data['visuals'])
        parts.append('</section>')
        if section['id'] == 'solution':
            requirements()
            inserted = True
    if not inserted:
        requirements()
    parts.append('<section id="sources"><h2>信息来源</h2>')
    for source in data['sources']:
        parts.append(f'<article class="source" id="source-{esc(source["id"])}"><strong>{esc(source["id"])} {esc(source["title"])}</strong><p>{esc(source["note"])}</p>')
        if source.get('url'):
            parts.append(f'<p><a href="{esc(source["url"])}" rel="noopener noreferrer">{esc(source["url"])}</a></p>')
        parts.append('</article>')
    parts.append('</section><footer><p class="muted">规则与验收的状态以条目为准。开始研发前须确认阻断事项；本文件不等于实施或上线批准。</p></footer></main></body></html>')
    return ''.join(parts)


def save(path, content, force=False):
    path = Path(path)
    if path.suffix.lower() != '.html':
        raise ValueError('输出必须使用 .html 扩展名')
    if not force:
        with path.open('x', encoding='utf-8', newline='') as stream:
            stream.write(content)
        return
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                                         dir=str(path.parent), delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, path)
    finally:
        if temp and temp.exists():
            temp.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='UTF-8 需求分析 JSON')
    parser.add_argument('--output', type=Path, required=True, help='离线 HTML 的目标路径')
    parser.add_argument('--force', action='store_true', help='显式允许更新目标文件')
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('输入与输出不能是同一文件')
        content = render(load(args.input))
        save(args.output, content, args.force)
    except (OSError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'output': str(args.output.resolve()), 'status': 'rendered',
                      'note': '结构已验证，视觉与业务语义仍须检查'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
