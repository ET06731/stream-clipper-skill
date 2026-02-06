#!/usr/bin/env python3
"""
分析弹幕密度，识别高互动时间点
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import xml.etree.ElementTree as ET


class DanmakuAnalyzer:
    """弹幕分析器"""

    def __init__(self, window_size: int = 30):
        """
        Args:
            window_size: 时间窗口大小（秒）
        """
        self.window_size = window_size

    def parse_danmaku_xml(self, xml_path: str) -> List[Dict]:
        """解析 B站弹幕 XML 文件"""
        danmaku_list = []

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for d in root.findall("d"):
                # 弹幕属性: p="时间,模式,字号,颜色,时间戳,弹幕池,用户ID,rowID"
                p = d.get("p", "").split(",")
                if len(p) >= 8:
                    time_sec = float(p[0])
                    danmaku_list.append(
                        {
                            "time": time_sec,
                            "text": d.text or "",
                            "mode": int(p[1]),
                            "user": p[6],
                        }
                    )

        except Exception as e:
            print(f"解析弹幕失败: {e}")

        return sorted(danmaku_list, key=lambda x: x["time"])

    def calculate_density(self, danmaku_list: List[Dict]) -> Dict:
        """
        计算弹幕密度分布

        Returns:
            {
                'windows': [
                    {'start': float, 'end': float, 'count': int, 'users': set}
                ],
                'avg_density': float,
                'peak_windows': [...]
            }
        """
        if not danmaku_list:
            return {"windows": [], "avg_density": 0, "peak_windows": []}

        # 按时间窗口分组
        windows = defaultdict(lambda: {"count": 0, "users": set(), "texts": []})

        for d in danmaku_list:
            window_start = int(d["time"] // self.window_size) * self.window_size
            windows[window_start]["count"] += 1
            windows[window_start]["users"].add(d["user"])
            windows[window_start]["texts"].append(d["text"])

        # 转换为列表
        window_list = []
        for start in sorted(windows.keys()):
            window_list.append(
                {
                    "start": start,
                    "end": start + self.window_size,
                    "count": windows[start]["count"],
                    "unique_users": len(windows[start]["users"]),
                    "texts": windows[start]["texts"],
                }
            )

        # 计算平均密度
        avg_density = (
            sum(w["count"] for w in window_list) / len(window_list)
            if window_list
            else 0
        )

        # 识别峰值窗口 (密度 > 平均值的 1.5 倍)
        peak_windows = [w for w in window_list if w["count"] > avg_density * 1.5]
        peak_windows.sort(key=lambda x: x["count"], reverse=True)

        return {
            "windows": window_list,
            "avg_density": avg_density,
            "peak_windows": peak_windows[:10],  # Top 10
        }

    def extract_keywords(self, texts: List[str], top_n: int = 10) -> List[str]:
        """提取高频关键词"""
        from collections import Counter

        # 简单的中文分词（基于字符）
        word_count = Counter()

        for text in texts:
            if not text:
                continue
            # 2-4 字符的词
            for i in range(len(text) - 1):
                for j in range(2, min(5, len(text) - i + 1)):
                    word = text[i : i + j]
                    if len(word) >= 2:
                        word_count[word] += 1

        # 过滤常见停用词
        stop_words = {
            "哈哈",
            "啊啊",
            "什么",
            "这个",
            "那个",
            "今天",
            "现在",
            "真的",
            "可以",
        }
        for sw in stop_words:
            if sw in word_count:
                del word_count[sw]

        return [word for word, _ in word_count.most_common(top_n)]

    def analyze(self, danmaku_path: str) -> Dict:
        """
        完整分析流程

        Returns:
            {
                'total_danmaku': int,
                'total_users': int,
                'avg_density': float,
                'peak_moments': [
                    {
                        'start': float,
                        'end': float,
                        'density': int,
                        'keywords': [str]
                    }
                ]
            }
        """
        print(f"📊 分析弹幕文件: {Path(danmaku_path).name}")

        # 解析弹幕
        danmaku_list = self.parse_danmaku_xml(danmaku_path)
        print(f"   总弹幕数: {len(danmaku_list)}")

        if not danmaku_list:
            return {
                "total_danmaku": 0,
                "total_users": 0,
                "avg_density": 0,
                "peak_moments": [],
            }

        # 计算密度
        density_result = self.calculate_density(danmaku_list)

        # 统计用户
        all_users = set(d["user"] for d in danmaku_list)

        # 处理峰值时刻
        peak_moments = []
        for window in density_result["peak_windows"]:
            keywords = self.extract_keywords(window["texts"], 5)
            peak_moments.append(
                {
                    "start": window["start"],
                    "end": window["end"],
                    "density": window["count"],
                    "unique_users": window["unique_users"],
                    "keywords": keywords,
                }
            )

        result = {
            "total_danmaku": len(danmaku_list),
            "total_users": len(all_users),
            "avg_density": density_result["avg_density"],
            "window_size": self.window_size,
            "peak_moments": peak_moments,
        }

        # 保存结果
        output_path = Path(danmaku_path).with_suffix(".danmaku_analysis.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n🔥 高密度时段:")
        for i, moment in enumerate(peak_moments[:5], 1):
            start_min = moment["start"] // 60
            start_sec = moment["start"] % 60
            print(
                f"   {i}. [{start_min:02d}:{start_sec:02d}] 密度: {moment['density']}条/30秒"
            )
            print(f"      关键词: {', '.join(moment['keywords'])}")

        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="分析弹幕密度")
    parser.add_argument("danmaku_file", help="弹幕 XML 文件路径")
    parser.add_argument("--window", "-w", type=int, default=30, help="时间窗口（秒）")

    args = parser.parse_args()

    analyzer = DanmakuAnalyzer(window_size=args.window)
    result = analyzer.analyze(args.danmaku_file)

    print(f"\n✅ 分析完成! 结果已保存")


if __name__ == "__main__":
    main()
