# M3 验证记录

日期：2026-11-08。目标为 ALPHA ATK-DL6Y2C、512 MiB DDR、SD 和 8 位 eMMC；版本沿用项目锁定的 Linux 6.18.62、Buildroot 2026.08.1。

## 当前结论

**M3 主机构建、产物校验和实板 RAM 存储只读检查已通过，里程碑尚未完成最终验收。** 用户确认仍只有原系统 SD 卡；本次未写入 SD/eMMC，也未保存 U-Boot 环境。外置 Buildroot rootfs 的部署、读写和重启持久化尚未执行。

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
- M3 上板前曾串口复核当时运行的 M2：`uname -r` 为 `6.18.62`，命令行仅含 `console=ttymxc0,115200`，根目录为 RAM rootfs，没有 MMC 块设备。日志为 `logs/m3/board-preflight.log`。此结果不作为 M3 存储识别证据。

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

## 实板 RAM 启动与存储读取

用户发布 TFTP 文件后，主机重新核对了三份文件的 SHA256 和字节数。通过串口从 M2 RAM 系统正常重启，中断自动启动，使用临时环境加载 M3 zImage、DTB 和 ramdisk。U-Boot 下载字节数全部匹配，ramdisk 校验和检查为 OK；`bootz 84000000 89000000 88000000` 成功进入 Linux 6.18.62 串口 root shell。

`m3-storage-report` 返回 0：根目录为 RAM `rootfs`，启动参数只有 `console=ttymxc0,115200`；SD/eMMC 块设备、分区及 eMMC boot0/boot1 均已设为只读。实测对应关系：

| Linux 设备 | 控制器/身份 | 容量（字节） | 实际运行参数 |
| --- | --- | ---: | --- |
| `mmcblk0` | USDHC1 `2190000.mmc`，SD32G，SD | 31,016,878,080 | 4 位，50 MHz，SD high-speed，3.3V |
| `mmcblk1` | USDHC2 `2194000.mmc`，8GTF4R，MMC | 7,818,182,656 | 8 位，50 MHz，MMC DDR52，3.3V |

CID 分别为 `27504853443332476001779106016c00` 和 `150100384754463452099e3bbc23b900`。原 SD 引导区未写入；eMMC boot0/boot1 均识别为 4 MiB，RPMB 为 512 KiB 字符设备，本次未访问其数据。

三个原分区的起始/长度均与 M0 相符，单位为 512 字节扇区：

| 分区 | 起始 | 扇区数 | `blkid` 类型 | 只读验证 |
| --- | ---: | ---: | --- | --- |
| `mmcblk0p1` | 8192 | 60571648 | ext4 | `ro,noload` 挂载，读取目录及 `/etc/inittab` SHA256 |
| `mmcblk1p1` | 20480 | 262144 | vfat | `ro` 挂载，读取目录及原 `zImage` SHA256 |
| `mmcblk1p2` | 282624 | 14987264 | ext3 | 由 ext4 驱动以 `ro,noload` 挂载，读取目录及 `/etc/passwd` SHA256 |

原 SD 的 DOS 分区类型字段仍为 `0c`，实际文件系统为 ext4；eMMC `p2` 本次探测为 ext3，能由 ext4 驱动读取。未更改分区表或文件系统。`/proc/mounts` 确认两个 ext 分区均为 `ro,norecovery`，内核日志明确显示 `ro without journal`。全部挂载已成功卸载，最终复核根目录仍在 RAM、MMC 只读标志仍为 1。

完整串口日志位于 `logs/m3/board-storage-probe.log`；选录和完整日志摘要见 [实板证据](m3-board-verification.txt)。一次最后的长串口命令曾丢失字符并进入续行提示，已取消后用短命令逐项复核；当时三个分区已卸载。该串口传输问题不影响上述最终状态。

U-Boot 对未启用 PHY 节点的提示、缺失 `regulatory.db` 等沿用 M2 的非阻断提示，未影响 MMC 识别和读取。网络仍待 M4。本次结束时板子停在 **M3 串口登录提示**，串口已释放。

## 尚待完成

准备独立测试介质、原存储备份及恢复路径，部署外置 Buildroot rootfs，核对实际根设备并完成创建文件、重启保留及断电重启测试。

具体命令见 [M3 构建与存储检查](m3-build.md)。只有上述外置 rootfs 持久化验收通过后才能将 M3 标记为完成；当前 RAM 诊断通过不替代该验收。
