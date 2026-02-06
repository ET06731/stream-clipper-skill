#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕提取模块 - Stream Clipper 核心组件
使用 Whisper 从视频提取字幕，支持完整提取或仅提取关键片段
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List
import json


class SubtitleExtractor:
    """字幕提取器"""

    def __init__(self, model: str = "small"):
        """
        初始化提取器

        Args:
            model: Whisper模型大小 (tiny/base/small/medium/large)
        """
        self.model = model
        self.check_whisper()

    def check_whisper(self) -> bool:
        """检查Whisper是否已安装"""
        try:
            import whisper

            return True
        except ImportError:
            print("[ERROR] Whisper未安装，请运行: pip install openai-whisper")
            return False

    def extract_full(
        self, video_path: str, output_path: Optional[str] = None, language: str = "en"
    ) -> str:
        """
        提取完整视频字幕

        Args:
            video_path: 视频文件路径
            output_path: 输出字幕文件路径，默认与视频同名
            language: 语言代码 (en/zh/ja等)

        Returns:
            字幕文件路径
        """
        video = Path(video_path)
        if not video.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        if output_path is None:
            output_path = video.with_suffix(".srt")

        print(f"[INFO] 开始提取字幕: {video.name}")
        print(f"[INFO] 使用模型: {self.model}")
        print(f"[INFO] 语言: {language}")
        print(f"[INFO] 这可能需要几分钟到几小时，取决于视频长度...")

        try:
            import whisper

            model = whisper.load_model(self.model)
            result = model.transcribe(video_path, language=language, verbose=False)

            # 保存为SRT格式
            srt_content = self.to_srt(result["segments"])
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

            print(f"[OK] 字幕提取完成: {output_path}")
            print(f"[INFO] 总时长: {result.get('duration', 'unknown')}秒")
            print(f"[INFO] 识别文本长度: {len(result['text'])}字符")

            return str(output_path)

        except Exception as e:
            print(f"[ERROR] 字幕提取失败: {e}")
            raise

    def extract_segments(
        self, video_path: str, segments: List[dict], output_dir: Optional[str] = None
    ) -> List[str]:
        """
        仅提取指定时间段的字幕（用于快速处理高密度片段）

        Args:
            video_path: 视频文件路径
            segments: 时间段列表 [{"start": 300, "end": 400, "label": "片段1"}, ...]
            output_dir: 输出目录

        Returns:
            字幕文件路径列表
        """
        video = Path(video_path)
        if output_dir is None:
            output_dir = video.parent / "subtitle_segments"
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        subtitle_files = []

        for i, seg in enumerate(segments, 1):
            start = seg["start"]
            end = seg["end"]
            label = seg.get("label", f"segment_{i:03d}")

            # 提取音频片段
            audio_file = output_dir / f"{label}_audio.wav"
            self._extract_audio(video_path, start, end, audio_file)

            # 转录音频
            subtitle_file = output_dir / f"{label}.srt"
            self._transcribe_audio(audio_file, subtitle_file)

            subtitle_files.append(str(subtitle_file))

            # 清理临时音频文件
            audio_file.unlink(missing_ok=True)

            print(f"[OK] 片段 {i}/{len(segments)} 完成: {label}")

        return subtitle_files

    def _extract_audio(
        self, video_path: str, start: int, end: int, output_audio: Path
    ) -> None:
        """提取音频片段"""
        duration = end - start
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            video_path,
            "-vn",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_audio),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _transcribe_audio(self, audio_path: Path, output_srt: Path) -> None:
        """转录音频为字幕"""
        import whisper

        model = whisper.load_model(self.model)
        result = model.transcribe(str(audio_path), verbose=False)

        srt_content = self.to_srt(result["segments"])
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write(srt_content)

    def to_srt(self, segments: List[dict]) -> str:
        """将Whisper结果转换为SRT格式"""
        srt_lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_time(seg["start"])
            end = self._format_time(seg["end"])
            text = seg["text"].strip()

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def _format_time(self, seconds: float) -> str:
        """格式化时间为SRT格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def get_segment_text(
        self, subtitle_path: str, start_time: float, end_time: float
    ) -> str:
        """
        获取指定时间段的字幕文本

        Args:
            subtitle_path: 字幕文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）

        Returns:
            该时间段的字幕文本
        """
        segments = self.parse_srt(subtitle_path)

        texts = []
        for seg in segments:
            if seg["end"] >= start_time and seg["start"] <= end_time:
                texts.append(seg["text"])

        return " ".join(texts)

    def parse_srt(self, subtitle_path: str) -> List[dict]:
        """解析SRT文件"""
        segments = []

        with open(subtitle_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 简单的SRT解析
        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                # 第二行是时间码
                time_line = lines[1]
                if "-->" in time_line:
                    start_str, end_str = time_line.split("-->")
                    start = self._parse_time(start_str.strip())
                    end = self._parse_time(end_str.strip())
                    text = " ".join(lines[2:])

                    segments.append({"start": start, "end": end, "text": text})

        return segments

    def _parse_time(self, time_str: str) -> float:
        """解析SRT时间格式为秒"""
        time_str = time_str.replace(",", ".")
        parts = time_str.split(":")
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0.0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="提取视频字幕")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("-o", "--output", help="输出字幕文件路径")
    parser.add_argument(
        "-m",
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper模型大小 (默认: small)",
    )
    parser.add_argument("-l", "--language", default="en", help="语言代码 (默认: en)")
    parser.add_argument(
        "--segments-only", action="store_true", help="仅提取关键片段（需要提供时间段）"
    )
    parser.add_argument("--segments-file", help="时间段JSON文件")

    args = parser.parse_args()

    extractor = SubtitleExtractor(model=args.model)

    if args.segments_only and args.segments_file:
        # 仅提取关键片段
        with open(args.segments_file, "r", encoding="utf-8") as f:
            segments = json.load(f)
        subtitle_files = extractor.extract_segments(args.video, segments)
        print(f"\n[OK] 已生成 {len(subtitle_files)} 个字幕片段")
    else:
        # 提取完整字幕
        subtitle_path = extractor.extract_full(
            args.video, output_path=args.output, language=args.language
        )
        print(f"\n[OK] 完整字幕已保存: {subtitle_path}")


if __name__ == "__main__":
    main()
