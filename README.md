<div align="center">

# 🌐 锐捷数据通信实验 Skill

### Ruijie Datacom Lab Skill

**一张拓扑图，全自动完成锐捷 RGOS 数据通信实验。**

<br>

[![Version](https://img.shields.io/badge/Version-v1.0-ee3f4d?style=for-the-badge&logo=github)](https://github.com/baiqiuran520/network)
[![License](https://img.shields.io/badge/License-署名--非商用-1e80ff?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-3776ab?style=for-the-badge&logo=python&logoColor=white)](scripts/)
[![Zero Deps](https://img.shields.io/badge/零依赖-标准库-only-2ea44f?style=for-the-badge)](scripts/)
[![Status](https://img.shields.io/badge/Status-完全托管-f5a623?style=for-the-badge)](SKILL.md)

<br>

| 🌍 语言 / Language |  |
|:---:|:---:|
| [**中文**](#-中文-chinese) | [**English**](#-english) |

</div>

---

## 目录 / Table of Contents

- [这是什么](#-这是什么)
- [核心亮点](#-核心亮点)
- [设计特点](#-设计特点)
- [目录结构](#-目录结构)
- [使用条件](#-使用条件)
- [快速开始](#-快速开始)
- [配置外置](#-配置外置)
- [安全提示](#-安全提示)
- [适用 / 不适用](#-适用--不适用)
- [版权与许可](#-版权与许可)
- [版本说明](#-版本说明)

---

## <a id="-中文-chinese"></a>🇨🇳 中文

### 📌 这是什么

一个用于驱动 **GNS3 + RG-NSE（锐捷 RGOS）模拟器**（或同类 RGOS 模拟器）完成数据通信实验的技能包（Skill）。

它把一次完整实验所需的全部能力，沉淀为 **「方法论 + 技术参考 + 可运行脚本」** 三合一，覆盖从
**连接发现 → 需求冲突检查 → 规划 → 改名 → 配置 → 验证 → 排障 → 总结** 的完整闭环。

### ✨ 核心亮点

> 给一张拓扑图 + 一个 GNS3 API 地址，即可**全自动托管**——

| 阶段 | 自动完成 |
|:---:|:---|
| 🏗️ 建拓扑 | 自动创建项目、节点、连线、启动设备 |
| 🔌 端口映射 | 自动分清「哪个设备对应哪个端口」，**免手动改名** |
| 🖥️ 观摩窗口 | 自动发现 Xshell / SecureCRT / PuTTY 等并批量弹窗，**配置过程全程可见** |
| ⚙️ 逐台配置 | 按拓扑设备名自动下发 RGOS 配置 |
| ✅ 分阶段验证 | 逐步 show / ping / tracert 验证并留档 |
| 📄 报告输出 | 自动生成交付报告 |

**用户只负责「看」，几乎零操作。**

### 🎯 设计特点

| 特点 | 说明 |
|:---|:---|
| 🧠 **零本地依赖 · 蒸馏内置** | 把 **RGSA / RGSP / RGSE 三级课件** 与 **7 份实战笔记** 蒸馏为 `references/` 下的 22 篇精炼参考，**开箱即用，无需任何外部文件** |
| 🎓 **三级全量考纲** | 覆盖锐捷 RGOS 数通认证全考纲，含无线/WAN、BFD/RLDP/策略路由、BGP/IS-IS/MPLS/IPv6、SR/EVPN VXLAN/QoS/组播/IPSec 等高级技术 |
| 📦 **课件不随包分发** | 原始课件/笔记不打包（体积与版权考量）；如需自备可用 `fetch_courseware.py` 重建，不影响任何功能 |
| 🔧 **通用化脚本** | 所有脚本纯 Python 标准库、零 pip 依赖，任何用户**拿到即用**，设备名严格按你的拓扑名称 |

### 📁 目录结构

```
ruijie-datacom-skill/
├── SKILL.md                      # 技能主文档（工作流 + AI 思考方式 + 命令规则 + 按需路由表）
├── README.md                     # 本文件
├── references/                   # 分级技术参考（蒸馏自课件+笔记，内置即用）
│   ├── 01-连接与发现.md
│   ├── 02-需求冲突检查.md
│   ├── 03-命令规则与基本配置.md
│   ├── 04-二层技术.md            # VLAN/Trunk/聚合/MSTP/端口安全/BPDU
│   ├── 05-三层与路由.md          # SVI/VRRP/OSPF/Loopback
│   ├── 06-DHCP与NAT与ACL.md      # DHCP中继/NAPT/ACL
│   ├── 07-验证与排障.md
│   ├── 08-高级技术概览.md        # BGP/IS-IS/MPLS/组播/QoS/IPv6/VSU
│   ├── 10-蒸馏速查-易错点.md     # 蒸馏自笔记的踩坑速查
│   ├── 11-能力框架对照.md        # 借华为30点做结构参考（锐捷优先）
│   ├── 12-术语对照-锐捷与思科IOS.md
│   ├── 13-锐捷认证考点与易错辨析.md
│   ├── 14-交付物模板-巡检变更验证报告.md
│   ├── 15-拓扑截图解析.md
│   ├── 16-使用说明-快速上手.md
│   ├── 17-GNS3拓扑自动搭建.md
│   ├── 18-锐捷三级考纲覆盖矩阵.md
│   ├── 19-无线WLAN与广域网.md
│   ├── 20-RGSP可靠性安全与策略路由.md
│   ├── 21-BGP与ISIS与MPLS与IPv6深化.md
│   ├── 22-SR与EVPNVXLAN与QoS组播IPSec.md
│   └── knowledge_index.md
└── scripts/                      # 可运行脚本（仅 python 标准库，零 pip 依赖）
    ├── topo_build.py             # GNS3 API 自动建拓扑
    ├── connect.py                # telnet 客户端 + 端口扫描 + 唤醒/进特权
    ├── deploy.py                 # 批量下发 + 错误检测 + write + 备份 + dry-run
    ├── verify.py                 # show 系列验证留档
    ├── open_console.py           # 观摩窗口（自动发现 Xshell/CRT/PuTTY 等）
    ├── lab_config.example.json   # 配置模板
    └── fetch_courseware.py       # 可选：用你自己的课件重建知识库
```

### ✅ 使用条件

| 条件 | 必需/可选 | 说明 |
| --- | :---: | --- |
| Python 3 | 🔴 **必需** | 脚本仅用标准库（socket/re/json），无需 pip 安装任何包 |
| GNS3 + 锐捷 RG-NSE（RGOS）镜像 | 🔴 **必需** | 拓扑搭建与设备配置的前提；镜像需预先导入 GNS3 |
| GNS3 Server API 可达 | 🔴 **必需**（自动建拓扑时） | 默认 `http://<GNS3主机>/v2`；若 API 只绑定 localhost，需改为 `0.0.0.0` |
| telnet 端口可达 | 🔴 **必需**（配置设备时） | 设备以 telnet console 端口暴露 |
| 终端工具（Xshell/CRT/PuTTY 等） | 🟡 可选 | 仅"观摩窗口"功能需要；没有也能用，脚本会打印手动连接清单 |
| `slidep`（PPT 提取） | 🟡 可选 | 仅 `fetch_courseware.py` 重建知识库时需要 |

### 🚀 快速开始

把整个 `ruijie-datacom-skill/` 目录放到以下任一 skill 目录即可，**无需 pip 安装任何东西**：

- 用户级：`~/.workbuddy/skills/ruijie-datacom-skill/`
- 项目级：`<你的项目>/.workbuddy/skills/ruijie-datacom-skill/`

> 在 WorkBuddy 里调用 `/ruijie-datacom-lab`（或自然语言触发）即可加载本 skill。

```bash
cd ruijie-datacom-skill/scripts

# 0) 询问拿到模拟器主机 IP 后，扫描开放端口，发现设备
python connect.py scan --host <模拟器IP> --start 5000 --end 5020

# 1) 复制配置模板，按你的实验填写 host / devices / configs
cp lab_config.example.json lab_config.json

# 2) 先空跑预览（不连设备、不下发）
python deploy.py --dry-run

# 3) 正式下发（会先备份 running-config，并让你确认设备清单）
python deploy.py
python deploy.py ACL          # 仅下发策略阶段

# 4) 分阶段验证
python verify.py before_acl
python verify.py after_acl
```

### 🔧 配置外置（核心设计）

所有实验参数都在 `scripts/lab_config.json`，脚本本身**不写死任何实验**：

| 字段 | 说明 |
|:---|:---|
| `host` | 模拟器主机 IP（每次按阶段 0 扫描结果填，不要写死） |
| `devices` | `设备名 -> {port, type}`，`type` 取值 `vpcs` / `switch` / `router` |
| `configs` | `设备名 -> 命令数组`；带前导空格的字符串表示子上下文 |
| `acl_stage`（可选） | 策略阶段命令，建议最后下发 |
| `verify_plan`（可选） | 分阶段验证命令集 |

> **改实验 = 只改这个 JSON，脚本一行都不用动。**

### 🛡️ 安全提示

- `deploy.py` 默认在下发前自动备份每台网络设备的 `running-config` 到 `backups/`，并打印设备清单要求确认。
- 强烈建议先 `--dry-run` 预览，再正式下发。
- `write` 会把配置写入 startup-config，重载不丢；大改前务必确认已备份。

### 🎯 适用 / 不适用

| | 内容 |
|:---:|:---|
| ✅ **适用** | 锐捷 RGOS 数据通信基础与可靠性/安全实验、模拟器连接与验证、教学/实训排障、锐捷认证备考 |
| ❌ **不适用** | 真实物理设备带外管理（需 SSH/Console 方案）、非锐捷命令集、RCIE/WLAN/安全产品专项（本包不含） |

---

## <a id="-english"></a>🇬🇧 English

### 📌 What is this

A skill package that drives **GNS3 + RG-NSE (Ruijie RGOS) simulators** (or similar RGOS simulators)
to complete data-communication labs. It bundles everything a full lab needs — **methodology,
technical references, and runnable scripts** — covering the complete loop from
**connection discovery → requirement-conflict check → planning → renaming → configuration →
verification → troubleshooting → summary**.

### ✨ Highlight

> Given one topology image + a GNS3 API address, it runs **fully hands-off** —

| Stage | Automated |
|:---:|:---|
| 🏗️ Build | Create project, nodes, links, and power on devices automatically |
| 🔌 Port mapping | Auto-resolve "which device maps to which port", **no manual renaming** |
| 🖥️ Observation | Auto-detect Xshell / SecureCRT / PuTTY and open windows, **config fully visible** |
| ⚙️ Configure | Push RGOS config per topology device name automatically |
| ✅ Verify | Staged show / ping / tracert verification with logging |
| 📄 Report | Auto-generate delivery report |

**The user just watches — almost zero operation.**

### 🎯 Design

| Trait | Description |
|:---|:---|
| 🧠 **Zero local dependency · distilled & built-in** | Distills **RGSA / RGSP / RGSE** courseware plus **7 sets of hands-on notes** into 22 concise reference docs under `references/` — works out of the box |
| 🎓 **Full three-level syllabus** | Covers the full Ruijie RGOS certification syllabus, including wireless/WAN, BFD/RLDP/policy routing, BGP/IS-IS/MPLS/IPv6, SR/EVPN VXLAN/QoS/multicast/IPSec |
| 📦 **Courseware not redistributed** | Original courseware/notes are not bundled (size & copyright); rebuild via `fetch_courseware.py` if desired |
| 🔧 **Universal scripts** | Python stdlib only, zero pip deps; device names strictly follow your topology names |

### 📁 Directory structure

```
ruijie-datacom-skill/
├── SKILL.md                      # Main skill doc (workflow + AI thinking + command rules + routing table)
├── README.md                     # This file
├── references/                   # Tiered technical references (distilled, built-in)
│   ├── 01-connection-and-discovery.md
│   ├── 02-requirement-conflict.md
│   ├── 03-command-rules.md
│   ├── 04-layer-2.md             # VLAN/Trunk/LACP/MSTP/port-security/BPDU
│   ├── 05-layer-3-routing.md     # SVI/VRRP/OSPF/Loopback
│   ├── 06-dhcp-nat-acl.md
│   ├── 07-verify-troubleshoot.md
│   ├── 08-advanced-overview.md
│   ├── 10-pitfall-cheatsheet.md
│   ├── 11-framework-mapping.md
│   ├── 12-ruijie-vs-cisco.md
│   ├── 13-exam-points.md
│   ├── 14-report-templates.md
│   ├── 15-topology-image-parse.md
│   ├── 16-quickstart.md
│   ├── 17-gns3-topology-build.md
│   ├── 18-syllabus-coverage-matrix.md
│   ├── 19-wireless-wan.md
│   ├── 20-rgsp-reliability-security-pbr.md
│   ├── 21-bgp-isis-mpls-ipv6.md
│   ├── 22-sr-evpnvxlan-qos-mcast-ipsec.md
│   └── knowledge_index.md
└── scripts/                      # Runnable scripts (Python stdlib only, zero pip deps)
    ├── topo_build.py             # GNS3 API auto topology build
    ├── connect.py                # telnet client + port scan + wake/enable
    ├── deploy.py                 # batch push + error detect + write + backup + dry-run
    ├── verify.py                 # show-series verification logging
    ├── open_console.py           # observation windows (auto-detect Xshell/CRT/PuTTY etc.)
    ├── lab_config.example.json   # config template
    └── fetch_courseware.py       # optional: rebuild knowledge base from your own courseware
```

### ✅ Requirements

| Requirement | Required/Optional | Notes |
| --- | :---: | --- |
| Python 3 | 🔴 **Required** | Scripts use stdlib only (socket/re/json); no pip install needed |
| GNS3 + Ruijie RG-NSE (RGOS) image | 🔴 **Required** | Prerequisite for topology build & configuration; import the image into GNS3 first |
| GNS3 Server API reachable | 🔴 **Required** (auto-build) | Default `http://<GNS3-host>/v2`; if API binds to localhost only, switch to `0.0.0.0` |
| telnet port reachable | 🔴 **Required** (configure) | Devices are exposed via telnet console ports |
| Terminal tool (Xshell/CRT/PuTTY etc.) | 🟡 Optional | Only for the observation-window feature; without it, a manual connection list is printed |
| `slidep` (PPT extractor) | 🟡 Optional | Only needed by `fetch_courseware.py` |

### 🚀 Quick start

Place the whole `ruijie-datacom-skill/` directory into one of the skill directories —
**no pip install required**:

- User-level: `~/.workbuddy/skills/ruijie-datacom-skill/`
- Project-level: `<your-project>/.workbuddy/skills/ruijie-datacom-skill/`

> In WorkBuddy, invoke `/ruijie-datacom-lab` (or trigger via natural language) to load this skill.

```bash
cd ruijie-datacom-skill/scripts

# 0) After getting the simulator host IP, scan open ports to discover devices
python connect.py scan --host <SIMULATOR-IP> --start 5000 --end 5020

# 1) Copy the config template and fill in host / devices / configs
cp lab_config.example.json lab_config.json

# 2) Dry-run preview (no connection, no push)
python deploy.py --dry-run

# 3) Real push (backs up running-config first, then asks you to confirm device list)
python deploy.py
python deploy.py ACL          # push only the policy stage

# 4) Staged verification
python verify.py before_acl
python verify.py after_acl
```

### 🔧 Externalized config (core design)

All lab parameters live in `scripts/lab_config.json`; scripts never hardcode any lab:

| Field | Description |
|:---|:---|
| `host` | simulator host IP (fill from the stage-0 scan each time, don't hardcode) |
| `devices` | `device-name -> {port, type}`; `type` is `vpcs` / `switch` / `router` |
| `configs` | `device-name -> command list`; leading-space strings denote sub-context |
| `acl_stage` (optional) | policy-stage commands, recommended to push last |
| `verify_plan` (optional) | staged verification command sets |

> **Change the lab = change this JSON only; no script edits needed.**

### 🛡️ Safety notes

- `deploy.py` auto-backs-up each device's `running-config` to `backups/` before pushing, and
  prints the device list for confirmation.
- Strongly recommended to `--dry-run` first.
- `write` persists config to startup-config; make sure a backup exists before big changes.

### 🎯 Suitable / not suitable

| | Content |
|:---:|:---|
| ✅ **Suitable** | Ruijie RGOS datacom fundamentals & reliability/security labs, simulator connection & verification, teaching/training troubleshooting, Ruijie certification prep |
| ❌ **Not suitable** | out-of-band management of real physical devices (needs SSH/Console), non-Ruijie command sets, RCIE/WLAN/security-product specializations (not included) |

---

## <a id="-版权与许可"></a>📜 版权与许可 / Copyright & License

**作者 / Author**：白虬髯 (Bai Qiuran)

本作品采用 **署名-非商业性使用** 许可（详见仓库根目录 `LICENSE` 文件）：

| | 说明 / Description |
|:---:|:---|
| ✅ **可以 / Allowed** | 免费用于学习、教学、个人实验、内部实训等**非商业**用途 |
| ⛔ **禁止商用 / No commercial use** | 未经原作者书面授权，不得用于出售、出租、付费分发、商业培训、捆绑进收费产品或服务等任何营利性用途 |
| 🔗 **二创必须署名 / Attribution required** | 任何二次创作、衍生作品、再分发（含部分摘录、翻译、改编），**必须**在显著位置保留原作者信息——作者「白虬髯 (Bai Qiuran)」、原作品名称「锐捷数据通信实验 Skill（ruijie-datacom-lab）」以及本许可协议的链接或全文 |
| 🔒 **延续本协议 / Same license** | 衍生作品须沿用本协议（署名-非商业性使用），不得去除约束后再分发 |

> 本作品「按现状」提供，作者不对其正确性与适用性作任何担保；
> 对真实生产网络设备执行配置前，请务必自行评估风险并做好备份。
> 商业使用请联系原作者另行授权。
>
> The work is provided "AS IS" with no warranty; before configuring real production
> devices, assess the risk yourself and back up first. Contact the author for commercial use.

---

## <a id="-版本说明"></a>🏷️ 版本说明 / Version Notes

| 版本 | 说明 |
| --- | --- |
| **v1.0** | 第一版（First Release）：三级考纲全量覆盖 + 完全托管闭环 + 观摩窗口 + 按需路由表（省 token） |

> 命令以锐捷 RGOS 标准语法为准；高级技术（无线/VXLAN/SR/MPLS VPN/IPSec）在不同版本间命令差异较大，
> 文档已统一标注「以设备 `?` 实测为准」。
> Commands follow Ruijie RGOS standard syntax; advanced topics (wireless/VXLAN/SR/MPLS VPN/IPSec)
> vary across versions and are marked "verify with `?` on the actual device".

---

<div align="center">

**Made with ❤️ by [白虬髯 (Bai Qiuran)](https://github.com/baiqiuran520)** · 署名-非商业性使用 · v1.0

</div>
