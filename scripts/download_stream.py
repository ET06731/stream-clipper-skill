#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载直播回放、弹幕和字幕
支持 Bilibili 和 YouTube 平台
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

try:
    import yt_dlp
except ImportError:
    print("[ERROR] 错误: yt-dlp 未安装")
    print("请运行: pip install yt-dlp")
    sys.exit(1)


class StreamDownloader:
    """直播下载器"""

    def __init__(self, output_dir: str = "./downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def detect_platform(self, url: str) -> str:
        """检测平台类型"""
        if "bilibili.com" in url or "b23.tv" in url:
            return "bilibili"
        elif "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        else:
            return "unknown"

    def download_bilibili_danmaku(
        self, video_id: str, output_path: str
    ) -> Optional[str]:
        """
        下载 B站弹幕
        使用 bilibili API 获取弹幕
        """
        try:
            import requests

            # B站弹幕 API
            danmaku_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={video_id}"

            # 需要先获取 cid
            info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
            resp = requests.get(
                info_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0:
                    cid = data["data"]["cid"]
                    danmaku_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"

                    # 下载弹幕
                    danmaku_resp = requests.get(
                        danmaku_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": f"https://www.bilibili.com/video/{video_id}",
                        },
                    )

                    if danmaku_resp.status_code == 200:
                        danmaku_file = Path(output_path).with_suffix(".danmaku.xml")
                        with open(danmaku_file, "wb") as f:
                            f.write(danmaku_resp.content)
                        print(f"[OK] 弹幕下载完成: {danmaku_file}")
                        return str(danmaku_file)

        except Exception as e:
            print(f"[WARN] 弹幕下载失败: {e}")

        return None

    def download(
        self, url: str, with_danmaku: bool = True, with_subtitle: bool = True
    ) -> Dict:
        """
        下载视频、弹幕和字幕

        Returns:
            {
                'video_path': str,
                'danmaku_path': Optional[str],
                'subtitle_path': Optional[str],
                'title': str,
                'duration': int,
                'platform': str
            }
        """
        platform = self.detect_platform(url)
        print(f"[INFO] 检测到平台: {platform}")

        # 配置 yt-dlp
        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
            "outtmpl": str(self.output_dir / "%(id)s.%(ext)s"),
            "writesubtitles": with_subtitle,
            "writeautomaticsub": with_subtitle,
            "subtitleslangs": ["zh", "zh-CN", "en"],  # 优先中文
            "subtitlesformat": "srt",
            "writethumbnail": False,
            "quiet": False,
            "no_warnings": False,
            "ffmpeg_location": "D:\\Project\\ffmpeg.exe",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\n[INFO] 获取视频信息...")
                info = ydl.extract_info(url, download=False)

                title = info.get("title", "Unknown")
                duration = info.get("duration", 0)
                video_id = info.get("id", "unknown")

                print(f"   标题: {title}")
                print(f"   时长: {duration // 60}分{duration % 60}秒")
                print(f"   ID: {video_id}")

                # 下载视频
                print(f"\n[INFO] 开始下载视频...")
                ydl.download([url])

                video_path = self.output_dir / f"{video_id}.mp4"

                # 查找字幕文件
                subtitle_path = None
                if with_subtitle:
                    for lang in ["zh", "zh-CN", "en"]:
                        sub_file = self.output_dir / f"{video_id}.{lang}.srt"
                        if sub_file.exists():
                            subtitle_path = str(sub_file)
                            print(f"[OK] 字幕文件: {sub_file.name}")
                            break

                # 下载弹幕 (B站)
                danmaku_path = None
                if with_danmaku and platform == "bilibili":
                    print(f"\n[INFO] 下载弹幕...")
                    danmaku_path = self.download_bilibili_danmaku(
                        video_id, str(video_path)
                    )

                result = {
                    "video_path": str(video_path),
                    "danmaku_path": danmaku_path,
                    "subtitle_path": subtitle_path,
                    "title": title,
                    "duration": duration,
                    "platform": platform,
                    "video_id": video_id,
                }

                # 保存元数据
                metadata_file = self.output_dir / f"{video_id}.json"
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                print(f"\n[OK] 下载完成!")
                print(f"   视频: {video_path.name}")
                if danmaku_path:
                    print(f"   弹幕: {Path(danmaku_path).name}")
                if subtitle_path:
                    print(f"   字幕: {Path(subtitle_path).name}")

                return result

        except Exception as e:
            print(f"[ERROR] 下载失败: {e}")
            raise


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="下载直播回放、弹幕和字幕")
    parser.add_argument("url", help="视频 URL (B站/YouTube)")
    parser.add_argument("--output", "-o", default="./downloads", help="输出目录")
    parser.add_argument("--no-danmaku", action="store_true", help="不下载弹幕")
    parser.add_argument("--no-subtitle", action="store_true", help="不下载字幕")

    args = parser.parse_args()

    downloader = StreamDownloader(args.output)
    result = downloader.download(
        url=args.url,
        with_danmaku=not args.no_danmaku,
        with_subtitle=not args.no_subtitle,
    )

    print(f"\n元数据已保存: {result['video_id']}.json")


if __name__ == "__main__":
    main()
