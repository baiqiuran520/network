# 知识来源说明（knowledge_index）

本 skill 已**蒸馏内置**锐捷数据通信的核心知识，用户无需准备任何外部文件，导入即用。

## 内置内容（蒸馏产物，开箱即用）
- `references/01~08`：核心方法论（连接发现、需求冲突、命令规则、二层、三层与路由、
  DHCP/NAT/ACL、验证与排障、RGSE 高级路由交换），覆盖 **RGSA（Associate）/
  RGSP（Professional）/ RGSE（Expert）三级别**的数据通信主干知识。
  > 说明：编号 `09` 已移除（原为真实题目案例，为通用化而删除），示例均改为文字占位符（如 `x.x.x.x`）。
- `references/10-蒸馏速查-易错点.md`：**从用户 7 份 RGSA/RGSP/RGSE 笔记中蒸馏出的实战踩坑速查**
  （VLAN/Super-VLAN、STP/MSTP、OSPF 特殊区域与虚链路、ACL、DHCP 中继、NAT/NAPT、
  BGP、IS-IS、重分布、VSU、IPv6 等高频易错点）。

## 内置范围说明
- 本 skill **覆盖 RGSA / RGSP / RGSE 三级别全量**（含无线/广域网、可靠性、安全、BGP/IS-IS/MPLS/
  IPv6/SR/EVPN VXLAN/QoS/组播/IPSec 等高级技术），不含 RCIE、安全产品等更专项的认证。
- 不随包附任何课件 pptx 或笔记原文件（体积与版权考量）；其精华已蒸馏进上面的 `references/`。

## 本次新增参考（v1.1）
- `11-能力框架对照.md`：把一份「华为 30 点网络 Skill 框架」映射为锐捷 RGOS 视角，标注已实现/可借鉴/不需要，并给出锐捷版 MVP 取舍。
- `12-术语对照-锐捷与思科IOS.md`：锐捷命令体系源自思科，列出常用命令对照与少量差异（AggregatePort、MSTP name/revision、VSU、NQA/Track 等）。
- `13-锐捷认证考点与易错辨析.md`：从用户 7 份笔记蒸馏，按 RGSA/RGSP/RGSE 三级组织「考点→易错→验证」。
- `14-交付物模板-巡检变更验证报告.md`：验证 / 巡检 / 变更 三张标准报告模板。
- `15-拓扑截图解析.md`：多模态输入能力——拓扑截图解析成连接表+拓扑图（识别+人工确认）。
- `16-使用说明-快速上手.md`：面向使用者的上手指南——告知 GNS3 端口地址 → AI 确认所有设备开启 → 询问并执行改名。

## 本次新增（v1.2）
- `scripts/topo_build.py` + `17-GNS3拓扑自动搭建.md`：GNS3 拓扑自动搭建闭环——拓扑图片解析为 topo.json 后，
  经 GNS3 API 自动建项目/放节点/连线/启动，输出「设备名→telnet端口」映射直接接管配置；含凭据说明与实测坑（模板实例化端点、builtin 节点、自动编号改名无效、坐标角色映射）。

## 本次新增（v1.3）
- `scripts/open_console.py`：观摩窗口——自动发现用户机器上的终端工具（Xshell/SecureCRT/PuTTY/MobaXterm/WindTerm），按端口映射批量打开 telnet 窗口，配置过程用户可见。
- SKILL.md 新增「完全托管模式」节 + 阶段 3.5（观摩）。

## 本次新增（v1.4 · 三级考纲全量补全）
- `18-锐捷三级考纲覆盖矩阵.md`：RGSA/RGSP/RGSE 官方考纲 → 现状覆盖矩阵（✅/🟡/❌），补全施工蓝图。
- `19-无线WLAN与广域网.md`：无线基础、胖/瘦 AP、AC 组网与网优、广域网（PPP/PPPoE/认证）。
- `20-RGSP可靠性安全与策略路由.md`：BFD、RLDP 环路检测、VSU 深化、策略路由 PBR、AAA/网络安全。
- `21-BGP与ISIS与MPLS与IPv6深化.md`：BGP 高级（RR/选路属性）、IS-IS、MPLS/MPLS VPN、IPv6（含 OSPFv3）。
- `22-SR与EVPNVXLAN与QoS组播IPSec.md`：SR、EVPN VXLAN、QoS、组播、IPSec、网络规划设计方法论。
> 补全原则：**锐捷优先**，命令以 RGOS 语法为准（show 非 display），拿不准处用 `?` 实测标注。

## 可选自备（增强，非必需）
如想把**你自己的同级别课件原文**也纳为可自查资料，可用：
```bash
python scripts/fetch_courseware.py --src "你的课件目录" --out knowledge_base
```
生成 `knowledge_base/` 后，可在 references 中按需引用。这一步纯增强，不做也不影响任何功能。
