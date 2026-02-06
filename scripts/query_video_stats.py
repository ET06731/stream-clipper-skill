#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询Bilibili视频数据
支持查询上传的视频列表和统计数据
"""

import json
import requests
from pathlib import Path


def get_user_videos(cookies_file: str):
    """获取用户上传的视频列表"""

    # 读取cookies
    with open(cookies_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    # 获取SESSDATA
    sessdata = None
    for cookie in cookies.get("cookie_info", {}).get("cookies", []):
        if cookie.get("name") == "SESSDATA":
            sessdata = cookie.get("value")
            break

    if not sessdata:
        print("[ERROR] 未找到SESSDATA，请检查cookies文件")
        return []

    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"SESSDATA={sessdata}",
        "Referer": "https://space.bilibili.com",
    }

    # 获取用户mid (从DedeUserID)
    mid = None
    for cookie in cookies.get("cookie_info", {}).get("cookies", []):
        if cookie.get("name") == "DedeUserID":
            mid = cookie.get("value")
            break

    if not mid:
        print("[ERROR] 未找到用户ID (DedeUserID)")
        return []

    # 获取视频列表
    url = f"https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=20&tid=0&pn=1&keyword=&order=pubdate"

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("code") == 0:
            videos = data.get("data", {}).get("list", {}).get("vlist", [])
            return videos
        else:
            print(f"[ERROR] 获取视频列表失败: {data.get('message')}")
            return []
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        return []


def display_video_stats(videos):
    """显示视频统计信息"""

    if not videos:
        print("\n[WARN] 未找到视频数据")
        return

    print("\n" + "=" * 80)
    print("[STATS] Bilibili 视频数据统计")
    print("=" * 80)

    for i, video in enumerate(videos[:10], 1):  # 显示最近10个视频
        title = video.get("title", "未知标题")
        bvid = video.get("bvid", "")
        play = video.get("play", 0)
        like = video.get("like", 0)
        comment = video.get("comment", 0)
        danmaku = video.get("video_review", 0)
        created = video.get("created", "")

        print(f"\n[{i}] {title}")
        print(f"    BV号: {bvid}")
        print(f"    播放量: {play if play != '--' else 0}")
        print(f"    点赞: {like}")
        print(f"    评论: {comment}")
        print(f"    弹幕: {danmaku}")
        print(f"    发布时间: {created}")

    print("\n" + "=" * 80)
    print(f"[OK] 共查询到 {len(videos)} 个视频")
    print("=" * 80)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="查询Bilibili视频数据")
    parser.add_argument(
        "--cookie", "-c", default="cookies.json", help="cookies文件路径"
    )

    args = parser.parse_args()

    # 查询视频
    videos = get_user_videos(args.cookie)
    display_video_stats(videos)


if __name__ == "__main__":
    main()
