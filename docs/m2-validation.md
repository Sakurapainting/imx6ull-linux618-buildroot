# M2 验收记录

日期：2026-11-08（Asia/Shanghai）。主机侧结果：**已通过**；实板 RAM 启动：**待执行**。

本次完成 M2 的首次完整构建；`scripts/verify-m2` 检查通过。验证输出见 [m2-verification.txt](m2-verification.txt)，产物与配置摘要见 [m2-artifacts.sha256](m2-artifacts.sha256)。在项目根目录执行 `sha256sum -c docs/m2-artifacts.sha256` 可核对本次基线。

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
| TFTP 下载新 zImage/DTB | 待执行；命令见 [M2 构建与 RAM 启动](m2-build.md) |
| Linux 版本和 DTB 模型 | 待执行 |
| 串口登录 shell | 待执行 |
| `uname -r` / `ps` / `mount` | 待执行 |
| SD/eMMC 未被写入 | M2 路径为 RAM 启动 |

实板日志应保存为 `logs/m2/board-ram-boot.log`。M2 通过条件是新内核能从现有 U-Boot 经 TFTP 启动，进入内置 initramfs 的串口 shell，并完成上述三个命令。

## 构建记录

首次内核下载检查因 Buildroot 未内置 Linux 6.18.62 摘要而停止；补入 `board/alpha/patches/linux/linux.hash` 后，沿用项目已签名核验的归档继续构建。强制摘要校验保持启用，未修改上游源码。

内核从上游 `imx_v6_v7_defconfig` 起步，本次只增加启动所需配置，尚未完成驱动全面裁剪；因此 rootfs 比 M1 大。DTS 仅启用 UART1，未启用 MMC、FEC、USB、LCD，也未继承旧板 320 MiB CMA 预留；内核保留上游 64 MiB 默认 CMA。

主机完整构建日志保存在 `logs/m2/build.log`，验证日志保存在 `logs/m2/verification.log`。`logs/` 和 `output/` 均由 Git 忽略，迁移工作区时另行携带。实板启动前还需恢复串口访问权限和主机 TFTP 服务。
