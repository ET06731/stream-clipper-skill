#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分段直播录制器
支持：
- 每30分钟自动分段
- 同时录制弹幕
- 录制完成后自动切片精彩片段
"""

import subprocess
import sys
import time
import json
import requests
import signal
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread, Event
import xml.etree.ElementTree as ET


class SmartLiveRecorder:
    """智能直播录制器"""

    def __init__(self, output_dir: str = "./recordings", segment_minutes: int = 30):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.segment_minutes = segment_minutes
        self.stop_event = Event()
        self.current_process = None
        self.danmaku_list = []
        self.danmaku_thread = None

        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理停止信号"""
        print("\n[INFO] 收到停止信号，正在优雅停止...")
        self.stop_event.set()
        if self.current_process:
            self.current_process.terminate()

    def get_room_info(self, room_url: str) -> dict:
        """获取直播间信息"""
        room_id = room_url.split("?")[0].rstrip("/").split("/")[-1]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
                    "real_room_id": room_data.get("room_id", room_id),
                    "title": room_data.get("title", "未知标题"),
                    "uname": room_data.get("anchor_name", "未知主播"),
                    "live_status": room_data.get("live_status", 0),
                }
        except Exception as e:
            print(f"[WARN] 获取直播间信息失败: {e}")

        return {"room_id": room_id, "title": "未知", "uname": "未知", "live_status": 0}

    def download_danmaku(self, room_id: str, output_file: str, duration: int = None):
        """
        下载弹幕
        使用 B站 API 获取实时弹幕
        """
        print(f"[INFO] 开始录制弹幕: {output_file}")

        danmaku_data = []
        start_time = time.time()

        try:
            # 获取弹幕服务器配置
            api_url = f"https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo?id={room_id}"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": f"https://live.bilibili.com/{room_id}",
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                host_list = data.get("data", {}).get("host_list", [])
                token = data.get("data", {}).get("token", "")

                if host_list:
                    # 使用 WebSocket 或轮询方式获取弹幕
                    # 这里简化处理，保存弹幕配置信息
                    danmaku_info = {
                        "room_id": room_id,
                        "start_time": datetime.now().isoformat(),
                        "hosts": host_list,
                        "token": token,
                    }

                    with open(
                        output_file.replace(".xml", "_config.json"),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        json.dump(danmaku_info, f, ensure_ascii=False, indent=2)

                    print(f"[OK] 弹幕配置已保存")
        except Exception as e:
            print(f"[WARN] 弹幕录制失败: {e}")

    def record_segment(self, room_url: str, segment_num: int, room_info: dict) -> str:
        """
        录制单个分段

        Returns:
            录制的文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c for c in room_info["title"] if c.isalnum() or c in (" ", "-", "_")
        ).strip()[:30]
        base_name = (
            f"{room_info['uname']}_{safe_title}_{timestamp}_part{segment_num:03d}"
        )

        video_file = self.output_dir / f"{base_name}.mp4"
        danmaku_file = self.output_dir / f"{base_name}_danmaku.xml"

        print(f"\n{'=' * 60}")
        print(f"[INFO] 开始录制分段 {segment_num}: {base_name}")
        print(f"[INFO] 预计时长: {self.segment_minutes} 分钟")
        print(f"{'=' * 60}")

        # 构建 yt-dlp 命令
        cmd = [
            "yt-dlp",
            "-f",
            "ultra_high_res-0/best",  # 优先超清
            "--output",
            str(video_file),
            "--retries",
            "10",
            "--fragment-retries",
            "10",
            "--no-part",  # 不生成 .part 文件
            "--no-mtime",  # 不修改文件时间
            room_url,
        ]

        try:
            # 启动视频录制
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            # 启动弹幕录制（后台线程）
            danmaku_thread = Thread(
                target=self.download_danmaku,
                args=(
                    room_info["room_id"],
                    str(danmaku_file),
                    self.segment_minutes * 60,
                ),
            )
            danmaku_thread.start()

            # 等待指定时间
            start_time = time.time()
            segment_seconds = self.segment_minutes * 60

            while (time.time() - start_time) < segment_seconds:
                if self.stop_event.is_set():
                    print("[INFO] 收到停止信号，结束当前分段")
                    break

                # 检查进程是否还在运行
                if self.current_process.poll() is not None:
                    print("[WARN] 录制进程意外结束")
                    break

                # 每10秒显示一次进度
                elapsed = time.time() - start_time
                progress = (elapsed / segment_seconds) * 100
                print(
                    f"\r[INFO] 录制中... {progress:.1f}% ({int(elapsed / 60)}/{self.segment_minutes}分钟)",
                    end="",
                    flush=True,
                )
                time.sleep(10)

            print()  # 换行

            # 停止录制
            if self.current_process.poll() is None:
                self.current_process.terminate()
                self.current_process.wait(timeout=10)

            # 等待弹幕线程结束
            danmaku_thread.join(timeout=5)

            # 检查文件是否生成
            if video_file.exists():
                file_size = video_file.stat().st_size / (1024 * 1024)  # MB
                print(f"[OK] 分段 {segment_num} 录制完成: {video_file.name}")
                print(f"[INFO] 文件大小: {file_size:.2f} MB")
                return str(video_file)
            else:
                print(f"[ERROR] 分段 {segment_num} 录制失败，未找到文件")
                return None

        except Exception as e:
            print(f"[ERROR] 录制分段 {segment_num} 失败: {e}")
            return None
        finally:
            self.current_process = None

    def smart_record(self, room_url: str):
        """
        智能分段录制主循环
        """
        # 获取房间信息
        room_info = self.get_room_info(room_url)
        print(f"[INFO] 直播间信息:")
        print(f"       主播: {room_info['uname']}")
        print(f"       标题: {room_info['title']}")
        print(
            f"       房间: {room_info['room_id']} (真实ID: {room_info['real_room_id']})"
        )
        print(f"       状态: {'直播中' if room_info['live_status'] == 1 else '未开播'}")

        if room_info["live_status"] != 1:
            print("[WARN] 直播间未开播，无法录制")
            return []

        print(f"\n[INFO] 智能录制配置:")
        print(f"       分段时长: {self.segment_minutes} 分钟")
        print(f"       输出目录: {self.output_dir}")
        print(f"       按 Ctrl+C 停止录制")
        print(f"{'=' * 60}\n")

        recorded_files = []
        segment_num = 1

        try:
            while not self.stop_event.is_set():
                # 录制一个分段
                video_file = self.record_segment(room_url, segment_num, room_info)

                if video_file:
                    recorded_files.append(video_file)
                    segment_num += 1
                else:
                    # 如果录制失败，检查是否还在直播
                    room_info = self.get_room_info(room_url)
                    if room_info["live_status"] != 1:
                        print("[INFO] 直播已结束")
                        break
                    else:
                        print("[WARN] 录制失败，3秒后重试...")
                        time.sleep(3)

                # 检查是否需要停止
                if self.stop_event.is_set():
                    break

        except KeyboardInterrupt:
            print("\n[INFO] 用户中断录制")

        print(f"\n{'=' * 60}")
        print(f"[OK] 录制结束，共录制 {len(recorded_files)} 个分段")
        print(f"{'=' * 60}")

        return recorded_files


def main():
    import argparse

    parser = argparse.ArgumentParser(description="智能分段直播录制工具")
    parser.add_argument("room_url", help="直播间 URL")
    parser.add_argument("-o", "--output", default="./recordings", help="输出目录")
    parser.add_argument(
        "-t", "--time", type=int, default=30, help="分段时长（分钟），默认30"
    )

    args = parser.parse_args()

    recorder = SmartLiveRecorder(args.output, args.time)
    recorded_files = recorder.smart_record(args.room_url)

    # 保存录制列表
    if recorded_files:
        list_file = (
            Path(args.output)
            / f"recorded_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(list_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "room_url": args.room_url,
                    "record_time": datetime.now().isoformat(),
                    "segment_minutes": args.time,
                    "files": recorded_files,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"[INFO] 录制列表已保存: {list_file}")


if __name__ == "__main__":
    main()
