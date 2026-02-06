#!/usr/bin/env python3
"""
上传模块 - 支持 Bilibili 等平台
自动生成语义标题和简介
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# 添加 biliup 路径
sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.*/site-packages"))

# 禁用 biliup 的错误钩子
try:
    import biliup.common

    biliup.common.new_hook = lambda t, v, tb: None
    from biliup.plugins.bili_webup import BiliWeb

    BILIUP_AVAILABLE = True
except ImportError:
    BILIUP_AVAILABLE = False
    print("[WARN] biliup 未安装，上传功能不可用")


@dataclass
class UploadInfo:
    """上传信息"""

    video_path: str
    title: str
    description: str
    tags: List[str]
    tid: int
    streamer_name: str


@dataclass
class StreamData:
    """BiliWeb 需要的数据结构"""

    name: str
    format_title: str = ""
    url: str = ""
    title: str = ""
    dirname: str = ""

    def __getitem__(self, key):
        return getattr(self, key)


class FileInfo:
    """文件信息包装器"""

    def __init__(self, path: str):
        self.video = os.path.abspath(path)


class StreamUploader:
    """直播切片上传器"""

    def __init__(self, template_manager=None, cookie_file: str = "cookies.json"):
        """
        Args:
            template_manager: 主播模板管理器
            cookie_file: Cookie 文件路径
        """
        self.template_manager = template_manager
        self.cookie_file = cookie_file

    def generate_title(self, clip_info: Dict, template: Dict = None) -> str:
        """
        生成上传标题

        策略:
        1. 优先使用 smart_clipper 推荐的标题
        2. 根据主播模板调整
        3. 确保长度合适（不超过80字符）
        """
        # 获取基础标题
        base_title = clip_info.get("title", "")

        if not base_title and clip_info.get("keywords"):
            # 根据关键词生成
            keywords = clip_info["keywords"]
            streamer = template.get("name", "主播") if template else "主播"
            base_title = f"[{streamer}]{keywords[0]} | 精彩片段"

        # 限制长度
        if len(base_title) > 80:
            base_title = base_title[:77] + "..."

        return base_title

    def generate_description(self, clip_info: Dict, template: Dict) -> str:
        """
        生成视频简介

        包含:
        - 主播介绍
        - 直播间链接
        - 个人空间链接
        - 相关标签
        - 切片姬身份披露
        """
        if not template:
            return clip_info.get("title", "直播精彩片段")

        streamer = template.get("name", "主播")
        live_room = template.get("live_room", "")
        space = template.get("space", "")
        topic = clip_info.get("title", "精彩片段")

        # 获取模板配置
        upload_template = template.get("upload_template", {})

        # 如果模板有自定义description_template，使用它
        description_template = upload_template.get("description_template", "")
        if description_template:
            # 替换变量
            tags = upload_template.get("tags", [])
            tags_str = " ".join(f"#{tag}" for tag in tags[:5])

            description = description_template.format(
                topic=topic,
                live_room=live_room or "暂无",
                space=space or "暂无",
                tags=tags_str,
            )
            return description

        # 默认简介格式
        lines = [
            f"【{streamer}】{topic}",
            "",
            f"{template.get('description', '')}",
            "",
            "更多精彩切片请查看合集~",
            "",
        ]

        # 添加链接
        if live_room:
            lines.append(f"📺 直播间: {live_room}")
        if space:
            lines.append(f"👤 主播空间: {space}")

        lines.extend(
            [
                "",
                f"#{streamer} #直播切片 #录播",
            ]
        )

        # 添加模板标签
        tags = upload_template.get("tags", [])
        if tags:
            lines.append(" ".join(f"#{tag}" for tag in tags[:5]))

        return "\n".join(lines)

    def prepare_upload(
        self, clip_info_path: str, template_name: str = None
    ) -> UploadInfo:
        """
        准备上传信息

        Args:
            clip_info_path: 切片信息 JSON 路径
            template_name: 主播模板名称

        Returns:
            UploadInfo: 上传信息
        """
        # 加载切片信息
        with open(clip_info_path, "r", encoding="utf-8") as f:
            clip_info = json.load(f)

        # 获取视频路径（优先使用_fixed版本）
        clip_dir = Path(clip_info_path).parent
        clip_name = clip_dir.name

        # 优先顺序：_fixed版本 > final字段 > 默认mp4
        fixed_video = clip_dir / f"{clip_name}_with_danmaku_fixed.mp4"
        if fixed_video.exists():
            video_path = str(fixed_video)
        else:
            final_file = clip_info.get("files", {}).get("final")
            if final_file:
                video_path = str(clip_dir / final_file)
            else:
                video_path = str(clip_dir / f"{clip_name}.mp4")

        # 获取模板
        template = None
        if template_name and self.template_manager:
            template = self.template_manager.get_template(template_name)

        # 生成标题和简介
        title = self.generate_title(clip_info, template)
        description = self.generate_description(clip_info, template)

        # 获取标签和分区
        if template:
            upload_config = template.get("upload_template", {})
            tags = upload_config.get("tags", ["直播切片"])
            tid = upload_config.get("tid", 138)
            streamer_name = template.get("name", "主播")
        else:
            tags = clip_info.get("keywords", [])[:10] or ["直播切片"]
            tid = 138
            streamer_name = "主播"

        return UploadInfo(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            tid=tid,
            streamer_name=streamer_name,
        )

    def upload_to_bilibili(self, upload_info: UploadInfo) -> Tuple[bool, str]:
        """
        上传到 Bilibili

        Returns:
            (success, message)
        """
        if not BILIUP_AVAILABLE:
            return False, "biliup 未安装，无法上传"

        if not os.path.exists(self.cookie_file):
            return False, f"Cookie 文件不存在: {self.cookie_file}"

        if not os.path.exists(upload_info.video_path):
            return False, f"视频文件不存在: {upload_info.video_path}"

            print(f"\n[UPLOAD] 准备上传到 Bilibili")
        print(f"   标题: {upload_info.title}")
        print(f"   标签: {', '.join(upload_info.tags)}")
        print(f"   分区: {upload_info.tid}")

        try:
            # 创建数据对象
            data = StreamData(
                name=upload_info.streamer_name,
                format_title=upload_info.title,
                url="",
                title=upload_info.title,
            )

            # 创建上传器
            uploader = BiliWeb(
                principal=upload_info.streamer_name,
                data=data,
                user={},
                user_cookie=self.cookie_file,
                tid=upload_info.tid,
                tags=upload_info.tags,
                description=upload_info.description,
                copyright=1,  # 自制
                lines="AUTO",
                threads=4,
            )

            # 执行上传
            print("   开始上传...")
            result = uploader.upload([FileInfo(upload_info.video_path)])

            return True, f"上传成功: {upload_info.title}"

        except Exception as e:
            error_msg = str(e)
            if "21070" in error_msg:
                return False, "上传频率限制，请等待30分钟后重试"
            else:
                return False, f"上传失败: {error_msg}"

    def upload_clip(
        self, clip_info_path: str, template_name: str = None, platform: str = "bilibili"
    ) -> Tuple[bool, str]:
        """
        上传单个切片

        Args:
            clip_info_path: 切片信息 JSON 路径
            template_name: 主播模板名称
            platform: 平台 (bilibili)

        Returns:
            (success, message)
        """
        # 准备上传信息
        upload_info = self.prepare_upload(clip_info_path, template_name)

        # 根据平台上传
        if platform == "bilibili":
            return self.upload_to_bilibili(upload_info)
        else:
            return False, f"不支持的平台: {platform}"

    def upload_batch(
        self,
        clips_dir: str,
        template_name: str = None,
        platform: str = "bilibili",
        delay: int = 60,
    ) -> List[Tuple[bool, str]]:
        """
        批量上传切片

        Args:
            clips_dir: 切片目录（包含多个 clip_xxx 子目录）
            template_name: 主播模板名称
            platform: 平台
            delay: 上传间隔（秒）

        Returns:
            List[Tuple[bool, str]]: 每个切片的上传结果
        """
        clips_dir = Path(clips_dir)

        # 查找所有切片目录
        clip_dirs = sorted(
            [
                d
                for d in clips_dir.iterdir()
                if d.is_dir() and d.name.startswith("clip_")
            ]
        )

        print(f"\n[INFO] 批量上传 {len(clip_dirs)} 个切片")
        print(f"   模板: {template_name or '默认'}")
        print(f"   平台: {platform}")
        print(f"   间隔: {delay}秒")

        results = []

        for i, clip_dir in enumerate(clip_dirs, 1):
            info_path = clip_dir / "info.json"

            if not info_path.exists():
                print(
                    f"\n[WARN] [{i}/{len(clip_dirs)}] 跳过 {clip_dir.name}: 无 info.json"
                )
                results.append((False, f"无 info.json: {clip_dir.name}"))
                continue

            print(f"\n[{i}/{len(clip_dirs)}] 上传: {clip_dir.name}")

            success, msg = self.upload_clip(
                str(info_path), template_name=template_name, platform=platform
            )

            results.append((success, msg))

            # 等待间隔
            if i < len(clip_dirs) and delay > 0:
                print(f"   等待 {delay} 秒...")
                time.sleep(delay)

        # 统计结果
        success_count = sum(1 for s, _ in results if s)
        print(f"\n{'=' * 60}")
        print(f"[OK] 上传完成: {success_count}/{len(results)} 成功")
        print(f"{'=' * 60}")

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="上传直播切片")
    parser.add_argument("clip_info", help="切片 info.json 路径或切片目录")
    parser.add_argument("--template", "-t", help="主播模板名称")
    parser.add_argument("--platform", "-p", default="bilibili", help="上传平台")
    parser.add_argument("--cookie", "-c", default="cookies.json", help="Cookie 文件")
    parser.add_argument(
        "--batch", "-b", action="store_true", help="批量上传目录下所有切片"
    )
    parser.add_argument(
        "--delay", "-d", type=int, default=60, help="批量上传间隔（秒）"
    )

    args = parser.parse_args()

    # 创建上传器
    uploader = StreamUploader(cookie_file=args.cookie)

    if args.batch:
        # 批量上传
        results = uploader.upload_batch(
            args.clip_info,
            template_name=args.template,
            platform=args.platform,
            delay=args.delay,
        )
    else:
        # 单个上传
        success, msg = uploader.upload_clip(
            args.clip_info, template_name=args.template, platform=args.platform
        )

        if success:
            print(f"[OK] {msg}")
        else:
            print(f"[FAIL] {msg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
