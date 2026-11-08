# M2 构建与 RAM 启动

M2 为 Linux 6.18.62、ALPHA ATK-DL6Y2C 板级 DTS 和内置 initramfs。输出目录独立于 M1，仍由同一个 Buildroot 容器构建。

## 构建

在项目根目录执行：

```sh
scripts/build-m2 imx6ull_m2_defconfig
scripts/build-m2
scripts/verify-m2
```

保存完整日志时：

```sh
mkdir -p logs/m2
set -o pipefail
scripts/build-m2 2>&1 | tee logs/m2/build.log
scripts/verify-m2 2>&1 | tee logs/m2/verification.log
```

M2 的主要产物为 `output/m2/images/zImage`、`imx6ull-alpha.dtb`、`rootfs.cpio` 和 `rootfs.cpio.gz`。`zImage` 已把同一份 `rootfs.cpio` 编入内核；DTB 的 `memory@80000000` 覆盖 512 MiB，UART1 为 `ttymxc0`。

## TFTP 临时启动

先保留原文件名，使用独立子目录或独立名称发布 M2 产物。以下命令只复制到主机 TFTP 服务目录，不写入板上存储：

```sh
sudo mkdir -p /srv/tftp/imx6ull-m2
sudo install -m 0644 output/m2/images/zImage /srv/tftp/imx6ull-m2/
sudo install -m 0644 output/m2/images/imx6ull-alpha.dtb /srv/tftp/imx6ull-m2/
sudo systemctl start tftpd.service
nmcli connection up imx6ull-m0-direct
sudo setfacl -m u:you:rw /dev/ttyUSB0
```

串口连接使用 115200、8N1。进入 U-Boot 后只设置当前会话环境：

```text
setenv serverip 192.168.10.100
setenv ipaddr 192.168.10.50
setenv netmask 255.255.255.0
setenv ethact FEC1
ping 192.168.10.100
tftp 84000000 imx6ull-m2/zImage
tftp 88000000 imx6ull-m2/imx6ull-alpha.dtb
setenv bootargs console=ttymxc0,115200
bootz 84000000 - 88000000
```

本次选用 `0x84000000` 加载 zImage、`0x88000000` 加载 DTB。内核解压至 `0x80008000`，含 BSS 的末端为 `0x81ba5210`，与两个输入文件均不重叠；加载地址处于实测 512 MiB DDR 内，并避开 U-Boot 高端保留区域。`CONFIG_AUTO_ZRELADDR=y` 的解压程序可由 `0x84000000` 推导同一内存基址。

`scripts/verify-m2` 每次根据实际镜像尺寸和 `System.map` 检查上述范围。执行前还需核对 TFTP 传输字节数与本次摘要：zImage 为 13,842,752 字节，DTB 为 23,211 字节。不要执行 `saveenv`，也不要设置旧系统的 `root=/dev/mmcblk0p1`。

## 串口验收

M2 的主机侧验证由 `scripts/verify-m2` 完成，检查内核配置、DTB、非压缩/压缩 cpio 一致性和启动文件。实板日志已确认：

```text
Linux version 6.18.62
ALPHA ATK-DL6Y2C i.MX6ULL
login:
uname -r
ps
mount
```

此阶段根文件系统在 RAM 中，暂不验证 SD/eMMC、网口和 SSH。实板串口日志保存到 `logs/m2/board-ram-boot.log`，产物摘要保存到 `docs/m2-artifacts.sha256`。
