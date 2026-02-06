#!/usr/bin/env python3
"""
视频剪辑和烧录模块
根据智能切片的推荐，剪辑视频并烧录弹幕/字幕
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ClipInfo:
    """切片信息"""

    start: float
    end: float
    title: str
    keywords: List[str]
    output_name: str


class ClipAndBurn:
    """剪辑和烧录处理器"""

    def __init__(self, ffmpeg_path: str = None):
        """
        Args:
            ffmpeg_path: FFmpeg 可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        """查找 FFmpeg 可执行文件"""
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            # 尝试常见路径
            possible_paths = [
                "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/usr/bin/ffmpeg",
                "D:/ffmpeg.exe",
                "C:/ffmpeg/bin/ffmpeg.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
        return ffmpeg

    def parse_recommendations(self, recommendations_path: str) -> List[ClipInfo]:
        """解析切片推荐 JSON"""
        with open(recommendations_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        clips = []
        for i, clip_data in enumerate(data.get("clips", []), 1):
            clip = ClipInfo(
                start=clip_data["start"],
                end=clip_data["end"],
                title=clip_data["title"],
                keywords=clip_data.get("keywords", []),
                output_name=f"clip_{i:03d}",
            )
            clips.append(clip)

        return clips

    def clip_video(self, video_path: str, clip: ClipInfo, output_dir: str) -> str:
        """
        剪辑视频片段

        Args:
            video_path: 原始视频路径
            clip: 切片信息
            output_dir: 输出目录

        Returns:
            输出视频路径
        """
        output_path = Path(output_dir) / f"{clip.output_name}.mp4"
        duration = clip.end - clip.start

        print(f"\n✂️  剪辑: {clip.title}")
        print(
            f"   时间: {self._seconds_to_time(clip.start)} - {self._seconds_to_time(clip.end)}"
        )
        print(f"   时长: {int(duration)}秒")

        cmd = [
            self.ffmpeg_path,
            "-ss",
            str(clip.start),
            "-i",
            video_path,
            "-t",
            str(duration),
            "-c",
            "copy",
            "-y",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"   ✅ 完成: {output_path.name}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 失败: {e.stderr}")
            raise

    def extract_danmaku_segment(
        self, danmaku_path: str, start: float, end: float, output_path: str
    ):
        """
        提取指定时间段的弹幕
        将 XML 转换为 ASS 格式
        """
        import xml.etree.ElementTree as ET

        # 解析原始弹幕
        tree = ET.parse(danmaku_path)
        root = tree.getroot()

        # 过滤时间范围内的弹幕
        filtered_danmaku = []
        for d in root.findall("d"):
            p = d.get("p", "").split(",")
            if len(p) >= 8:
                time_sec = float(p[0])
                if start <= time_sec <= end:
                    # 调整时间戳
                    p[0] = str(time_sec - start)
                    d.set("p", ",".join(p))
                    filtered_danmaku.append(d)

        # 创建新的 XML
        new_root = ET.Element("i")
        for d in filtered_danmaku:
            new_root.append(d)

        # 保存过滤后的弹幕
        xml_output = Path(output_path).with_suffix(".xml")
        ET.ElementTree(new_root).write(
            xml_output, encoding="utf-8", xml_declaration=True
        )

        # 转换为 ASS (这里简化处理，实际需要更复杂的转换)
        ass_output = Path(output_path).with_suffix(".ass")
        self._xml_to_ass(str(xml_output), str(ass_output))

        return str(ass_output)

    def _xml_to_ass(self, xml_path: str, ass_path: str):
        """
        将弹幕 XML 转换为 ASS 格式
        简化版本，实际使用需要更完整的样式配置
        """
        import xml.etree.ElementTree as ET

        # ASS 头部
        ass_header = """[Script Info]
Title: Danmaku
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H7F404040,0,0,0,0,100,100,0,0,1,2,0,2,20,20,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        tree = ET.parse(xml_path)
        root = tree.getroot()

        events = []
        for d in root.findall("d"):
            p = d.get("p", "").split(",")
            if len(p) >= 8 and d.text:
                time_sec = float(p[0])
                # 简单的滚动弹幕
                start_time = self._seconds_to_ass_time(time_sec)
                end_time = self._seconds_to_ass_time(time_sec + 8)  # 显示8秒

                # 转义特殊字符
                text = d.text.replace(",", "，").replace("\n", " ")

                event = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}"
                events.append(event)

        # 写入文件
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header)
            f.write("\n".join(events))

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """转换为 ASS 时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def _seconds_to_time(self, seconds: float) -> str:
        """转换为可读时间"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def burn_subtitles(self, video_path: str, subtitle_path: str, output_path: str):
        """
        烧录字幕到视频

        Args:
            video_path: 视频路径
            subtitle_path: 字幕文件路径 (ASS/SRT)
            output_path: 输出路径
        """
        print(f"   🔥 烧录字幕...")

        # 处理路径空格问题
        with tempfile.TemporaryDirectory() as tmpdir:
            # 复制文件到临时目录
            tmp_video = Path(tmpdir) / "video.mp4"
            tmp_sub = Path(tmpdir) / "subtitle.ass"
            tmp_output = Path(tmpdir) / "output.mp4"

            shutil.copy(video_path, tmp_video)
            shutil.copy(subtitle_path, tmp_sub)

            # 转换字幕编码为 UTF-8
            self._convert_to_utf8(str(tmp_sub))

            cmd = [
                self.ffmpeg_path,
                "-i",
                str(tmp_video),
                "-vf",
                f"subtitles={tmp_sub.name}:force_style='FontSize=24,MarginV=30'",
                "-c:a",
                "copy",
                "-y",
                str(tmp_output),
            ]

            try:
                subprocess.run(cmd, cwd=tmpdir, capture_output=True, check=True)
                shutil.copy(tmp_output, output_path)
                print(f"   ✅ 字幕烧录完成")
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  字幕烧录失败，使用原视频: {e}")
                shutil.copy(video_path, output_path)

    def _convert_to_utf8(self, file_path: str):
        """转换文件为 UTF-8 编码"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ["gbk", "gb2312", "big5"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return
                except:
                    continue

    def process_clip(
        self,
        video_path: str,
        danmaku_path: str,
        subtitle_path: str,
        clip: ClipInfo,
        output_dir: str,
        burn_danmaku: bool = True,
        burn_subtitle: bool = True,
    ) -> Dict:
        """
        处理单个切片（剪辑+烧录）

        Returns:
            {
                'clip': ClipInfo,
                'video_path': str,
                'danmaku_path': Optional[str],
                'subtitle_path': Optional[str],
                'final_path': str
            }
        """
        # 创建切片输出目录
        clip_dir = Path(output_dir) / clip.output_name
        clip_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "clip": clip,
            "video_path": None,
            "danmaku_path": None,
            "subtitle_path": None,
            "final_path": None,
        }

        # 1. 剪辑视频
        clipped_video = self.clip_video(video_path, clip, str(clip_dir))
        result["video_path"] = clipped_video

        final_video = clipped_video

        # 2. 处理弹幕
        if burn_danmaku and danmaku_path and Path(danmaku_path).exists():
            try:
                danmaku_ass = self.extract_danmaku_segment(
                    danmaku_path,
                    clip.start,
                    clip.end,
                    str(clip_dir / f"{clip.output_name}_danmaku"),
                )
                result["danmaku_path"] = danmaku_ass

                # 烧录弹幕
                burned_video = str(clip_dir / f"{clip.output_name}_with_danmaku.mp4")
                self.burn_subtitles(clipped_video, danmaku_ass, burned_video)
                final_video = burned_video
            except Exception as e:
                print(f"   ⚠️  弹幕处理失败: {e}")

        # 3. 处理字幕
        if burn_subtitle and subtitle_path and Path(subtitle_path).exists():
            # TODO: 提取字幕片段
            pass

        result["final_path"] = final_video

        # 保存切片信息
        info_path = clip_dir / "info.json"
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "title": clip.title,
                    "keywords": clip.keywords,
                    "start": clip.start,
                    "end": clip.end,
                    "files": {
                        "video": str(Path(result["video_path"]).name),
                        "danmaku": str(Path(result["danmaku_path"]).name)
                        if result["danmaku_path"]
                        else None,
                        "final": str(Path(final_video).name),
                    },
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        return result

    def process_all(
        self,
        video_path: str,
        recommendations_path: str,
        danmaku_path: str = None,
        subtitle_path: str = None,
        output_dir: str = "./clips",
        burn_danmaku: bool = True,
        burn_subtitle: bool = True,
    ) -> List[Dict]:
        """
        处理所有推荐切片

        Returns:
            List[Dict]: 每个切片的处理结果
        """
        print("=" * 60)
        print("🎬 开始处理切片")
        print("=" * 60)

        # 加载切片推荐
        clips = self.parse_recommendations(recommendations_path)
        print(f"共 {len(clips)} 个切片")

        results = []
        for i, clip in enumerate(clips, 1):
            print(f"\n[{i}/{len(clips)}] 处理切片...")
            try:
                result = self.process_clip(
                    video_path,
                    danmaku_path,
                    subtitle_path,
                    clip,
                    output_dir,
                    burn_danmaku,
                    burn_subtitle,
                )
                results.append(result)
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")

        print("\n" + "=" * 60)
        print(f"✅ 完成 {len(results)}/{len(clips)} 个切片")
        print(f"📁 输出目录: {output_dir}")
        print("=" * 60)

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="剪辑视频并烧录弹幕")
    parser.add_argument("--video", "-v", required=True, help="视频文件路径")
    parser.add_argument("--recommendations", "-r", required=True, help="切片推荐 JSON")
    parser.add_argument("--danmaku", "-d", help="弹幕 XML 文件")
    parser.add_argument("--subtitle", "-s", help="字幕 SRT 文件")
    parser.add_argument("--output", "-o", default="./clips", help="输出目录")
    parser.add_argument("--no-danmaku", action="store_true", help="不烧录弹幕")
    parser.add_argument("--no-subtitle", action="store_true", help="不烧录字幕")

    args = parser.parse_args()

    processor = ClipAndBurn()
    results = processor.process_all(
        video_path=args.video,
        recommendations_path=args.recommendations,
        danmaku_path=args.danmaku,
        subtitle_path=args.subtitle,
        output_dir=args.output,
        burn_danmaku=not args.no_danmaku,
        burn_subtitle=not args.no_subtitle,
    )


if __name__ == "__main__":
    main()
