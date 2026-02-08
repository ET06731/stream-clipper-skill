#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量上传新的切片（排除已上传的重复内容）
"""

import subprocess
import sys
from pathlib import Path

# 新的切片目录
clips_dir = Path("D:/Project/bili-clipper/clips_extended")

# 需要跳过的重复切片（clip_003, clip_005 与之前的重复，clip_002标题相似但其实是新的）
# clip_003: 蘑菇名场面（重复）
# clip_005: 丸辣翻车（重复）
# 其他都是新的
skip_clips = ["clip_003", "clip_005"]

# 获取所有需要上传的切片
clip_dirs = sorted(
    [
        d
        for d in clips_dir.iterdir()
        if d.is_dir() and d.name.startswith("clip_") and d.name not in skip_clips
    ]
)

print(f"找到 {len(clip_dirs)} 个新切片需要上传")
print(f"跳过的重复切片: {skip_clips}")
print("=" * 60)

success_count = 0
fail_count = 0

for i, clip_dir in enumerate(clip_dirs, 1):
    clip_name = clip_dir.name
    info_file = clip_dir / "info.json"

    print(f"\n[{i}/{len(clip_dirs)}] 上传: {clip_name}")

    if not info_file.exists():
        print(f"   [WARN] 跳过: 无 info.json")
        continue

    # 执行上传
    cmd = [
        "python",
        "scripts/upload_clip.py",
        str(info_file),
        "--template",
        "evil_neuro",
        "--platform",
        "bilibili",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd="C:/Users/su/.agents/skills/stream-clipper",
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print(f"   [OK] 上传成功")
            success_count += 1
        else:
            print(f"   [FAIL] 上传失败")
            print(f"   {result.stderr[:200]}")
            fail_count += 1

    except Exception as e:
        print(f"   [ERROR] {e}")
        fail_count += 1

print("\n" + "=" * 60)
print(f"上传完成: {success_count} 成功, {fail_count} 失败")
print("=" * 60)
