# -*- coding: utf-8 -*-
"""锐捷 RG-NSE 模拟器 telnet 客户端：端口扫描 + 连接 + 唤醒/进特权模式。

子命令：
  scan   扫描主机开放的可 telnet 端口，返回 port -> banner(设备类型线索)
  shell  连上单台设备，进入特权模式，执行若干命令并打印

依赖：仅标准库（socket / re / time / argparse）。

作者 / Author: 白虬髯 (Bai Qiuran)
许可 / License: Attribution-NonCommercial (署名-非商业性使用；禁止商用；二创须保留原作者署名，详见 LICENSE)
版本 / Version: v1.0
"""
import socket
import time
import re
import argparse

# 通用工具：不内置任何真实环境地址。host 与端口映射必须来自用户告知、
# scan 子命令结果，或 topo_build.py 生成的 lab_config.json。
DEFAULT_HOST = ""   # 必须显式指定 --host，勿依赖默认值
# 端口映射示例（仅示意格式，不代表任何真实实验）：
# DEVICES = {"<设备名>": <端口>}
DEVICES = {}
DEVICE_HINTS = {
    "VPCS": ("PC",), "PC": (), "RG-NSE": (), "Ruijie": (),
}


def _strip_ansi(b):
    return re.sub(rb"\x1b\[[0-9;?]*[a-zA-Z]", b"", b)


def _iac_reply(s, data):
    out = bytearray()
    i = 0
    while i + 2 < len(data):
        if data[i] == 255:
            cmd, opt = data[i + 1], data[i + 2]
            if cmd in (251, 252):
                out += bytes([255, 254, opt])
            elif cmd in (253, 254):
                out += bytes([255, 252, opt])
            i += 3
        else:
            i += 1
    if out:
        try:
            s.sendall(bytes(out))
        except Exception:
            pass


def _strip_iac(b):
    out = bytearray()
    i = 0
    while i < len(b):
        if b[i] == 255 and i + 1 < len(b):
            cmd = b[i + 1]
            if cmd == 250:
                j = i + 2
                while j + 1 < len(b) and not (b[j] == 255 and b[j + 1] == 240):
                    j += 1
                i = j + 2
            elif cmd == 255:
                out.append(255); i += 2
            else:
                i += 3 if cmd in (251, 252, 253, 254) else 2
        else:
            out.append(b[i]); i += 1
    return bytes(out)


class RGConsole:
    """单台设备的 telnet 会话。"""

    def __init__(self, host, port, timeout=2.5):
        self.host = host
        self.port = port
        self.sock = None
        self.banner = ""

    def open(self):
        s = socket.socket()
        s.settimeout(2.5)
        s.connect((self.host, self.port))
        self.sock = s
        self.banner = self._drain(0.8)
        for _ in range(5):
            if re.search(r"[>#]\s*$", self.banner.strip()):
                break
            try:
                self.sock.sendall(b"\r")
            except Exception:
                break
            self.banner += self._drain(0.7)
        return self

    def _drain(self, seconds):
        end = time.time() + seconds
        out = b""
        while time.time() < end:
            self.sock.settimeout(0.2)
            try:
                d = self.sock.recv(8192)
                if not d:
                    break
                out += d
                _iac_reply(self.sock, d)
            except socket.timeout:
                pass
            except Exception:
                break
        return _strip_ansi(_strip_iac(out)).decode("utf-8", errors="replace")

    def cmd(self, command, wait=1.0, max_wait=15, paging=True):
        try:
            self.sock.sendall(command.encode("utf-8") + b"\r")
        except Exception as e:
            return "SEND ERROR: %s" % e
        text = self._drain(wait)
        start = time.time()
        while time.time() - start < max_wait:
            if paging and re.search(r"--\s*More\s*--|<\s*-+\s*More", text, re.I):
                try:
                    self.sock.sendall(b" ")
                except Exception:
                    break
                text += self._drain(0.7)
                continue
            more = self._drain(0.7)
            if more:
                text += more
            else:
                break
        return text

    def push(self, line, settle=0.3):
        try:
            self.sock.sendall(line.encode("utf-8") + b"\r")
        except Exception as e:
            return "SEND ERROR: %s" % e
        return self._drain(settle)

    def enable_and_config(self):
        """唤醒并进入全局配置模式；VPCS 不进配置模式。返回最后提示符。"""
        last = self.banner.strip().splitlines()[-1].strip() if self.banner.strip() else ""
        if last.startswith("PC") or "VPCS" in self.banner:
            return last
        if last.endswith(">"):
            self.cmd("enable", wait=0.5, max_wait=1.5)
            last = "#"
        if not last.endswith("(config)#"):
            self.cmd("configure terminal", wait=0.5, max_wait=1.5)
        return last

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


def scan_ports(host, start, end, timeout=0.4):
    """TCP 端口扫描，返回 [(port, banner)]，仅保留能连上且有 banner 的。"""
    found = []
    for port in range(start, end + 1):
        s = socket.socket()
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            # 读一点 banner 判断设备类型
            s.settimeout(0.6)
            buf = b""
            t = time.time() + 0.6
            while time.time() < t:
                try:
                    d = s.recv(4096)
                    if not d:
                        break
                    buf += d
                    _iac_reply(s, d)
                except socket.timeout:
                    break
                except Exception:
                    break
            banner = _strip_ansi(_strip_iac(buf)).decode("utf-8", "ignore").strip()
            found.append((port, banner))
        except Exception:
            pass
        finally:
            try:
                s.close()
            except Exception:
                pass
    return found


def main():
    ap = argparse.ArgumentParser(description="锐捷模拟器 telnet 工具")
    sub = ap.add_subparsers(dest="cmd")
    sp = sub.add_parser("scan", help="扫描开放端口")
    sp.add_argument("--host", required=True, help="GNS3 服务器 IP（必须显式指定）")
    sp.add_argument("--start", type=int, default=5000)
    sp.add_argument("--end", type=int, default=5020)
    sh = sub.add_parser("shell", help="连单台设备执行命令")
    sh.add_argument("--host", required=True, help="GNS3 服务器 IP（必须显式指定）")
    sh.add_argument("--port", type=int, required=True)
    sh.add_argument("--run", nargs="*", default=["show version"])
    args = ap.parse_args()

    if args.cmd == "scan":
        print("scanning %s %d-%d ..." % (args.host, args.start, args.end))
        for port, banner in scan_ports(args.host, args.start, args.end):
            # 类型线索
            kind = "VPCS" if ("PC" in banner or "VPCS" in banner) else (
                "RGOS" if ("RG-NSE" in banner or "Ruijie" in banner) else "unknown")
            head = banner.splitlines()[0] if banner else "(no banner)"
            print("  port %5d  kind=%-6s  %s" % (port, kind, head[:60]))
    elif args.cmd == "shell":
        c = RGConsole(args.host, args.port).open()
        c.enable_and_config()
        for r in args.run:
            print("### %s" % r)
            print(c.cmd(r, wait=1.0, max_wait=14))
        c.close()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
