# M1 构建与验证

本阶段建立主机侧的新构建环境，生成 ARM 工具链和最小 BusyBox rootfs。板级 DTS、内核镜像与实板 RAM 启动属于 M2。

2026-11-08 已通过 M1 验收，版本、最终产物摘要及验证边界见 [M1 验收记录](m1-validation.md)。

## 构建环境

主机检查（2026-11-08）：CachyOS、x86_64 Ryzen 7 8845HS、16 线程、约 22 GiB RAM，开始时约 14 GiB 可用内存和 118 GiB 磁盘空间。使用现有 rootless Podman，构建并发设置为 8。

`dev-env/Containerfile` 使用 Debian bookworm-slim，固定基础镜像 digest。安装主机编译工具与 Buildroot 依赖；交叉工具链由本项目 Buildroot 从源码构建。`scripts/env` 仅挂载本项目到容器 `/work`，使用 `--userns=keep-id` 和当前用户 UID/GID，编译进程为普通用户。

`scripts/build` 设置 Git ceiling，避免解包后的 Buildroot 归档向上找到本项目的 `.git`，从而把本项目提交号误用为 Buildroot 版本标签。

首次镜像 ID、主机编译器与 apt 软件包清单记录在 `logs/m1/container-inspect.json`、`logs/m1/container-packages.txt`。apt 仓库随时间更新，尚未使用 Debian snapshot；流程可重建与逐字节相同是不同验收目标。

## 从零构建

在项目根目录执行（主机需要 Podman、curl、GnuPG、xz、tar、sha256sum）：

```sh
scripts/fetch-sources
scripts/env image
scripts/build imx6ull_m1_defconfig
scripts/build
scripts/verify-m1
```

需要保存日志时：

```sh
mkdir -p logs/m1
set -o pipefail
scripts/build 2>&1 | tee logs/m1/build.log
scripts/verify-m1 2>&1 | tee logs/m1/verification.log
```

源码官方签名、公钥来源和 SHA256 见 [源码验证记录](source-verification/README.md)。`scripts/fetch-sources` 可重复运行；已存在的归档仍会重新核验，已解包源码树不会覆盖。如怀疑源码树被手动修改，保留修改后移走相应目录，再重新解包。

## 配置与产物

入口为 `br2-external/configs/imx6ull_m1_defconfig`，设置 ARM little-endian、Cortex-A7、EABIhf、NEON/VFPv4、Buildroot 内部 musl 工具链，Linux headers 固定为 `6.18.62`。BusyBox init、devtmpfs 和 `ttymxc0,115200` getty 使用 Buildroot 标准机制。

M1 不启用内核或 U-Boot 构建，输出 cpio 和 gzip cpio。root 登录沿用最小 Buildroot 默认空密码，供后续 RAM 串口调试；M5 再配置 SSH 用户和公钥。

| 路径 | 用途 |
| --- | --- |
| `sources/buildroot-2026.08.1/` | 官方 Buildroot 源码 |
| `sources/linux-6.18.62/` | 已验证 Linux 源码，供 M2 查阅及适配 |
| `dl/` | Buildroot 依赖下载缓存；官方 Linux 归档预置在 `dl/linux/` |
| `output/m1/.config` | 完整 Buildroot 配置 |
| `output/m1/host/bin/arm-buildroot-linux-musleabihf-gcc` | 交叉编译器，在同一容器中使用 |
| `output/m1/host/arm-buildroot-linux-musleabihf/sysroot/` | 目标 sysroot |
| `output/m1/images/rootfs.cpio` | 完整 newc initramfs 归档 |
| `output/m1/images/rootfs.cpio.gz` | 压缩归档 |
| `output/m1/probe/` | ARM 编译与链接探针、ELF 属性 |
| `logs/m1/` | 下载、容器、配置、构建及验证日志 |

不要将 `output/m1/target/` 直接当成最终 rootfs：权限、设备节点和 `/init` 由生成镜像时的 fakeroot 阶段完成。核验针对 `images/rootfs.cpio`。

## 日常操作

```sh
scripts/build menuconfig
scripts/build savedefconfig
scripts/build
scripts/verify-m1
scripts/env shell
```

`savedefconfig` 会写回本项目 defconfig，应在审阅差异后保留。工具链选项或 ABI 改动应使用新输出目录完整重建；当前入口固定 `output/m1`。本阶段只验证一次首次完整构建，M6 再验收全新输出目录重建。

`scripts/verify-m1` 编译并链接 ARM 探针，检查 ELF 位宽、端序、ARMv7 和 VFP 参数 ABI，再检查生成归档中的启动路径、BusyBox、动态加载器、启动文件的 root 所有权、所有条目的 UID/GID 与账户表、`/dev/console` 及串口 getty。它不在主机执行 ARM 程序，实板执行与内核启动由 M2 验收。
