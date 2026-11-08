# M3：存储适配与外置根文件系统

状态（2026-11-08）：**主机构建及产物验证已通过，实板验收待进行**。用户确认仍只有原系统 SD 卡。原 SD 和 eMMC 的内容保留，外置根文件系统写入与持久化验收等待独立测试介质和恢复条件。结果见 [M3 验证记录](m3-validation.md)。

## 构建

在项目根目录执行：

```sh
scripts/build-m3 imx6ull_m3_defconfig
mkdir -p logs/m3
scripts/build-m3 > logs/m3/build.log 2>&1
scripts/verify-m3 > logs/m3/verification.log 2>&1
```

输出位于 `output/m3/`，采用与 M1/M2 相同的固定版本和 Buildroot 内部工具链，独立从源码构建。主要文件：

| 产物 | 用途 |
| --- | --- |
| `images/zImage` | 常规 Linux 6.18.62 内核，未嵌入 Buildroot rootfs |
| `images/imx6ull-alpha-m3.dtb` | UART1、512 MiB 内存、USDHC1 SD 和 USDHC2 eMMC |
| `images/rootfs.ext4` | 128 MiB ext4 文件系统镜像，标签 `imx6ull-m3`；实际文件为 `rootfs.ext2`，`.ext4` 为 Buildroot 的链接名 |
| `images/rootfs.tar` | 部署到已准备好文件系统的分区时使用的归档 |
| `images/rootfs.cpio.gz` | 独立的 gzip initramfs |
| `images/rootfs.cpio.uboot` | 同一 initramfs 加上 legacy U-Boot ramdisk 头，用于存储只读检查 |

`rootfs.ext4` 是单个文件系统镜像，不含分区表或 U-Boot，不能把它当成完整测试 SD 卡镜像写到整盘。

M3 与 M2 使用不同 DTB 名称。自定义 DTS 目录也会生成 M2 的 `imx6ull-alpha.dtb`；M3 上板时必须选择 `imx6ull-alpha-m3.dtb`。

## 设备树与内核

M3 DTS 引用已验收的 M2 DTS，追加存储节点，原 M2 文件不变。接线依据原工作 DTS 和 Linux 6.18 的 `fsl-imx-esdhc.yaml`、`mmc-controller.yaml`：

- SD：USDHC1、4 位，GPIO1_IO19 低有效卡检测；补充该 GPIO 的 pinctrl，固定 3.3V SD 供电，禁用写保护检测。
- eMMC：USDHC2、NAND 引脚组的 8 位总线，`non-removable`；沿用原工作 DTS 的 `no-1-8-v`。
- 两者先限制为最高 50 MHz、关闭 1.8V 切换，不在首轮启用 UHS/HS200。
- MMC、SDHCI、i.MX eSDHC、DOS 分区解析、ext4、GPIO 和固定稳压器驱动全部内建。

上述为软件适配依据；实际枚举、容量、编号和读取结果仍以 M3 实板日志为准。内核不固定 `root=`，由 U-Boot 临时传入。正常启动不传 initramfs；诊断启动明确传入独立 ramdisk。

## TFTP 发布与 RAM 诊断启动

主机管理员发布到独立目录：

```sh
sudo install -d /srv/tftp/imx6ull-m3
sudo install -m 644 \
  output/m3/images/zImage \
  output/m3/images/imx6ull-alpha-m3.dtb \
  output/m3/images/rootfs.cpio.uboot \
  /srv/tftp/imx6ull-m3/
sudo systemctl start tftpd.service
```

直连网络仍使用 `imx6ull-m0-direct`，主机 `192.168.10.100/24`，开发板 `192.168.10.50/24`。串口为 `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`、115200、8N1。如果串口权限因拔插失效，主机执行 `sudo setfacl -m u:you:rw /dev/ttyUSB0`。

进入 U-Boot 后逐条执行，核对每个文件下载成功及字节数：

```text
setenv serverip 192.168.10.100
setenv ipaddr 192.168.10.50
setenv netmask 255.255.255.0
setenv ethact FEC1
ping 192.168.10.100
tftp 84000000 imx6ull-m3/zImage
tftp 88000000 imx6ull-m3/imx6ull-alpha-m3.dtb
tftp 89000000 imx6ull-m3/rootfs.cpio.uboot
setenv bootargs console=ttymxc0,115200
bootz 84000000 89000000 88000000
```

不要执行 `saveenv`。三个输入文件分别位于 `0x84000000`、`0x88000000`、`0x89000000`；`scripts/verify-m3` 使用实际产物和 `System.map` 检查它们与解压后内核、DDR 及 U-Boot 保留区的边界。

本次下载字节数分别为：zImage **10,211,984**，M3 DTB **24,136**，ramdisk **3,649,428**。摘要见 `docs/m3-artifacts.sha256`，重新构建后应重新生成并核对实际值。

诊断模式使用 root 空密码串口登录，根目录在 RAM。先记录：

```sh
m3-storage-report
```

该脚本仅允许在 RAM `rootfs` 根目录中运行，先通过 `blockdev --setro` 将所有 MMC 块设备及分区设为内核只读状态，并逐一检查标志，再打印内核、根目录、分区、容量、CID、文件系统 UUID 和驱动日志。此标志只影响本次内核运行，不修改介质内容，重启后重新设置。

确认容量、CID、控制器和分区编号后才读取分区。原 SD 的 ext4 读取应明确指定 `mount -t ext4 -o ro,noload <已核对分区> <挂载点>`；`noload` 阻止 ext4 日志重放。检查期间不进行格式化、分区、修复或写入。日志保存到 `logs/m3/board-storage-probe.log`。

## 外置根文件系统验收（待介质就绪）

当前不生成带真实设备路径的写盘命令。用户只有原系统 SD 卡，eMMC 也已有两个原分区，尚未完成备份与恢复验证。后续需要：

1. 确定独立测试 SD、读卡器、源和目标设备，备份原引导材料，并为测试卡准备可用 U-Boot。板子目前从 SD 进入 U-Boot，只放一个 rootfs 的测试卡无法保证启动。
2. 在测试卡的已核对根分区部署 `rootfs.ext4` 或以 root 权限解包 `rootfs.tar`，记录实际分区表及 PARTUUID。不得覆盖原 SD。
3. 使用 M3 正常 zImage 和配套 DTB，不传诊断 initramfs。临时 bootargs 为 `console=ttymxc0,115200 root=PARTUUID=<实测分区标识> rootwait rw`，启动为 `bootz 84000000 - 88000000`。尖括号内容必须替换为真实值。
4. 串口核对 `uname -r`、`/proc/cmdline`、`/proc/mounts` 和实际根设备，证明根目录来自测试卡上的 ext4。
5. 在测试根目录创建标记文件、`sync`，正常重启并再次执行同一临时启动流程；验证文件保留、串口可登录，记录证据。随后进行断电重启验收。

RAM 诊断成功不等于 M3 完成。M3 的最终验收必须包含外置 rootfs 启动与持久化；永久启动环境与 SSH 分别在后续阶段处理。
