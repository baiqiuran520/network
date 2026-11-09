---
name: ruijie-datacom-lab
description: 通过 telnet 连接 GNS3 模拟器（内运行锐捷 RG-NSE 的 RGOS 设备镜像），完成数据通信实验的规划、配置、验证与排障。覆盖 VLAN/Trunk/链路聚合/MSTP/VRRP/OSPF/DHCP 中继/ACL/NAT/端口安全/BPDU 防护等。当用户要连 GNS3 模拟器、下发锐捷 RGOS 配置、做 show/ping/tracert 验证或排障时使用。
author: 白虬髯
license: Attribution-NonCommercial (署名-非商业性使用；禁止商用；二创须保留原作者署名，详见 LICENSE)
version: v1.0
---

# 锐捷数据通信实验 Skill

本 skill 用于驱动 **GNS3 模拟器**（内运行锐捷 RG-NSE 的 RGOS 设备镜像，或同类 RGOS 模拟器）中的设备，
按一套可复用的工作流完成数据通信实验：**连接发现 → 需求冲突检查 → 规划 → 确认改名
→ 基本配置 → 具体配置 → 验证 → 排障 → 总结询问**。

> **自包含设计（零本地依赖）**：本 skill 不依赖任何一台机器上的私有文件。
> 所有实验参数（设备 IP/端口/类型/配置命令）都通过 `scripts/lab_config.json` 外置，
> 核心方法论已沉淀在 `references/`，无需任何课件即可独立运行。
> 内置知识范围聚焦 **RGSA（Associate）/ RGSP（Professional）/ RGSE（Expert）三级别 + 笔记蒸馏**，
> 不含 RCIE / WLAN / 安全产品等专项，也不随包附任何课件原文件。

> **版本与溯源**：skill 版本 `v1.0`（第一版 / First Release）；覆盖锐捷 RGOS 大纲 **RGSA / RGSP / RGSE（锐捷数通认证三级，全量）**；
> 命令语法以锐捷官方教材与用户笔记为准，参考文档均蒸馏内置，无外部依赖；
> 如发现命令差异，以设备 `?` 实测为准（见 `03-命令规则`）。
> **作者**：白虬髯（参考文档蒸馏自其锐捷认证笔记与课件）。

> **版权**：本 skill 采用「署名-非商业性使用」许可（详见 `LICENSE`）——禁止商用；
> 任何二创/衍生/再分发必须保留原作者「白虬髯 (Bai Qiuran)」署名及本许可。

配套脚本在 `scripts/`（仅 python 标准库，无需 pip 安装）：
- `topo_build.py`：GNS3 拓扑自动搭建（API 建项目/节点/链路/启动，输出端口映射）
- `connect.py`：telnet 客户端（原生 socket + IAC 协商）+ **端口扫描** + 唤醒/进入特权模式
- `deploy.py`：按 `lab_config.json` 批量下发，带错误检测、`write` 保存、**下发前备份**、`--dry-run` 预览
- `verify.py`：按 `lab_config.json` 执行 show 系列，分设备/分阶段留档
- `open_console.py`：**观摩窗口**——自动发现用户机器上的终端工具（Xshell/SecureCRT/PuTTY/
  MobaXterm/WindTerm），按端口映射批量打开各设备 telnet 窗口，让用户实时观摩配置过程
- `lab_config.example.json`：配置模板（复制为 `lab_config.json` 后按实验修改）
- `fetch_courseware.py`：可选，用你**自己的**课件重建知识库

参考文档在 `references/`（共 21 篇 + knowledge_index，编号 01–22 中 `09` 已移除，详见下方索引表）：使用说明（快速上手）、连接与发现、
需求冲突检查、命令规则、二/三层技术、验证与排障、高级技术概览、能力框架对照、
术语对照（锐捷↔思科）、认证考点、报告模板、拓扑截图解析、GNS3 拓扑自动搭建、三级考纲覆盖矩阵，
以及无线/广域网、RGSP 可靠性与安全、RGSE 高级技术深化（BGP/IS-IS/MPLS/IPv6/SR/EVPN VXLAN/QoS/组播/IPSec）。

---

## 一、核心原则：AI 的思考方式

> 这部分是 skill 的"灵魂"，每次执行都必须遵守。

1. **多思考**：动手前先想清楚四件事——拓扑物理连接、业务需求、地址/VLAN 规划、
   每台设备的角色与关键技术点。不要拿到题就无脑敲命令。每一步配置前都在脑里
   先推演"这条命令下去会发生什么、验证该看什么"。
2. **多分析**：出现报错或验证不通时，**分层定位**（物理层 → 数据链路层 → 网络层 →
   策略层），先找根因再处理，禁止盲目反复重试同一条命令。
3. **不要一条命令出错就逃避（重点）**：单条命令报错（含 `^` 截断、`Ambiguous`、
   `Invalid`、`Incomplete`）时，**绝对禁止跳过它或绕开它**。必须先思考"为什么错"——
   是视图进错、参数不全、语法差异、还是该平台不支持——把**假设 + 已排查项**向用户
   总结清楚，再给出修正后的命令重试。逃避只会造成后面更大的连锁故障；宁可多想几轮、
   多 ping/多 show 几次，也不要因为一条命令报错就放弃整段配置。
4. **多总结**：每完成一个阶段，用一句话向用户总结"当前状态 + 已验证 + 风险点"；
   遇到报错时额外总结"错在哪、为什么、下一步怎么改"。
5. **不确定就汇总询问**：凡是题面有歧义、关键参数未给定、存在多种合理方案、或环境
   与预期不符——先把所有疑问**汇总成清单**一次性问用户，绝不擅自假设后直接执行。
6. **主动汇报**：连接是否成功、配置进度、验证结果、发现的需求冲突，都要主动告诉用户，
   而不是等用户来问。

---

## 二、适用场景

- 连接 **GNS3 模拟器**（内运行锐捷 RG-NSE 的 RGOS V1.06 设备镜像），设备以 telnet 端口暴露
- 二层/三层交换、路由、可靠性、安全类实验（含上述技术栈）
- 用 `show` 系列命令核验、用 `ping`/`trace`（VPCS 终端）做连通性与路径验证
- 实验前的需求评审与冲突检查、实验后的排障复盘

> 注意：本环境里**终端是 VPCS**（`PC1>` 提示符，无 `configure terminal`），
> 交换机/路由器是 RGOS（`hostname#` / `hostname(config)#`）。两类设备的配置方式不同，
> 下发前务必识别设备类型（见 `references/01-连接与发现.md`）。

---

## 三、标准工作流（SOP，9 个阶段）

### ★ 完全托管模式（用户给一张拓扑图，其余全自动）
> 这是本 skill 的 headline 能力：**用户只提供拓扑图片 + GNS3 API 地址，其余零操作**——
> 不拉拓扑、不开机、不配置，只需在观摩窗口里看 AI 配。
> 唯一可能绕不开的用户操作：环境缺镜像时需要用户先导入（见第 2 步）。

自动执行序列（AI 按序推进，无需用户干预）：

1. **解析拓扑图** → 连接表（`references/15`），列出请用户**确认**（识别歧义逐条标出，不猜）。
2. **镜像/图标自检**：`topo_build.py list-templates --api <API>` 核对拓扑所需设备型号的
   模板、磁盘镜像、专属图标是否齐全。**缺模板/缺镜像/缺图标都停下来**，明确告诉用户
   "需先导入 X 镜像（或补全图标）"，不硬跑。
3. **搭建**：`topo_build.py build --api <API> --topo topo.json --start --out lab_config.json`
   ——建项目→放节点→连线→启动，输出「设备名→端口」映射（建后自检 name/symbol）。
4. **等引导**：RGOS 内核引导约 30–60s，等够再连，避免误判离线（`references/17`）。
5. **拉端口映射**：以 `status` 返回的 console 端口为准，更新 `lab_config.json`。
6. **开观摩窗**：询问用户后 `open_console.py open --config lab_config.json`，批量弹 telnet 窗口。
7. **配置**：阶段 4→5 自动下发（基本配置→按模块叠加→策略最后）。
8. **验证**：阶段 6 分阶段验证（基础连通→加策略后），留档 `verify_logs/`。
9. **报告**：阶段 8 输出验证结论表。

> 中断续跑：任何一步失败都**不跳过不逃避**（见思考原则第 3 条），定位修复后从断点继续；
> `topo_build.py` 的链路幂等 + `deploy.py` 的下发前备份保证重复执行安全。

---

### 阶段 0　连接与发现（主动询问 IP + 端口扫描）
> 若拓扑尚未搭建：走上方「完全托管模式」第 1–5 步（用户给拓扑图片 + GNS3 API 地址），
> 用 `scripts/topo_build.py` 自动建项目/节点/链路/启动并输出端口映射，直接跳到本阶段第 3 步。

1. **主动询问**用户当前 GNS3 模拟器所在主机的 IP。不要硬编码，每次都问。
2. 拿到 IP 后，**扫描该主机开放的可 telnet 端口**（用 `scripts/connect.py` 的
   `scan_ports`），常见段如 5000–5020、2000–2100。把"端口 → 设备"映射列出给用户确认。
3. 逐个 telnet 连上，**唤醒**设备（发回车）、进入特权模式 `enable`，读取 `show version`/
   `show running-config` 摘要，确认设备类型（交换机/路由器/VPCS）与当前主机名。
4. 把连接结果汇总给用户，再进入下一阶段。

> 若用户提供了**拓扑截图 / 托盘截图 / 拓扑图**，先按 `references/15-拓扑截图解析.md`
> 解析成连接表，再与端口扫描结果交叉核对（截图仅作草图，端口号以设备 `show interface` 实际为准）。

### 阶段 1　需求分析与冲突检查（必须先做）
- 把题面逐条拆成"硬性需求"，逐项检查是否存在**技术冲突**。
- 经典冲突示例与解法见 `references/02-需求冲突检查.md`：
  - 标准 ACL 按源地址过滤 → "两 PC 互访"与"标准 ACL 隔离"互斥 → 要么改扩展 ACL，
    要么删除互访需求（见 `references/02-需求冲突检查.md` 的冲突示例）。
  - 公网网段掩码不一致（/24 vs /30）、NAT 地址池不在直连段需回程路由等。
- **发现冲突先停下来，向用户说明并给出 2–3 个可选方案，等用户拍板后再配置。**

### 阶段 2　规划（把脑子里的东西落表）
在动手前先产出一张规划表，至少包含：
- VLAN 规划（VLAN ID / 名称 / 网段 / 网关 / SVI 地址 / DHCP 范围）
- 互联链路规划（点对点网段、两端地址、承载 VLAN）
- 设备角色与关键技术（哪台是根桥、VRRP 主备、OSPF Router-ID、NAT 边界）
- 地址未给定处，由考生/用户规划并在表中写明（不要留空）。

### 阶段 3　确认改名（设备改名 + shell 对话框改名）
- **询问用户**：是否要把每台设备改成题面要求的名称（如 SW1/SW2/SW3 → S1/S2/S3），
  以及**是否把每个 shell/终端对话框也改了名**以便区分。
- 改名用 `hostname xxx`，并 `write` 保存。
- 只有当用户确认"已改名且 shell 也改名"后，后续流程才按新名称引用设备。

### 阶段 3.5　打开观摩窗口（配置前，询问用户）
- **询问用户**：是否需要打开各设备的观摩窗口，让配置过程对你可见。
- 用户同意后执行 `python scripts/open_console.py open --config lab_config.json`：
  自动发现其机器上的终端工具（Xshell / SecureCRT / PuTTY / MobaXterm / WindTerm，
  依次查注册表、安装目录、PATH、桌面便携版），按端口映射批量打开 telnet 窗口。
- GNS3 console 支持多连接，观摩窗口与 AI 自己的 telnet 通道互不影响。
- 一台工具都没装时：脚本会打印 `telnet <IP> <端口>` 清单，提示用户手动连接或安装工具。
- 用户拒绝观摩则跳过，不影响后续配置。

### 阶段 4　基本配置（每台设备先做）
- 改主机名、关掉无关服务（`no cwmp`）、`service dhcp`（若需）、`logging synchronous`、
  `spanning-tree` 全局开启等。
- 创建所需 VLAN（`vlan 10` / `vlan 20` / `vlan 99` / `vlan 100` 等）。
- 进入配置模式的正确顺序：`enable` → `configure terminal`（VPCS 例外）。

### 阶段 5　具体配置（按模块叠加）
顺序建议：**接入层 → 汇聚层 → 核心/边界 → 终端 → 策略最后下发**。
常见模块见 `references/`：
- 二层：`VLAN / Trunk / 链路聚合(AggregatePort) / MSTP 多实例 / 端口安全 / BPDU Guard`
- 三层：`SVI / VRRP / OSPF 区域0 / Loopback(Router-ID)`
- 服务：`DHCP 与中继(ip helper-address) / NAPT / 标准&扩展 ACL`
- **策略类（ACL）单独最后下发**，便于先验证基础连通、再加策略验证隔离效果。

### 阶段 6　验证效果（show + ping + trace，分阶段）
- **阶段验证 A（基础连通）**：下发完二三层后，先验证 VLAN、Trunk、聚合、OSPF 邻居、
  VRRP 状态、DHCP 获取。
- **阶段验证 B（加策略后）**：下发 ACL 后再验证隔离是否生效、其余业务是否不受影响。
- 终端侧用 `ping` / `trace`（VPCS），网络设备侧用 `show` 系列。清单见
  `references/07-验证与排障.md` 与 `scripts/verify.py`。
- 注意：**协议刚配完有收敛时间**（OSPF/VRRP/MSTP），等几秒再验证，避免"假故障"。

### 阶段 7　排障（分层定位）
按 `物理 → 二层 → 三层 → 策略` 逐层排查，常用命令与典型症状见
`references/07-验证与排障.md`。核心心法：**先看 show 状态，再比对规划表，最后改配置**。

### 阶段 8　总结与询问（收尾）
- 输出一份验证结论表（每项需求是否满足、证据命令、是否达标）。
- **把实验中所有"不确定 / 用户未给定 / 我的假设"汇总成清单，一次性询问用户**。
- 如用户要求，备份各设备 `show running-config` 到本地。

---

## 四、锐捷 RGOS 命令规则（必知）

### 4.1 配置上下文依赖
- 用户模式 `Switch>` → `enable` → 特权模式 `Switch#` → `configure terminal` →
  全局配置 `Switch(config)#` → `interface xxx` → 接口配置 `Switch(config-if)#`。
- **VPCS 终端没有配置模式**：直接在 `PC1>` 下敲命令（如 `ip dhcp`、`show ip`），
  不要写 `configure terminal`。
- 子命令缩进表示它属于上一级上下文（如 `vrrp 10 priority 120` 在 `interface vlan 10` 内）。

### 4.2 `no` 命令与 `^` 截断规则（重点）
- 删除某条配置：`no <原命令>`。例如 `no ip address`、`no vlan 20`、`no access-list 1`。
- **`^` 表示命令行在 `^` 处被截断/报错**（设备回显里常出现 `        ^` 指向出错位置）。
  当上一条长命令因 `^` 报错时，**只需从 `^` 之前截断重发**，不必整行重试。
  例：
  ```
  no  123  123  123  123  123  123
        ^
  ```
  只需执行 `no 123 123 123` 即可删除上一条配置；后面的 `123 123 123` 是多余导致 `^`。
- 删整段配置（如整条 ACL）用 `no ip access-list standard 1` 比逐条删更稳妥。

### 4.3 拿不准的命令用 `?` 补全
- 在任意上下文敲 `?` 看当前可用的后续关键字；`命令 ?` 看该命令的参数。
- 遇到 `Ambiguous command`（歧义）时，用 `?` 补全到唯一匹配再回车。
- 拿不准完整语法时，先 `?` 探路，再写进下发脚本，避免反复试错刷屏。

### 4.4 保存与备份
- 配置生效后要 `write`（或 `write memory`）保存到 startup-config，否则重载即丢。
- 动大改前先 `show running-config` 备份（本 skill 的 `deploy.py` 会在每台设备下发后自动 `write`）。

---

## 五、按需路由表（省 token，先看这里再决定读哪篇）

> **关键机制：`references/` 是"用哪篇读哪篇"，不要一次读全 21 篇。**
> 先按下方任务类型定位到 1–3 篇，只读这几篇即可，其余不读。读完按文档里的
> 命令序列执行，遇到报错再按需翻 `07`/`10` 排障。

| 你要做的事 | 只读这几篇（编号） |
| --- | --- |
| 连设备 / 扫端口 / 识别设备类型 / 进特权 | `01` |
| 接到新题、拆需求、查冲突 | `02` |
| 命令语法（no/^/?/write）、基本配置 | `03` |
| 二层：VLAN/Trunk/聚合/MSTP/端口安全/BPDU | `04` |
| 三层：SVI/VRRP/OSPF/Loopback | `05` |
| 服务：DHCP 中继/NAT/ACL | `06` |
| 验证或排障（show/ping/trace、分层定位） | `07` |
| 排障踩坑速查（易错点） | `10` |
| 无线 / 广域网 / AP / AC / PPP | `19` |
| 可靠性：BFD/RLDP/VSU、策略路由 PBR、AAA 安全 | `20` |
| 高级路由：BGP 高级/IS-IS/MPLS/IPv6 | `21` |
| SR / EVPN VXLAN / QoS / 组播 / IPSec / 规划设计 | `22` |
| 看考纲覆盖情况 / 规划补学路径 | `18` |
| 锐捷↔思科命令对照 | `12` |
| 认证考点与易错辨析 | `13` |
| 拓扑截图解析成连接表 | `15` |
| GNS3 自动搭建拓扑（API） | `17` |
| 写巡检/变更/验证报告模板 | `14` |
| 告知使用者怎么上手 / 观摩窗口说明 | `16` |
| 术语/框架结构参考（锐捷优先，对照用） | `11` |

> 通用流程（阶段 0–8）本文件已写全，默认无需额外读文档；仅在进入某一具体模块时，
> 按上表读对应 1 篇即可。

---

## 五、参考文档索引（`references/`）

| 文件 | 内容 |
| --- | --- |
| `01-连接与发现.md` | telnet 连接、端口扫描、设备类型识别、唤醒与 enable |
| `02-需求冲突检查.md` | 冲突类型、识别方法、可选解法（含标准/扩展 ACL 取舍） |
| `03-命令规则与基本配置.md` | no/^、?、上下文、`write`、基本配置清单 |
| `04-二层技术.md` | VLAN / Trunk / 链路聚合 / MSTP / 端口安全 / BPDU Guard |
| `05-三层与路由.md` | SVI / VRRP / OSPF / Loopback-Router-ID |
| `06-DHCP与NAT与ACL.md` | DHCP 与中继、NAPT、标准/扩展 ACL 写法与注意事项 |
| `07-验证与排障.md` | show 清单、ping/trace 验证、分层排障表 |
| `08-高级技术概览.md` | RGSE 级高级路由交换：BGP / IS-IS / MPLS·MPLS VPN / 组播 / QoS / IPv6 / VSU / 重分布 |
| `10-蒸馏速查-易错点.md` | **蒸馏自用户 7 份 RGSA/RGSP/RGSE 笔记**的实战踩坑速查（VLAN/OSPF/ACL/NAT/BGP 等） |
| `11-能力框架对照.md` | 锐捷 RGOS 视角，借华为 30 点做结构参考（锐捷优先声明 + 已实现/可借鉴/不需要标注） |
| `12-术语对照-锐捷与思科IOS.md` | 锐捷 RGOS ↔ 思科 IOS 命令对照与差异（锐捷命令体系源自思科） |
| `13-锐捷认证考点与易错辨析.md` | 按 RGSA/RGSP/RGSE 三级整理的考点→易错→验证（蒸馏自笔记） |
| `14-交付物模板-巡检变更验证报告.md` | 验证 / 巡检 / 变更 三张标准报告模板 |
| `15-拓扑截图解析.md` | 多模态输入：拓扑截图→连接表+拓扑图（识别+人工确认） |
| `16-使用说明-快速上手.md` | **面向使用者**：告知 GNS3 端口地址格式 → AI 确认所有设备开启 → 询问并执行改名 |
| `17-GNS3拓扑自动搭建.md` | 拓扑图片→topo.json→API 自动建项目/节点/链路/启动→端口映射落盘接管（含凭据说明与实测坑） |
| `18-锐捷三级考纲覆盖矩阵.md` | RGSA/RGSP/RGSE 官方考纲→现状覆盖矩阵（✅/🟡/❌），补全施工蓝图 |
| `19-无线WLAN与广域网.md` | 无线基础/胖瘦AP、AC 组网与网优、广域网（PPP/PPPoE/认证） |
| `20-RGSP可靠性安全与策略路由.md` | BFD、RLDP 环路检测、VSU 深化、策略路由 PBR、AAA/网络安全 |
| `21-BGP与ISIS与MPLS与IPv6深化.md` | BGP 高级（RR/选路）、IS-IS、MPLS/MPLS VPN、IPv6（含 OSPFv3） |
| `22-SR与EVPNVXLAN与QoS组播IPSec.md` | SR、EVPN VXLAN、QoS、组播、IPSec、网络规划设计方法论 |
| `knowledge_index.md` | 知识来源说明：references 为蒸馏内置，原始课件/笔记可选自备 |

---

## 六、脚本使用（`scripts/`）

所有实验参数（host / 设备端口 / 类型 / 配置命令）都在 `scripts/lab_config.json` 里，
**脚本本身不写死任何实验**，任何人填自己的配置即可。首次使用先复制模板：
`cp lab_config.example.json lab_config.json` 并按题面修改。

```bash
# 0) 询问拿到 GNS3 模拟器主机 IP 后，扫描开放端口，主动发现设备
python connect.py scan --host <GNS3模拟器IP> --start 5000 --end 5020

# 1) 连单台设备进特权模式执行命令（host/port 来自你的 lab_config.json）
python connect.py shell --host <GNS3模拟器IP> --port <设备端口> --run "show version"

# 2) 先空跑预览（不连设备、不下发），确认计划无误
python deploy.py --dry-run

# 3) 正式下发（默认先备份 running-config，并打印清单让你确认）
python deploy.py                 # 全部设备
python deploy.py SW1 SW2         # 仅指定设备
python deploy.py ACL             # 仅下发策略阶段（建议最后发）

# 4) 分阶段验证（stage 名对应 lab_config.json 里的 verify_plan，缺省按设备类型通用验证）
python verify.py before_acl
python verify.py after_acl
```

> 安全护栏：`deploy.py` 下发前自动备份每台网络设备的 `running-config` 到 `backups/`，
> 并会打印设备清单要求确认（`--yes` 跳过确认）；强烈建议先 `--dry-run`。
> 默认主机/端口**不要写死**，每次按阶段 0 的扫描结果填进 `lab_config.json`。
