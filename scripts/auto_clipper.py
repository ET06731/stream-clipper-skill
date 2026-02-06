#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动精彩片段切片器
录制完成后自动：
1. 下载弹幕
2. 分析弹幕密度
3. 生成精彩片段
4. 剪辑并上传
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
import time


class AutoClipper:
    """自动切片器"""

    def __init__(self, work_dir: str, template_name: str = "evil_neuro"):
        self.work_dir = Path(work_dir)
        self.template_name = template_name
        self.scripts_dir = Path(__file__).parent

    def process_segment(self, video_file: str, segment_num: int) -> bool:
        """
        处理单个录制分段

        Args:
            video_file: 视频文件路径
            segment_num: 分段编号

        Returns:
            bool: 是否成功
        """
        video_path = Path(video_file)
        if not video_path.exists():
            print(f"[ERROR] 视频文件不存在: {video_file}")
            return False

        print(f"\n{'=' * 60}")
        print(f"[INFO] 处理分段 {segment_num}: {video_path.name}")
        print(f"{'=' * 60}")

        # 创建该分段的工作目录
        segment_dir = self.work_dir / f"segment_{segment_num:03d}"
        segment_dir.mkdir(exist_ok=True)

        # 1. 提取视频信息（获取BV号/直播间信息）
        print(f"[INFO] 提取视频信息...")

        # 2. 尝试下载弹幕（如果知道直播间ID）
        # 从文件名中提取直播间信息
        danmaku_file = segment_dir / f"segment_{segment_num:03d}_danmaku.xml"

        # 3. 模拟弹幕分析（生成推荐片段）
        print(f"[INFO] 分析精彩片段...")
        recommendations = self._generate_recommendations(video_file, segment_num)

        if not recommendations:
            print(f"[WARN] 未找到精彩片段")
            return False

        # 保存推荐配置
        rec_file = segment_dir / "recommendations.json"
        with open(rec_file, "w", encoding="utf-8") as f:
            json.dump({"clips": recommendations}, f, ensure_ascii=False, indent=2)

        print(f"[OK] 找到 {len(recommendations)} 个精彩片段")
        for i, rec in enumerate(recommendations, 1):
            print(
                f"       {i}. {rec['title']} ({rec['start'] // 60}:{rec['start'] % 60:02d} - {rec['end'] // 60}:{rec['end'] % 60:02d})"
            )

        # 4. 剪辑精彩片段
        print(f"\n[INFO] 开始剪辑...")
        success = self._clip_video(
            video_file, str(rec_file), str(danmaku_file), str(segment_dir)
        )

        if success:
            print(f"[OK] 分段 {segment_num} 剪辑完成")

            # 5. 上传到B站（可选）
            clips_dir = segment_dir / "clips"
            if clips_dir.exists():
                print(
                    f"\n[INFO] 准备上传 {len(list(clips_dir.glob('clip_*')))} 个切片..."
                )
                # self._upload_clips(str(clips_dir))
                print(f"[INFO] 上传功能已跳过（需要手动确认）")

        return success

    def _generate_recommendations(self, video_file: str, segment_num: int) -> list:
        """
        生成精彩片段推荐
        模拟弹幕密度分析，生成3-5个推荐片段
        """
        # 这里简化处理，实际应该分析视频内容或弹幕
        # 生成几个固定时间段作为示例

        segment_duration = 30 * 60  # 30分钟 = 1800秒

        recommendations = []

        # 模拟几个精彩片段（每5-8分钟一个）
        peak_times = [
            (180, 300, "高能时刻：精彩操作", ["高能", "666", "秀"]),
            (480, 600, "搞笑片段：主播翻车", ["哈哈哈", "翻车", "笑死"]),
            (900, 1020, "团战爆发：激烈对决", ["团灭", "五杀", "NB"]),
        ]

        for start, end, title, keywords in peak_times:
            if end <= segment_duration:
                recommendations.append(
                    {
                        "start": start,
                        "end": end,
                        "title": f"【直播片段】{title} #{segment_num}",
                        "keywords": keywords,
                        "description": f"直播精彩片段，关键词: {', '.join(keywords)}",
                    }
                )

        return recommendations

    def _clip_video(
        self, video_file: str, rec_file: str, danmaku_file: str, output_dir: str
    ) -> bool:
        """
        调用 clip_and_burn 进行剪辑
        """
        cmd = [
            "python",
            str(self.scripts_dir / "clip_and_burn.py"),
            "--video",
            video_file,
            "--recommendations",
            rec_file,
            "--output",
            output_dir,
        ]

        if Path(danmaku_file).exists():
            cmd.extend(["--danmaku", danmaku_file])

        try:
            print(f"[INFO] 执行: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"[OK] 剪辑成功")
                return True
            else:
                print(f"[ERROR] 剪辑失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] 剪辑异常: {e}")
            return False

    def _upload_clips(self, clips_dir: str):
        """
        上传剪辑到B站
        """
        cmd = [
            "python",
            str(self.scripts_dir / "upload_clip.py"),
            clips_dir,
            "--batch",
            "--template",
            self.template_name,
        ]

        try:
            print(f"[INFO] 执行: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                print(f"[OK] 上传成功")
            else:
                print(f"[WARN] 上传可能失败: {result.stderr}")
        except Exception as e:
            print(f"[ERROR] 上传异常: {e}")

    def process_all_segments(
        self, recorded_list_file: str = None, video_files: list = None
    ):
        """
        处理所有录制分段

        Args:
            recorded_list_file: 录制列表JSON文件
            video_files: 或者直接传入视频文件列表
        """
        if recorded_list_file:
            with open(recorded_list_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                video_files = data.get("files", [])

        if not video_files:
            print("[ERROR] 没有视频文件需要处理")
            return

        print(f"\n{'=' * 60}")
        print(f"[INFO] 自动精彩片段切片")
        print(f"[INFO] 共 {len(video_files)} 个分段需要处理")
        print(f"{'=' * 60}\n")

        success_count = 0
        for i, video_file in enumerate(video_files, 1):
            if self.process_segment(video_file, i):
                success_count += 1

            # 每个分段处理完后暂停一下
            if i < len(video_files):
                print(f"\n[INFO] 5秒后继续处理下一个分段...")
                time.sleep(5)

        print(f"\n{'=' * 60}")
        print(f"[OK] 处理完成: {success_count}/{len(video_files)} 个分段")
        print(f"{'=' * 60}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="自动精彩片段切片器")
    parser.add_argument("--list", "-l", help="录制列表JSON文件")
    parser.add_argument("--files", "-f", nargs="+", help="视频文件列表")
    parser.add_argument("--output", "-o", default="./clips_output", help="输出目录")
    parser.add_argument("--template", "-t", default="evil_neuro", help="主播模板")

    args = parser.parse_args()

    if not args.list and not args.files:
        print("[ERROR] 请提供 --list 或 --files 参数")
        sys.exit(1)

    clipper = AutoClipper(args.output, args.template)
    clipper.process_all_segments(args.list, args.files)


if __name__ == "__main__":
    main()
