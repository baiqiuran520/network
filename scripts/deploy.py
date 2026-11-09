# -*- coding: utf-8 -*-
"""按 lab_config.json 批量下发锐捷 RGOS 配置。带错误检测、自动 write、下发前备份、dry-run。

配置外置：所有设备端口、类型、命令都在 scripts/lab_config.json 里（首次请复制
lab_config.example.json 改名后修改）。脚本本身不再写死任何实验内容，因此可原样
给任何人使用，只需对方填自己的 lab_config.json。

用法:
  python deploy.py                       # 下发 configs 里全部设备
  python deploy.py <设备名1> <设备名2>   # 仅指定设备（按 lab_config 里的名字）
  python deploy.py ACL                  # 仅下发 acl_stage（策略建议最后发）
  python deploy.py --dry-run            # 只打印计划，不连设备、不下发（安全预览）
  python deploy.py --config mylab.json  # 指定配置文件
  python deploy.py --yes                # 跳过「确认设备清单」交互

安全护栏:
  - 默认下发前会把每台网络设备的 running-config 备份到 ../backups/<name>.rc.txt
  - 默认会打印设备清单并让你确认（--yes 跳过）
  - --dry-run 完全不连接设备，只展示将要做什么

依赖: 同目录 connect.py（仅 python 标准库）
"""
import os
import re
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "lab_config.json")

ERR = re.compile(
    r"% Invalid|% Incomplete|% Unknown|Invalid arguments|Unknown command|"
    r"doesn't have sufficient privilege|% Error|Ambiguous command|"
    r"% Command|Failed|not supported|Unrecognized", re.I)


def load_config(path):
    if not os.path.exists(path):
        sys.stderr.write("未找到配置文件: %s\n" % path)
        sys.stderr.write("请先复制 %s 为同目录的 lab_config.json，并按你的实验修改。\n"
                         % os.path.join(HERE, "lab_config.example.json"))
        sys.exit(2)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _detect_type(c, declared):
    last = c.banner.strip().splitlines()[-1].strip() if c.banner.strip() else ""
    if declared == "vpcs" or last.startswith("PC") or "VPCS" in c.banner:
        return "vpcs"
    return declared or "switch"


def deploy_device(host, devices, name, lines, backup=True):
    import connect as C  # noqa
    spec = devices[name]
    port = spec["port"]
    c = C.RGConsole(host, port).open()
    declared = spec.get("type", "switch")
    dtype = _detect_type(c, declared)
    log = ["=== DEVICE %s (port %s type %s) ===" % (name, port, dtype)]

    # 进特权
    if dtype != "vpcs":
        last = c.banner.strip().splitlines()[-1].strip() if c.banner.strip() else ""
        if last.endswith(">"):
            c.cmd("enable", wait=0.5, max_wait=1.5)

    # 下发前备份
    if backup and dtype != "vpcs":
        c.cmd("end", wait=0.3)
        rc = c.cmd("show running-config", wait=1.5, max_wait=15)
        bdir = os.path.join(HERE, "..", "backups")
        os.makedirs(bdir, exist_ok=True)
        open(os.path.join(bdir, name + ".rc.txt"), "w", encoding="utf-8").write(rc)
        log.append("\n--- BACKUP saved to backups/%s.rc.txt ---\n" % name)

    # 进配置模式（VPCS 无配置模式）
    if dtype != "vpcs":
        c.cmd("configure terminal", wait=0.4, max_wait=1.5)

    errors = []
    for line in lines:
        out = c.push(line, 0.3)
        log.append(">>> %s" % line)
        if out.strip():
            log.append(out.rstrip())
        if ERR.search(out):
            errors.append((line, " ".join(out.split())[:180]))

    if dtype != "vpcs":
        c.cmd("end", wait=0.4)
        save = c.cmd("write", wait=1.0, max_wait=4)
        log.append("\n--- SAVE ---\n" + save)
    c.close()

    ldir = os.path.join(HERE, "..", "deploy_logs")
    os.makedirs(ldir, exist_ok=True)
    open(os.path.join(ldir, name + ".log"), "w", encoding="utf-8").write("\n".join(log))
    print("[%s] cmds=%d errors=%d" % (name, len(lines), len(errors)))
    for line, msg in errors:
        print("   ERR %-50s -> %s" % (line[:50], msg))
    return errors


def main():
    ap = argparse.ArgumentParser(description="按 lab_config.json 下发锐捷配置")
    ap.add_argument("devices", nargs="*", help="要下发的设备名（与 lab_config 一致）；ACL 表示策略阶段")
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不连设备不下发")
    ap.add_argument("--yes", action="store_true", help="跳过确认交互")
    ap.add_argument("--no-backup", action="store_true", help="不下发前备份 running-config")
    args = ap.parse_args()

    cfg = load_config(args.config)
    host = cfg.get("host") or os.environ.get("RG_HOST")
    devices = cfg.get("devices", {})
    configs = cfg.get("configs", {})
    acl_stage = cfg.get("acl_stage", {})

    do_acl = "ACL" in args.devices
    names = [n for n in args.devices if n != "ACL"] or list(configs.keys())

    # 校验并收集执行计划
    plan = []  # list of (kind, name)
    for n in names:
        if n not in devices:
            print("skip %s: 未在 devices 中定义" % n); continue
        if n not in configs:
            print("skip %s: 未在 configs 中定义" % n); continue
        plan.append(("cfg", n))
    if do_acl:
        for n in acl_stage:
            if n not in devices:
                print("skip ACL %s: 未在 devices 中定义" % n); continue
            plan.append(("acl", n))

    if not plan:
        print("没有可下发的设备，请检查 lab_config.json。")
        sys.exit(1)

    # dry-run
    if args.dry_run:
        print("DRY-RUN  host=%s" % host)
        for kind, n in plan:
            spec = devices[n]
            tag = "ACL阶段" if kind == "acl" else "基础配置"
            src = acl_stage[n] if kind == "acl" else configs[n]
            print("  将连接 %s:%s (%s) 下发 %s 共 %d 条命令"
                  % (host, spec["port"], spec.get("type"), tag, len(src)))
        print("（未连接任何设备，未做任何改动）")
        return

    # 确认
    if not args.yes:
        print("准备向以下设备下发配置 (host=%s):" % host)
        for kind, n in plan:
            spec = devices[n]
            tag = "ACL阶段" if kind == "acl" else "基础配置"
            print("  %-6s %s:%s (%s)  %s" % (n, host, spec["port"], spec.get("type"), tag))
        ans = input("确认下发? [y/N] ").strip().lower()
        if ans != "y":
            print("已取消。")
            return

    total = []
    for kind, n in plan:
        src = acl_stage[n] if kind == "acl" else configs[n]
        total += [(n, *e) for e in deploy_device(host, devices, n, src, backup=not args.no_backup)]
    print("\nTOTAL ERRORS:", len(total))


if __name__ == "__main__":
    main()
