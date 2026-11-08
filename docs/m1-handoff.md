# M1 接续说明

交接日期：2026-11-07；M1/M2 进度更新：2026-11-08。详细步骤与验收条件以 [移植计划](bringup-plan.md) 为准，构建操作见 [M1 构建说明](m1-build.md) 和 [M2 构建说明](m2-build.md)。

## 工作目录和阶段

- 项目目录：`/home/you/vm-dev/linux/imx6ull-linux618-buildroot`。
- 旧工程及恢复镜像位于父目录：`/home/you/vm-dev/linux`。
- M0 曾进入原 Linux 4.1.15 完成恢复与基线采集；M2 已另行进入新 Linux 6.18.62 / Buildroot 串口 shell。
- M1、M2 均已于 2026-11-08 通过验收：Linux 6.18.62、ALPHA DTS、内置 initramfs、zImage/DTB、产物级校验和实板 RAM 串口 shell 均完成。`br2-external/` 已加入 M1/M2 defconfig、Linux headers 摘要和 Linux 归档摘要。
- M0 尚有实物核对、独立测试介质和备份恢复待办；这些待办不阻止先开展 M1 构建。M2 的首次新系统启动采用 TFTP 加载、RAM 内置 initramfs。
- 本次 M2 验收结束后，板子停在新系统的串口登录提示，串口已释放。断电后仍按原 SD 中的 U-Boot 环境启动；未执行 `saveenv`。

## M0 已做的工作

| 工作 | 已确认结果 | 记录位置 |
| --- | --- | --- |
| 恢复主机 TFTP | 原虚拟机已停用；CachyOS 配置直连网卡、TFTP 服务及指定网卡/地址的防火墙放行后，两个原镜像下载成功 | [板级基线](board-baseline.md)、[主机文件校验](../logs/m0/host-tftp-check.txt)、[防火墙排查](../logs/m0/tftp-firewall-block.log) |
| 启动原系统 | 旧 zImage 和 DTB 经 TFTP 加载后，`bootz` 成功进入 Linux 4.1.15 串口 shell | [原系统启动日志](../logs/m0/original-linux-boot.log) |
| 采集 Linux 基线 | 已保存内核版本、命令行、内存、分区、挂载、接口、PHY ID 和 dmesg；SD 的 ext4 分区是原根文件系统 | [Linux 基线日志](../logs/m0/original-linux-baseline.log) |
| 采集 U-Boot 基线 | U-Boot 2016.03、512 MiB DDR，范围 `[0x80000000, 0xa0000000)`；完整环境及 `bootz` 帮助已保存 | [U-Boot 基线日志](../logs/m0/original-uboot-baseline.log) |
| 直接核对存储与启动来源 | `mmc 0` 为 SD，`mmc 1` 为 eMMC；身份、分区表和起始扇区已记录，启动寄存器与旧 BSP 对照确定当前 U-Boot 来自 SD | [存储日志](../logs/m0/direct-uboot-storage.log)、[文件和寄存器日志](../logs/m0/direct-uboot-files-and-boot-regs.log) |
| 验证文件加载 | `ext4load` 从 SD、`fatload` 从 eMMC 各读取 64 字节至 RAM，确认命令实际可用 | [加载测试日志](../logs/m0/direct-uboot-load-test.log) |
| 核对网口资料 | 原 Linux `eth0` 为 SoC FEC2，PHY 地址 1；另一个 PHY 地址 2。两颗 ID 均为 `0x001cc816`，匹配 RTL8201F 驱动；原 DTB 复位配置、U-Boot 时钟配置和官方参考资料已对照，实物芯片型号未确认 | [板级基线](board-baseline.md)、[官方硬件对照](alpha-hardware-reference.md)、[原 DTB 反编译](../logs/m0/original-tftp-dtb.dts) |
| 保存原系统恢复步骤 | 现有 SD/U-Boot 保留时，已验证通过主机 TFTP 恢复原 Linux 的步骤；原镜像大小和 SHA256 已记录 | [原系统恢复](original-system-recovery.md) |

M0 串口直接核对仅执行读取、切换当前 MMC 设备和加载文件片段至 RAM；未写入 SD/eMMC，也未执行 `saveenv`。当时操作结束时恢复 `mmc 0` 并停在 U-Boot；M2 结束后的板端状态见上方记录，新会话操作前应重新确认。

全部采集材料在 [logs/m0](../logs/m0/)；其中 [direct-evidence.sha256](../logs/m0/direct-evidence.sha256) 覆盖六份直接核对材料。`logs/` 已列入 `.gitignore`，原始日志目前保存在本机，不能假定将来只复制已跟踪文件也会带上日志。

## 关键配置和约束

- 板卡：用户确认正点原子 ALPHA `ATK-DL6Y2C`；PCB 版本和当前网口丝印尚未提供。
- 用户只有当前原 SD 卡；它同时承载 U-Boot 和原根文件系统。M1 不涉及写卡，M2 先在 RAM 中运行，新 rootfs 写入测试留至 M3 条件具备后。
- 原 TFTP 文件为父目录 `tftpboot/zImage`、`tftpboot/imx6ull-alientek-emmc.dtb`，服务端副本在 `/srv/tftp/`。后续新产物使用独立名称或目录，保留原恢复文件。
- 已验证原镜像加载地址为 `0x80800000`、DTB 为 `0x83000000`；新镜像必须按实际大小重新检查加载及解压区域。
- 主机直连连接名为 `imx6ull-m0-direct`，绑定 `enp101s0f3u1c2`；主机地址 `192.168.10.100/24`，板卡 `192.168.10.50/24`。恢复连接及服务命令见恢复文档。
- 调试串口为 `/dev/ttyUSB0`、115200、8N1，Linux 控制台为 `ttymxc0`。用户已退出 root 的 picocom 并为当前设备授予用户 `you` 读写权限；设备重插后需要重新检查权限及占用。M1 主机侧构建不需要接管串口。
- 旧 `dev-env/` 使用 GCC 4.9.4，仅作旧 BSP 对照；为新项目准备独立构建环境和 Buildroot 内部工具链。
- [versions.env](../versions.env) 固定 Linux `6.18.62`、Buildroot `2026.08.1`。两份归档的官方签名及摘要已核验，公钥、签名者指纹和验证记录在 [源码验证记录](source-verification/README.md)。板级兼容性仍待后续验收。

## M1 已完成结果

- 构建入口：`scripts/env`、`scripts/fetch-sources`、`scripts/build`、`scripts/verify-m1`。操作见 [M1 构建说明](m1-build.md)。
- 配置：`br2-external/configs/imx6ull_m1_defconfig`，Cortex-A7、ARM little-endian、EABIhf、NEON/VFPv4、musl、BusyBox init、`ttymxc0/115200`。
- 实际工具链：GCC `15.3.0`、binutils `2.45.1`、musl `1.2.6`、Linux headers `6.18.62`。用户空间 BusyBox `1.38.0`。
- 产物：`output/m1/images/rootfs.cpio`（1,833,984 字节）和 `rootfs.cpio.gz`（995,021 字节）。373 项归档检查通过，包含 `/init`、`/dev/console`、动态加载器和串口 getty。
- 版本、最终产物 SHA256、验收边界见 [M1 验收记录](m1-validation.md)。详细日志在忽略的 `logs/m1/`，摘要和签名证据已纳入项目文件。
- 构建使用普通用户 UID/GID 1000、8 路并发；总构建输出约 6.6 GiB。初次检查发现 Buildroot 向上读取父仓库版本标签，已在入口设置 Git ceiling 并修正最终编译器与 rootfs 的版本信息。

## 新会话接续位置：M3 外置 rootfs

1. 阅读本文件、[M2 验收记录](m2-validation.md) 和 [移植计划](bringup-plan.md) 的 M3 部分。需要重建 M1/M2 时使用已有入口，无需重做原系统启动测试。
2. M2 已在现有 U-Boot 上通过 TFTP/RAM 启动；串口日志位于 `logs/m2/board-ram-boot.log`，未写入 SD/eMMC。
3. M3 需要独立测试介质和恢复条件，在此基础上启用 USDHC、分区和 ext4，逐步切换为外置 rootfs。

M2 已完成新 Linux 6.18.62 的串口 shell 和运行日志；M1 的主机检查不能代替实板启动。下一阶段为 M3 外置 rootfs，M0 剩余硬件与恢复待办保持如下。

## 保留的 M0 待办

- PCB 版本、当前物理网口丝印及其与控制器的对应关系。
- 本板 PHY 实物型号、实际复位接线、50 MHz 参考时钟方向及供电的最终核对；参考图与软件配置不等同于本板测量。
- 原 SD 引导区/原存储备份及恢复验证，独立测试介质和其可用引导程序。eMMC 中的旧内核/DTB 与已验证的 TFTP 文件大小不同，尚不能作为已验证的备用启动链。
