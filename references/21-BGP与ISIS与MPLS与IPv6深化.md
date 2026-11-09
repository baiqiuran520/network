# 21　BGP 高级、IS-IS、MPLS 与 IPv6（RGSE 深化）
> **作者 / Author**：白虬髯 (Bai Qiuran)　·　**许可 / License**：署名-非商业性使用（禁止商用，二创须保留原作者署名，详见 LICENSE）　·　**版本 / Version**：v1.0


> 把 RGSE 的 BGP 高级、IS-IS、MPLS/MPLS VPN、IPv6 从"概述级"深化到**可落地配置**。
> 命令以锐捷 RGOS 为准（`show` 非 `display`），拿不准处用 `?` 实测。

## 一、BGP 高级特性

### 1.1 邻居与源接口
- EBGP 默认 TTL=1（直连建邻）；用 loopback 建邻需 `neighbor x.x.x.x ebgp-multihop 2` + `update-source loopback 0`。
- IBGP 默认 TTL=255，全互联或用**路由反射器 RR / 联盟**。
```
router bgp 65001
 bgp router-id <本机Loopback>
 neighbor <对端Loopback> remote-as 65001
 neighbor <对端Loopback> update-source loopback 0
 neighbor <对端Loopback> next-hop-self
```

### 1.2 路由反射器（RR）
- RR 反射路由给客户端，避免 IBGP 全互联。**反射规则**：从客户端学到的反射给所有（客户端+非客户端）；
  从非客户端学到的只反射给客户端。
```
router bgp 65001
 neighbor <客户端Loopback> route-reflector-client   ! 把 <客户端Loopback> 设为客户端
```
- 易错：**RR 必须有一方是客户端**才反射；RR 与客户端间不能有普通 IBGP 邻居冲突。

### 1.3 选路属性（权重→LocalPref→AS-PATH→Origin→MED…）
| 属性 | 方向 | 命令 |
| --- | --- | --- |
| Weight（本地） | 出向选路 | `neighbor x route-map in` set weight |
| Local-Pref | IBGP 内选 | `bgp default local-preference 200` |
| AS-PATH | 防环+选路 | `set as-path prepend 65001 65001` |
| MED | 跨 AS 入向建议 | `set metric 100` |
```
route-map SETLP permit 10
 set local-preference 200
router bgp 65001
 neighbor <对端Loopback> route-map SETLP in
```

### 1.4 验证
`show ip bgp summary` / `show ip bgp` / `show ip bgp neighbors <对端Loopback>` / `show ip bgp neighbors <对端Loopback> advertised-routes`

## 二、IS-IS

### 2.1 原理
- 链路状态 IGP，分层 **Level-1（区域内）/ Level-2（骨干）/ Level-1-2**。
- 标识：**NET 地址**（Area ID + System ID + NSEL，NSEL 恒 00）；System ID 全局唯一。

### 2.2 配置骨架
```
router isis
 net 49.0001.1111.1111.1111.00       ! Area 49.0001，System-ID 1111.1111.1111
 is-type level-1-2
interface gigabitEthernet 0/1
 ip router isis                          ! 接口加入 ISIS
```
- 易错：**level-1 不能直接和 level-2 建邻，必须经 level-1-2**；
  一个设备最多 3 个 net，area-id 可不同但 **system-id 必须一致**；
  `net` 的 NSEL 段恒为 00。

### 2.3 验证
`show isis neighbors` / `show isis database` / `show isis route`

## 三、MPLS 与 MPLS VPN

### 3.1 MPLS 基础
- 标签转发：LER（边缘）打/剥标签，LSR（核心）按标签交换，LDP 分发标签。
```
mpls ip
interface gigabitEthernet 0/0
 mpls ip                  ! 接口启用 MPLS
```
- 验证：`show mpls ldp neighbor`、`show mpls forwarding-table`、`show mpls ldp binding`。

### 3.2 MPLS L3VPN（MP-BGP + VRF）
- 用 VRF 隔离租户，MP-BGP VPNv4 传递路由，**RT（route-target）决定 import/export**。
```
ip vrf CUST_A
 rd 65001:100
 route-target export 65001:100
 route-target import 65001:100
interface gigabitEthernet 0/1
 ip vrf forwarding CUST_A
 ip address x.x.x.x 255.255.255.0   ! 示例占位
router bgp 65001
 address-family vpnv4
  neighbor <对端Loopback> activate
  neighbor <对端Loopback> send-community extended
```
- 易错：**RT 必须一方 export 被另一方 import** 才通；PE 之间要建 VPNv4 邻居；VRF 接口地址不能与全局冲突。

### 3.3 验证
`show ip vrf` / `show bgp vpnv4 all summary` / `show ip route vrf CUST_A` / `show mpls forwarding-table`

## 四、IPv6 深化

### 4.1 地址与邻居发现
- 地址类型：链路本地（fe80::/10，仅链路内）、全局单播、组播。**无广播，用 ND（邻居发现）替代 ARP**。
- 无状态自动配置（SLAAC）：路由器 RA 通告前缀，终端用 EUI-64 生成地址，**前缀必须是 /64**。

### 4.2 配置骨架（双栈）
```
ipv6 unicast-routing
interface gigabitEthernet 0/1
 ipv6 address 2001:db8:1::1/64
 ipv6 enable
interface loopback 0
 ipv6 address 2001:db8::1/128
ipv6 route 2001:db8:2::/64 2001:db8:1::2
```
### 4.3 OSPFv3
```
router ospfv3 1
 router-id <本机Loopback>
interface gigabitEthernet 0/1
 ipv6 ospf 1 area 0
```
- 易错：OSPFv3 用 **router-id（IPv4 形式）标识路由器**（不自动从接口取）；区域划分、进程号与地址族分离。
- 验证：`show ipv6 interface brief`、`show ipv6 route`、`show ipv6 ospf neighbor`、`show ipv6 neighbors`（ND 表）
