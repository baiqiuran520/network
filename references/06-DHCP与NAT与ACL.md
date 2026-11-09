# 06　DHCP 与 NAT 与 ACL
> **作者 / Author**：白虬髯 (Bai Qiuran)　·　**许可 / License**：署名-非商业性使用（禁止商用，二创须保留原作者署名，详见 LICENSE）　·　**版本 / Version**：v1.0


## 6.1 DHCP 服务器（由边界/核心设备承担）
```
service dhcp                                  ! 先开服务
ip dhcp excluded-address <起始> <网关>         ! 排除保留/网关地址
ip dhcp pool <池名>
 network <网段> <掩码>
 default-router <网关地址>                    ! 指向 VRRP 虚拟 IP
 dns-server <DNS地址>
 exit
```
- 终端（VPCS）拿地址：`ip dhcp`，再 `show ip` 确认。

## 6.2 DHCP 中继（汇聚交换机 SVI 上）
PC 与 DHCP 服务器跨网段时，在用户 VLAN 的 SVI 上指中继：
```
interface vlan 10
 ip helper-address <DHCP服务器地址>   ! DHCP 服务器 Loopback 或接口地址
```
- 中继交换机本身也要 `service dhcp`（仅做中继转发，不分配地址）。

## 6.3 NAPT（出公网地址复用）
```
interface gigabitEthernet 0/0
 ip nat inside
interface gigabitEthernet 0/1
 ip nat outside
!
ip nat pool <池名> <池地址> <池地址> netmask <掩码>
ip nat inside source list 1 pool <池名> overload
!
ip access-list standard 1
 10 permit <内网网段A> <反掩码>
 20 permit <内网网段B> <反掩码>
!
ip route 0.0.0.0 0.0.0.0 <运营商/对端地址>   ! 默认路由
```
- `overload` = PAT（多内网地址复用同一公网 IP 的不同端口）。
- **回程路由**：若 NAT 池地址不在本机与对端的直连段内，对端需加
  `ip route <池地址> 255.255.255.255 <本机互联地址>`，否则回包找不到路。
- 验证：`show ip nat translations`、`show ip nat statistics`。

## 6.4 标准 ACL（按源地址）
```
ip access-list standard 1
 10 deny <源网段> <反掩码>
 20 permit any
interface vlan 10
 ip access-group 1 out          ! 方向：out=离开该接口；in=进入
```
- 标准 ACL **只看源 IP**，无法区分目的，因此“单向允许互访、单向拒绝某网段”做不到。
- 应用方向：`ip access-group <号> in|out`，方向错则过滤不生效或误伤。

## 6.5 扩展 ACL（源+目的+协议+端口）
```
ip access-list extended 100
 10 deny ip <源网段> <反掩码> <目的网段> <反掩码>
 20 permit ip any any
interface vlan 20
 ip access-group 100 in
```
- 扩展 ACL 可精细控制“网段 A→网段 B 拒绝、其余允许”，解决标准 ACL 的冲突。
- **策略类 ACL 放最后单独下发**：先验证基础连通，再加策略验证隔离。

## 6.6 ACL 验证
`show access-lists`、`show running-config | include access-group`。
