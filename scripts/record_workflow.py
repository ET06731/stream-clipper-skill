#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播录制完整工作流
1. 分段录制直播（每30分钟一段）
2. 同时下载弹幕
3. 录制完成后自动切片精彩片段
4. 可选：上传到B站

使用方法：
    python record_workflow.py "https://live.bilibili.com/55"
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


def run_command(cmd, cwd=None):
    """运行命令并打印输出"""
    print(f"\n[CMD] {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"[WARN] {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] 命令执行失败: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python record_workflow.py <直播间URL> [输出目录]")
        print("Example: python record_workflow.py https://live.bilibili.com/55")
        sys.exit(1)

    room_url = sys.argv[1]
    output_dir = (
        sys.argv[2] if len(sys.argv) > 2 else "D:/Project/bili-clipper/recordings"
    )

    scripts_dir = Path(__file__).parent

    print("=" * 60)
    print("🎬 Bilibili 直播录制完整工作流")
    print("=" * 60)
    print(f"📺 直播间: {room_url}")
    print(f"📁 输出目录: {output_dir}")
    print(f"⏱️  分段时长: 30分钟")
    print(f"✂️  自动切片: 启用")
    print(f"💬 弹幕录制: 启用")
    print("=" * 60)

    # Phase 1: 分段录制
    print("\n🎥 Phase 1: 智能分段录制")
    print("-" * 60)

    record_cmd = [
        "python",
        str(scripts_dir / "smart_record.py"),
        room_url,
        "-o",
        output_dir,
        "-t",
        "30",  # 30分钟分段
    ]

    success = run_command(record_cmd)

    if not success:
        print("\n[ERROR] 录制失败，工作流中止")
        sys.exit(1)

    # 查找录制列表文件
    output_path = Path(output_dir)
    list_files = sorted(output_path.glob("recorded_list_*.json"), reverse=True)

    if not list_files:
        print("\n[ERROR] 未找到录制列表文件")
        sys.exit(1)

    latest_list = list_files[0]
    print(f"\n[INFO] 录制列表: {latest_list.name}")

    # 询问是否继续切片
    print("\n" + "=" * 60)
    print("✅ 录制完成！")
    print("=" * 60)
    print("\n是否继续自动切片精彩片段？")
    print("输入 'y' 继续，其他键退出")

    try:
        user_input = input("> ").strip().lower()
    except:
        user_input = "y"  # 默认继续

    if user_input != "y":
        print("\n[INFO] 用户选择退出，录制文件保存在:")
        print(f"       {output_dir}")
        sys.exit(0)

    # Phase 2: 自动切片
    print("\n✂️ Phase 2: 自动精彩片段切片")
    print("-" * 60)

    clipper_cmd = [
        "python",
        str(scripts_dir / "auto_clipper.py"),
        "--list",
        str(latest_list),
        "--output",
        str(output_path / "clips_output"),
        "--template",
        "evil_neuro",
    ]

    run_command(clipper_cmd)

    # 完成
    print("\n" + "=" * 60)
    print("🎉 工作流完成！")
    print("=" * 60)
    print(f"📁 录制文件: {output_dir}")
    print(f"✂️  精彩片段: {output_path / 'clips_output'}")
    print("\n接下来你可以：")
    print("1. 查看精彩片段并手动上传")
    print("2. 使用 upload_clip.py 批量上传")
    print("3. 继续录制其他直播间")
    print("=" * 60)


if __name__ == "__main__":
    main()
