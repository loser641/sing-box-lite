#!/usr/bin/env python3
# sing-box 协议裁剪器（fail-closed）
# 用法: python trim.py <sing-box 源码根目录>
# 只改写 include/registry.go：删除不用的协议注册及其 import，
# 让 Go 链接器把整个协议子树从二进制剔除。
# 上游如果新增了清单外的注册调用，脚本直接报错退出，不会静默放过。
import re
import sys
from pathlib import Path

# ---- 裁剪清单（按需修改这里）----
# 保留的协议包（我们部署脚本实际用到的）
KEEP = {
    "direct",        # 出站直连 + direct 入站
    "shadowsocks",
    "vless",         # 含 REALITY
    "anytls",
    "block",
    "group",         # selector / urltest（很小，留着兼容）
}
# 删除的协议包
DROP = {
    "tun", "redirect", "socks", "http", "mixed", "snell",
    "vmess", "trojan", "naive", "shadowtls", "bridge", "tor", "ssh",
}
# 非协议注册（dns transport / service / certificate provider），默认保留
KEEP_OTHER = {
    "transport", "hosts", "local", "mdns", "fakeip", "resolved",
    "api", "ssmapi", "originca",
}
# ---------------------------------


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python trim.py <sing-box 源码根目录>")
        return 2
    reg = Path(sys.argv[1]) / "include" / "registry.go"
    if not reg.is_file():
        print(f"[FAIL] 找不到 {reg}")
        return 1
    src = reg.read_text(encoding="utf-8")

    # 收集所有 pkg.RegisterXxx(registry) 调用，逐条分类；未知包名一律中止
    call_re = re.compile(r"^\t([a-z0-9_]+)\.\w*Register\w*\(registry\)$", re.M)
    unknown = sorted({m for m in call_re.findall(src)
                      if m not in KEEP and m not in DROP and m not in KEEP_OTHER})
    if unknown:
        print(f"[FAIL] 上游 registry.go 出现清单外的注册包: {unknown}")
        print("       请确认它们该保留还是删除，更新 trim.py 里的清单后重跑。")
        return 1

    orig = src
    # 1) 删 DROP 包的注册调用行
    for m in list(call_re.finditer(src)):
        if m.group(1) in DROP:
            line = m.group(0) + "\n"
            assert src.count(line) == 1, line
            src = src.replace(line, "")
    # 2) 删 DROP 包的 import 行
    for pkg in sorted(DROP):
        line = f'\t"github.com/sagernet/sing-box/protocol/{pkg}"\n'
        if line in src:
            src = src.replace(line, "")

    if src == orig:
        print("[OK] registry.go 无需改动（可能已经裁剪过）")
    else:
        reg.write_text(src, encoding="utf-8", newline="\n")
        print(f"[OK] registry.go 已裁剪: {len(orig)} -> {len(src)} 字节")
    kept = sorted({m for m in call_re.findall(src)
                   if m in KEEP or m in KEEP_OTHER})
    print("保留的注册包:", ", ".join(kept))
    return 0


if __name__ == "__main__":
    sys.exit(main())
