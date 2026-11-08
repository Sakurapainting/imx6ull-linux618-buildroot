# 现有工程基线

记录日期：2026-11-07。以下分别记录本机源码检查、网络启动恢复过程和实板采集结果；尚未核实的硬件信息单独列出。

M0 状态：**进行中，尚未完成验收**。原系统恢复、U-Boot/Linux 基线、存储布局和文件加载验证已完成；用户已确认 ALPHA ATK-DL6Y2C 型号及目前只有原 SD 卡。PCB 版本、物理网口及接线、独立测试介质与恢复备份仍有待办。执行状态同步于 `docs/bringup-plan.md`。

## 用户补充与单卡约束（2026-11-07）

- 用户提供的板卡名称为“正点原子 alpha atk-dl6y2c imx6ull 开发板”，记录型号为 `ATK-DL6Y2C`；尚未提供 PCB 版本或当前插线网口的丝印。
- 用户确认目前只有当前这张 SD 卡。该卡已经验证同时承载 U-Boot 与原 Linux 根文件系统，继续保留其内容。
- 新系统先采用 TFTP 加载内核/DTB、内置 initramfs 在 RAM 中运行的方式，允许推进 M1 构建及 M2 串口 shell；独立介质与恢复条件就绪后再进行 M3 写入测试。
- 已查阅官方 ALPHA 底板版本、ENET 原理图和引脚复用表；这些是系列参考资料，尚未确定与本板 PCB 版本完全一致。对照结果见 [官方硬件资料](alpha-hardware-reference.md)。

## 本地已确认的信息

| 项目 | 本地证据 | 对新项目的影响 |
| --- | --- | --- |
| 板卡资料 | 驱动仓库 README 标注正点原子 ALPHA i.MX6ULL、Cortex-A7 | 使用 32 位 ARM 目标配置 |
| 旧内核 | 工作内核 Makefile 为 4.1.15 | 用作接线与行为对照 |
| 旧 U-Boot | U-Boot Makefile 为 2016.03 | 优先验证板上现有版本是否能加载新内核 |
| 板型配置 | 工作 DTS 文件名为 `imx6ull-alientek-emmc.dts` | 暂按 eMMC 板型规划，实板待确认 |
| 旧内存声明 | `0x80000000` 起始、`0x20000000` 长度，即 512 MiB | 仍需与实板 DDR 容量核对 |
| CMA 预留 | `0x14000000`，即 320 MiB | 最小系统重新配置，避免占用过多内存 |
| 串口 | UART1 启用；文档使用 `console=ttymxc0,115200` | 新系统控制台/getty 的候选配置 |
| SD | USDHC1，GPIO1_IO19 为卡检测脚 | 验证卡检测、供电和 pinctrl |
| eMMC | USDHC2、8 位、non-removable | 验证新内核枚举及实际根分区 |
| 以太网 | FEC1、FEC2，均为 RMII | 先打通一个物理接口 |
| PHY 复位 | FEC1 GPIO5_IO7，FEC2 GPIO5_IO8，低有效 | 按新 binding 适配复位及时序 |
| MDIO | 总线节点在 FEC2，PHY 节点地址为 2 和 1 | 先确认实际接线和 PHY 地址 |
| 地址冲突 | 网络教程给出 0 和 1，与工作 DTS 不同 | 以原理图、芯片/MDIO 检测和实板日志为准 |
| 工具链 | 旧容器固定 Linaro GCC 4.9.4 | 新建适用于 6.18 的独立环境 |

现有 `dev-env/README.md` 记录完成了旧内核和模块的主机侧构建。本次已验证原 `tftpboot/` 镜像能启动实板；它与此前构建目录中的产物是否一致尚未逐一核对。

## M0 当前起点：恢复原系统的网络启动

本节按排查顺序保留当时状态；当前启动和 Linux 基线见本节末尾。

2026-11-07 用户补充：原系统由虚拟机通过局域网 TFTP 提供内核和设备树；虚拟机已不再使用，迁移到 CachyOS 后无法启动。当前先恢复原系统启动链，再采集实板基线。

本次主机检查结果：

- 原工程的 `tftpboot/zImage`（6,935,080 字节）和 `tftpboot/imx6ull-alientek-emmc.dtb`（38,049 字节）仍在；尚未验证它们是否就是板上当前启动配置所需的镜像。
- 已安装 `tftp-hpa` 的服务端与客户端；`tftpd.service` 未运行，配置为 `TFTPD_ARGS="--secure /srv/tftp/"`，该服务目录为空。
- 主机当前 Wi-Fi 地址为 `10.238.196.163/24`，未发现有线网卡或 USB 串口设备；地址和设备状态需在连接开发板时重新确认。
- 执行系统目录写入和启动服务需要 sudo；本次 `sudo -n true` 返回需要密码，尚未修改 `/srv/tftp/` 或启动系统服务。

原 TFTP 文件的 SHA256：

```text
33a00566c68a62472a49687deef289389cd4a2d5644e034be341526b63206688  tftpboot/zImage
7c34eec0509ce7c9fe5760251282d08977bbe90425e52d644581a6bb47e76fc6  tftpboot/imx6ull-alientek-emmc.dtb
```

下一步先将上述旧文件放入 TFTP 服务目录并验证本机下载，再根据实板 `printenv bootcmd bootargs serverip ipaddr netmask ethact` 的输出核对网络和文件名。尤其需要检查 `bootargs` 的 `root=`/`nfsroot=`：根文件系统若也依赖原虚拟机，恢复 TFTP 后还需恢复相应的 NFS 服务。首次排查保留现有环境记录，临时调整不执行 `saveenv`。

后续进展（2026-11-07）：

- 用户确认开发板网线直连 CachyOS 的有线网口或 USB 网卡，并已将旧镜像复制到 `/srv/tftp/`、启动 `tftpd.service`。
- 已通过 `127.0.0.1` 以 TFTP binary 模式实际下载两个文件，字节数和 SHA256 均与原 `tftpboot/` 文件一致。主机验证记录：`logs/m0/host-tftp-check.txt`。开发板到主机的传输尚未验证。
- USB 网卡已枚举为 `enp101s0f3u1c2`，当前无 IP 且 `carrier=0`；待核对开发板供电、U-Boot 网口选择及链路状态后配置直连地址。
- USB 串口已枚举为 `/dev/ttyUSB0`，稳定路径为 `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`，设备权限为 `root:uucp`、`0660`。下一步以 115200 波特率记录串口日志并读取原 U-Boot 环境。

实板串口记录（`logs/m0/serial-original.log`）和用户提供的 U-Boot 输出已确认：

| 项目 | 实板记录 |
| --- | --- |
| U-Boot | 2016.03，构建时间 `Jul 21 2025 - 15:16:39 +0800` |
| CPU/板卡横幅 | i.MX6ULL rev1.1；`I.MX6U ALPHA\|MINI`，板卡具体版本仍待核实 |
| DDR | U-Boot 报告 `512 MiB`；起始地址与具体边界仍需 `bdinfo` 核实 |
| MMC 枚举 | `FSL_SDHC: 0, FSL_SDHC: 1`，当前选择 `mmc0`；尚未确认 SD/eMMC 对应关系和分区 |
| 当前网口 | `ethact=FEC1`；启动日志出现 PHY 协商完成，型号/地址仍待核实 |
| 网络环境 | `serverip=192.168.10.100`、`ipaddr=192.168.10.50`、`netmask=255.255.255.0` |
| 启动参数 | `console=ttymxc0,115200 root=/dev/mmcblk0p1 rootwait rw`；当前配置指向本地 MMC 根分区，实际挂载待 Linux 启动后验证 |

原 `bootcmd`：

```text
tftp 80800000 zImage;tftp 83000000 imx6ull-alientek-emmc.dtb;bootz 80800000 - 83000000
```

主机直连配置已创建并激活：NetworkManager 连接 `imx6ull-m0-direct`，绑定 `enp101s0f3u1c2`，IPv4 为 `192.168.10.100/24`，不设网关、不提供默认路由、IPv6 关闭、自动连接关闭。此后如需手动恢复该连接，可运行 `nmcli connection up imx6ull-m0-direct`。尚未修改实板 U-Boot 环境；下一步在 U-Boot 执行 `ping 192.168.10.100`，验证开发板到主机的连通性。

开发板网络测试进展：

- 串口日志已确认 U-Boot `ping 192.168.10.100` 返回 `host 192.168.10.100 is alive`。
- 首次 `tftp 80800000 zImage` 连续超时。内核日志明确记录 UFW 拦截从 `192.168.10.50` 到 `192.168.10.100` 的 UDP 69 请求，证据保存在 `logs/m0/tftp-firewall-block.log`。
- 主机 UFW 已启用，默认入站 DROP、出站 ACCEPT；TFTP 服务仍正常运行，文件可读。用户已执行以下规则，随后已从 `/etc/ufw/user.rules` 核对到相应放行项：

```bash
sudo ufw allow in on enp101s0f3u1c2 proto udp from 192.168.10.50 to 192.168.10.100 port 69
```

- 放行后，串口日志确认 `tftp 80800000 zImage` 成功，`Bytes transferred = 6935080 (69d228 hex)`，速度显示 `5.2 MiB/s`；随后 `tftp 83000000 imx6ull-alientek-emmc.dtb` 成功，`Bytes transferred = 38049 (94a1 hex)`，速度显示 `4.5 MiB/s`。内核和配套 DTB 均已下载到 RAM，下一步验证原系统启动。

原系统启动结果（2026-11-07）：

- `bootz 80800000 - 83000000` 成功进入 Linux 4.1.15，串口出现 `/ #` shell。完整记录保存在 `logs/m0/original-linux-boot.log`。
- U-Boot 报告 DDR 为 512 MiB；内核实际识别 `524288K`。启动日志中的 `178080K available` 与单独列出的 320 MiB CMA 需结合 `/proc/meminfo` 解读，不能据此认为运行系统只有约 178 MiB 可用。
- 内核命令行仍为 `console=ttymxc0,115200 root=/dev/mmcblk0p1 rootwait rw`；`mmcblk0` 是 28.8 GiB SD 卡、只有 `p1`，根 ext4 已成功挂载。`mmcblk1` 是 7.28 GiB eMMC，存在 `p1`、`p2`。
- Linux `eth0` 对应 `20b4000.ethernet`（旧 SoC DTS 中的 `fec2`），绑定 MDIO 地址 1；链路为 `100Mbps/Full`。Linux `eth1` 对应 `2188000.ethernet`（旧 SoC DTS 中的 `fec1`）。U-Boot 当前选择的名称为 `FEC1`，不能直接按该名称推断 Linux 网口编号。
- 内核设备树模型字符串为 `Freescale i.MX 6 ULL 14x14 EVK Board`，与 U-Boot 的 `I.MX6U ALPHA|MINI` 横幅不完全一致；新 6.18 板级 DTS 需以实板连接核对，不能只复制该模型字符串。

Linux 基线采集结果（2026-11-07）：

用户提供的 `uname`、`/proc/cmdline`、`/proc/meminfo`、`/proc/partitions`、`mount`、`ip addr`、PHY ID 和完整 `dmesg` 已原样保存至 `logs/m0/original-linux-baseline.log`。

| 项目 | 实板采集结果 |
| --- | --- |
| 内核 | `Linux (none) 4.1.15 #16 SMP PREEMPT Mon Nov 10 20:31:09 CST 2025 armv7l` |
| 内存 | `MemTotal=506204 kB`、`MemAvailable=455396 kB`；`CmaTotal=327680 kB`、`CmaFree=293864 kB` |
| 根文件系统 | `root=/dev/mmcblk0p1`；`/dev/root` 挂载于 `/`，ext4、读写 |
| SD | `mmcblk0` 为 `SD32G`，容量 28.8 GiB；`p1` 为 30285824 个 1 KiB 块 |
| eMMC | `mmcblk1` 为 `8GTF4R`，容量 7.28 GiB；`p1` 为 128 MiB、`p2` 为 7493632 个 1 KiB 块；另有 boot0、boot1 和 rpmb |
| 当前网口 | `eth0` 为 UP/LOWER_UP，IPv4 为 `192.168.10.50/24`；`eth1` 为 DOWN |
| PHY 检测 | `20b4000.ethernet:01` 与 `20b4000.ethernet:02` 均读到 `phy_id=0x001cc816`；实际检测地址为 1、2，与旧工作 DTS 一致 |
| MAC | `eth0`、`eth1` 当前均显示 `00:04:9f:04:d2:35`；后续启用双网口前需配置各自唯一的 MAC |
| 主机连通性 | 主机通过 `enp101s0f3u1c2` ping `192.168.10.50`，3 发 3 收、丢包率 0% |

PHY 型号、复位脚和参考时钟方向仍需结合硬件资料核实。已读取 PHY ID 和地址不等于完成这些接线核对；`eth1` 尚未进行链路测试。

U-Boot 完整基线采集结果（2026-11-07）：

用户提供的 `bdinfo`、`mmc list`、完整 `printenv` 和 `help bootz` 输出已保存至 `logs/m0/original-uboot-baseline.log`。

| 项目 | 实板采集结果 |
| --- | --- |
| DRAM 边界 | 起始 `0x80000000`，大小 `0x20000000`；有效范围为 `[0x80000000, 0xa0000000)` |
| U-Boot 运行区域 | `relocaddr=0x9ff55000`、`TLB addr=0x9fff0000`、`sp start=0x9ef52e90`；DRAM 内有 U-Boot 自身占用区域 |
| 已验证的原镜像地址 | zImage 为 `0x80800000`、DTB 为 `0x83000000`；新镜像仍需按实际尺寸检查加载和解压区域 |
| MMC 列表 | `FSL_SDHC: 0 (SD)`、`FSL_SDHC: 1`；待用 `mmc info` 和 `mmc part` 核对身份与分区起始位置 |
| 启动命令支持 | `help bootz` 明确支持 zImage、可选 initrd 和第三参数 DTB；TFTP 已实际验证 |
| 控制台 | 输入、输出、错误均为 serial；波特率 115200 |

当前 `bootcmd` 直接使用文件名 `zImage`、`imx6ull-alientek-emmc.dtb`，再执行 `bootz`，没有调用 `mmcboot` 或 `netboot`。实际根分区由当前 `bootargs` 的 `/dev/mmcblk0p1` 指定，已在 Linux 验证。环境中另存的 `mmcroot=/dev/mmcblk0p2`、`fdt_file=imx6ull-14x14-emmc-4.3-800x480-c.dtb` 属于其他脚本参数，不能据此改写已验证的恢复步骤；`initrd_addr=0x83800000` 也尚未实际验证。

当前 M0 已确认：原 TFTP 启动链、DDR 容量和边界、完整 U-Boot 环境、SD 上的 ext4 根分区、eMMC 枚举、Linux 串口控制台及当前网口连通性。下一步核对两块 MMC 的身份与分区布局、SD 加载命令和硬件资料。

## 串口直接核对结果（2026-11-07）

用户退出 picocom 并授予当前用户串口权限后，已直接连接 `/dev/ttyUSB0`、115200、8N1 采集以下信息。本次只读取存储和寄存器、切换当前 MMC 设备，并将文件片段加载至 RAM；没有写入 SD/eMMC，也未执行 `saveenv`。结束时当前设备恢复为 `mmc 0`，板子停在 U-Boot 提示符。

### 存储身份及分区

| U-Boot | 原 Linux | 设备身份 | 总线 |
| --- | --- | --- | --- |
| `mmc 0` | `mmcblk0` | SD，厂商 ID `27`、OEM `5048`、名称 `SD32G`；U-Boot 显示 28.9 GiB | USDHC1，4 位、50 MHz |
| `mmc 1`，user area | `mmcblk1` | eMMC，厂商 ID `15`、OEM `100`、名称 `8GTF4`；U-Boot 显示 7.3 GiB | USDHC2，8 位、52 MHz |

两者均使用 DOS 分区表；下表的起始位置和长度以 512 字节扇区为单位。

| 设备/分区 | 起始扇区 | 扇区数 | 起始偏移 | 容量 | 分区类型 | 文件系统证据 |
| --- | ---: | ---: | --- | --- | --- | --- |
| SD `0:1` | 8192 | 60571648 | 4 MiB | 30285824 KiB | `0c` | 原 Linux 作为 ext4 根分区挂载；U-Boot `ext4ls`/`ext4load` 成功 |
| eMMC `1:1` | 20480 | 262144 | 10 MiB | 128 MiB | `0c` | `fatls`/`fatload` 成功，包含旧 zImage 和多种显示面板 DTB |
| eMMC `1:2` | 282624 | 14987264 | 138 MiB | 7493632 KiB | `83` | `ext4ls` 成功，可列出根目录 |

SD 的 DOS 分区类型为 `0c`，但实际可按 ext4 读取且已由 Linux 挂载为根文件系统。分区类型字段与实际文件系统不同，不据此将其当作 FAT 或改写原分区表。SD 没有 `/boot` 目录。eMMC FAT 分区的 zImage 为 6,785,480 字节，与本次成功启动的 TFTP zImage（6,935,080 字节）不同；eMMC 启动文件尚未作为恢复镜像验证。

`help fatload`、`help ext4load` 均存在，随后实际执行：

```text
ext4load mmc 0:1 84000000 /gdbtest 40
fatload mmc 1:1 84000000 zimage 40
```

两条命令各读取 64 字节，`md.b` 可看到对应 ELF 文件头和 zImage 开头。`40` 为十六进制字节数，本次仅验证文件读取能力，没有执行这些片段。证据：`logs/m0/direct-uboot-storage.log`、`logs/m0/direct-uboot-files-and-boot-regs.log`、`logs/m0/direct-uboot-load-test.log`。

### U-Boot 启动来源与恢复约束

| 寄存器 | 直接读数 | 对照旧 BSP 的解释 |
| --- | --- | --- |
| `SRC_SBMR1`，`0x020d8004` | `0x00000042` | `get_boot_device()` 解析为 SD1，即 USDHC1 的 SD |
| `SRC_SBMR2`，`0x020d801c` | `0x02000001` | 保留原始读数，供启动模式核对 |
| `SRC_GPR9/10`，`0x020d8040/44` | 均为 `0` | 未设置源码所述的 GPR10 bit 28 启动来源覆盖 |

按板上读数和旧 U-Boot 的 `arch/arm/cpu/armv7/mx6/soc.c:get_boot_device()`，当前 U-Boot 来自 SD，与其后的 TFTP 内核加载属于不同阶段。当前这张 SD 还承载原根文件系统；更换为仅有新 rootfs 的空白测试卡不能保证进入现有 U-Boot。独立卡准备时需要处理引导程序，原卡引导区和存储备份尚未采集。已整理 [原系统恢复步骤](original-system-recovery.md)，该文档用于保留现有 SD/U-Boot 时恢复 TFTP 启动，不能代替整卡备份。

### PHY 型号与配置证据

实测两个 `phy_id=0x001cc816` 与 Linux v6.18 `drivers/net/phy/realtek/realtek_main.c` 中的 `PHY_ID_MATCH_EXACT(0x001cc816)`、`RTL8201F Fast Ethernet` 匹配。已保存来源与代码摘录于 `logs/m0/phy-id-reference.txt`。这是 PHY ID 与驱动的匹配结论，尚未核对板上芯片丝印。

官方 ALPHA 硬件资料说明不同底板版本的 PHY 有差异，较新版本使用 SR8201F；因此不将上述驱动匹配结果写成“实物已确认是 RTL8201F”。官方 ENET 参考图及引脚复用表对应的 GPIO5_IO7/8 复位网络与原 DTB 配置相符，但本板的 PCB 版本、芯片丝印、实际供电和参考时钟方向仍待核对，详见 [官方硬件资料](alpha-hardware-reference.md)。

成功启动所用的 `tftpboot/imx6ull-alientek-emmc.dtb` 已反编译，SHA256 仍为 `7c34eec0509ce7c9fe5760251282d08977bbe90425e52d644581a6bb47e76fc6`，输出保存于 `logs/m0/original-tftp-dtb.dts`。

| 原 DTB 控制器 | 原 Linux | PHY 地址 | 原 DTB 复位配置 |
| --- | --- | --- | --- |
| `ethernet@020b4000`，SoC FEC2 | `eth0`，当前工作口 | 1 | GPIO5_IO8，低有效，200 ms |
| `ethernet@02188000`，SoC FEC1 | `eth1`，尚未测试链路 | 2 | GPIO5_IO7，低有效，200 ms |

旧 U-Boot 的生成配置引用 `configs/mx6ullevk.h`，板级源码位于 `board/freescale/mx6ullevk/mx6ullevk.c`；其中也将 GPIO5_IO7/8 用作复位，并配置 50 MHz ANATOP loopback 参考时钟。实板读取 `IOMUXC_GPR1`（`0x020e4004`）为 `0x0f440005`，bit 14 为 0、bit 18 为 1，与源码中 FEC2 的时钟选择配置一致。上述数据说明软件配置；实际时钟方向、供电和物理连接仍需原理图/实物核对，原内核的复位 pinctrl 警告仍需在新 DTS 中处理。

## 对照资料位置

下面路径相对于父目录 `/home/you/vm-dev/linux`：

- `dev-env/README.md`：旧构建环境、验证结果与部署注意事项。
- `dev-env/Containerfile`：Ubuntu 20.04 / GCC 4.9.4 旧环境。
- `IMX6ULL/linux/linux-imx-rel_imx_4.1.15_2.1.0_ga/`：旧工作内核。
- 上述内核中的 `arch/arm/boot/dts/imx6ull-alientek-emmc.dts`：本次检查的工作设备树。
- 上述内核中的 `.config`：旧内核配置。
- `IMX6ULL/uboot/alientek_uboot/`：旧 U-Boot 源码。
- U-Boot 中的 `configs/mx6ull_alientek_emmc_defconfig`：引用 DDR512 配置；不是板上实测容量证明。
- `IMX6ULL/you-imx6ull-linux-driver/README.md`：板卡身份与旧启动示例。
- `IMX6ULL/Linux_Drivers/net/README.md`：网络教程，部分数据与工作 DTS 有差异。
- `IMX6ULL/Linux_Drivers/buildroot/README.md`：Buildroot 2019.02.6 历史教程；新项目按所选版本官方手册配置。

## M0 核对清单

- [x] DDR 容量为 512 MiB；Linux 可识别 SD 和 eMMC。
- [x] 原 U-Boot 版本和 TFTP 启动命令；原内核、DTB 可重新下载并启动至 shell。
- [x] 调试串口 `/dev/ttyUSB0`、115200 波特率及 Linux 控制台 `ttymxc0`。
- [x] Linux 根分区为 SD 的 `mmcblk0p1`，ext4 读写挂载。
- [x] MDIO 地址 1、2 和两颗 PHY 的原始 ID。
- [x] 实测 PHY ID 与 RTL8201F 驱动匹配；已核对原启动 DTB 的复位属性和旧 U-Boot 时钟配置。
- [x] 主机直连静态网络、当前单网口链路和 IP 连通性。
- [x] 用户确认板卡型号为正点原子 ALPHA ATK-DL6Y2C。
- [ ] ALPHA 板卡具体版本及物理网口标记。
- [x] 官方 ENET 参考原理图已保存，引脚复用表已对照；已区分系列资料与本板实物确认。
- [x] `bdinfo`、完整 U-Boot 环境、`bootz` 帮助和实际 TFTP 下载。
- [x] 文件加载命令可用；`ext4load` 从 SD、`fatload` 从 eMMC 实际读取成功。
- [x] 当前 U-Boot 启动来源、U-Boot/Linux 的 SD/eMMC 编号对应和分区起始位置。
- [ ] 原存储及引导区备份、备份恢复验证。
- [ ] PHY 实物型号、复位接线、50 MHz 参考时钟方向及供电。
- [x] 用户确认目前只有原 SD 卡；M1/M2 先采用保留原卡的 TFTP/RAM 路径。
- [ ] 用于新系统的独立测试 SD 卡及原系统恢复条件。

SSH 登录账户及用于注入的主机公钥在后续 SSH 阶段确认。
