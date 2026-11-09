#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GNS3 拓扑自动搭建工具（仅 python 标准库，无第三方依赖）。

典型流程：AI 解析拓扑图片 -> 生成 topo.json -> 本脚本建项目/节点/链路/启动 ->
输出 lab_config.json（设备名 -> telnet 端口映射），供 connect.py / deploy.py 直接接管。

用法（把 <API> 换成你的 GNS3 服务器地址，如 http://<GNS3服务器IP>/v2 或 :3080）：
  python topo_build.py list-projects  --api <API>
  python topo_build.py list-templates --api <API>
  python topo_build.py build --api <API> --topo topo.json [--start] [--out lab_config.json]
  python topo_build.py status --api <API> --project <项目名>

topo.json 格式（名称完全自定义，画布设备名与此严格一致）：
{
  "project": "my-lab",
  "nodes": [
    {"name": "<设备名>", "template": "<模板名>", "x": 0, "y": 0}
  ],
  "links": [
    {"a": "<设备A>", "a_port": "<接口>", "b": "<设备B>", "b_port": "<接口>"}
  ]
}

实现要点（实测 GNS3 2.2.52）：
- 所有节点一律走 POST /projects/{pid}/nodes 全属性创建：先从模板 GET 属性、
  剔除模板级字段后作为 properties 传入。这样**设备名严格按 topo.json 命名**，
  不会被模板的 default_name_format 自动编号覆盖（模板实例化端点有此坑，勿用）。
- builtin 节点（vpcs/cloud/nat/ethernet_switch 等）无 properties，同样走 POST /nodes，
  必须显式给 node_type + compute_id="local"。
- 防重名：同名项目非空直接停止，绝不覆盖现有项目；链路幂等，重复执行安全。
- **建后校验（必须）**：每次建节点后核对返回的 name 与 symbol：
  * name 不符 = 项目内有同名残留（GNS3 同项目内重名自动 +1，R2 会变 R3），直接报错停止；
  * symbol 不符 = 图标掉成默认 computer.svg（symbol 是节点级字段、不在 properties 里），
    自动用 PUT 补上模板图标（PUT symbol 可靠；PUT name 不可靠，见 references/17）。

作者 / Author: 白虬髯 (Bai Qiuran)
许可 / License: Attribution-NonCommercial (署名-非商业性使用；禁止商用；二创须保留原作者署名，详见 LICENSE)
版本 / Version: v1.0
"""
import argparse, json, time, urllib.request, urllib.error

BUILTIN_TYPES = {"vpcs", "cloud", "nat", "ethernet_switch", "ethernet_hub",
                 "frame_relay_switch", "atm_switch"}
# 模板级字段，不进节点 properties
TEMPLATE_ONLY_KEYS = {"template_id", "template_type", "builtin", "category",
                      "compute_id", "name", "default_name_format", "symbol", "usage"}


class Gns3:
    def __init__(self, api):
        self.api = api.rstrip('/')

    def req(self, method, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        r = urllib.request.Request(self.api + path, data=body, method=method)
        if body:
            r.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                txt = resp.read().decode()
                return json.loads(txt) if txt else {}
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'{method} {path} -> HTTP {e.code}: {e.read().decode()[:400]}')
        except urllib.error.URLError as e:
            raise RuntimeError(f'{method} {path} -> 连接失败: {e.reason}（检查 API 地址/网络）')


def parse_port(p):
    """'G0/0' -> 0 ; 'eth0' -> 0"""
    return int(str(p).split('/')[-1].replace('eth', ''))


def build(g, topo, do_start):
    name = topo['project']
    # 0) 防重名：存在且非空 -> 停；空 -> 复用
    projs = g.req('GET', '/projects')
    proj = next((p for p in projs if p['name'] == name), None)
    if proj:
        pid = proj['project_id']
        if g.req('GET', f'/projects/{pid}/nodes'):
            raise SystemExit(f'项目 {name} 已存在且非空，停止（绝不覆盖他人拓扑）')
        print(f'[i] 复用已有空项目 {name} | {pid}')
    else:
        pid = g.req('POST', '/projects', {'name': name})['project_id']
        print(f'[+] 项目已创建: {name} | {pid}')
    g.req('POST', f'/projects/{pid}/open')

    # 1) 模板表（先自检镜像，缺失直接停）
    tpls = check_templates(g, topo)
    role = {}  # 逻辑名 -> node_id
    for nd in topo['nodes']:
        tname = nd['template']
        t = tpls[tname]
        payload = {'name': nd['name'], 'node_type': t['template_type'],
                   'compute_id': 'local', 'x': nd.get('x', 0), 'y': nd.get('y', 0)}
        # symbol 是节点级字段（不在 properties 内），必须显式带上，否则图标掉成默认 computer.svg
        if t.get('symbol'):
            payload['symbol'] = t['symbol']
        if t['template_type'] not in BUILTIN_TYPES:
            full = g.req('GET', f"/templates/{t['template_id']}")
            payload['properties'] = {k: v for k, v in full.items() if k not in TEMPLATE_ONLY_KEYS}
        n = g.req('POST', f'/projects/{pid}/nodes', payload)
        role[nd['name']] = n['node_id']
        if n['name'] != nd['name']:
            raise SystemExit(f"设备名未受控: 期望 {nd['name']} 实际 {n['name']} "
                             f"（项目内可能有同名残留节点，先清空或换项目名）")
        # 图标兜底：若服务器仍给了默认图标，用 PUT 补上（PUT symbol 可靠）
        if t.get('symbol') and n.get('symbol') != t['symbol']:
            g.req('PUT', f"/projects/{pid}/nodes/{n['node_id']}", {'symbol': t['symbol']})
        print(f"[+] 节点 {nd['name']} ({tname}) icon={t.get('symbol', '-')}")

    # 2) 链路（幂等）
    have = {frozenset((x['node_id'], x['adapter_number']) for x in lk['nodes'])
            for lk in g.req('GET', f'/projects/{pid}/links')}
    for lk in topo['links']:
        ap, bp = parse_port(lk['a_port']), parse_port(lk['b_port'])
        key = frozenset([(role[lk['a']], ap), (role[lk['b']], bp)])
        if key in have:
            print(f"[=] 链路已存在: {lk['a']} {lk['a_port']} <-> {lk['b']} {lk['b_port']}")
            continue
        g.req('POST', f'/projects/{pid}/links', {'nodes': [
            {'node_id': role[lk['a']], 'adapter_number': ap, 'port_number': 0},
            {'node_id': role[lk['b']], 'adapter_number': bp, 'port_number': 0}]})
        print(f"[+] 链路 {lk['a']} {lk['a_port']} <-> {lk['b']} {lk['b_port']}")

    # 3) 启动
    if do_start:
        g.req('POST', f'/projects/{pid}/nodes/start')
        print('[+] 全部节点启动指令已下发（RGOS 内核引导约需 30-60s）')
        time.sleep(8)
    return pid


def status(g, project):
    pid = next(p['project_id'] for p in g.req('GET', '/projects') if p['name'] == project)
    g.req('POST', f'/projects/{pid}/open')
    out = {'project': project, 'project_id': pid, 'api_base': g.api, 'devices': {}}
    for n in g.req('GET', f'/projects/{pid}/nodes'):
        out['devices'][n['name']] = {
            'port': n.get('console'), 'node_type': n['node_type'], 'status': n.get('status')}
        print(f"{n['name']:10s} console={n.get('console')} {n.get('console_type')} status={n.get('status')}")
    return out


def check_templates(g, topo):
    """镜像/图标自检：核对拓扑所需模板（含其镜像文件与 symbol 图标）是否都齐。

    返回模板表；缺模板或缺镜像/图标时 raise 并给出明确清单，让用户在 GNS3 导入后再重试。
    """
    tpls = {t['name']: t for t in g.req('GET', '/templates')}
    needed = sorted({nd['template'] for nd in topo['nodes']})
    missing = [t for t in needed if t not in tpls]
    if missing:
        raise SystemExit(
            '缺少模板，请先在 GNS3 导入对应镜像后再重试：\n  ' + '\n  '.join(missing) +
            '\n（可用 list-templates 查看已有哪些模板）')

    # 逐模板检查镜像文件与 symbol 图标是否齐全
    problems = []
    for name in needed:
        t = tpls[name]
        if t['template_type'] in BUILTIN_TYPES:
            continue  # vpcs/cloud 等内置节点无镜像/图标依赖
        full = g.req('GET', f"/templates/{t['template_id']}")
        # 镜像：qemu 模板取 hda_disk_image；其余类型回退到 image 字段
        img = (full.get('hda_disk_image') or full.get('image') or '').strip()
        if not img:
            problems.append(f'  {name}：未配置磁盘镜像')
        if not full.get('symbol') or 'computer.svg' in str(full.get('symbol')):
            problems.append(f'  {name}：缺少专属图标（symbol 为空或默认 computer.svg）')
    if problems:
        raise SystemExit(
            '以下模板的镜像/图标不完整，请在 GNS3 中补全后再重试：\n' + '\n'.join(problems))
    print('[i] 模板自检通过（镜像+图标齐全）：' + '、'.join(needed))
    return tpls


def main():
    ap = argparse.ArgumentParser(description='GNS3 拓扑自动搭建（仅标准库）')
    ap.add_argument('action', choices=['list-projects', 'list-templates', 'build', 'status'])
    ap.add_argument('--api', required=True,
                    help='GNS3 API 根地址，如 http://<GNS3服务器IP>/v2 或 :3080/v2')
    ap.add_argument('--topo', help='topo.json 路径（build 用）')
    ap.add_argument('--project', help='项目名（status 用）')
    ap.add_argument('--start', action='store_true', help='build 后立即启动全部节点')
    ap.add_argument('--out', help='输出设备端口映射 JSON（lab_config 用）')
    a = ap.parse_args()
    g = Gns3(a.api)

    if a.action == 'list-projects':
        for p in g.req('GET', '/projects'):
            print(f"{p['name']:30s} {p['project_id']} {p.get('status')}")
    elif a.action == 'list-templates':
        for t in g.req('GET', '/templates'):
            print(f"{t['name']:20s} {t['template_type']:18s} {t['template_id']}")
    elif a.action == 'build':
        if not a.topo:
            raise SystemExit('build 需要 --topo topo.json')
        with open(a.topo, encoding='utf-8') as f:
            topo = json.load(f)
        pid = build(g, topo, a.start)
        if a.out:
            cfg = status(g, topo['project'])
            with open(a.out, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            print(f'[+] 端口映射已写入 {a.out}')
    elif a.action == 'status':
        if not a.project:
            raise SystemExit('status 需要 --project 项目名')
        status(g, a.project)


if __name__ == '__main__':
    main()
