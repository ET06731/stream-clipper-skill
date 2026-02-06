#!/usr/bin/env python3
"""
字幕语义分析模块
解析字幕内容，识别话题结构和精彩点
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class SubtitleEntry:
    """字幕条目"""

    start: float
    end: float
    text: str
    index: int


@dataclass
class Segment:
    """语义段落"""

    start: float
    end: float
    text: str
    topic: str
    excitement_score: int  # 1-5
    key_quotes: List[str]
    keywords: List[str]


class SemanticAnalyzer:
    """字幕语义分析器"""

    # 情绪关键词映射
    EMOTION_KEYWORDS = {
        "excited": [
            "哈哈",
            "笑死",
            "卧槽",
            "牛逼",
            "太强了",
            "神",
            "名场面",
            "经典",
            "震撼",
            "惊讶",
        ],
        "funny": ["哈哈", "hhh", "笑", "草", "233", " funny", " hilarious"],
        "shocked": ["什么", "不可能", "真的假的", "惊", "吓", "???", "？"],
        "angry": ["气", "怒", "讨厌", "烦", "滚", "可恶"],
        "sad": ["哭", "泪", "难受", "心疼", " sad", "泪目"],
    }

    # 话题转换标记词
    TOPIC_TRANSITIONS = [
        "接下来",
        "然后",
        "那么",
        "好了",
        "接下来我们",
        "现在",
        "next",
        "so",
        "alright",
        "okay then",
        "moving on",
    ]

    def __init__(self):
        self.subtitles: List[SubtitleEntry] = []

    def parse_srt(self, srt_path: str) -> List[SubtitleEntry]:
        """解析 SRT 字幕文件"""
        entries = []

        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 分割字幕块
        blocks = re.split(r"\n\n+", content.strip())

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            # 解析序号
            try:
                index = int(lines[0])
            except ValueError:
                continue

            # 解析时间戳
            time_line = lines[1]
            time_match = re.match(
                r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", time_line
            )
            if not time_match:
                continue

            start = self._time_to_seconds(time_match.group(1))
            end = self._time_to_seconds(time_match.group(2))

            # 解析文本
            text = " ".join(lines[2:])

            entries.append(SubtitleEntry(start=start, end=end, text=text, index=index))

        return entries

    def _time_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒"""
        # 格式: 00:00:00,000
        parts = time_str.replace(",", ".").split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

    def detect_topic_changes(self, entries: List[SubtitleEntry]) -> List[int]:
        """
        检测话题转换点
        返回转换点的索引列表
        """
        change_points = [0]  # 开头总是转换点

        for i in range(1, len(entries)):
            current_text = entries[i].text.lower()

            # 1. 检查话题转换标记词
            for marker in self.TOPIC_TRANSITIONS:
                if marker in current_text:
                    change_points.append(i)
                    break

            # 2. 检查长时间间隔 (> 2秒)
            time_gap = entries[i].start - entries[i - 1].end
            if time_gap > 2.0:
                change_points.append(i)

        # 去重并排序
        change_points = sorted(set(change_points))

        return change_points

    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """提取关键词（简单的频率统计）"""
        from collections import Counter

        # 简单的中文分词（基于字符）
        words = []
        for i in range(len(text) - 1):
            for j in range(2, min(5, len(text) - i + 1)):
                word = text[i : i + j]
                # 过滤停用词和短词
                if len(word) >= 2 and not word.isdigit():
                    words.append(word)

        word_freq = Counter(words)

        # 过滤常见停用词
        stop_words = {"这个", "那个", "什么", "一个", "可以", "就是", "我们", "你们"}
        for sw in stop_words:
            if sw in word_freq:
                del word_freq[sw]

        return [word for word, _ in word_freq.most_common(top_n)]

    def calculate_excitement(self, text: str) -> int:
        """
        计算文本的兴奋度评分 (1-5)
        基于情绪关键词密度
        """
        text_lower = text.lower()
        score = 1

        # 统计各类情绪词
        emotion_counts = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            emotion_counts[emotion] = count

        # 根据情绪词数量评分
        total_emotion_words = sum(emotion_counts.values())

        if total_emotion_words >= 5:
            score = 5
        elif total_emotion_words >= 3:
            score = 4
        elif total_emotion_words >= 2:
            score = 3
        elif total_emotion_words >= 1:
            score = 2

        return score

    def extract_key_quotes(self, entries: List[SubtitleEntry]) -> List[str]:
        """提取关键语录/名言"""
        quotes = []

        for entry in entries:
            text = entry.text

            # 1. 包含强烈情绪词的句子
            if any(kw in text for kw in self.EMOTION_KEYWORDS["excited"]):
                # 提取包含情绪词的完整句子
                quotes.append(text)

            # 2. 包含感叹号的句子（通常表达强烈情绪）
            elif "！" in text or "!" in text:
                if len(text) > 10:  # 过滤太短的
                    quotes.append(text)

            # 3. 包含问号的疑问句（可能有梗）
            elif "？" in text or "?" in text:
                if any(kw in text for kw in ["什么", "为什么", "怎么", "真的"]):
                    quotes.append(text)

        # 去重并限制数量
        quotes = list(dict.fromkeys(quotes))[:10]

        return quotes

    def generate_topic(self, text: str) -> str:
        """
        基于文本内容生成话题标签
        简单的启发式方法
        """
        text_lower = text.lower()

        # 话题关键词映射
        topic_keywords = {
            "编程": ["代码", "程序", "编程", "python", "javascript", "bug", "报错"],
            "游戏": ["游戏", "打", "玩", "通关", "boss", "关卡", "游戏"],
            "聊天": ["聊天", "说", "讲", "聊", "话题", "讨论"],
            "唱歌": ["唱歌", "歌", "唱", "音乐"],
            "搞笑": ["笑", "搞笑", "哈哈哈", "梗", "段子"],
        }

        # 匹配话题
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                topic_scores[topic] = score

        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        else:
            return "直播互动"

    def analyze(self, subtitle_path: str) -> Dict:
        """
        完整分析流程

        Returns:
            {
                'total_subtitles': int,
                'total_duration': float,
                'segments': [
                    {
                        'start': float,
                        'end': float,
                        'topic': str,
                        'excitement_score': int,
                        'key_quotes': [str],
                        'keywords': [str]
                    }
                ],
                'highlights': [
                    {
                        'start': float,
                        'end': float,
                        'reason': str,
                        'score': int
                    }
                ]
            }
        """
        print(f"📖 分析字幕文件: {Path(subtitle_path).name}")

        # 解析字幕
        self.subtitles = self.parse_srt(subtitle_path)
        print(f"   总字幕数: {len(self.subtitles)}")

        if not self.subtitles:
            return {
                "total_subtitles": 0,
                "total_duration": 0,
                "segments": [],
                "highlights": [],
            }

        # 检测话题转换点
        change_points = self.detect_topic_changes(self.subtitles)
        print(f"   检测到 {len(change_points)} 个话题转换点")

        # 分段分析
        segments = []
        for i in range(len(change_points)):
            start_idx = change_points[i]
            end_idx = (
                change_points[i + 1]
                if i + 1 < len(change_points)
                else len(self.subtitles)
            )

            segment_entries = self.subtitles[start_idx:end_idx]

            if not segment_entries:
                continue

            # 合并文本
            segment_text = " ".join(e.text for e in segment_entries)

            # 分析段落
            segment = Segment(
                start=segment_entries[0].start,
                end=segment_entries[-1].end,
                text=segment_text[:200] + ("..." if len(segment_text) > 200 else ""),
                topic=self.generate_topic(segment_text),
                excitement_score=self.calculate_excitement(segment_text),
                key_quotes=self.extract_key_quotes(segment_entries),
                keywords=self.extract_keywords(segment_text),
            )

            segments.append(segment)

        # 识别精彩片段 (兴奋度 >= 4)
        highlights = []
        for segment in segments:
            if segment.excitement_score >= 4:
                highlights.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "reason": f"高情绪反应 (评分: {segment.excitement_score}/5)",
                        "score": segment.excitement_score,
                        "key_quotes": segment.key_quotes[:3],
                        "topic": segment.topic,
                    }
                )

        # 按评分排序
        highlights.sort(key=lambda x: x["score"], reverse=True)

        result = {
            "total_subtitles": len(self.subtitles),
            "total_duration": self.subtitles[-1].end if self.subtitles else 0,
            "segments": [
                {
                    "start": s.start,
                    "end": s.end,
                    "topic": s.topic,
                    "excitement_score": s.excitement_score,
                    "key_quotes": s.key_quotes,
                    "keywords": s.keywords,
                }
                for s in segments
            ],
            "highlights": highlights[:10],  # Top 10
        }

        # 保存结果
        output_path = Path(subtitle_path).with_suffix(".semantic_analysis.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n🌟 精彩片段:")
        for i, hl in enumerate(highlights[:5], 1):
            start_min = int(hl["start"] // 60)
            start_sec = int(hl["start"] % 60)
            print(
                f"   {i}. [{start_min:02d}:{start_sec:02d}] {hl['topic']} - {hl['reason']}"
            )
            if hl["key_quotes"]:
                print(f'      "{hl["key_quotes"][0][:50]}..."')

        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="分析字幕语义")
    parser.add_argument("subtitle_file", help="字幕 SRT 文件路径")

    args = parser.parse_args()

    analyzer = SemanticAnalyzer()
    result = analyzer.analyze(args.subtitle_file)

    print(f"\n✅ 分析完成! 识别 {len(result['highlights'])} 个精彩片段")


if __name__ == "__main__":
    main()
