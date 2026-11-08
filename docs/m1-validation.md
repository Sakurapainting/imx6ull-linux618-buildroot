# M1 验收记录

日期：2026-11-08（Asia/Shanghai）。结果：**M1 通过**。本次完成主机侧首次完整构建和产物检查。

## 验收项

| 项目 | 实测结果 |
| --- | --- |
| 独立构建环境 | Debian 12 bookworm-slim，基础镜像 digest 固定；rootless Podman；编译 UID/GID `1000:1000`；8 路并发 |
| 源码身份 | Linux `6.18.62` / Buildroot `2026.08.1`，官方签名、固定签名者指纹及压缩归档 SHA256 均通过 |
| 内部工具链 | GCC `15.3.0`、binutils `2.45.1`、musl `1.2.6`、Linux headers `6.18.62` |
| 目标 ABI | Cortex-A7、ARMv7-A、ELF32、小端、EABI5、hard-float；属性包含 VFPv4、NEON、`Tag_ABI_VFP_args: VFP registers` |
| 实际交叉编译 | 生成 ARM relocatable `probe.o`，并成功链接 ARM PIE 可执行文件；解释器为 `/lib/ld-musl-armhf.so.1` |
| 最小用户空间 | BusyBox `1.38.0` 构建成功，生成完整 newc cpio 和 gzip cpio |
| 归档内容 | 373 项；压缩与非压缩内容一致；`/init` 可执行并挂载 devtmpfs 后运行 `/sbin/init`；BusyBox shell、init、getty、mount、ps、uname 和 musl 动态加载器齐全 |
| 控制台与权限 | `/dev/console` 为字符设备 `5:1`；getty 为 `ttymxc0/115200`、respawn；启动文件属于 root，所有 UID/GID 均可在归档账户表中找到 |
| 版本标签 | 最终 GCC 为 `(Buildroot 2026.08.1) 15.3.0`；rootfs `os-release` 的 `VERSION` 与 `VERSION_ID` 均为 `2026.08.1` |

## 最终产物

| 路径 | 字节数 | SHA256 |
| --- | ---: | --- |
| `output/m1/images/rootfs.cpio` | 1,833,984 | `32fc0c8f28f392ebd269bb8bec922046420c41638800899a484ee818da222bca` |
| `output/m1/images/rootfs.cpio.gz` | 995,021 | `cd3eb828fc66251f4db416373888a444b12e6c8f0a520755756f50aebdce80ce` |

当前完整 `.config` 的 SHA256 为 `134d309afd927e61f418cb0b6b69c2013d886e35a188e9852001e7f15bbc6538`。最终产物、配置和构建入口摘要保存在 [m1-artifacts.sha256](m1-artifacts.sha256)，可在项目根目录运行 `sha256sum -c docs/m1-artifacts.sha256` 检查本次基线。重新生成归档可能改变时间戳和摘要。

验证输出见 [m1-verification.txt](m1-verification.txt)，实际选项与版本见 [m1-build-versions.txt](m1-build-versions.txt)。源码签名与公钥来源见 [源码验证记录](source-verification/README.md)，从零构建命令见 [M1 构建说明](m1-build.md)。

## 构建记录与修正

首次 `scripts/build` 完整构建成功。整理版本时发现上游 Buildroot 的 `setlocalversion` 向上探测到本项目 Git，误把父仓库提交号用作版本标签。已在 `scripts/build` 设置 `GIT_CEILING_DIRECTORIES=/work`，重新配置最终 GCC，并让其版本头文件生成器重新构建；随后重新安装 GCC、生成 rootfs 并运行最终验证。干净构建直接使用修正后的入口，无需手改源码或 output 文件。

归档验证脚本同时按标准账户表检查所有权，并按 getty 命令参数检查串口配置，兼容标准目录的 `www-data` 所有权与配置中的连续空格。

本机详细记录在 `logs/m1/`：初次构建 `build.log`、版本修正 `gcc-version-fix.log` / `gcc-version-rebuild.log`、最终 rootfs 生成 `finalize.log`、最终验证 `verification.log`、环境与容器包清单、依赖包信息和下载文件摘要。`build-evidence.sha256` 覆盖主要本地证据；`logs/` 由 Git 忽略，迁移时需单独携带。输出约 6.6 GiB，下载缓存约 291 MiB，归档及源码约 1.9 GiB。

## 验收边界和下一步

- 本次未接管串口、未修改 SD/eMMC、未更新 TFTP 服务端文件，也未构建新内核或 DTB。
- M1 的 ARM 探针完成编译和链接；未在主机模拟器或实板上运行。新内核与用户空间的实板运行由 M2 验证。
- M0 剩余硬件核对、备份和独立介质条件仍保留。M2 继续使用 TFTP/RAM 内置 initramfs 路径；M3 写入阶段仍等待条件就绪。
- 这是首次完整构建；从全新输出目录再构建属于 M6。apt 软件包尚未使用 snapshot 固定，未验证逐字节可复现。

下一步：以 Linux 6.18.62 EVK/SoC DTS 和旧板接线资料为依据，创建 ALPHA 板级 DTS 与 M2 配置，构建带内置 initramfs 的 zImage 和配套 DTB，再按实际尺寸设计 RAM 启动布局。
