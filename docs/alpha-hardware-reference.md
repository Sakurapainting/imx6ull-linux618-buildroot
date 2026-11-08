# ALPHA 官方硬件资料对照

记录日期：2026-11-07。用户确认板卡为正点原子 ALPHA `ATK-DL6Y2C`，PCB 版本和当前插线网口的丝印尚未提供。本页保存系列资料，并区分参考图与本板实测结论。

## 型号和版本边界

型号按用户提供的 `ATK-DL6Y2C` 记录，不据此指定屏幕配置或底板版本。

官方 ALPHA 硬件参考手册将 V2.4 以前的 LAN8720A 电路与 V2.4 及以后使用的 SR8201F 电路分别列图，并明确提示 PHY 地址有变化。因此，系列名称或 PHY ID 都不足以单独确定本板 PCB 版本。

本页保存的是 SR8201F 参考电路；复位网络与 GPIO 的对应关系还需结合官方引脚复用表，不仅依靠 ENET 局部图判断。

来源：

- [官方 ALPHA 底板原理图详解，1.3.23 以太网接口](https://wiki.alientek.com/docs/Boards/Linux/IMX6U/I.MX6U%20%E7%A1%AC%E4%BB%B6%E5%8F%82%E8%80%83%E6%89%8B%E5%86%8C/baseboard/)
- [官方核心板引脚复用表，J2 座](https://wiki.alientek.com/docs/Boards/Linux/IMX6U/I.MX6U%20%E6%A0%B8%E5%BF%83%E6%9D%BF%E5%BC%95%E8%84%9A%E5%A4%8D%E7%94%A8%E8%A1%A8/6U/)

## ENET 参考图与已有证据

从官方硬件页保存了两张 ENET 图：[ENET1](references/alientek-alpha-enet1-reference.png)、[ENET2](references/alientek-alpha-enet2-reference.png)。原始地址、文件字节数及 SHA256 记录于 [来源清单](references/sources.json)。文件名中的 reference 表示系列参考图，不表示已确认对应本板 PCB 版本。

| 核对项 | 官方参考图及引脚复用表 | 本板已有证据与边界 |
| --- | --- | --- |
| PHY | 两图均标为 SR8201F | 两颗实测 ID 均为 `0x001cc816`，匹配 Linux 的 RTL8201F 驱动；芯片丝印尚未核对 |
| ENET1 复位 | 图中网络为 ENET1_RST；复用表 J2 第 10 脚对应 GPIO5_IO07 | 原启动 DTB 的 SoC FEC1 使用 GPIO5_IO7、低有效；该控制器为原 Linux `eth1` |
| ENET2 复位 | 图中网络为 ENET2_RST；复用表 J2 第 9 脚对应 GPIO5_IO08 | 原启动 DTB 的 SoC FEC2 使用 GPIO5_IO8、低有效；该控制器为原 Linux `eth0`，当前可通信 |
| MDIO | 两颗 PHY 共用 ENET_MDC/ENET_MDIO，连接 GPIO1_IO07/06；复用表列出这些引脚的 ENET2_MDC/MDIO 功能 | 原 DTB 的 MDIO 位于 FEC2，实测地址为 1、2；物理插座与接口名称对应仍待补充 |
| 供电 | PHY 参考电路使用 3.3 V 电源 | 属于原理图资料，尚未测量本板供电 |
| 晶振与参考时钟 | PHY XI/XO 外接 25 MHz 晶振，TXC 接 ENETn_TX_CLK 网络 | 25 MHz 晶振不等于 RMII 的 50 MHz 参考时钟。U-Boot 源码和 GPR1 读数提供 FEC2 50 MHz 配置证据，实际方向/波形尚未核对 |

当前结论：官方图纸与引脚复用表支持原 DTB 所记录的复位网络和共享 MDIO 结构，可用于后续 DTS 对照；尚不能替代本板版本、网口丝印和实际接线的确认。Linux 新驱动的最终选择和时钟/复位配置仍需在新系统实测。
