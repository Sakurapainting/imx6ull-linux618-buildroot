# 源码锁定与官方签名

验证日期：2026-11-08（Asia/Shanghai）。固定 Linux `6.18.62` 和 Buildroot `2026.08.1`，压缩归档 SHA256 保存在项目根目录 `sources.lock.sha256`。此记录证明源码身份及传输完整性；板级兼容性由后续 M2 验证。

## 下载来源

| 对象 | 官方来源 |
| --- | --- |
| Buildroot 归档 | `https://buildroot.org/downloads/buildroot-2026.08.1.tar.xz` |
| Buildroot 签名 | `https://buildroot.org/downloads/buildroot-2026.08.1.tar.xz.sign` |
| Linux 归档 | `https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.62.tar.xz` |
| Linux 签名 | `https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.62.tar.sign` |

## 公钥与信任依据

- Buildroot：Arnout Vandecappelle，主钥指纹 `18C7DF2819C1733D822D599EA500D6EE9CB0E540`。公钥从签名文件指向的发布者地址 `https://gitlab.com/-/snippets/4836881/raw/main/arnout@rnout.be.asc` 获取，官方签名入口为 `https://buildroot.org/download.html`。公钥副本在 `keys/buildroot-release.asc`。这是经 HTTPS 官方发布渠道建立的信任，未声称完成线下身份认证或独立 Web of Trust 认证。
- Linux：Greg Kroah-Hartman，主钥指纹 `647F28654894E3BD457199BE38DBBDC86092693E`。通过 `gpg --auto-key-locate clear,wkd --locate-keys gregkh@kernel.org` 获取，并与 `https://www.kernel.org/signature.html` 的 Important fingerprints 对照。公钥副本在 `keys/gregkh.asc`。

GPG 的 `TRUST_UNDEFINED` 提示表示本地未对公钥作个人信任认证；验证记录中的 `VALIDSIG` 已与上述固定指纹核对。脚本使用独立临时 keyring，不修改用户个人信任设置。

## 核验方法与结果

1. Buildroot 的 `.sign` 是 clear-signed 文本。先验证文本签名，再从签名覆盖的文本读取 SHA256，与实际 `.tar.xz` 比对。只执行 `gpg --verify *.sign` 不能证明压缩包一致。本次两步均成功，记录为 `buildroot-signature.txt` 和 `logs/m1/fetch-sources.log`。
2. Linux 是解压后 `.tar` 的 detached signature。本次以 `xz -dc ...tar.xz | gpg --verify ...tar.sign -` 验证成功，记录为 `linux-signature.txt`，再计算 `.tar.xz` SHA256 并锁定。
3. 签名原件、公钥和摘要均纳入版本控制；大归档和源码树保存在忽略的 `sources/`。重新获取运行 `scripts/fetch-sources`，必须通过固定摘要、签名及签名者指纹检查后才解包。
4. Linux 同一归档供 Buildroot 的 `linux-headers` 使用；`br2-external/board/alpha/patches/linux-headers/linux-headers.hash` 保存其 SHA256，配置启用 `BR2_DOWNLOAD_FORCE_CHECK_HASHES`。其余依赖由固定 Buildroot 版本内各包的 hash 文件校验。

原始下载、key import、签名和构建日志在忽略的 `logs/m1/`；本目录保留可随 Git 迁移的签名证据。流程与配置可重建，容器中的 apt 软件包尚未按 Debian snapshot 固定，不声称产物逐字节可复现。
