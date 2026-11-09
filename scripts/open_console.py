#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""观摩窗口打开工具（仅标准库）：自动发现用户机器上的终端工具并按端口映射批量打开 telnet 窗口。

用途：AI 通过 telnet 端口下发配置时，同步在用户机器上打开各设备的控制台窗口，
让用户实时观摩配置过程（只增开窗口，不影响 AI 自己的 telnet 通道；GNS3 console 支持多连）。

支持工具（自动发现）：Xshell / SecureCRT / PuTTY / MobaXterm / WindTerm。
发现顺序：注册表卸载项 -> 常见安装目录 -> PATH -> 用户桌面便携版。

用法：
  python open_console.py detect                                   # 只列出发现的终端工具
  python open_console.py open --config lab_config.json            # 用发现的首选工具打开全部设备
  python open_console.py open --config lab_config.json --tool putty
  python open_console.py open --config lab_config.json --devices <设备名1>,<设备名2>
  python open_console.py open --host <IP> --map "<设备名>=<端口>,<设备名>=<端口>"  # 不读配置文件直接给映射

注意：仅 Windows（winreg 检测）；其他平台退化为提示用户自行用 telnet 连接。
"""
import argparse
import json
import os
import subprocess
import sys
import glob

# 工具定义：kind -> (匹配关键词, 可执行文件名, 启动参数构造函数, 说明)
def _args_url(exe, host, port, title):
    return [exe, 'telnet://%s:%d' % (host, port)]

def _args_crt(exe, host, port, title):
    return [exe, '/T', '/TELNET', host, str(port)]

def _args_putty(exe, host, port, title):
    return [exe, '-telnet', '-P', str(port), host]

TOOLS = {
    'xshell':    {'exe': 'Xshell.exe',    'kw': ['xshell'],              'args': _args_url},
    'securecrt': {'exe': 'SecureCRT.exe', 'kw': ['securecrt'],           'args': _args_crt},
    'putty':     {'exe': 'putty.exe',     'kw': ['putty'],               'args': _args_putty},
    'mobaxterm': {'exe': 'MobaXterm.exe', 'kw': ['mobaxterm'],           'args': _args_url},
    'windterm':  {'exe': 'WindTerm.exe',  'kw': ['windterm'],            'args': _args_url},
}
PREFERENCE = ['xshell', 'securecrt', 'mobaxterm', 'putty', 'windterm']

COMMON_DIRS = [
    r'C:\Program Files\NetSarang', r'C:\Program Files (x86)\NetSarang',
    r'C:\Program Files\VanDyke Software', r'C:\Program Files (x86)\VanDyke Software',
    r'C:\Program Files\PuTTY', r'C:\Program Files (x86)\PuTTY',
    r'C:\Program Files\Mobatek', r'C:\Program Files (x86)\Mobatek',
    r'C:\Program Files\WindTerm', r'C:\Program Files (x86)\WindTerm',
]


def _from_registry():
    found = {}
    try:
        import winreg
    except ImportError:
        return found
    roots = []
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for sub in (r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                    r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'):
            roots.append((root, sub))
    for root, path in roots:
        try:
            k = winreg.OpenKey(root, path)
        except OSError:
            continue
        for i in range(winreg.QueryInfoKey(k)[0]):
            try:
                sk = winreg.OpenKey(k, winreg.EnumKey(k, i))
                name = winreg.QueryValueEx(sk, 'DisplayName')[0].lower()
                icon = ''
                try:
                    icon = winreg.QueryValueEx(sk, 'DisplayIcon')[0].split(',')[0].strip('"')
                except OSError:
                    pass
                for kind, meta in TOOLS.items():
                    if kind in found:
                        continue
                    if any(w in name for w in meta['kw']):
                        cand = [icon] if icon else []
                        try:
                            inst = winreg.QueryValueEx(sk, 'InstallLocation')[0]
                            cand.append(os.path.join(inst, meta['exe']))
                        except OSError:
                            pass
                        for c in cand:
                            if c and os.path.isfile(c):
                                found[kind] = c
                                break
            except OSError:
                continue
    return found


def _from_paths():
    found = {}
    for kind, meta in TOOLS.items():
        if kind in found:
            continue
        for d in COMMON_DIRS:
            for exe in glob.glob(os.path.join(d, '**', meta['exe']), recursive=True):
                found.setdefault(kind, exe)
                break
    return found


def _from_path_env_and_desktop():
    found = {}
    search_dirs = [os.path.join(os.path.expanduser('~'), 'Desktop'),
                   os.path.join(os.path.expanduser('~'), 'Desktop', '**')]
    for kind, meta in TOOLS.items():
        if kind in found:
            continue
        # PATH
        for d in os.environ.get('PATH', '').split(os.pathsep):
            p = os.path.join(d, meta['exe'])
            if os.path.isfile(p):
                found.setdefault(kind, p)
                break
        # 桌面（含一级子目录，兼容便携版）
        if kind not in found:
            for pat in search_dirs:
                hits = glob.glob(os.path.join(pat, meta['exe'])) or \
                       glob.glob(os.path.join(pat, '*', meta['exe']))
                if hits:
                    found.setdefault(kind, hits[0])
                    break
    return found


def find_tools():
    found = {}
    for source in (_from_registry, _from_paths, _from_path_env_and_desktop):
        for k, v in source().items():
            found.setdefault(k, v)
    return found


def main():
    ap = argparse.ArgumentParser(description='打开设备控制台观摩窗口（自动发现终端工具）')
    ap.add_argument('action', choices=['detect', 'open'])
    ap.add_argument('--config', help='lab_config.json（含 host 与 devices 端口映射）')
    ap.add_argument('--host', help='不读配置文件时直接给 GNS3 服务器 IP')
    ap.add_argument('--map', help='不读配置文件时直接给映射，如 "<设备名>=<端口>,<设备名>=<端口>"')
    ap.add_argument('--tool', choices=list(TOOLS) + ['auto'], default='auto',
                    help='指定工具；默认 auto 按优先级自动选')
    ap.add_argument('--devices', help='只打开指定设备，逗号分隔；默认全部')
    a = ap.parse_args()

    tools = find_tools()
    if a.action == 'detect':
        if not tools:
            print('未发现终端工具。可安装 Xshell / SecureCRT / PuTTY / MobaXterm 之一，'
                  '或将便携版 exe 放到桌面后重试。')
            return
        for kind in PREFERENCE:
            if kind in tools:
                print('%-10s %s' % (kind, tools[kind]))
        return

    # open：解析设备映射
    if a.config:
        with open(a.config, encoding='utf-8') as f:
            cfg = json.load(f)
        host = cfg['host']
        devmap = {name: (d['port'] if isinstance(d, dict) else d)
                  for name, d in cfg['devices'].items()}
    elif a.host and a.map:
        host = a.host
        devmap = {}
        for item in a.map.split(','):
            name, port = item.strip().split('=')
            devmap[name.strip()] = int(port)
    else:
        raise SystemExit('open 需要 --config lab_config.json，或 --host + --map')

    if a.devices:
        keep = {x.strip() for x in a.devices.split(',')}
        devmap = {k: v for k, v in devmap.items() if k in keep}
    if not devmap:
        raise SystemExit('没有可打开的设备')

    if not tools:
        print('[!] 未发现终端工具，请手动用 telnet 连接：')
        for name, port in sorted(devmap.items()):
            print('    %s -> telnet %s %d' % (name, host, port))
        return
    kind = a.tool if a.tool != 'auto' else next((k for k in PREFERENCE if k in tools), None)
    if not kind:
        raise SystemExit('指定的工具未安装：%s（detect 查看已发现的工具）' % a.tool)
    exe = tools[kind]
    print('[i] 使用 %s：%s' % (kind, exe))
    for name, port in sorted(devmap.items()):
        args = TOOLS[kind]['args'](exe, host, port, name)
        try:
            subprocess.Popen(args)
            print('    [+] %s -> telnet %s:%d' % (name, host, port))
        except OSError as e:
            print('    [!] %s 打开失败：%s' % (name, e))


if __name__ == '__main__':
    main()
