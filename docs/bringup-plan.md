# 移植计划

## 范围与完成标准

在正点原子 ALPHA i.MX6ULL 实板上完成 Linux 6.18 LTS + Buildroot 最小系统。先启用串口、SD/eMMC 和一个有线网口；LCD、触摸、音频、摄像头、Wi-Fi 和教学驱动排在最小系统验收之后。

完成标准：干净输出目录可重新构建；配对的 zImage 与 DTB 可在实板启动；串口登录、根文件系统读写、以太网通信和 SSH 登录均成功；断电重启后仍可使用 SSH，服务器主机密钥保持稳定。

## M0：确认实板基线

状态（2026-11-08）：**进行中，尚未完成验收**。原系统的 TFTP 启动已在 CachyOS 恢复，U-Boot、Linux、存储布局及文件加载能力已采集验证；用户确认型号为 ALPHA `ATK-DL6Y2C`，目前只有原 SD 卡。PCB 版本、物理网口及接线、独立测试介质和恢复备份仍有待办。M1、M2 已通过，M3 进行中，M4～M6 待开始。

1. 从串口记录现有系统完整上电日志，确认板型、DDR 容量、启动介质、U-Boot 版本、串口和网口。
2. 在 U-Boot 中记录 `version`、`bdinfo`、`printenv`、`mmc list`；检查 `help bootz`、TFTP/SD 加载命令，以及内核、DTB 可用加载地址。
3. 在原 Linux 中记录 `uname -a`、`cat /proc/cmdline`、`cat /proc/meminfo`、`cat /proc/partitions`、`mount`、`ip addr` 和 `dmesg`。PHY ID 可从存在的 `/sys/bus/mdio_bus/devices/*/phy_id` 读取。
4. 根据实板/原理图核实 PHY 型号、MDIO 地址、复位脚和参考时钟。重点解决旧 DTS 的地址 2/1 与教程地址 0/1 的差异。
5. 记录当前分区布局与可恢复的启动方式，准备测试 SD 卡和串口。首次临时启动仅在内存中设置 U-Boot 环境。

产物：板级信息表、原系统启动日志、环境记录和恢复步骤。

验收：已确认内存边界、可用启动方式、测试根文件系统介质及一个有线接口的硬件连接。

当前单卡条件下的推进安排：保留原 SD 的 U-Boot 和根文件系统，M1 的构建与 M2 的 TFTP/RAM 启动可先进行；M3 的新 rootfs 写入测试等待独立测试介质和恢复条件。此安排不代表上述 M0 待办已通过验收。

当前进度：

| 核对项 | 状态与证据 |
| --- | --- |
| 原系统启动与串口 | 已完成：原 zImage/DTB 经 TFTP 下载后可进入 Linux 4.1.15 shell；控制台为 `ttymxc0,115200` |
| 内存与 U-Boot 信息 | 已完成：512 MiB DDR，范围 `[0x80000000, 0xa0000000)`；已采集版本、`bdinfo`、完整环境、`mmc list` 和 `help bootz` |
| 原 Linux 基线 | 已完成：内核信息、启动参数、内存、分区容量、挂载、接口地址、PHY ID 和完整 dmesg 已保存；SD 的 `mmcblk0p1` 为 ext4 根分区，另可识别 eMMC |
| 当前网口与 MDIO 地址 | 已完成连通性和地址采集：Linux `eth0` 为 `20b4000.ethernet`，100 Mbps 全双工；主机 ping 3/3 成功；MDIO 实测地址为 1、2，ID 均为 `0x001cc816`，已解决与教程 0/1 的地址差异 |
| 存储及文件加载命令 | 已完成：U-Boot `mmc 0` 为 SD、`mmc 1` 为 eMMC，与原 Linux 编号一致；已采集身份、DOS 分区表和起始扇区；`ext4load` 从 SD、`fatload` 从 eMMC 各实际读取 64 字节至 RAM |
| 板卡与网口硬件资料 | 部分完成：用户确认 ALPHA ATK-DL6Y2C；实测 PHY ID 匹配 RTL8201F 驱动，官方资料说明较新底板使用 SR8201F，因此仍不能确定实物芯片型号。已记录原 DTB 的地址 1/2、GPIO5_IO8/7 复位及 U-Boot 时钟配置；官方 ENET 原理图已留存。PCB 版本、物理口及本板接线/供电仍待核对 |
| 测试与恢复条件 | 部分完成：用户确认目前只有原 SD 卡；U-Boot 从该卡的 USDHC1 启动，原根文件系统也在该卡。原镜像、环境、分区表和恢复步骤已保存；独立测试介质、引导区/原存储备份及恢复验证尚未完成。M1/M2 采用保留原卡的 TFTP/RAM 路径 |

记录与证据：

- [板级基线与核对清单](board-baseline.md)。
- `logs/m0/host-tftp-check.txt`：主机 TFTP 文件校验。
- `logs/m0/original-linux-boot.log`：原内核启动至 shell 的日志。
- `logs/m0/original-linux-baseline.log`：原 Linux 信息采集。
- `logs/m0/original-uboot-baseline.log`：U-Boot 内存信息、完整环境及 bootz 帮助。
- `logs/m0/direct-uboot-storage.log`：直接采集的 MMC 身份、分区表和加载命令帮助。
- `logs/m0/direct-uboot-files-and-boot-regs.log`：存储目录、启动寄存器及网口时钟选择寄存器。
- `logs/m0/direct-uboot-load-test.log`：文件实际加载到 RAM 的验证。
- `logs/m0/original-tftp-dtb.dts`、`logs/m0/phy-id-reference.txt`：原 DTB 反编译与 Linux PHY ID 对照。
- [原系统恢复步骤与存储保护](original-system-recovery.md)。
- [ALPHA 官方硬件资料与实板对应边界](alpha-hardware-reference.md)：底板版本差异、ENET 原理图及引脚复用表对照。

M1 已完成工具链和最小用户空间构建，M2 已通过 RAM 串口 shell 验收。PCB 版本和当前物理网口丝印仍待补充。M2 只临时设置 U-Boot 环境；当前原 SD 不作新 rootfs 的写入目标。备份及独立测试卡的具体步骤待读卡器和介质条件明确后制定，测试卡需要包含可用的 U-Boot。

## M1：建立新构建环境

状态（2026-11-08）：**已通过验收**。独立容器、源码签名核验、Buildroot defconfig 与入口已建立，内部工具链和最小 rootfs 首次完整构建成功。GCC 15.3.0 的 ARM 编译、链接和 ELF 属性检查通过；rootfs 的 init、console、getty、动态加载器和账户所有权检查通过。具体操作见 [M1 构建说明](m1-build.md)，证据与产物摘要见 [M1 验收记录](m1-validation.md)。原 Linux 4.1.15 的上板测试属于 M0，新 Linux 6.18 启动已在 M2 完成。

1. 为新项目建立单独的构建容器；现有 `dev-env/` 中的 GCC 4.9.4 环境用于旧 BSP 对照。
2. 下载 `versions.env` 中固定版本的 Buildroot 和 Linux，核对官方签名，保存 SHA256 及签名验证记录。
3. Buildroot 使用内部工具链，目标为 ARM little-endian、Cortex-A7、EABIhf，具体编译选项保存在 defconfig。Linux v6.18 的最低 GCC 要求为 8.1，不沿用旧交叉编译器。
4. 使用 `BR2_EXTERNAL` 管理板级配置、DTS/补丁、overlay 和脚本；使用独立输出目录，以普通用户编译。
5. 先构建最小 BusyBox 用户空间，再接入自定义内核。默认由 Buildroot 统一构建内核，保存其实际使用的工具链和配置。

产物：构建容器文件、源码锁定记录、初始 Buildroot defconfig 和构建入口。

验收：交叉编译器可生成 ARM 目标文件，最小 rootfs 构建成功，版本与校验记录齐全。

## M2：Linux 6.18 启动到串口 shell

状态（2026-11-08）：**已通过验收**。已完成 ALPHA 板级 DTS、Linux 6.18.62 配置、内置 initramfs、zImage/DTB 构建、产物检查，并通过现有 U-Boot 的 TFTP/RAM 路径进入串口 root shell。命令、产物和串口日志见 [M2 构建与 RAM 启动](m2-build.md)、[M2 验收记录](m2-validation.md)。

1. 以 6.18 源码中的 i.MX6ULL EVK/SoC 设备树为参考，创建本项目的 ALPHA eMMC 板级 DTS，逐项核对电源、时钟、pinctrl、UART 和内存配置。
2. 根据实板设置内存；最小版本移除旧 DTS 中面向显示的 320 MiB CMA 预留和无关外设，核对继承节点的状态。
3. 从 6.18 的 i.MX 配置起步裁剪，内建串口控制台、devtmpfs 和 initramfs 支持。将旧 DTS 作为接线资料，按 6.18 binding 重写板级差异。
4. 使用 Buildroot 生成的用户空间制作内置 initramfs 的 zImage，配置 BusyBox init 与 `ttymxc0`、115200 波特率的 getty。
5. 使用现有 U-Boot 的 `bootz` 临时启动新 zImage 和配套新 DTB；根据 M0 的内存边界及镜像实际尺寸选择地址。

当前传输方式使用已验证的 TFTP，原 SD 仅保留现有引导用途。内置 initramfs 的启动参数在本阶段单独制定，不沿用原系统指向 SD 根分区的 `root=/dev/mmcblk0p1`。

产物：板级 DTS、Linux 配置、带 initramfs 的 zImage、配套 DTB 和串口日志。

验收：已完成。日志显示 6.18.62，能在串口登录并执行 `uname -r`、`ps`、`mount`；根文件系统为 RAM 内置 initramfs，未写入 SD/eMMC。网络仍留待 M4。

排查顺序：内核无输出时查串口、DTB、加载地址和启动参数；内核已启动但没有 shell 时查 `/sbin/init`、解释器/动态加载器、`/dev/console` 与 getty。

## M3：切换到 SD/eMMC 根文件系统

状态（2026-11-08）：**主机构建和产物校验已通过，尚未完成实板验收**。已新增 M3 独立 defconfig、存储 DTS、内核与 BusyBox 配置、ext4/归档产物及验证入口。证据见 [M3 验证记录](m3-validation.md)，具体命令与阶段边界见 [M3 构建与存储检查](m3-build.md)。

用户再次确认仍只有原系统 SD 卡。先进行主机镜像验证和 RAM initramfs 中的 SD/eMMC 只读识别；本阶段的写入与外置根文件系统验收暂缓。准备写入前先落实原存储备份及恢复方式。

1. 适配 USDHC1 的 SD 卡与 USDHC2 的 8 位 eMMC，核对供电、卡检测和 pinctrl。
2. 将启动所需的 MMC、分区解析和 ext4 驱动编入内核。生成外置 ext4 rootfs，并切换至不带内置 initramfs 的常规 zImage。
3. 首先使用独立 SD 卡测试；根据实际分区使用已确认的根设备或 PARTUUID 配置 `root=`、`rootwait` 等参数。
4. 用串口验证根目录来源、读写和重启行为。不要直接沿用旧教程的 `/dev/mmcblk0p1`，新内核的设备编号需要重新确认。
5. SD 验证通过后，如需部署到 eMMC，再根据真实分区布局编写具体部署/恢复步骤。

产物：常规 zImage、DTB、ext4/rootfs.tar、根分区标识与启动记录。

验收：从外置根文件系统启动，能创建文件且重启后保留，串口登录正常。

## M4：打通一个有线网口

1. 内建 i.MX FEC、MDIO 和实板 PHY 所需驱动，适配 RMII 的引脚、50 MHz 参考时钟、复位与供电。
2. 核对两个 MAC 共用 MDIO 的关系。旧工程的 MDIO 节点位于 FEC2；即使先测一个网口，也要保留其所依赖的总线和时钟配置。
3. 按 6.18 binding 处理 PHY 节点和复位属性；核对 U-Boot 传递的 MAC 地址及 Linux 实际接口名称。
4. 主机直连时先用静态地址验证；接入存在 DHCP 服务的网络后再测试 DHCP。
5. 检查链路协商，验证板到主机以及主机到板的通信，保存 FEC/PHY 日志。

产物：网口 DTS/内核配置、网络启动配置、物理接口与 Linux 接口名称对应关系。

验收：至少一个有线网口重启后可自动配置地址，双向通信稳定。U-Boot 中 TFTP 成功不能代替 Linux 网口验收。

## M5：启用 SSH

1. 在 Buildroot 中加入 Dropbear，使用其启动脚本配置开机启动。
2. 配置具有可用登录 shell 的用户与 SSH 公钥，检查 home 和 `authorized_keys` 权限；公钥通过本地配置注入，私钥保留在主机。
3. 将主机密钥保存在可写且持久化的位置，验证首次生成和后续复用。
4. 从主机执行 `ssh <user>@<board-ip>`，在远程会话中检查 `uname -r`、根文件系统和网络。
5. 断电重启后再次登录，确认网络、Dropbear 自启动及主机密钥稳定。

产物：账户/公钥注入配置、Dropbear 配置和 SSH 验收记录。

验收：首次启动及断电重启后均能通过 SSH 登录到目标板的 6.18 系统。

## M6：整理为可复现项目

1. 保存最小 defconfig、Linux 配置、板级 DTS/补丁、overlay、脚本、容器配置和源码校验记录。
2. 完善 `build`、镜像导出和启动说明，记录镜像 SHA256、构建日志与串口日志。
3. 使用全新的输出目录完成一次构建，用新产物重复串口、存储、网络和 SSH 验收。
4. 编写从零构建、测试 SD 卡准备、临时启动、可选 eMMC 部署及恢复文档。

验收：构建过程不依赖旧目录中的二进制或手工修改的 output 文件。此处的可复现指流程和配置可重建；逐字节一致另行验证。

## 后续扩展

基础系统验收后，再逐个加入 LED/按键、I2C/SPI、ADC、LCD、音频等功能；旧 4.1.15 的驱动源码需要按新内核 API 单独适配和测试，旧 `.ko` 不作为新系统的部署产物。

## 官方参考

- Linux 发布信息：<https://www.kernel.org/releases.json>
- Linux v6.18 构建要求：<https://github.com/torvalds/linux/blob/v6.18/Documentation/process/changes.rst>
- i.MX6ULL EVK DTS：<https://github.com/torvalds/linux/blob/v6.18/arch/arm/boot/dts/nxp/imx/imx6ull-14x14-evk.dts>
- FEC binding：<https://github.com/torvalds/linux/blob/v6.18/Documentation/devicetree/bindings/net/fsl,fec.yaml>
- Buildroot 下载与签名：<https://buildroot.org/download.html>
- Buildroot 手册，重点参阅 br2-external、内核配置、overlay 和 init 配置：<https://buildroot.org/downloads/manual/manual.html>
