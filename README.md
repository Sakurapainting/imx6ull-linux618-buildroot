# i.MX6ULL：Linux 6.18 LTS + Buildroot

在现有正点原子 ALPHA i.MX6ULL 工程的基础上，新建独立项目，完成 Linux 6.18 LTS 板级适配及 Buildroot 根文件系统构建。

第一版验收目标：开发板启动到串口登录 shell，有线网络可用，主机可以通过 SSH 登录；重启后仍能登录。

## 当前状态

2026-11-08：**M1、M2 已通过验收**。Linux 6.18.62 的 ALPHA 板级 DTS、内核配置、内置 initramfs、zImage 和 DTB 均已构建，并从现有 U-Boot 经 TFTP 在 RAM 启动到串口 root shell；具体证据见 [M1 验收记录](docs/m1-validation.md) 和 [M2 验收记录](docs/m2-validation.md)。

M3 **主机构建、产物校验及实板存储只读检查已通过，最终验收尚待完成**：Linux 6.18.62 已从独立 initramfs 启动，正确识别 USDHC1 的 SD 和 USDHC2 的 8 位 eMMC，三个原分区均只读挂载及文件读取成功。用户确认仍只有原系统 SD 卡，外置 Buildroot rootfs 写入与重启持久化验收等待测试介质和恢复条件。操作见 [M3 构建与存储检查](docs/m3-build.md)，证据见 [M3 验证记录](docs/m3-validation.md)。

M0 尚未完成验收。用户已确认板卡为正点原子 ALPHA `ATK-DL6Y2C`，目前只有承载原系统的这张 SD 卡。串口接管后已核对存储布局、U-Boot 启动来源和文件加载命令；剩余为 PCB 版本、物理网口及接线确认，以及独立测试介质与恢复备份。逐项进度见 [移植计划](docs/bringup-plan.md)。

实板确认使用 U-Boot 2016.03、512 MiB DDR（`0x80000000` 起始）。原系统已验证的启动链为 SD 上的 U-Boot → 主机 TFTP 提供原内核/DTB → 同一 SD 的 ext4 根分区；当前运行的 M3 诊断系统则使用 RAM initramfs。M3 已识别 28.9 GiB SD 和 7.28 GiB eMMC，分区起始扇区与原基线一致。原系统及 U-Boot 的有线通信已验证；新 Linux 网口仍待 M4。MDIO 地址为 1、2，实测 PHY ID 均为 `0x001cc816`，与 Linux 驱动中的 RTL8201F 匹配；实物丝印和接线仍待核对。

## 技术路线

```text
板上现有 U-Boot（先确认能正常工作）
    → Linux 6.18.y + 新适配的板级 DTB
    → Buildroot / BusyBox init
    → ttymxc0 串口登录
    → 有线以太网
    → Dropbear SSH
```

调试顺序：保留当前 SD 卡上的 U-Boot 和原系统，通过 TFTP 加载带内置 initramfs 的新内核和配套 DTB，在 RAM 中验证内核和用户空间。M1 构建与 M2 RAM 启动可先推进；M3 写入新 rootfs 的测试待独立测试介质及恢复条件就绪后进行。独立 SD 验证稳定后再安排 eMMC 部署。

内核和用户空间拟由 Buildroot 统一构建，使用 Buildroot 内部工具链。初期沿用板上已有 U-Boot，兼容性在上板阶段验证。

固定版本记录于 `versions.env`：Linux 6.18.62、Buildroot 2026.08.1。官方签名和归档摘要已核验，见 [源码验证记录](docs/source-verification/README.md)；串口 RAM 启动已通过 M2，存储和网络由后续里程碑继续验证。

## 目录

```text
imx6ull-linux618-buildroot/
├── README.md
├── versions.env
├── sources.lock.sha256
├── dev-env/
│   └── Containerfile
├── scripts/
│   ├── env
│   ├── fetch-sources
│   ├── build
│   ├── build-m2
│   ├── build-m3
│   ├── verify-m1
│   ├── verify-m2
│   └── verify-m3
├── docs/
│   ├── bringup-plan.md
│   ├── board-baseline.md
│   ├── m1-build.md
│   ├── m2-build.md
│   ├── m2-validation.md
│   ├── m3-build.md
│   └── m3-validation.md
└── br2-external/
    ├── configs/imx6ull_m1_defconfig
    ├── configs/imx6ull_m2_defconfig
    ├── configs/imx6ull_m3_defconfig
    ├── board/alpha/dts/nxp/imx/imx6ull-alpha.dts
    ├── board/alpha/dts/nxp/imx/imx6ull-alpha-m3.dts
    ├── board/alpha/linux/m2.fragment
    ├── board/alpha/linux/m3.fragment
    ├── board/alpha/busybox/m3.fragment
    ├── board/alpha/rootfs-overlay-m3/
    ├── board/alpha/patches/linux-headers/linux-headers.hash
    ├── board/alpha/patches/linux/linux.hash
    ├── external.desc
    ├── external.mk
    └── Config.in
```

`br2-external/` 已包含 M1/M2/M3 defconfig、板级 DTS、Linux/BusyBox 配置片段、M3 rootfs overlay 与归档摘要。

源码、缓存和产物分别位于 `sources/`、`dl/`、`output/m1/`、`output/m2/`、`output/m3/`，均由 Git 忽略。现有 BSP 在父目录中作为对照资料。从零构建与验证命令见 [M1 构建说明](docs/m1-build.md)、[M2 构建说明](docs/m2-build.md) 和 [M3 构建说明](docs/m3-build.md)。

## 推进文档

- [交接状态：M0/M1 结果、约束和 M2 下一步](docs/m1-handoff.md)
- [M1 构建环境、命令与验证](docs/m1-build.md)
- [M1 验收记录与产物摘要](docs/m1-validation.md)
- [M2 构建、TFTP/RAM 启动与串口验证](docs/m2-build.md)
- [M2 主机与实板验收记录](docs/m2-validation.md)
- [M3 构建、存储只读检查与外置 rootfs 验收步骤](docs/m3-build.md)
- [M3 验证进度与证据](docs/m3-validation.md)
- [源码签名与固定摘要](docs/source-verification/README.md)
- [移植步骤与验收条件](docs/bringup-plan.md)
- [现有板级信息与待确认项](docs/board-baseline.md)
- [原系统恢复步骤与存储保护](docs/original-system-recovery.md)
- [ALPHA 官方硬件资料与实板对应边界](docs/alpha-hardware-reference.md)

M3 的主机构建和 RAM 存储只读检查已通过；独立测试介质和恢复条件具备后再写入并验收外置 rootfs。原 SD 卡继续保留原内容，PCB 版本和物理网口标记仍待补充；M4 再适配有线网络。
