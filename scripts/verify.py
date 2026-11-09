# -*- coding: utf-8 -*-
"""按 lab_config.json 的设备执行 show 系列验证，结果按 stage 分设备留档。

配置外置：设备清单/端口来自 scripts/lab_config.json，因此可给任何人使用。

用法:
  python verify.py                 # 默认 stage=all（对每台设备跑通用验证）
  python verify.py before_acl      # 自定义阶段名（对应 lab_config.verify_plan 的 key）
  python verify.py all --config mylab.json

验证命令来源优先级：
  1) lab_config.json 里的 verify_plan[stage]（你自定义每台设备要跑什么）
  2) 否则按设备类型用内置默认集（vpcs / switch / router）
     - vpcs:    show ip, show arp
     - switch:  show vlan, show ip interface brief, show spanning-tree summary, show running-config
     - router:  show ip interface brief, show ip route, show running-config

依赖: 同目录 connect.py（仅 python 标准库）
"""
import os
import re
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DEFAULT_CONFIG = os.path.join(HERE, "lab_config.json")

DEFAULT_PLAN = {
    "vpcs": ["show ip", "show arp"],
    "switch": ["show vlan", "show ip interface brief",
               "show spanning-tree summary", "show running-config"],
    "router": ["show ip interface brief", "show ip route", "show running-config"],
}


def load_config(path):
    if not os.path.exists(path):
        sys.stderr.write("未找到配置文件: %s\n" % path)
        sys.stderr.write("请先复制 %s 为同目录的 lab_config.json 并按你的实验修改。\n"
                         % os.path.join(HERE, "lab_config.example.json"))
        sys.exit(2)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def summarize_ping(out):
    hits = re.findall(r"(\d+)\s+packets?\s+(?:transmitted|sent).*?(\d+)\s+(?:packets?\s+)?received",
                      out, re.I | re.S)
    if hits:
        return "%s/%s received" % (hits[-1][1], hits[-1][0])
    n = len(re.findall(r"bytes from|icmp_seq=", out, re.I))
    return "reply lines=%d" % n if n else "no reply"


def run():
    ap = argparse.ArgumentParser(description="按 lab_config 验证设备")
    ap.add_argument("stage", nargs="?", default="all")
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    args = ap.parse_args()

    import connect as C  # noqa
    cfg = load_config(args.config)
    host = cfg.get("host") or os.environ.get("RG_HOST")
    devices = cfg.get("devices", {})
    verify_plan = cfg.get("verify_plan", {})

    stage = args.stage
    if stage in verify_plan:
        target = verify_plan[stage]
    else:
        target = {n: DEFAULT_PLAN.get(devices[n].get("type", "switch"), DEFAULT_PLAN["switch"])
                  for n in devices}

    LOGDIR = os.path.join(HERE, "..", "verify_logs", stage)
    os.makedirs(LOGDIR, exist_ok=True)

    print("STAGE:", stage, " host:", host)
    for name, cmds in target.items():
        if name not in devices:
            print("  skip %s: 未在 devices 中定义" % name); continue
        port = devices[name]["port"]
        c = C.RGConsole(host, port).open()
        last = c.banner.strip().splitlines()[-1].strip() if c.banner.strip() else ""
        if not (last.startswith("PC") or "VPCS" in c.banner) and last.endswith(">"):
            c.cmd("enable", wait=0.5, max_wait=2)
        log = ["=== %s ===" % name]
        for cmd in cmds:
            out = c.cmd(cmd, wait=1.0, max_wait=14)
            log.append("\n### %s\n%s" % (cmd, out))
            if cmd.strip().startswith("ping"):
                print("  %-6s %-22s %s" % (name, cmd, summarize_ping(out)))
        c.close()
        open(os.path.join(LOGDIR, name + ".log"), "w", encoding="utf-8").write("\n".join(log))
        print("  %-6s show x%d saved" % (name, len(cmds)))
    print("logs:", LOGDIR)


if __name__ == "__main__":
    run()
