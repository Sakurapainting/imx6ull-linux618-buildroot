# i.MX6ULL：Linux 6.18 LTS + Buildroot

在现有正点原子 ALPHA i.MX6ULL 工程的基础上，新建独立项目，完成 Linux 6.18 LTS 板级适配及 Buildroot 根文件系统构建。

第一版验收目标：开发板启动到串口登录 shell，有线网络可用，主机可以通过 SSH 登录；重启后仍能登录。

## 当前状态

2026-11-07：M0 进行中。已检查旧 BSP、建立项目骨架，并在 CachyOS 恢复原 Linux 4.1.15 的 TFTP 启动，进入实板 shell 并采集 Linux 基线。新内核/Buildroot 尚未下载、配置、编译或上板验证。

M0 尚未完成验收。用户已确认板卡为正点原子 ALPHA `ATK-DL6Y2C`，目前只有承载原系统的这张 SD 卡。串口接管后已核对存储布局、U-Boot 启动来源和文件加载命令；剩余为 PCB 版本、物理网口及接线确认，以及独立测试介质与恢复备份。逐项进度见 [移植计划](docs/bringup-plan.md)。

实板确认使用 U-Boot 2016.03、512 MiB DDR（`0x80000000` 起始）。U-Boot 当前从 SD 启动，随后通过主机 TFTP 加载内核和 DTB，以同一 SD 卡上的 ext4 分区作为根文件系统；另可识别 7.28 GiB eMMC。两块存储的分区起始扇区已记录，`ext4load` 和 `fatload` 均已实际读取文件至 RAM。当前有线网络可通，MDIO 地址为 1、2，实测 PHY ID 均为 `0x001cc816`，与 Linux 驱动中的 RTL8201F 匹配；实物丝印和接线仍待核对。

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

初始候选版本记录于 `versions.env`：Linux 6.18.62、Buildroot 2026.08.1。版本号已核对官方发布信息；归档签名、校验值、完整构建和板级兼容性尚未验证，不是已通过验收的版本组合。

## 目录

```text
imx6ull-linux618-buildroot/
├── README.md
├── versions.env
├── docs/
│   ├── bringup-plan.md
│   └── board-baseline.md
└── br2-external/
    ├── external.desc
    ├── external.mk
    └── Config.in
```

`br2-external/` 当前只有基础入口。板级 DTS、Linux 配置、Buildroot defconfig、overlay 和构建脚本将在对应里程碑加入，不把未验证配置当作可用镜像交付。

源码下载、缓存和产物计划分别放到 `sources/`、`dl/`、`output/`。现有 BSP 在父目录中作为对照资料。

## 推进文档

- [新会话接续 M1：M0 结果、约束和下一步](docs/m1-handoff.md)
- [移植步骤与验收条件](docs/bringup-plan.md)
- [现有板级信息与待确认项](docs/board-baseline.md)
- [原系统恢复步骤与存储保护](docs/original-system-recovery.md)
- [ALPHA 官方硬件资料与实板对应边界](docs/alpha-hardware-reference.md)

下一步可开展 M1 的新构建环境准备，首个上板目标为 M2 的 RAM 串口 shell。PCB 版本和物理网口标记仍待补充；当前 SD 卡继续保留原内容，未来准备独立测试卡时需要包含可用引导程序。
