# 术语对照：锐捷 RGOS ↔ 思科 IOS
> **作者 / Author**：白虬髯 (Bai Qiuran)　·　**许可 / License**：署名-非商业性使用（禁止商用，二创须保留原作者署名，详见 LICENSE）　·　**版本 / Version**：v1.0


> 锐捷 RGOS 命令体系**源自思科 IOS**，熟悉思科的人可近乎无缝迁移到锐捷。
> 本文给出常用命令对照，并指出少数差异点。**不要用华为 `display` 思维**——锐捷用 `show`。

## 一、通用对照表
| 功能 | 锐捷 RGOS | 思科 IOS | 备注 |
| --- | --- | --- | --- |
| 进入全局配置 | `configure terminal` | `configure terminal` | 完全相同 |
| 改主机名 | `hostname X` | `hostname X` | 相同 |
| 查看运行配置 | `show running-config`（或 `show run`） | `show running-config` | 相同 |
| 查看（通用） | `show ...` | `show ...` | 锐捷**没有** `display` |
| 保存配置 | `write` / `copy running-config startup-config` | `write memory` / `copy run start` | 锐捷 `write` 最常用 |
| 特权密码 | `enable password` / `enable secret` | 同 | 远程登录必须有 enable 密码 |
| 接口进入 | `interface gigabitEthernet 0/1` | `interface GigabitEthernet0/1` | 格式略异（锐捷有空格） |
| 创建 VLAN | `vlan 10` | `vlan 10` | 相同 |
| Trunk | `switchport mode trunk` | 同 | 锐捷一般只需配 mode |
| Access | `switchport mode access` + `switchport access vlan 10` | 同 | 相同 |
| 三层交换 | `no switchport` | 同 | 相同 |
| 链路聚合 | `interface aggregateport 1` + `port-group 1` | `interface port-channel 1` + `channel-group 1` | 锐捷叫 **AggregatePort** |
| STP | `spanning-tree` / `spanning-tree mst configuration` | 同 | 锐捷 MSTP 需 `name`+`revision` |
| OSPF | `router ospf 1` + `network x.x.x.x wildcard area` | 同 | 相同 |
| 静态路由 | `ip route 网段 掩码 下一跳` | 同 | 锐捷可绑定 track |
| ACL | `ip access-list standard/extended` | 同 | 相同 |
| VRRP | `vrrp 10 ip x.x.x.x` + `vrrp 10 priority` | 同 | 相同 |
| DHCP 服务 | `service dhcp`（全局开启） | `service dhcp` | 锐捷中继前需开服务 |
| DHCP 中继 | `ip helper-address x.x.x.x` | 同 | 相同 |
| DHCP 地址池 | `ip dhcp pool NAME` | 同 | 相同 |
| NAT | `ip nat inside/outside` + `ip nat inside source` | 同 | NAPT 写法相同 |
| 端口安全 | `switchport port-security` | 同 | 相同 |
| BPDU 防护 | `spanning-tree bpduguard enable`（接口级） | 同 | 建议接口级，避免误伤 |
| 调试 | `debug ...` | 同 | 排障用，用完 `no debug all` |

## 二、锐捷特有 / 与思科的少量差异
- **链路聚合**：锐捷聚合口叫 `AggregatePort N`，思科叫 `Port-channel N`；成员加入用 `port-group N`。
- **MSTP**：锐捷 MST 实例配置必须 `name <域名>` + `revision <号>`，且默认域名常是 `ruijie`，两端需一致。
- **设备虚拟化**：锐捷 **VSU** ≈ 思科 VSS / StackWise；`switch id` 不能相同，分裂合并时选举失败方短暂恢复。
- **NQA/Track**：锐捷 `ip rns`（如 `icmp-echo`）+ `track` 做链路检测，`delay up/down` 控制翻转，思科用 `ip sla`+`track`。
- **提示符**：锐捷用户模式 `Switch>`、特权 `Switch#`、全局 `Switch(config)#`、接口 `Switch(config-if)#`；VPCS 终端是 `PC1>`（无配置模式）。

## 三、迁移心法
1. 拿到题先想「这在思科怎么配」——90% 直接搬；剩下 10% 看上面差异表。
2. 拿不准命令在锐捷里敲 `?` 探路（见 `03-命令规则`），不要凭华为 `display` 记忆硬套。
3. 验证一律用 `show`（不是 `display`）：`show vlan`、`show ip ospf neighbor`、`show vrrp`、`show ip interface brief`。
