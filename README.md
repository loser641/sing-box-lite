# sing-box-lite

sing-box 低内存 / 小体积定制构建（**非官方**，与 SagerNet 无关）。

跟随上游 [SagerNet/sing-box](https://github.com/SagerNet/sing-box) 正式版本自动裁剪、编译、发布，为 64MB 内存的 NAT VPS 一类低配环境设计，配合 [singbox-deploy](https://github.com/loser641/singbox-deploy) 一键脚本使用。

## 实测数据（Alpine 64MB NAT 容器，同配置 A/B）

| 指标 | 官方 v1.14.3 | 本构建 | 变化 |
|---|---|---|---|
| 二进制体积 | 87.7 MB | 34.8 MB | **-60%** |
| 启动内存峰值（VmHWM） | 44.8 MB | 35.5 MB | **-21%** |
| 稳态堆内存（anon） | ~11.8 MB | 10.4 MB | 持平略降 |

体积小 → 下载快、小盘友好；启动峰值低 → 64MB 机器不容易在内核启动瞬间被 OOM killer 杀掉。稳态内存与官方相当（没用到的协议代码本来就不会加载进内存），真正稳定的省内存手段是给进程设 `GOMEMLIMIT`（如 `GOMEMLIMIT=24MiB`）。

## 保留与裁剪

**保留**（[singbox-deploy](https://github.com/loser641/singbox-deploy) 支持的全部协议）：

- 入站/出站：`vless`（含 REALITY）、`anytls`、`shadowsocks`、`tuic`、`hysteria2`（含 hysteria）
- 基础：`direct`、`block`、`selector`/`urltest`、DNS 全套（local/hosts/fakeip/https/quic 等）
- 构建标签：`with_quic`、`with_utls`

**裁掉**：vmess、trojan、socks、http、mixed、snell、naive、shadowtls、ssh、tor、tun/redirect/tproxy、wireguard、tailscale、openvpn、openconnect、cloudflared、gvisor、clash api、usbip、内置 acme 等。

配置里用到被裁掉的协议时会明确报错：`unknown inbound type: vmess`，不会静默失效。

## 下载

Releases 页面提供 `sing-box-<版本>-linux-<架构>.tar.gz`（amd64 / arm64 / armv7），包内是名为 `sing-box` 的静态二进制，musl（Alpine）和 glibc 通用。请用 `sha256sums.txt` 校验。

## 配合 singbox-deploy 使用

```sh
SB_KERNEL=lite sh -c "$(wget -qO- https://github.com/loser641/singbox-deploy/raw/main/sb.sh)"
```

或在面板（`singbox` / `lsb`）里选「切换/更新内核」，随时在官方版与裁剪版之间切换。不设置 `SB_KERNEL` 时默认用官方内核，行为与从前完全一致。

## 自动跟版

`.github/workflows/build.yml` 每天检查上游 release：

1. 上游发新版 → 自动裁剪、编译（amd64/arm64/armv7）→ 冒烟测试 → 发布 `vX.Y.Z-lite.N`
2. 冒烟测试：5 种保留协议的配置必须全部通过 `sing-box check`，被裁协议的配置必须被拒绝
3. 上游新增协议/注册点时，`trim.py` 会 **fail-closed** 报错并停住构建（不会静默编出错东西），维护者更新清单后放行
4. 遇到安全补丁可在 Actions 页手动触发（可选「强制重建」）

版本号 `vX.Y.Z-lite.N`：X.Y.Z 是上游版本，N 是本仓库对同版本的第 N 次构建。

## 复现构建

```sh
git clone --depth 1 --branch vX.Y.Z https://github.com/SagerNet/sing-box
python3 trim.py sing-box server   # Windows 客户端用 client
cd sing-box
LDF="$(cat release/LDFLAGS)"
CGO_ENABLED=0 go build -trimpath \
  -ldflags "-X github.com/sagernet/sing-box/constant.Version=X.Y.Z-lite.1 ${LDF} -s -w -buildid=" \
  -tags "with_quic,with_utls,badlinkname,tfogo_checklinkname0" \
  -o sing-box ./cmd/sing-box
```

Windows 客户端版：`GOOS=windows`，tags 追加 `with_gvisor`（TUN 的 gvisor 栈，不加会在运行时拒绝启动 TUN），产物为 `sing-box.exe`，打包成 zip。

裁剪全部由 [`trim.py`](trim.py) 完成（清单在文件头部），本仓库不含上游源码副本；源码以 GPL-3.0 从上游获取，修改内容即 trim.py 与构建工作流。

## 合规声明

基于 sing-box（Copyright (C) 2022 by nekohasekai，GPL-3.0）修改构建，LICENSE 与上游一致。本仓库公开全部修改（裁剪脚本与构建流程），可按上文复现。本项目为第三方构建，与 SagerNet 官方无关，不提供任何担保。
