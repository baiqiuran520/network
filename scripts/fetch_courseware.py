# -*- coding: utf-8 -*-
"""用「你自己的」锐捷课件（pptx）重建 skill 的 knowledge_base。

这是 *可选* 步骤：本 skill 的 references/ 已经把核心方法论提炼完整，
不依赖 knowledge_base 也能正常工作。只有当你想把自己的课件也纳入
「可自查知识库」时，才需要运行本脚本。

前提：需要 WorkBuddy 内置的 slidep 二进制（用于把 pptx 转成 slides.md）。
如果没有，本脚本会给出安装/定位提示。

用法：
  python fetch_courseware.py --src "D:/锐捷课件" --out knowledge_base
  python fetch_courseware.py --src "D:/锐捷课件" --out knowledge_base --slidep "C:/path/slidep"

依赖：python 标准库 + 外部 slidep（非标准库，仅本脚本需要）。

作者 / Author: 白虬髯 (Bai Qiuran)
许可 / License: Attribution-NonCommercial (署名-非商业性使用；禁止商用；二创须保留原作者署名，详见 LICENSE)
版本 / Version: v1.0
"""
import os
import sys
import glob
import json
import argparse
import subprocess


def find_slidep(explicit=None):
    if explicit:
        return explicit if os.path.exists(explicit) else None
    env = os.environ.get("SLIDEP")
    if env and os.path.exists(env):
        return env
    # 常见内置位置（WorkBuddy 在 Windows 下的二进制目录）
    candidates = []
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    if home:
        base = os.path.join(home, ".workbuddy", "binaries", "node")
        for root, _dirs, files in os.walk(base):
            for f in files:
                if f == "slidep":
                    candidates.append(os.path.join(root, f))
    for c in candidates:
        return c  # 取第一个找到的
    return None


def main():
    ap = argparse.ArgumentParser(description="用自有课件重建 knowledge_base")
    ap.add_argument("--src", required=True, help="存放 .pptx 课件的目录（会递归查找）")
    ap.add_argument("--out", default="knowledge_base", help="输出目录（默认 knowledge_base）")
    ap.add_argument("--slidep", default=None, help="slidep 可执行文件路径")
    args = ap.parse_args()

    slidep = find_slidep(args.slidep)
    if not slidep:
        sys.stderr.write(
            "未找到 slidep。它是 WorkBuddy 内置的 PPT 提取工具。\n"
            "请确认 WorkBuddy 已安装，或用 --slidep 指定其完整路径。\n")
        sys.exit(2)

    if not os.path.isdir(args.src):
        sys.stderr.write("源目录不存在: %s\n" % args.src)
        sys.exit(2)

    pptxs = sorted(glob.glob(os.path.join(args.src, "**", "*.pptx"), recursive=True))
    if not pptxs:
        sys.stderr.write("在 %s 下未找到任何 .pptx 文件。\n" % args.src)
        sys.exit(2)

    os.makedirs(args.out, exist_ok=True)
    manifest = os.path.join(args.out, "_manifest.tsv")
    ok = 0
    fail = 0
    with open(manifest, "w", encoding="utf-8") as mf:
        mf.write("idx\tstatus\tsrc\n")
        for i, p in enumerate(pptxs, 1):
            idx = "p%03d" % i
            outdir = os.path.join(args.out, idx)
            os.makedirs(outdir, exist_ok=True)
            try:
                r = subprocess.run(
                    [slidep, "inspect", p, "--out", outdir],
                    timeout=180, capture_output=True, text=True)
                status = "OK" if os.path.exists(os.path.join(outdir, "slides.md")) else "EMPTY"
                if status == "OK":
                    ok += 1
                else:
                    fail += 1
            except Exception as e:  # noqa
                status = "ERR"
                fail += 1
                sys.stderr.write("  [%s] %s -> %s\n" % (idx, os.path.basename(p), e))
            mf.write("%s\t%s\t%s\n" % (idx, status, p))
            print("  [%s] %-8s %s" % (idx, status, os.path.basename(p)))
    print("\n完成：OK=%d  FAIL=%d  清单: %s" % (ok, fail, manifest))


if __name__ == "__main__":
    main()
