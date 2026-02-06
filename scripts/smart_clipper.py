#!/usr/bin/env python3
"""
智能切片决策引擎
结合弹幕密度和字幕语义分析，生成最优切片方案
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class ClipRecommendation:
    """切片推荐"""

    start: float
    end: float
    duration: float
    title: str
    keywords: List[str]
    score: int  # 0-100
    score_breakdown: Dict[str, int]  # 各维度得分
    reason: str  # 推荐理由


class SmartClipper:
    """智能切片器"""

    # 评分权重
    WEIGHTS = {
        "danmaku_density": 0.30,  # 弹幕密度 30%
        "semantic_quality": 0.40,  # 语义质量 40%
        "template_match": 0.20,  # 模板匹配 20%
        "duration_fit": 0.10,  # 时长合适 10%
    }

    def __init__(self, template: Optional[Dict] = None):
        """
        Args:
            template: 主播模板配置
        """
        self.template = template or {}
        self.clip_config = template.get("clip_config", {}) if template else {}

    def load_analysis(
        self, danmaku_result_path: str, semantic_result_path: str
    ) -> Tuple[Dict, Dict]:
        """加载分析结果"""
        with open(danmaku_result_path, "r", encoding="utf-8") as f:
            danmaku_result = json.load(f)

        with open(semantic_result_path, "r", encoding="utf-8") as f:
            semantic_result = json.load(f)

        return danmaku_result, semantic_result

    def score_danmaku_density(self, moment: Dict) -> int:
        """
        评分弹幕密度 (0-100)
        基于密度相对于平均值的比例
        """
        density = moment.get("density", 0)

        # 简单评分：密度越高分越高
        if density >= 150:
            score = 100
        elif density >= 100:
            score = 80
        elif density >= 80:
            score = 60
        elif density >= 50:
            score = 40
        else:
            score = 20

        return score

    def score_semantic_quality(self, highlight: Dict) -> int:
        """
        评词语义质量 (0-100)
        基于兴奋度和内容质量
        """
        excitement = highlight.get("excitement_score", 1)

        # 兴奋度 1-5 映射到 20-100
        score = excitement * 20

        # 如果有关键语录，额外加分
        if highlight.get("key_quotes"):
            score = min(100, score + 10)

        return score

    def score_template_match(self, moment: Dict, highlight: Dict) -> int:
        """
        评分模板匹配度 (0-100)
        检查是否包含主播的经典梗
        """
        score = 50  # 基础分

        if not self.template:
            return score

        memes = self.template.get("memes", [])
        keywords = moment.get("keywords", []) + highlight.get("keywords", [])

        # 检查关键词是否包含梗
        text = " ".join(keywords).lower()
        matched_memes = [meme for meme in memes if meme.lower() in text]

        # 每匹配一个梗加10分
        score += len(matched_memes) * 10

        return min(100, score)

    def score_duration_fit(self, duration: float) -> int:
        """
        评分时长合适度 (0-100)
        基于模板推荐时长
        """
        if not self.clip_config:
            # 默认 1-3 分钟合适
            if 60 <= duration <= 180:
                return 100
            elif 30 <= duration < 60 or 180 < duration <= 300:
                return 70
            else:
                return 40

        min_duration = self.clip_config.get("min_duration", 60)
        max_duration = self.clip_config.get("max_duration", 300)

        if min_duration <= duration <= max_duration:
            return 100
        elif duration < min_duration:
            # 太短
            return max(0, 100 - (min_duration - duration) * 2)
        else:
            # 太长
            return max(0, 100 - (duration - max_duration) * 0.5)

    def generate_title(self, keywords: List[str], highlight: Dict) -> str:
        """生成切片标题"""
        streamer = self.template.get("name", "主播")

        # 选择最重要的关键词
        main_keyword = keywords[0] if keywords else "精彩时刻"

        # 如果有关键语录，优先使用
        if highlight.get("key_quotes"):
            quote = highlight["key_quotes"][0]
            if len(quote) <= 20:
                title = f"[{streamer}] {quote}"
            else:
                title = f"[{streamer}]{main_keyword} | 高能名场面"
        else:
            title = f"[{streamer}]{main_keyword} | 精彩片段"

        # 限制长度
        if len(title) > 80:
            title = title[:77] + "..."

        return title

    def merge_moments(self, danmaku_result: Dict, semantic_result: Dict) -> List[Dict]:
        """
        合并弹幕和语义分析的时刻
        找出两者都认为是精彩的时段
        """
        merged = []

        # 获取弹幕高峰时刻
        danmaku_peaks = danmaku_result.get("peak_moments", [])

        # 获取语义精彩片段
        semantic_highlights = semantic_result.get("highlights", [])

        # 1. 直接匹配重叠时段
        for dm_peak in danmaku_peaks:
            dm_start, dm_end = dm_peak["start"], dm_peak["end"]

            for hl in semantic_highlights:
                hl_start, hl_end = hl["start"], hl["end"]

                # 检查时间重叠
                overlap = max(0, min(dm_end, hl_end) - max(dm_start, hl_start))

                if overlap > 10:  # 至少重叠10秒
                    # 合并时段
                    merged_start = min(dm_start, hl_start)
                    merged_end = max(dm_end, hl_end)

                    # 限制最大时长（3分钟）
                    if merged_end - merged_start > 180:
                        merged_end = merged_start + 180

                    merged.append(
                        {
                            "start": merged_start,
                            "end": merged_end,
                            "danmaku": dm_peak,
                            "semantic": hl,
                            "overlap": overlap,
                        }
                    )

        # 2. 如果没有足够的重叠，单独添加高分项
        if len(merged) < 5:
            # 添加弹幕高峰
            for dm_peak in danmaku_peaks[:5]:
                if not any(m["danmaku"] == dm_peak for m in merged):
                    merged.append(
                        {
                            "start": dm_peak["start"],
                            "end": dm_peak["end"],
                            "danmaku": dm_peak,
                            "semantic": None,
                            "overlap": 0,
                        }
                    )

            # 添加语义亮点
            for hl in semantic_highlights[:5]:
                if not any(m["semantic"] == hl for m in merged):
                    merged.append(
                        {
                            "start": hl["start"],
                            "end": hl["end"],
                            "danmaku": None,
                            "semantic": hl,
                            "overlap": 0,
                        }
                    )

        # 去重并排序
        seen = set()
        unique_merged = []
        for m in merged:
            key = (int(m["start"]), int(m["end"]))
            if key not in seen:
                seen.add(key)
                unique_merged.append(m)

        unique_merged.sort(key=lambda x: x["start"])

        return unique_merged

    def generate_recommendations(
        self, danmaku_result_path: str, semantic_result_path: str, top_n: int = 10
    ) -> List[ClipRecommendation]:
        """
        生成切片推荐

        Returns:
            List[ClipRecommendation]: 推荐切片列表
        """
        print("🧠 智能切片决策中...")

        # 加载分析结果
        danmaku_result, semantic_result = self.load_analysis(
            danmaku_result_path, semantic_result_path
        )

        # 合并时刻
        merged = self.merge_moments(danmaku_result, semantic_result)
        print(f"   找到 {len(merged)} 个候选时段")

        # 评分每个候选
        recommendations = []

        for moment in merged:
            dm_data = moment.get("danmaku", {}) or {}
            hl_data = moment.get("semantic", {}) or {}

            duration = moment["end"] - moment["start"]

            # 各维度评分
            dm_score = self.score_danmaku_density(dm_data)
            sem_score = self.score_semantic_quality(hl_data)
            template_score = self.score_template_match(dm_data, hl_data)
            duration_score = self.score_duration_fit(duration)

            # 加权总分
            total_score = int(
                dm_score * self.WEIGHTS["danmaku_density"]
                + sem_score * self.WEIGHTS["semantic_quality"]
                + template_score * self.WEIGHTS["template_match"]
                + duration_score * self.WEIGHTS["duration_fit"]
            )

            # 收集关键词
            keywords = []
            if dm_data.get("keywords"):
                keywords.extend(dm_data["keywords"])
            if hl_data.get("keywords"):
                keywords.extend(hl_data["keywords"])
            keywords = list(dict.fromkeys(keywords))[:5]  # 去重并限制

            # 生成推荐理由
            reasons = []
            if dm_data.get("density", 0) > 80:
                reasons.append("弹幕密集")
            if hl_data.get("excitement_score", 0) >= 4:
                reasons.append("情绪高涨")
            if template_score > 70:
                reasons.append("包含经典梗")

            reason = " + ".join(reasons) if reasons else "精彩片段"

            # 生成标题
            title = self.generate_title(keywords, hl_data)

            recommendation = ClipRecommendation(
                start=moment["start"],
                end=moment["end"],
                duration=duration,
                title=title,
                keywords=keywords,
                score=total_score,
                score_breakdown={
                    "danmaku": dm_score,
                    "semantic": sem_score,
                    "template": template_score,
                    "duration": duration_score,
                },
                reason=reason,
            )

            recommendations.append(recommendation)

        # 按总分排序
        recommendations.sort(key=lambda x: x.score, reverse=True)

        # 去重（时间过于接近的只保留最高分）
        filtered = []
        for rec in recommendations:
            # 检查是否与已保留的时段重叠太多
            overlap = False
            for kept in filtered:
                overlap_start = max(rec.start, kept.start)
                overlap_end = min(rec.end, kept.end)
                if overlap_end - overlap_start > 30:  # 重叠超过30秒
                    overlap = True
                    break

            if not overlap:
                filtered.append(rec)

        return filtered[:top_n]

    def save_recommendations(
        self, recommendations: List[ClipRecommendation], output_path: str
    ):
        """保存推荐结果"""
        result = {
            "total_recommendations": len(recommendations),
            "clips": [asdict(rec) for rec in recommendations],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 生成 {len(recommendations)} 个切片推荐")
        print(f"   结果已保存: {output_path}")

    def display_recommendations(self, recommendations: List[ClipRecommendation]):
        """展示推荐结果"""
        print("\n" + "=" * 60)
        print("🎬 智能切片推荐")
        print("=" * 60)

        for i, rec in enumerate(recommendations[:10], 1):
            start_min = int(rec.start // 60)
            start_sec = int(rec.start % 60)
            end_min = int(rec.end // 60)
            end_sec = int(rec.end % 60)

            print(f"\n切片 {i}/{len(recommendations)} (评分: {rec.score}/100)")
            print(
                f"   时间: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} ({int(rec.duration)}秒)"
            )
            print(f"   标题: {rec.title}")
            print(f"   关键词: {', '.join(rec.keywords)}")
            print(f"   推荐理由: {rec.reason}")

            # 显示得分详情
            breakdown = rec.score_breakdown
            print(
                f"   得分详情: 弹幕{breakdown['danmaku']} + 语义{breakdown['semantic']} + "
                f"模板{breakdown['template']} + 时长{breakdown['duration']}"
            )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="智能切片决策")
    parser.add_argument("--danmaku", "-d", required=True, help="弹幕分析结果 JSON")
    parser.add_argument("--semantic", "-s", required=True, help="语义分析结果 JSON")
    parser.add_argument("--template", "-t", help="主播模板 JSON")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--top-n", "-n", type=int, default=10, help="推荐数量")

    args = parser.parse_args()

    # 加载模板
    template = None
    if args.template and os.path.exists(args.template):
        with open(args.template, "r", encoding="utf-8") as f:
            template = json.load(f)

    # 创建智能切片器
    clipper = SmartClipper(template)

    # 生成推荐
    recommendations = clipper.generate_recommendations(
        args.danmaku, args.semantic, top_n=args.top_n
    )

    # 展示结果
    clipper.display_recommendations(recommendations)

    # 保存结果
    if args.output:
        clipper.save_recommendations(recommendations, args.output)
    else:
        output_path = Path(args.danmaku).parent / "clip_recommendations.json"
        clipper.save_recommendations(recommendations, str(output_path))


if __name__ == "__main__":
    main()
