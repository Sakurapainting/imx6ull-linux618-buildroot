# M3 验证记录

日期：2026-11-08。目标为 ALPHA ATK-DL6Y2C、512 MiB DDR、SD 和 8 位 eMMC；版本沿用项目锁定的 Linux 6.18.62、Buildroot 2026.08.1。

## 当前结论

**M3 主机完整构建和产物校验已通过，里程碑尚未完成验收。** RAM 存储只读识别待 TFTP 发布后上板。用户确认仍只有原系统 SD 卡，外置 rootfs 的部署、读写和重启持久化尚未执行。

## 软件实现

- `imx6ull_m3_defconfig` 使用独立 `output/m3` 和 Buildroot 内部工具链，不复制 M2 输出作为构建输入。
- `imx6ull-alpha-m3.dts` 引用 M2 板级 DTS，启用 USDHC1 的 4 位 SD（GPIO1_IO19 卡检测）和 USDHC2 的 8 位 eMMC，最高 50 MHz，禁用 1.8V 切换。
- `m3.fragment` 将启动所需 MMC、DOS 分区解析、ext4、GPIO 和供电驱动内建，`CONFIG_INITRAMFS_SOURCE=""`。
- 输出常规 zImage、M3 DTB、128 MiB ext4、tar，以及用于 RAM 诊断的独立 gzip cpio/legacy U-Boot ramdisk。
- BusyBox 启用 `blockdev` 与文件系统类型识别；overlay 使用 ext4 根目录 fstab，提供仅允许在 RAM 根目录运行的 `m3-storage-report`。

## 已执行的初步检查

- M3 DTS 已使用 Linux 6.18 的头文件预处理，并通过 DTC 编译。
- 原 M2 DTS 重新编译的 DTB 与 M2 已验收产物逐字节一致。
- `scripts/verify-m2` 回归通过，日志为 `logs/m3/m2-regression.log`。
- 串口只读复核当前运行的 M2：`uname -r` 为 `6.18.62`，命令行仅含 `console=ttymxc0,115200`，根目录为 RAM rootfs，没有 MMC 块设备。日志为 `logs/m3/board-preflight.log`。此结果不作为 M3 存储识别证据。

## 主机产物验证

`scripts/build-m3` 完成独立工具链、内核及用户空间构建；在最终配置中合入 BusyBox 诊断工具和 overlay 后再次生成所有文件系统。日志为 `logs/m3/build.log` 与 `logs/m3/finalize.log`。`scripts/verify-m3` 返回 0，输出留存在 [验证记录](m3-verification.txt)，[产物摘要](m3-artifacts.sha256) 可在项目根目录用 `sha256sum -c docs/m3-artifacts.sha256` 检查。

已检查：

- 实际 Linux 配置的 MMC、SDHCI、i.MX eSDHC、DOS 分区、ext4、GPIO、固定稳压器、控制台及 devtmpfs 均为内建。
- zImage 为 **10,211,984 字节**；`CONFIG_INITRAMFS_SOURCE=""`，最终 Image 不包含 Buildroot cpio，gzip 压缩链及 zImage 头一致。
- M3 DTB 为 **24,136 字节**；512 MiB 内存、UART1、MMC 别名、总线位宽、卡检测 GPIO、供电、pinctrl 和频率限制均匹配。
- 独立 ramdisk 为 **3,649,428 字节**；legacy U-Boot 头、ARM/Linux/ramdisk 类型、头与数据 CRC、gzip 内容均通过。
- ext4 为 **134,217,728 字节**，标签 `imx6ull-m3`，有 journal、无 64bit 特性；`e2fsck -fn` 五轮检查通过。
- cpio 的 init、设备节点、串口 getty、ELF 加载器和账户/所有权通过；ext4 中的 BusyBox、libc、init 链接、账户、getty、ext4 fstab 和可执行诊断脚本通过。BusyBox 最终配置包含 `blockdev` 与文件系统类型识别。

RAM 范围使用本次 `System.map` 和实际文件尺寸计算，互不重叠，且均低于 `0x9e000000` 的保守 U-Boot 保留边界：

| 区域 | 起始（含） | 末端（不含） |
| --- | --- | --- |
| 解压后内核（含 BSS） | `0x80008000` | `0x817a5210` |
| zImage | `0x84000000` | `0x849bd290` |
| DTB | `0x88000000` | `0x88005e48` |
| 诊断 ramdisk | `0x89000000` | `0x8937af94` |

## 尚待完成

1. 将三个 RAM 诊断启动文件发布到 `/srv/tftp/imx6ull-m3/`，通过现有 U-Boot 启动；记录 SD/eMMC 的控制器、设备名、容量、CID 和分区。
2. 在设备只读且 ext4 使用 `ro,noload` 的条件下检查原分区可读性。
3. 准备独立测试介质、原存储备份及恢复路径，部署外置 Buildroot rootfs，核对实际根设备并完成文件重启保留测试。

具体命令见 [M3 构建与存储检查](m3-build.md)。只有第 3 项通过后才能将 M3 标记为完成。
