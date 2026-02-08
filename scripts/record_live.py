#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播录制模块
使用 biliup 或 streamlink 录制直播间
"""

import subprocess
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime


class LiveRecorder:
    """直播录制器"""

    def __init__(self, output_dir: str = "./recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_room_info(self, room_url: str) -> dict:
        """获取直播间信息"""
        # 提取 room_id
        room_id = room_url.split("?")[0].rstrip("/").split("/")[-1]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://live.bilibili.com",
        }

        try:
            api_url = (
                f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
            )
            response = requests.get(api_url, headers=headers, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                room_data = data.get("data", {})
                return {
                    "room_id": room_id,
                    "title": room_data.get("title", "未知标题"),
                    "uname": room_data.get("anchor_name", "未知主播"),
                    "live_status": room_data.get("live_status", 0),
                    "area_name": room_data.get("area_name", ""),
                }
        except Exception as e:
            print(f"[WARN] 获取直播间信息失败: {e}")

        return {
            "room_id": room_id,
            "title": "未知标题",
            "uname": "未知主播",
            "live_status": 0,
        }

    def get_live_url(self, room_id: str) -> str:
        """获取直播流地址"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://live.bilibili.com",
        }

        try:
            api_url = f"https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?room_id={room_id}&protocol=0,1&format=0,1,2&codec=0,1&qn=10000"
            response = requests.get(api_url, headers=headers, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                streams = data.get("data", {}).get("play_url", {}).get("stream", [])
                if streams:
                    # 获取第一个可用的流
                    stream = streams[0]
                    formats = stream.get("format", [])
                    if formats:
                        # 优先使用 flv
                        for fmt in formats:
                            if fmt.get("format_name") == "flv":
                                codecs = fmt.get("codec", [])
                                if codecs:
                                    return codecs[0].get("url", "")
                        # 如果没有 flv，使用第一个格式
                        codecs = formats[0].get("codec", [])
                        if codecs:
                            return codecs[0].get("url", "")
        except Exception as e:
            print(f"[ERROR] 获取直播流失败: {e}")

        return ""

    def record_with_ffmpeg(
        self, stream_url: str, output_file: str, duration: int = None
    ):
        """使用 FFmpeg 录制直播"""
        if not stream_url:
            print("[ERROR] 直播流地址为空")
            return False

        cmd = [
            "ffmpeg",
            "-i",
            stream_url,
            "-c",
            "copy",  # 直接复制流，不重新编码
            "-bsf:a",
            "aac_adtstoasc",
            "-y",
        ]

        if duration:
            cmd.extend(["-t", str(duration)])

        cmd.append(output_file)

        print(f"[INFO] 开始录制: {output_file}")
        print(f"[INFO] 命令: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            print(f"[OK] 录制已开始，PID: {process.pid}")
            print(f"[INFO] 按 Ctrl+C 停止录制")

            # 等待进程结束
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"[OK] 录制完成: {output_file}")
                return True
            else:
                print(f"[WARN] 录制进程退出，代码: {process.returncode}")
                return True  # 正常结束

        except KeyboardInterrupt:
            print("\n[INFO] 收到停止信号，正在停止录制...")
            process.terminate()
            process.wait(timeout=5)
            print(f"[OK] 录制已停止，文件保存至: {output_file}")
            return True
        except Exception as e:
            print(f"[ERROR] 录制失败: {e}")
            return False

    def record_room(self, room_url: str, duration: int = None, output_name: str = None):
        """
        录制直播间

        Args:
            room_url: 直播间 URL
            duration: 录制时长（秒），None 表示一直录制
            output_name: 输出文件名，None 则自动生成
        """
        # 获取房间信息
        room_info = self.get_room_info(room_url)
        print(f"[INFO] 直播间信息:")
        print(f"       标题: {room_info['title']}")
        print(f"       主播: {room_info['uname']}")
        print(f"       分区: {room_info['area_name']}")
        print(f"       状态: {'直播中' if room_info['live_status'] == 1 else '未开播'}")

        if room_info["live_status"] != 1:
            print("[WARN] 直播间未开播，无法录制")
            return False

        # 获取直播流地址
        stream_url = self.get_live_url(room_info["room_id"])
        if not stream_url:
            print("[ERROR] 无法获取直播流地址")
            return False

        # 生成输出文件名
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(
                c for c in room_info["title"] if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            output_name = f"{room_info['uname']}_{safe_title}_{timestamp}.mp4"

        output_path = self.output_dir / output_name

        # 开始录制
        return self.record_with_ffmpeg(stream_url, str(output_path), duration)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bilibili 直播录制工具")
    parser.add_argument("room_url", help="直播间 URL")
    parser.add_argument("-o", "--output", default="./recordings", help="输出目录")
    parser.add_argument("-n", "--name", help="输出文件名")
    parser.add_argument("-t", "--time", type=int, help="录制时长（秒）")
    parser.add_argument(
        "--daemon", action="store_true", help="后台模式（循环检测开播）"
    )
    parser.add_argument("-i", "--interval", type=int, default=60, help="检测间隔（秒）")

    args = parser.parse_args()

    recorder = LiveRecorder(args.output)

    if args.daemon:
        # 后台模式：循环检测开播并录制
        print(f"[INFO] 后台模式启动，检测间隔: {args.interval}秒")
        print(f"[INFO] 按 Ctrl+C 退出")

        while True:
            try:
                room_info = recorder.get_room_info(args.room_url)

                if room_info["live_status"] == 1:
                    print(f"\n[INFO] 检测到开播，开始录制...")
                    recorder.record_room(args.room_url, args.time, args.name)
                    print(f"\n[INFO] 录制结束，继续检测...")
                else:
                    print(f"\r[INFO] 未开播，等待中...", end="", flush=True)

                time.sleep(args.interval)

            except KeyboardInterrupt:
                print("\n[INFO] 退出后台模式")
                break
    else:
        # 单次录制模式
        success = recorder.record_room(args.room_url, args.time, args.name)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
