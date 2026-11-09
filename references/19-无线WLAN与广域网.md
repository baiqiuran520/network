# 19　无线 WLAN 与广域网基础
> **作者 / Author**：白虬髯 (Bai Qiuran)　·　**许可 / License**：署名-非商业性使用（禁止商用，二创须保留原作者署名，详见 LICENSE）　·　**版本 / Version**：v1.0


> 覆盖 RGSA「无线基础、胖瘦 AP 组网、广域网基础」+ RGSP「WLAN 技术、无线典型组网与网优」。
> 命令以锐捷 RGOS 语法为准（`show` 非 `display`），拿不准处用 `?` 实测补正。

## 一、无线基础（RGSA）

### 1.1 无线协议与频段
- **802.11 系列**：802.11b/g 2.4GHz（b 最高 11Mbps、g 54Mbps）、802.11a 5GHz（54Mbps）、
  802.11n（2.4/5G 双频，MIMO，最高 600Mbps）、802.11ac（5G，最高多 Gbps）、802.11ax（Wi-Fi 6，OFDMA）。
- **频段**：2.4GHz 信道 1/6/11 互不重叠；5GHz 信道多、干扰小。选信道避免重叠。
- **SSID / BSSID**：SSID 是网络名（可多个），BSSID 是 AP 射频的 MAC；ESS 由多 AP 同 SSID 组成。
- **安全**：WEP（已废弃）→ WPA → WPA2（AES/CCMP，主流）→ WPA3（SAE）。企业级用 802.1X（认证）+ AES。

### 1.2 胖 AP / 瘦 AP 组网
- **胖 AP（FAT）**：独立工作，自带配置、认证、漫游弱；适合小场景（办公室、门店）。
- **瘦 AP（FIT）**：只做射频，控制/转发/管理集中在 **AC（无线控制器）**，需 CAPWAP 隧道；
  适合园区级、需统一认证与无缝漫游。
- 关键差异：FAT 单点配置，FIT 由 AC 集中下发；FIT AP 首次要发现 AC（DHCP option 43/138、DNS、广播）。

## 二、WLAN 组网与配置（RGSP）

### 2.1 典型组网
- **AC + FIT AP 直连/旁挂**：AP 经 PoE 交换机接 AC；AC 旁挂时数据可本地转发或集中转发。
- **本地转发 vs 集中转发**：本地转发 AP 直接桥接进业务 VLAN（省 AC 压力）；集中转发流量先到 AC 再回（易控制）。
- **漫游**：多 AP 同 SSID、同安全策略、VLAN 一致，可实现二层漫游；跨三层需三层漫游（AC 间隧道）。

### 2.2 锐捷 AC 配置要点（示例骨架，以 `?` 为准）
```
# 基本 AC 管理
ac
 hostname AC1
 vlan 10                    ! 管理 VLAN
 interface vlan 10
  ip address 10.1.0.1 255.255.255.0
 wlan-config 1 ruijie-wifi    ! 定义 WLAN，SSID
  enable-broad-ssid
  security wpa2              ! 或 security wpa aes
 ap-config ap1
  ap-mac 00xx.xxxx.xxxx
  wlan-config 1
```
> 锐捷无线命令行不同版本差异较大（`wlan-config` / `ap-config` / AC 模板），
> 务必以设备 `?` 实测为准；本 skill 只保证组网思路与排障框架正确。

### 2.3 无线网优要点
- 信道规划：2.4G 用 1/6/11 蜂窝错开，5G 全复用；
- 功率调整：避免覆盖重叠过度与同频干扰；开启 AP 间负载均衡、波段引导（5G 优先）；
- 关弱信号接入：设置最低 RSSI 门限，避免低速终端拖累；
- 射频调优：WLAN 自动信道/功率（RRM），干扰源旁挂。

## 三、广域网基础（RGSA）

### 3.1 广域网接入方式
| 方式 | 说明 | 典型接口/命令 |
| --- | --- | --- |
| PPP（串行） | 点对点，支持认证（PAP/CHAP） | `encapsulation ppp`、`ppp authentication chap` |
| PPPoE | 以太网承载 PPP，常见拨号上网 | `pppoe-client`、`dialer` |
| HDLC | 思科默认串行封装（简单） | `encapsulation hdlc` |
| 帧中继 FR | 已基本淘汰的 PVC 虚电路 | `frame-relay` |
| 专线/以太网 | 城域以太网、MSTP 专线 | 三层 IP 直连 |

### 3.2 PPP 与认证（CHAP 三步）
- CHAP：验证方发 challenge → 被验证方用密码 hash 回应 → 验证方比对。密码不直接传，安全。
- PAP：明文发密码，不安全，仅测试用。
```
interface serial 0/0
 encapsulation ppp
 ppp authentication chap
 ppp chap password <密码>
```

### 3.3 NAT 与广域网出口结合
广域网出口常用 NAPT（见 06）：内网私有地址经出口路由器 `ip nat inside/outside` 复用公网地址上网。
要点：出口需有到公网的默认路由 + 回程 NAT 条目。

## 四、易错与验证（无线/广域网）

| 易错点 | 说明 |
| --- | --- |
| FIT AP 上线不了 | 先查 AP 能否发现 AC：DHCP option 43/138、DNS、二层广播；再看 CAPWAP 隧道状态 |
| 漫游掉线 | 多 AP 的 SSID/安全策略/VLAN 是否一致；二层漫游需同 VLAN |
| 2.4G 慢/干扰 | 信道重叠；改用 1/6/11 错开，引导终端到 5G |
| PPP 认证失败 | 两端认证方式/密码一致；CHAP 需两端都配 `ppp authentication` |
| PPPoE 拨不上 | 账号密码、VLAN、MTU（PPPoE 需留 8 字节头，常见 MTU 1492） |

**验证命令**：
- 无线：`show wlan-config`、`show ap-config`、`show ac-config client summary`（关联终端数）、`show ap summary`
- 广域网：`show interface serial 0/0`（LCP up）、`show pppoe session`、`show ip route`
