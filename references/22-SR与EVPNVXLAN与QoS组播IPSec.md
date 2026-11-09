# 22　SR、EVPN VXLAN、QoS、组播、IPSec 与规划设计（RGSE 深化）
> **作者 / Author**：白虬髯 (Bai Qiuran)　·　**许可 / License**：署名-非商业性使用（禁止商用，二创须保留原作者署名，详见 LICENSE）　·　**版本 / Version**：v1.0


> 补齐 RGSE 缺失项：**SR、EVPN VXLAN**，并深化 **QoS、组播、IPSec、规划设计方法论**。
> 命令以锐捷 RGOS 为准（`show` 非 `display`），拿不准处用 `?` 实测。

## 一、SR（Segment Routing，分段路由）

### 1.1 原理
- SR 用**源路由**思想：源节点把路径压成**段（Segment）列表**（SID），转发节点按 SID 列表逐跳转发，无需在中间节点维护每条业务的状态。
- 数据面分 **SR-MPLS**（SID 编码为 MPLS 标签）与 **SRv6**（SID 编码为 IPv6 地址）。
- 控制面：SR-MPLS 靠 IGP（OSPF/IS-IS）扩展（Segment 分发）；标签分配用 **SRGB（全局标签块）**，Prefix-SID 全局唯一。

### 1.2 关键概念
| 概念 | 说明 |
| --- | --- |
| Prefix-SID | 节点前缀对应的全局 SID，IGP 泛洪 |
| Adjacency-SID | 链路段 SID，仅本地有效 |
| SRGB | 全局标签范围，如 16000–23999 |
| SR-TE | 用 SR 实现流量工程（取代 RSVP-TE） |

### 1.3 配置骨架（SR-MPLS + IS-IS）
```
mpls ip
router isis
 net 49.0001.1111.1111.1111.00
 segment-routing mpls
 segment-routing global-block 16000 23999
interface loopback 0
 ip router isis
 isis prefix-sid index 100      ! 给 loopback 分配 index，映射到 SRGB 标签
```
- 易错：SRGB 全网要一致（或需换算）；Prefix-SID 要在 loopback 上通告。
- 验证：`show isis segment-routing`、`show mpls forwarding-table`、`show ip route`。

## 二、EVPN VXLAN

### 2.1 原理
- **VXLAN** 用 UDP（目的端口 4789）在 L3 网络上打隧道承载二层，**VNI**（24bit，约 1600 万）隔离租户，解决传统 VLAN（4096）不足 + 大二层扩展。
- **EVPN** 是 VXLAN 的控制面（MP-BGP EVPN 地址族），用 **Type-2（MAC/IP 路由）、Type-3（组播）、Type-5（前缀路由）** 传递，替代纯数据面泛洪学习。
- 角色：**VTEP**（隧道端点，做 VXLAN 封装/解封）；**VNI ↔ VLAN 映射**在接入 VTEP。

### 2.2 配置骨架
```
vxlan vni 10010                      ! 定义 VNI
 bridge-domain 10010
  vxlan vni 10010                    ! VNI 与 BD 绑定
interface nve 1
 source-interface loopback 0         ! VTEP 源
 member vni 10010 mcast-group <组播组地址>   ! 头端复制（或用 EVPN BGP）
router bgp 65001
 address-family l2vpn evpn
  neighbor <对端Loopback> activate
  neighbor <对端Loopback> send-community extended
```
- 易错：VTEP 之间要**三层可达**（loopback 路由）；EVPN 用 MP-BGP，RT 要匹配；头端复制需组播可达（或配 BGP EVPN 免组播）。
- 验证：`show vxlan vni`、`show nve peers`、`show bgp l2vpn evpn summary`、`show bridge-domain`。

## 三、QoS 深化

### 3.1 模型
- **分类 → 标记 → 队列调度 → 拥塞避免 → 整形/限速**。
- 信任边界、优先级字段：二层 CoS（802.1p）、三层 DSCP/IP Precedence。

### 3.2 配置骨架
```
class-map match-any VOICE
 match dscp ef
policy-map EDGE
 class VOICE
  priority percent 30          ! 低时延队列 LLQ
class-map class-default
policy-map EDGE
 class class-default
  bandwidth percent 20         ! 剩余带宽
interface gigabitEthernet 0/1
 service-policy output EDGE
```
- 易错：**核心层高速转发不要加控制类配置**；`priority` 会优先调度，需防饿死其他队列。
- 验证：`show policy-map interface`、`show class-map`、`show queueing interface`。

## 四、组播深化

### 4.1 原理
- IGMP（终端↔路由器）+ PIM（路由器间）。PIM 分 DM（密集，推后剪枝）/ SM（稀疏，靠 RP 汇聚）/ SSM（指定源）。
- **RPF 检查**：收到组播的入接口必须是指向源的最优下一跳，否则丢弃（防环）。
- SM 核心：**RP（汇聚点）**，接收者经 `(*,G)` 向 RP 建树，源向 RP 注册。

### 4.2 配置骨架
```
ip multicast-routing
interface gigabitEthernet 0/1
 ip pim sparse-mode
 ip igmp version 3
ip pim rp-address x.x.x.x          ! 指定 RP（示例占位）
```
- 易错：RPF 失败要剪枝；RP 配置全网一致（或 BSR 自动选举）；两接口收相同组播时竞选 iif。
- 验证：`show ip mroute`、`show ip pim neighbor`、`show ip igmp groups`、`show ip pim rp mapping`。

## 五、IPSec 深化

### 5.1 原理
- IPSec 提供机密性（加密）+ 完整性 + 抗重放 + 源认证。两阶段：**IKE SA（协商密钥）→ IPSec SA（加密数据）**。
- 模式：**传输模式**（仅加密载荷，端到端）/ **隧道模式**（加密整个 IP 头，站点间 VPN）。
- 组件：AH（完整性）/ ESP（加密+完整性，主流）。

### 5.2 配置骨架（站点到站 VPN）
```
crypto isakmp policy 10
 encryption aes 256
 hash sha256
 authentication pre-share
 group 14
crypto isakmp key 0 <共享密钥> address <对端地址>
crypto ipsec transform-set TS esp-aes esp-sha-hmac
access-list 100 permit ip 10.1.0.0 0.0.0.255 10.2.0.0 0.0.0.255
crypto map VPN 10 ipsec-isakmp
 set peer <对端地址>
 set transform-set TS
 match address 100
interface gigabitEthernet 0/0
 crypto map VPN
```
- 易错：**经过 NAT 源地址必变**，影响 IPSec 身份与 ACL 匹配（需 NAT 穿透或先 NAT 后 IPsec）；
  **DPD 不能用手工 SA**；两端 proposal（加密/哈希/组）必须一致。
- 验证：`show crypto isakmp sa`、`show crypto ipsec sa`、`show crypto map`。

## 六、网络规划设计方法论（局域网/路由）

### 6.1 局域网设计
- 分层：**接入层 → 汇聚层 → 核心层**；接入做端口隔离/VLAN，汇聚做网关/策略/冗余，核心做高速转发/不做复杂控制。
- 冗余：核心/汇聚双机 VRRP + 链路聚合/MSTP，消除单点。
- 地址规划：按业务分 VLAN、预留扩展、网关统一 SVI。

### 6.2 路由规划设计
- 园区内 IGP 选 OSPF/IS-IS（区域规划：area 0 骨干 + 非骨干）；出口用静态/默认 + BGP（多出口）。
- 选路：双出口用 PBR/BGP 属性做流量分担与主备；引入路由要防环（route-map/度量/标签）。
- 锐捷典型方案：园区"核心-汇聚-接入"三层 + VSU 简化 + AC 无线 + 出口防火墙/NAT。

### 6.3 设计输出物（对齐 14 交付模板）
网络拓扑图 → IP/VLAN 规划表 → 设备清单与角色 → 冗余/高可用设计 → 安全策略 → 验证方案。
