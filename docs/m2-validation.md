# M2 验收记录

日期：2026-11-08（Asia/Shanghai）。结果：**M2 通过**。

本次完成 M2 的首次完整构建和实板 RAM 启动；`scripts/verify-m2` 检查通过。验证输出见 [m2-verification.txt](m2-verification.txt)，产物与配置摘要见 [m2-artifacts.sha256](m2-artifacts.sha256)。在项目根目录执行 `sha256sum -c docs/m2-artifacts.sha256` 可核对本次基线。

## 主机侧

| 项目 | 结果 |
| --- | --- |
| Buildroot 配置 | `br2-external/configs/imx6ull_m2_defconfig` |
| Linux | `6.18.62`，`imx_v6_v7` 基础配置加 M2 fragment |
| 板级 DTB | `imx6ull-alpha.dtb`，UART1 / `ttymxc0`，512 MiB DDR |
| 内置 initramfs | `rootfs.cpio` 与 `rootfs.cpio.gz`，均通过内容校验 |
| zImage | 13,842,752 字节，ARM 小端 zImage，内含经过验证的同一份 Image 和 cpio |
| DTB | 23,211 字节，FDT v17；UART、内存和无关外设禁用状态检查通过 |
| rootfs | 9,935,872 字节，gzip 为 3,647,092 字节，共 704 项；包含上游配置生成的内核模块 |
| RAM 布局 | kernel `[0x80008000, 0x81ba5210)`，zImage `[0x84000000, 0x84d33940)`，DTB `[0x88000000, 0x88005aab)`，无重叠 |
| 验证入口 | `scripts/verify-m2` |

## 实板侧

| 项目 | 结果 |
| --- | --- |
| TFTP 下载新 zImage/DTB | 已通过：zImage `13,842,752` 字节，DTB `23,211` 字节；加载地址 `0x84000000` / `0x88000000` |
| Linux 版本和 DTB 模型 | 已通过：Linux `6.18.62`；`ALPHA ATK-DL6Y2C i.MX6ULL` |
| 串口登录 shell | 已通过：内置 initramfs 登录 `root` 后得到 shell |
| `uname -r` / `ps` / `mount` | 已通过：`6.18.62`、PID 1 为 `init`、根为 `rootfs (rw)` |
| SD/eMMC 未被写入 | M2 路径为 RAM 启动 |

实板日志保存在 `logs/m2/board-ram-boot.log`，SHA256 为 `aa1ab1204d1fb1127afd34becbae99985ff0d8cef156b57bd503c9932f045f0e`；关键输出另保存为已跟踪的 [m2-board-verification.txt](m2-board-verification.txt)。板端内存总量为 `497328 kB`，`/proc/partitions` 未列出 MMC，根文件系统和所有已挂载文件系统均位于 RAM。验收后退出 root shell，开发板留在 M2 登录提示，主机串口已释放。

启动时 U-Boot 报告旧路径下的 PHY 地址 2 节点不存在；M2 未配置 FEC/MDIO，网络节点在 M4 适配。上游配置启用了 cfg80211，但 rootfs 未打包 `regulatory.db`，日志记录固件加载 `-2`；SNVS pinctrl 空组等提示也保留在完整日志中。这些提示未阻断串口启动及命令验收；本阶段未验证网络、无线或 PXP 等外设功能。

## 构建记录

首次内核下载检查因 Buildroot 未内置 Linux 6.18.62 摘要而停止；补入 `board/alpha/patches/linux/linux.hash` 后，沿用项目已签名核验的归档继续构建。强制摘要校验保持启用，未修改上游源码。

内核从上游 `imx_v6_v7_defconfig` 起步，本次只增加启动所需配置，尚未完成驱动全面裁剪；因此 rootfs 比 M1 大。板级 DTS 仅显式启用 UART1，MMC、FEC、USB、LCD 保持禁用；SoC DTS 中默认启用的内部节点仍保留，包括 PXP。未继承旧板 320 MiB CMA 预留，内核保留上游 64 MiB 默认 CMA。

主机完整构建日志保存在 `logs/m2/build.log`，验证日志保存在 `logs/m2/verification.log`。`logs/` 和 `output/` 均由 Git 忽略，迁移工作区时另行携带。M2 没有写入 SD/eMMC，也没有执行 `saveenv`。
