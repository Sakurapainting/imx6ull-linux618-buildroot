# 原系统恢复步骤

记录日期：2026-11-07。适用于保留当前原 SD 卡及其 U-Boot 的场景。已实际验证的启动链为：SD 上的 U-Boot → CachyOS TFTP 提供原内核/DTB → SD `mmcblk0p1` 上的 ext4 根文件系统。

## 已保存的恢复材料

- 主机原镜像：`/home/you/vm-dev/linux/tftpboot/zImage`、`/home/you/vm-dev/linux/tftpboot/imx6ull-alientek-emmc.dtb`。
- TFTP 服务目录：`/srv/tftp/`，文件名同上。
- U-Boot 原环境：`logs/m0/original-uboot-baseline.log`。
- 原系统启动与 Linux 基线：`logs/m0/original-linux-boot.log`、`logs/m0/original-linux-baseline.log`。
- 存储身份和分区表：`logs/m0/direct-uboot-storage.log`。

镜像 SHA256：

```text
33a00566c68a62472a49687deef289389cd4a2d5644e034be341526b63206688  zImage
7c34eec0509ce7c9fe5760251282d08977bbe90425e52d644581a6bb47e76fc6  imx6ull-alientek-emmc.dtb
```

## 主机侧恢复直连 TFTP

开发板网线接当前 USB 网卡 `enp101s0f3u1c2`，使用已建立的 NetworkManager 连接：

```bash
nmcli connection up imx6ull-m0-direct
sudo systemctl start tftpd.service
systemctl is-active tftpd.service
```

该连接为 `192.168.10.100/24`，无默认网关。主机已有指定网卡、源地址和 UDP 69 端口的 UFW 放行规则。若镜像文件缺失，重新复制已校验的原文件：

```bash
sudo install -m 644 \
  /home/you/vm-dev/linux/tftpboot/zImage \
  /home/you/vm-dev/linux/tftpboot/imx6ull-alientek-emmc.dtb \
  /srv/tftp/
```

## 板端临时恢复启动

插入原 SD 卡，上电时中断自动启动，进入 `=>`。串口为 115200、8N1。逐条执行，每次下载成功后再执行下一条：

```text
setenv serverip 192.168.10.100
setenv ipaddr 192.168.10.50
setenv netmask 255.255.255.0
setenv ethact FEC1
setenv bootargs console=ttymxc0,115200 root=/dev/mmcblk0p1 rootwait rw
ping 192.168.10.100
tftp 80800000 zImage
tftp 83000000 imx6ull-alientek-emmc.dtb
bootz 80800000 - 83000000
```

预期内核下载 6,935,080 字节、DTB 下载 38,049 字节，启动后出现 Linux 4.1.15 串口 shell。以上设置只在内存中生效，不执行 `saveenv`。

当前 `bootcmd` 没有调用环境中另存的 `mmcboot`、`mmcroot` 或 `fdt_file`；恢复时沿用已经验证的 `/dev/mmcblk0p1` 和原 TFTP DTB 文件名。

## 测试卡与备份的待办

当前 U-Boot 从 SD 启动，原根文件系统也在这张卡上。保留原卡可恢复上述启动链；替换成仅写入 rootfs 的新卡可能无法进入 U-Boot。

用户已确认目前只有这张原 SD 卡。M1/M2 先使用现有 U-Boot 经 TFTP 加载新内核及 DTB，并在 RAM 内运行内置 initramfs；原 SD 保留现有内容，M3 的新 rootfs 写入测试暂缓，也不据此改用 eMMC 覆盖原内容。

原 SD 引导区/整卡备份及备份恢复尚未验证。后续准备独立测试卡时，需要先确定读卡器及源/目标设备，再备份原引导材料、准备测试卡上的引导程序。eMMC FAT 分区虽然含旧内核和 DTB，但其文件大小与本次 TFTP 镜像不同，尚未作为备用启动链验证。
