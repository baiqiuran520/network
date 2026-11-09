# 20　RGSP 可靠性、安全与策略路由（BFD / RLDP / VSU / PBR / AAA）
> **作者 / Author**：白虬髯 (Bai Qiuran)　·　**许可 / License**：署名-非商业性使用（禁止商用，二创须保留原作者署名，详见 LICENSE）　·　**版本 / Version**：v1.0


> 覆盖 RGSP 缺失项：**BFD、RLDP 环路检测、策略路由 PBR、AAA/网络安全**，并**深化 VSU**。
> 命令以锐捷 RGOS 为准（`show` 非 `display`），拿不准处用 `?` 实测。

## 一、BFD（双向转发检测，快速故障感知）

### 1.1 原理
- BFD 用毫秒级 hello 快速检测链路/下一跳故障，为上层协议（OSPF/BGP/VRRP/静态路由）提供**快速收敛**触发。
- 相比协议自身 hello（秒级），BFD 可做到 50ms×3 内发现故障，配合 track/协议联动实现亚秒收敛。
- 会话分**异步模式**（默认）与查询模式；参数：发送/接收间隔、检测倍数（detect multiplier）。

### 1.2 静态路由联动 BFD 配置骨架
```
bfd
 exit
interface gigabitEthernet 0/1
 bfd interval 50 min_rx 50 multiplier 3     ! 本接口 BFD 参数
 ip address x.x.x.x 255.255.255.0           ! 示例占位
ip route 0.0.0.0 0.0.0.0 <下一跳>
 bfd <下一跳>                                ! 静态路由绑定 BFD 下一跳
```
> 与 track 的关系：BFD 检测更快，常替代 NQA/track 做快速切换；也可 BFD→track→静态路由多级联动。

### 1.3 OSPF/BGP 联动
- OSPF：接口下 `ip ospf bfd` 或全局 `bfd all-interfaces`；
- BGP：`neighbor x.x.x.x fall-over bfd`。
- 验证：`show bfd neighbors`、`show bfd sessions`。

## 二、RLDP（环路检测协议）

### 2.1 原理与用途
- RLDP 用于**检测网络中私自连接造成的二层环路**（如误把交换机两端口对接）。
- 检测到环路时可选动作：告警、`shutdown` 端口（可设恢复时间）、或只记录。
- 常与 STP 互补：STP 防环（逻辑阻断），RLDP 是**主动发现**物理环路并处置。

### 2.2 配置骨架
```
rldp enable                          ! 全局开启
interface gigabitEthernet 0/1
 rldp port loop-detect shutdown-port ! 检测到环路关闭该端口
```
- 恢复：`rldp port loop-detect` 可设 `recover-time <秒>` 自动恢复。
- 验证：`show rldp`、`show rldp port`。

## 三、VSU（虚拟交换单元，深化）

### 3.1 原理
- VSU 把多台（通常 2 台）盒式交换机虚拟成一台逻辑交换机，实现**统一管理 + 跨机链路聚合（M-LAG）+ 简化拓扑**。
- 两台成员有主/备之分（switch id），通过 **VSL（虚拟交换链路）** 互联同步状态。

### 3.2 配置骨架
```
switch virtual domain 1               ! 虚拟域
 switch 1
 switch 1 priority 200                ! 优先级决定主备
 switch 1 description SW-A
switch convert mode virtual           ! 转换到 VSU 模式（需重启）
vsl-port                              ! 配置 VSL 口
 port-member interface tenGigabitEthernet 0/49
 port-member interface tenGigabitEthernet 0/50
```
- 易错：**switch id 不能相同**；`switch convert mode virtual` 会重启并清空部分配置（需提前备份）；
  分裂合并时主备选举，抢占时延只在主设备配。

### 3.3 验证
- `show switch virtual`、`show vsu`、`show vsl-port`、`show switch virtual role`（主/备角色）。

## 四、策略路由 PBR（基于策略的选路）

### 4.1 原理
- 普通路由按目的地址查表转发；**PBR 按源地址、协议、端口等做策略选路**，优先级高于路由表。
- 典型场景：不同源网段走不同出口、双出口负载/备份、QoS 分流。

### 4.2 配置骨架（route-map + 接口挂载）
```
access-list 100 permit ip <源网段> <反掩码> any
route-map PBR permit 10
 match ip address 100
 set ip next-hop <下一跳>            ! 或 set ip next-hop 也可用 default 表示保底
interface gigabitEthernet 0/1
 ip policy route-map PBR             ! 入接口挂载策略路由
```
- 易错：PBR 挂**入接口**；`set ip next-hop` 必须可达，否则丢包（可加 `set ip default next-hop` 保底）；
  match 无命中走正常路由表（route-map 无 match 的 permit 会匹配所有）。

### 4.3 验证
- `show route-map`、`show ip policy`、`show ip route` + 源地址 trace 确认走哪条出口。

## 五、AAA 与网络安全（RGSP）

### 5.1 AAA 框架
- **Authentication 认证 / Authorization 授权 / Accounting 计费**。园区常用：设备登录用 AAA（本地或 RADIUS/TACACS+）、接入认证用 802.1X。
- 本地认证骨架：
```
aaa new-model
aaa authentication login default local
username admin password 0 <明文密码>
line vty 0 4
 login authentication default
```
- 远程 RADIUS：
```
aaa authentication login default group radius local
radius-server host <RADIUS服务器地址> key <共享密钥>
```

### 5.2 常见安全技术（速查）
| 技术 | 作用 | 关键命令 |
| --- | --- | --- |
| 端口安全 | 限制端口 MAC 数、绑定 MAC | `switchport port-security`、`maximum`、`mac-address sticky` |
| DHCP Snooping | 防伪造 DHCP 服务器 | `ip dhcp snooping`、`trust` |
| IPSG | 防私改 IP | `ip verify source`、绑定表放行 |
| DAI | 防 ARP 欺骗 | `ip arp inspection` |
| 风暴控制 | 抑制广播/组播/未知单播 | `storm-control` |
| 802.1X | 端口接入认证 | `dot1x port-control auto` |

### 5.3 易错与验证
- 端口安全 `maximum 1` 后接不同 MAC 会 shutdown，`sticky` 自动学习首 MAC。
- DHCP Snooping 开启后**上联/服务器口要 trust**，否则终端拿不到地址。
- 802.1X 未认证前端口在未授权 VLAN，认证通过才切换业务 VLAN。
- 验证：`show port-security`、`show ip dhcp snooping`、`show ip verify source`、`show dot1x`。

## 六、本节验证命令汇总
`show bfd neighbors` / `show rldp` / `show switch virtual` / `show route-map` /
`show aaa` / `show port-security` / `show ip dhcp snooping binding` / `show dot1x`
