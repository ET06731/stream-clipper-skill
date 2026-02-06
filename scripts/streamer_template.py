#!/usr/bin/env python3
"""
主播模板管理系统
管理主播的风格、梗、切片配置等
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class StreamerTemplate:
    """主播模板数据类"""

    name: str
    description: str
    live_room: str
    space: str
    style: Dict
    memes: List[str]
    clip_config: Dict
    upload_template: Dict


class StreamerTemplateManager:
    """主播模板管理器"""

    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 模板配置文件路径
        """
        if config_path is None:
            # 默认路径
            skill_dir = Path(__file__).parent.parent
            config_path = skill_dir / "config" / "streamer_templates.yaml"

        self.config_path = Path(config_path)
        self.templates: Dict[str, Dict] = {}
        self.load_templates()

    def load_templates(self):
        """加载所有主播模板"""
        if not self.config_path.exists():
            print(f"⚠️  模板文件不存在: {self.config_path}")
            print("   将使用默认模板")
            self.templates = self._get_default_templates()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.templates = data.get("streamers", {})

            print(f"✅ 已加载 {len(self.templates)} 个主播模板")

        except Exception as e:
            print(f"❌ 加载模板失败: {e}")
            self.templates = self._get_default_templates()

    def _get_default_templates(self) -> Dict:
        """获取默认模板"""
        return {
            "generic": {
                "name": "通用模板",
                "description": "默认模板，适用于未知主播",
                "live_room": "",
                "space": "",
                "style": {
                    "tone": "根据主播特点",
                    "content_type": "直播内容",
                    "language": "中文",
                    "personality": "未知",
                },
                "memes": [],
                "clip_config": {
                    "preferred_duration": "1-3分钟",
                    "min_duration": 60,
                    "max_duration": 300,
                    "focus_on": ["高能时刻", "精彩对话", "技术展示"],
                },
                "upload_template": {
                    "title_template": "[{streamer}]{topic}",
                    "description_template": "【{streamer}】{topic}\n\n更多精彩切片请查看合集~",
                    "tags": ["直播切片", "录播"],
                    "tid": 138,
                    "copyright": "original",
                },
            }
        }

    def get_template(self, streamer_name: str) -> Optional[Dict]:
        """获取指定主播的模板"""
        # 尝试精确匹配
        if streamer_name in self.templates:
            return self.templates[streamer_name]

        # 尝试不区分大小写匹配
        for key, template in self.templates.items():
            if key.lower() == streamer_name.lower():
                return template
            if template.get("name", "").lower() == streamer_name.lower():
                return template

        return None

    def list_streamers(self) -> List[str]:
        """列出所有主播名称"""
        return [template.get("name", key) for key, template in self.templates.items()]

    def template_exists(self, streamer_name: str) -> bool:
        """检查模板是否存在"""
        return self.get_template(streamer_name) is not None

    def create_template_interactive(self) -> Dict:
        """交互式创建新主播模板"""
        print("\n" + "=" * 60)
        print("📝 创建新主播模板")
        print("=" * 60)

        # 基本信息
        name = input("\n主播名称: ").strip()
        if not name:
            print("❌ 主播名称不能为空")
            return None

        # 检查是否已存在
        if self.template_exists(name):
            print(f"⚠️  主播 '{name}' 已存在")
            overwrite = input("是否覆盖? (y/n): ").strip().lower()
            if overwrite != "y":
                return None

        description = input("主播描述: ").strip()
        live_room = input("直播间链接: ").strip()
        space = input("个人空间链接: ").strip()

        # 风格
        print("\n--- 主播风格 ---")
        tone = input("语言风格 (如: 幽默风趣、严肃认真): ").strip()
        content_type = input("直播内容 (如: 游戏、聊天、编程): ").strip()
        language = input("主要语言 (如: 中文、英文): ").strip() or "中文"
        personality = input("性格特点 (如: 活泼开朗、高冷): ").strip()

        # 梗
        print("\n--- 著名梗/口头禅 ---")
        print("输入主播的标志性语句或梗 (每行一个，空行结束):")
        memes = []
        while True:
            meme = input("> ").strip()
            if not meme:
                break
            memes.append(meme)

        # 切片配置
        print("\n--- 切片配置 ---")
        preferred_duration = input("推荐切片时长 (如: 1-3分钟): ").strip() or "1-3分钟"
        try:
            min_duration = int(input("最小时长 (秒): ").strip() or "60")
            max_duration = int(input("最大时长 (秒): ").strip() or "300")
        except ValueError:
            min_duration, max_duration = 60, 300

        print("重点切片内容 (用逗号分隔):")
        focus_input = input("> ").strip()
        focus_on = [f.strip() for f in focus_input.split(",") if f.strip()]
        if not focus_on:
            focus_on = ["高能时刻", "精彩对话"]

        # 上传模板
        print("\n--- 上传配置 ---")
        title_template = input("标题模板 (如: [{streamer}]{topic}): ").strip()
        if not title_template:
            title_template = f"[{name}]{{topic}}"

        print("标签 (用逗号分隔):")
        tags_input = input("> ").strip()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        if not tags:
            tags = ["直播切片", "录播"]

        # 构建模板
        template = {
            "name": name,
            "description": description,
            "live_room": live_room,
            "space": space,
            "style": {
                "tone": tone,
                "content_type": content_type,
                "language": language,
                "personality": personality,
            },
            "memes": memes,
            "clip_config": {
                "preferred_duration": preferred_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "focus_on": focus_on,
            },
            "upload_template": {
                "title_template": title_template,
                "tags": tags,
                "tid": 138,  # 默认生活/搞笑
                "copyright": "original",
            },
        }

        # 保存
        key = name.lower().replace(" ", "_")
        self.templates[key] = template
        self.save_templates()

        print(f"\n✅ 主播 '{name}' 模板已创建!")

        return template

    def save_templates(self):
        """保存所有模板到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "streamers": self.templates,
                "platforms": {
                    "bilibili": {
                        "enabled": True,
                        "cookie_file": "cookies.json",
                        "default_tid": 138,
                    }
                },
            }

            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)

            print(f"✅ 模板已保存: {self.config_path}")

        except Exception as e:
            print(f"❌ 保存模板失败: {e}")

    def display_template(self, streamer_name: str):
        """展示主播模板信息"""
        template = self.get_template(streamer_name)

        if not template:
            print(f"❌ 未找到主播: {streamer_name}")
            return

        print("\n" + "=" * 60)
        print(f"👤 {template['name']}")
        print("=" * 60)
        print(f"描述: {template.get('description', 'N/A')}")
        print(f"直播间: {template.get('live_room', 'N/A')}")
        print(f"个人空间: {template.get('space', 'N/A')}")

        print("\n风格:")
        style = template.get("style", {})
        for key, value in style.items():
            print(f"  {key}: {value}")

        print(f"\n梗/口头禅:")
        for meme in template.get("memes", []):
            print(f"  - {meme}")

        print(f"\n切片配置:")
        clip_config = template.get("clip_config", {})
        print(f"  推荐时长: {clip_config.get('preferred_duration', 'N/A')}")
        print(
            f"  时长范围: {clip_config.get('min_duration', 60)}-{clip_config.get('max_duration', 300)}秒"
        )
        print(f"  重点: {', '.join(clip_config.get('focus_on', []))}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="主播模板管理")
    parser.add_argument("--config", "-c", help="模板配置文件路径")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有主播")
    parser.add_argument("--show", "-s", help="展示指定主播模板")
    parser.add_argument("--create", action="store_true", help="创建新模板")

    args = parser.parse_args()

    manager = StreamerTemplateManager(args.config)

    if args.list:
        streamers = manager.list_streamers()
        print(f"\n已加载 {len(streamers)} 个主播模板:")
        for i, name in enumerate(streamers, 1):
            print(f"  {i}. {name}")

    elif args.show:
        manager.display_template(args.show)

    elif args.create:
        manager.create_template_interactive()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
