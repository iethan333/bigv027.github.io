#!/usr/bin/env python3
"""把 site/ 同步到 GitHub Pages 仓库根目录，并清掉上一版残留页面。

用法：
    python3 deploy.py /path/to/iethan333.github.io   同步到另一个仓库副本
    python3 deploy.py .                              就地同步（工程本身就在仓库里）

只做文件搬运，不执行 git commit / push。
"""
import json
import shutil
import sys
from pathlib import Path

from siteconf import ASSETS_DIR, OUT_DIR, PAGES_DIR, POSTS_DIR, ROOT

MANIFEST = ".build-manifest.json"
SOURCE_FILES = ["build.py", "content.py", "render.py", "templates.py",
                "feeds.py", "siteconf.py", "deploy.py", ".gitignore"]
SOURCE_DIRS = {"_posts": POSTS_DIR, "_pages": PAGES_DIR, "assets": ASSETS_DIR}


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法：python3 deploy.py /path/to/repo")
    target = Path(sys.argv[1]).expanduser().resolve()
    if not (target / ".git").is_dir():
        raise SystemExit(f"✗ {target} 不是一个 git 仓库")

    if not OUT_DIR.is_dir():
        raise SystemExit("✗ 还没构建，先跑 python3 build.py")

    # 上一版生成过、这一版不再需要的文件
    man = target / MANIFEST
    old = set()
    if man.is_file():
        try:
            old = set(json.loads(man.read_text(encoding="utf-8")).get("files", []))
        except json.JSONDecodeError:
            old = set()

    new = set()
    for src in OUT_DIR.rglob("*"):
        if src.is_file():
            rel = src.relative_to(OUT_DIR)
            new.add(str(rel))
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    for rel in sorted(old - new):
        p = target / rel
        if p.is_file():
            p.unlink()
            print(f"  - 删除残留 {rel}")

    # 工程本身就在仓库里时（GitHub Actions 就是这样），源文件不用再自我复制
    inplace = target == ROOT

    for name in SOURCE_FILES:
        src = ROOT / name
        if not inplace and src.is_file():
            shutil.copy2(src, target / name)

    for name, src_dir in SOURCE_DIRS.items():
        if inplace or not src_dir.is_dir():
            continue
        dst_dir = target / name
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns(".obsidian"))

    man.write_text(json.dumps({"files": sorted(new)}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"✓ {len(new)} 个文件已同步到 {target}")
    print("  下一步：git status 看改动，确认后 commit / push")


if __name__ == "__main__":
    main()
