#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于字幕内容生成切片标题
分析字幕文件，提取金句、搞笑对话，生成吸引点击的标题
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter


class TitleGenerator:
    """基于字幕的标题生成器"""

    def __init__(self, streamer_name: str = "Evil"):
        self.streamer_name = streamer_name
        self.meme_phrases = {
            "evil": ["evil laugh", "whipped", "slaves", "darkness", "chaos"],
            "neuro": ["vedal", "cheese", "swarm", "beef", "clutch or kick"],
        }

    def generate_title(
        self,
        subtitle_text: str,
        danmaku_keywords: List[str] = None,
        time_range: tuple = None,
    ) -> Dict:
        """
        基于字幕内容生成标题

        Args:
            subtitle_text: 该时间段的字幕文本
            danmaku_keywords: 该时间段的弹幕关键词
            time_range: (start, end) 时间段

        Returns:
            包含标题、描述、标签的字典
        """
        # 1. 提取关键句子
        key_sentences = self.extract_key_sentences(subtitle_text)

        # 2. 分析情感/话题类型
        topic_type = self.analyze_topic_type(subtitle_text, danmaku_keywords)

        # 3. 选择标题策略并生成
        title_data = self._apply_title_strategy(
            key_sentences, topic_type, danmaku_keywords
        )

        return title_data

    def extract_key_sentences(self, text: str) -> List[Dict]:
        """提取关键句子（金句、搞笑、梗）"""
        sentences = []

        # 按句子分割
        text_parts = re.split(r"[.!?。！？]+", text)

        for sent in text_parts:
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 200:
                continue

            score = 0
            features = []

            # 检查是否包含梗
            for meme in self.meme_phrases.get(self.streamer_name.lower(), []):
                if meme.lower() in sent.lower():
                    score += 10
                    features.append(f"梗: {meme}")

            # 检查是否有情绪词
            emotion_words = [
                "hate",
                "love",
                "kill",
                "die",
                "wonderful",
                "terrible",
                "amazing",
                "hate",
                "生气",
                "爱",
                "死",
                "杀",
                "笑",
                "哈哈哈",
            ]
            for word in emotion_words:
                if word.lower() in sent.lower():
                    score += 5
                    features.append("情绪词")
                    break

            # 检查是否有问句（引发好奇）
            if (
                "?" in sent
                or "？" in sent
                or any(q in sent.lower() for q in ["what", "how", "why", "do you"])
            ):
                score += 8
                features.append("问句")

            # 检查是否幽默/搞笑
            funny_patterns = [
                "mean",
                "joke",
                "funny",
                "laugh",
                "哈哈哈",
                "笑死",
                "幽默",
            ]
            for pattern in funny_patterns:
                if pattern.lower() in sent.lower():
                    score += 6
                    features.append("幽默")
                    break

            if score > 10:
                sentences.append({"text": sent, "score": score, "features": features})

        # 按分数排序
        sentences.sort(key=lambda x: x["score"], reverse=True)
        return sentences[:5]  # 返回前5个

    def analyze_topic_type(self, text: str, danmaku_keywords: List[str] = None) -> str:
        """分析话题类型"""
        text_lower = text.lower()

        # 定义话题类型关键词
        topic_types = {
            "suspense": [
                "secret",
                "truth",
                "actually",
                "whipped",
                "control",
                "dominant",
            ],
            "funny": ["joke", "laugh", "haha", "funny", "meme", "失败", "翻车"],
            "wholesome": ["love", "care", "sweet", "cute", "heart", "温暖"],
            "savage": ["kill", "destroy", "better than", "trash", "菜", "垃圾"],
            "gameplay": ["game", "play", "win", "lose", "level", "游戏"],
            "meta": ["chat", "stream", "viewer", "弹幕", "观众"],
        }

        scores = {}
        for topic, keywords in topic_types.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if danmaku_keywords:
                score += sum(
                    1
                    for kw in keywords
                    if any(kw.lower() in dk.lower() for dk in danmaku_keywords)
                )
            scores[topic] = score

        # 返回得分最高的话题类型
        if scores:
            return max(scores, key=scores.get)
        return "general"

    def _apply_title_strategy(
        self,
        key_sentences: List[Dict],
        topic_type: str,
        danmaku_keywords: List[str] = None,
    ) -> Dict:
        """应用标题策略生成标题"""

        if not key_sentences:
            return {
                "title": f"【{self.streamer_name}】精彩直播片段",
                "description": "直播精彩片段",
                "tags": [self.streamer_name, "直播切片"],
            }

        top_sentence = key_sentences[0]["text"]

        # 策略1: Suspense/争议性话题（制造悬念）
        if topic_type == "suspense":
            # 去掉上下文，只保留核心词
            core_words = self._extract_core_words(top_sentence)
            title = f"【{self.streamer_name}】{self.streamer_name}谈{core_words}体验"
            description = f"{top_sentence}... 完整内容请点击观看"

        # 策略2: 搞笑/梗（展示对话）
        elif topic_type == "funny":
            if len(top_sentence) > 50:
                # 截断，保留前半部分
                short_quote = top_sentence[:40] + "..."
            else:
                short_quote = top_sentence
            title = f'【{self.streamer_name}】"{short_quote}"'
            description = top_sentence

        # 策略3: Savage/互怼（突出冲突）
        elif topic_type == "savage":
            title = f'【{self.streamer_name}】"{top_sentence[:50]}..."'
            description = f"{self.streamer_name}直言不讳，太敢说了！"

        # 策略4: 弹幕互动
        elif topic_type == "meta" and danmaku_keywords:
            top_danmaku = danmaku_keywords[0] if danmaku_keywords else "666"
            title = f'【{self.streamer_name}】弹幕："{top_danmaku}" {self.streamer_name}："{top_sentence[:30]}..."'
            description = f"和弹幕的爆笑互动：{top_sentence}"

        # 默认策略: 直接引用
        else:
            if len(top_sentence) <= 40:
                title = f'【{self.streamer_name}】"{top_sentence}"'
            else:
                # 取前30字+省略号
                short = top_sentence[:30] + "..."
                title = f"【{self.streamer_name}】{short}"
            description = top_sentence

        # 生成标签
        tags = [self.streamer_name, "直播切片", topic_type]
        if danmaku_keywords:
            tags.extend(danmaku_keywords[:3])

        return {
            "title": title,
            "description": description,
            "tags": list(set(tags))[:5],  # 去重，最多5个
        }

    def _extract_core_words(self, text: str) -> str:
        """提取核心词（用于制造悬念）"""
        # 去掉常见的上下文词，保留核心名词
        words_to_remove = [
            "you",
            "know",
            "think",
            "feel",
            "like",
            "want",
            "need",
            "我",
            "你",
            "知道",
            "觉得",
            "想",
            "要",
        ]

        words = text.split()
        core_words = [w for w in words if w.lower() not in words_to_remove]

        # 返回最重要的2-3个词
        if core_words:
            return " ".join(core_words[:3])
        return text[:20]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="基于字幕生成切片标题")
    parser.add_argument("subtitle", help="字幕文件路径(.srt)")
    parser.add_argument("--start", type=float, help="开始时间(秒)")
    parser.add_argument("--end", type=float, help="结束时间(秒)")
    parser.add_argument("--danmaku-analysis", help="弹幕分析JSON文件")
    parser.add_argument("--streamer", default="Evil", help="主播名称")
    parser.add_argument("-o", "--output", help="输出JSON文件")

    args = parser.parse_args()

    # 读取字幕
    from extract_subtitles import SubtitleExtractor

    extractor = SubtitleExtractor()

    if args.start and args.end:
        # 提取特定时间段
        text = extractor.get_segment_text(args.subtitle, args.start, args.end)
    else:
        # 读取完整字幕
        segments = extractor.parse_srt(args.subtitle)
        text = " ".join([seg["text"] for seg in segments])

    # 读取弹幕关键词
    danmaku_keywords = []
    if args.danmaku_analysis:
        with open(args.danmaku_analysis, "r", encoding="utf-8") as f:
            analysis = json.load(f)
            # 提取峰值时段的关键词
            for moment in analysis.get("peak_moments", [])[:3]:
                danmaku_keywords.extend(moment.get("keywords", []))

    # 生成标题
    generator = TitleGenerator(streamer_name=args.streamer)
    result = generator.generate_title(
        text,
        danmaku_keywords=danmaku_keywords,
        time_range=(args.start, args.end) if args.start and args.end else None,
    )

    print("\n" + "=" * 60)
    print("生成的标题信息")
    print("=" * 60)
    print(f"标题: {result['title']}")
    print(f"描述: {result['description']}")
    print(f"标签: {', '.join(result['tags'])}")
    print("=" * 60)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] 已保存: {args.output}")


if __name__ == "__main__":
    main()
