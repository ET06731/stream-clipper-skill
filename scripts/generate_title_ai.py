#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-powered 标题生成模块
基于 AI 语义理解生成吸引人的直播切片标题
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TitleCandidate:
    """标题候选"""

    title: str
    title_type: str  # suspense/quote/topic/wholesome/savage
    reason: str
    score: Optional[float] = None


@dataclass
class GeneratedTitles:
    """生成的标题结果"""

    highlight_info: Dict
    streamer: str
    platform: str
    titles: List[TitleCandidate]
    recommended: str
    tags: List[str]
    description: str
    generated_at: str


class AITitleGenerator:
    """
    AI-powered 标题生成器

    设计原则：
    1. 接收 AI 分析的精彩片段信息
    2. 生成多风格、多版本的标题
    3. 考虑主播风格和平台特点
    4. 支持批量生成和单条精修
    """

    # 标题风格模板
    TITLE_PATTERNS = {
        "suspense": [
            "【{streamer}】{topic}？{streamer}的说法让所有人沉默",
            "【{streamer}】{topic}体验 | 看完你就懂了",
            "【{streamer}】关于{topic}，{streamer}说出了真相",
            "【{streamer}】{topic}的背后，隐藏着",
            "【{streamer}】{topic}！{streamer}的反应亮了",
        ],
        "quote": [
            '【{streamer}】"{quote}"',
            '【{streamer}】{streamer}："{quote_frag}..."',
            "【{streamer}】{quote}",
            "【{streamer}】名场面 | {quote_frag}",
            '【{streamer}】{streamer}语录"{quote_frag}"',
        ],
        "topic": [
            "【{streamer}】{topic} | {modifier}",
            "【{streamer}】{topic}片段",
            "【{streamer}】{topic}高光时刻",
            "【{streamer}】{topic}精华",
            "【{streamer}】{topic}名场面",
        ],
        "funny": [
            "【{streamer}】{streamer}翻车现场",
            "【{streamer}】{topic}翻车合集",
            "【{streamer}】{streamer}搞笑片段",
            "【{streamer}】{topic}还能这样？",
            "【{streamer}】{topic}名场面笑死",
        ],
        "savage": [
            "【{streamer}】{streamer}太敢说了",
            "【{streamer}】{topic} {streamer}直接开团",
            "【{streamer}】{streamer}锐评{topic}",
            "【{streamer}】{topic}被{streamer}整活了",
        ],
        "wholesome": [
            "【{streamer}】{topic}温馨时刻",
            "【{streamer}】{topic}感动瞬间",
            "【{streamer}】{streamer}与{topic}的美好回忆",
            "【{streamer}】{topic}治愈时刻",
        ],
        "interaction": [
            '【{streamer}】弹幕："{danmaku}" {streamer}回应',
            "【{streamer}】{streamer}与弹幕互动名场面",
            "【{streamer}】弹幕整活 {streamer}接住",
        ],
    }

    def __init__(self, streamer_name: str = "Unknown", streamer_template: Dict = None):
        """
        初始化标题生成器

        Args:
            streamer_name: 主播名称
            streamer_template: 主播模板
        """
        self.streamer_name = streamer_name
        self.streamer_template = streamer_template or {}

        # 加载模板配置
        upload_template = self.streamer_template.get("upload_template", {})
        self.default_template = upload_template.get(
            "title_template", "[{streamer}]{topic}"
        )
        self.default_tags = upload_template.get("tags", [streamer_name, "直播切片"])
        self.style = self.streamer_template.get("style", {})
        self.memes = self.streamer_template.get("memes", [])

    def generate_ai_prompt(
        self, highlight: Dict, platform: str = "bilibili", num_options: int = 5
    ) -> str:
        """
        生成 AI 标题生成的提示词

        Args:
            highlight: 精彩片段信息
            platform: 目标平台
            num_options: 生成标题数量

        Returns:
            AI 提示词
        """
        template = self.streamer_template

        prompt = f"""你是一个专业的社交媒体标题策划专家。请为以下直播片段生成吸引人的标题。

## 直播信息
- 主播: {self.streamer_name}
- 主播风格: {self.style.get("tone", "幽默风趣")}
- 著名梗: {", ".join(self.memes[:5]) if self.memes else "无"}
- 直播内容: {self.style.get("content_type", "通用")}

## 片段详情
- 时间范围: {highlight.get("start_time", "Unknown")} - {highlight.get("end_time", "Unknown")}
- 时长: {highlight.get("duration_seconds", "Unknown")} 秒
- AI推荐标题: {highlight.get("title", "无")}
- 精彩原因: {highlight.get("reason", "无")}
- 金句引用: {highlight.get("quote", "无")}
- 关键词: {", ".join(highlight.get("keywords", []))}
- 内容描述: {highlight.get("description", "无")}
- 评分: {highlight.get("score", "Unknown")}

## 平台要求 ({platform})
"""

        if platform == "bilibili":
            prompt += """- 标题风格：B站用户喜欢玩梗、吐槽、夸张表达
- 长度限制：80字符以内（建议30字左右）
- 常用元素：【】符号、"|"分隔、梗前缀
- 示例：【主播】名场面、【主播】封神、【主播】翻车
"""
        elif platform == "youtube":
            prompt += """- 标题风格：YouTube 用户更直接、信息量大
- 长度限制：100字符以内
- 常用元素：EMOJ、大写字母、吸引眼球的表达
- 示例：主播 NAME does THIS | UNBELIEVABLE
"""
        elif platform == "tiktok":
            prompt += """- 标题风格：抖音用户注意力短，需要快速抓住眼球
- 长度限制：30字以内
- 常用元素：问号、感叹号、简单直接
- 示例：主播这句话绝了！| 看完笑到
"""

        prompt += f"""
## 输出格式
生成 {num_options} 个不同风格的标题（必须是有效的 JSON 数组格式）：

```json
[
  {{
    "type": "悬念型",
    "title": "【{self.streamer_name}】完整标题内容",
    "reason": "为什么这个标题有效",
    "score": 0.95
  }},
  {{
    "type": "引用型",
    "title": "【{self.streamer_name}】引用金句或对话",
    "reason": "引用了片段中的什么内容",
    "score": 0.92
  }}
]
```

## 标题类型说明
1. **悬念型**: 用问号或暗示制造好奇，让观众想点开看
2. **引用型**: 直接引用片段中的金句、搞笑对话、梗
3. **话题型**: 突出片段的核心话题或事件
4. **搞笑型**: 强调翻车、搞笑、整活元素
5. **锐评型**: 突出主播的毒舌、犀利观点
6. **互动型**: 突出主播与弹幕/观众的互动

## 要求
- 每个标题要包含主播名：{self.streamer_name}
- 标题要吸引人但不标题党（真实反映内容）
- 长度：B站30字左右，其他平台适当调整
- 适当使用梗，但要确保大多数人能理解
- 最后标注推荐的标题

请直接输出 JSON 数组，不要有其他文字："""

        return prompt

    def _extract_quote_fragments(self, quote: str, max_len: int = 15) -> List[str]:
        """提取金句片段（用于标题模板）"""
        if not quote:
            return ["精彩片段"]

        # 清理
        quote = quote.strip().strip('"').strip("'")

        # 如果太长，截取关键部分
        if len(quote) > max_len:
            # 尝试在标点处截断
            for sep in ["！", "。", "？", "！", "?", ".", ",", "，"]:
                if sep in quote:
                    idx = quote.find(sep)
                    if idx > 5 and idx < max_len:
                        return [quote[: idx + 1]]
            return [quote[:max_len] + "..."]

        return [quote]

    def _generate_rule_based_titles(self, highlight: Dict) -> List[TitleCandidate]:
        """基于规则生成标题（fallback）"""
        titles = []
        topic = highlight.get("topic", "精彩片段")
        quote = highlight.get("quote", "")
        keywords = highlight.get("keywords", [])
        reason = highlight.get("reason", "")

        # 根据 reason 判断类型
        reason_lower = reason.lower()

        if "笑" in reason or "搞笑" in reason or "翻车" in reason:
            title_type = "funny"
        elif "弹幕" in reason or "互动" in reason:
            title_type = "interaction"
        elif "震惊" in reason or "不可能" in reason or "?" in reason:
            title_type = "suspense"
        elif quote:
            title_type = "quote"
        else:
            title_type = "topic"

        # 生成标题
        patterns = self.TITLE_PATTERNS.get(title_type, self.TITLE_PATTERNS["topic"])

        for i, pattern in enumerate(patterns[:3]):
            quote_frags = self._extract_quote_fragments(quote)

            title = pattern.format(
                streamer=self.streamer_name,
                topic=topic[:20] if topic else "精彩片段",
                quote=quote[:40] if quote else "精彩片段",
                quote_frag=quote_frags[0] if quote_frags else "精彩片段",
                danmaku=keywords[0] if keywords else "666",
                modifier="高光时刻",
            )

            titles.append(
                TitleCandidate(
                    title=title,
                    title_type=title_type,
                    reason=f"基于 {title_type} 类型自动生成",
                    score=0.7 + (i * 0.05),
                )
            )

        return titles

    def generate_titles(
        self, highlight: Dict, platform: str = "bilibili", use_ai: bool = True
    ) -> GeneratedTitles:
        """
        生成标题（主入口）

        Args:
            highlight: 精彩片段信息
            platform: 目标平台
            use_ai: 是否使用 AI 生成（False 则使用规则）

        Returns:
            GeneratedTitles 对象
        """
        if use_ai:
            # 生成 AI 提示词（用户需要发送给 AI）
            ai_prompt = self.generate_ai_prompt(highlight, platform)

            # 这里不实际调用 AI，而是返回提示词
            # 用户需要将提示词发送给 AI，然后解析返回结果
            print(f"\n📝 AI 标题生成提示词（发送给 AI）:")
            print(f"{'=' * 60}")
            print(ai_prompt)
            print(f"{'=' * 60}")

            # 返回带提示词的结果
            return GeneratedTitles(
                highlight_info=highlight,
                streamer=self.streamer_name,
                platform=platform,
                titles=[],  # AI 会填充
                recommended="",
                tags=self.default_tags.copy(),
                description=highlight.get("description", ""),
                generated_at=datetime.now().isoformat(),
            )
        else:
            # 使用规则 fallback
            titles = self._generate_rule_based_titles(highlight)

            return GeneratedTitles(
                highlight_info=highlight,
                streamer=self.streamer_name,
                platform=platform,
                titles=titles,
                recommended=titles[0].title
                if titles
                else f"[{self.streamer_name}]精彩片段",
                tags=self.default_tags.copy(),
                description=highlight.get("description", ""),
                generated_at=datetime.now().isoformat(),
            )

    def parse_ai_response(self, ai_output: str) -> GeneratedTitles:
        """
        解析 AI 返回的标题结果

        Args:
            ai_output: AI 返回的文本

        Returns:
            GeneratedTitles 对象
        """
        # 尝试提取 JSON
        json_match = re.search(r"```json\s*(.+?)\s*```", ai_output, re.DOTALL)
        if json_match:
            try:
                titles_data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                titles_data = []
        else:
            try:
                titles_data = json.loads(ai_output)
            except json.JSONDecodeError:
                titles_data = []

        # 转换为 TitleCandidate 列表
        titles = []
        recommended = ""

        for item in titles_data:
            titles.append(
                TitleCandidate(
                    title=item.get("title", ""),
                    title_type=item.get("type", "unknown"),
                    reason=item.get("reason", ""),
                    score=item.get("score"),
                )
            )
            if item.get("score", 0) >= 0.9:
                recommended = item.get("title", recommended)

        if not recommended and titles:
            recommended = titles[0].title

        if not recommended:
            recommended = f"[{self.streamer_name}]精彩片段"

        return GeneratedTitles(
            highlight_info={},
            streamer=self.streamer_name,
            platform="",
            titles=titles,
            recommended=recommended,
            tags=self.default_tags.copy()
            if hasattr(self, "default_tags")
            else [self.streamer_name, "直播切片"],
            description="",
            generated_at=datetime.now().isoformat(),
        )

    def create_description(
        self, highlight: Dict, title: str, platform: str = "bilibili"
    ) -> str:
        """
        生成视频描述文案

        Args:
            highlight: 精彩片段信息
            title: 使用的标题
            platform: 目标平台

        Returns:
            描述文案
        """
        template = self.streamer_template

        # 获取模板配置
        desc_template = template.get("upload_template", {}).get(
            "description_template",
            "【{streamer}】{topic}\n\n更多精彩切片请查看合集~\n\n#直播切片 #",
        )

        # 构建描述
        description = desc_template.format(
            streamer=self.streamer_name,
            topic=highlight.get("topic", "精彩片段"),
            title=title,
            description=highlight.get("description", ""),
            keywords=", ".join(highlight.get("keywords", [])[:5]),
            start_time=highlight.get("start_time", ""),
            end_time=highlight.get("end_time", ""),
        )

        # 添加标签
        tags = self.default_tags.copy()
        if highlight.get("keywords"):
            tags.extend([kw for kw in highlight["keywords"][:3] if kw not in tags])

        # 添加平台特定信息
        if platform == "bilibili":
            live_room = template.get("live_room", "")
            space = template.get("space", "")

            if live_room:
                description += f"\n\n📺 主播直播间: {live_room}"
            if space:
                description += f"\n👤 主播空间: {space}"

        description += "\n\n" + " ".join([f"#{t}" for t in tags[:10]])

        return description

    def batch_generate(
        self, highlights: List[Dict], platform: str = "bilibili", use_ai: bool = True
    ) -> List[GeneratedTitles]:
        """
        批量生成标题

        Args:
            highlights: 精彩片段列表
            platform: 目标平台
            use_ai: 是否使用 AI

        Returns:
            生成结果列表
        """
        results = []

        for i, highlight in enumerate(highlights, 1):
            print(f"\n[{i}/{len(highlights)}] 处理片段...")
            result = self.generate_titles(highlight, platform, use_ai)
            results.append(result)

            if not use_ai and result.titles:
                print(f"   生成标题: {result.titles[0].title}")

        return results


def main():
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="AI-powered 标题生成")
    parser.add_argument("highlight", help="精彩片段 JSON 文件或 JSON 字符串")
    parser.add_argument("--streamer", "-s", default="Unknown", help="主播名称")
    parser.add_argument("--template", "-t", help="主播模板 YAML 文件")
    parser.add_argument(
        "--platform",
        "-p",
        default="bilibili",
        choices=["bilibili", "youtube", "tiktok"],
    )
    parser.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    # 加载精彩片段数据
    if args.highlight.endswith(".json"):
        with open(args.highlight, "r", encoding="utf-8") as f:
            highlight = json.load(f)
    else:
        try:
            highlight = json.loads(args.highlight)
        except json.JSONDecodeError:
            highlight = {"title": args.highlight}

    # 加载模板
    streamer_template = None
    if args.template:
        with open(args.template, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            streamer_template = data.get(
                args.streamer.lower(),
                data.get("streamers", {}).get(args.streamer.lower()),
            )

    # 创建生成器
    generator = AITitleGenerator(
        streamer_name=args.streamer, streamer_template=streamer_template or {}
    )

    # 生成标题
    result = generator.generate_titles(highlight, args.platform, use_ai=True)

    # 输出
    if result.titles:
        print(f"\n🎯 推荐的标题: {result.recommended}")
        print(f"\n📋 所有选项:")
        for i, t in enumerate(result.titles, 1):
            print(f"   {i}. [{t.title_type}] {t.title}")
            print(f"      {t.reason}")

        print(f"\n🏷️  建议标签: {' '.join(result.tags)}")
    else:
        print("\n⚠️  未生成标题（请将提示词发送给 AI）")
        print(f"   输出文件已保存（包含 AI 提示词）")

    # 保存结果
    output_data = {
        "highlight": highlight,
        "streamer": args.streamer,
        "platform": args.platform,
        "titles": [t.__dict__ for t in result.titles] if result.titles else [],
        "recommended": result.recommended,
        "tags": result.tags,
        "description": result.description,
        "generated_at": result.generated_at,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存: {args.output}")


if __name__ == "__main__":
    main()
