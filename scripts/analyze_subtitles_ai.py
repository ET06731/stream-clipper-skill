#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-powered 字幕分析模块
借助 AI 语义理解能力进行深度字幕分析
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class SubtitleEntry:
    """字幕条目"""
    start: float
    end: float
    text: str
    index: int


@dataclass
class AIDisplaySegment:
    """AI分析的语义段落"""
    start: float
    end: float
    text_preview: str  # 前100字符预览
    full_text: str    # 完整文本（AI分析时使用）
    ai_analysis: Optional[Dict] = None  # AI分析结果


@dataclass
class HighlightMoment:
    """精彩片段"""
    start: float
    end: float
    reason: str
    score: float
    title: str
    description: str
    keywords: List[str]
    quote: Optional[str] = None


class SubtitleAnalyzerAI:
    """
    AI-powered 字幕分析器
    
    设计原则：
    1. 准备 AI-friendly 的结构化数据
    2. 生成详细的分析提示词
    3. 支持 Claude/GPT 等 LLM 进行深度语义分析
    4. 保留 fallback 规则分析（无 AI 时使用）
    """

    # 用于时间格式转换的工具函数
    @staticmethod
    def time_to_seconds(time_str: str) -> float:
        """将时间字符串转换为秒"""
        time_str = time_str.strip().replace(",", ".")
        parts = time_str.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])

    @staticmethod
    def seconds_to_time(seconds: float, include_hours: bool = True) -> str:
        """将秒转换为时间字符串"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if include_hours or hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def __init__(self, streamer_name: str = "Unknown", streamer_template: Dict = None):
        """
        初始化分析器
        
        Args:
            streamer_name: 主播名称
            streamer_template: 主播模板（包含风格、梗等信息）
        """
        self.streamer_name = streamer_name
        self.streamer_template = streamer_template or {}
        self.memes = self.streamer_template.get("memes", [])
        self.focus_on = self.streamer_template.get("clip_config", {}).get("focus_on", [])

    def parse_srt(self, srt_path: str) -> List[SubtitleEntry]:
        """解析 SRT 字幕文件"""
        entries = []
        
        if not Path(srt_path).exists():
            raise FileNotFoundError(f"字幕文件不存在: {srt_path}")
        
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 分割字幕块
        blocks = re.split(r"\n\n+", content.strip())
        
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0])
            except ValueError:
                continue
            
            # 解析时间戳
            time_line = lines[1]
            time_match = re.match(
                r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})",
                time_line
            )
            if not time_match:
                continue
            
            start = self.time_to_seconds(time_match.group(1))
            end = self.time_to_seconds(time_match.group(2))
            text = " ".join(lines[2:])
            
            entries.append(SubtitleEntry(start=start, end=end, text=text, index=index))
        
        return entries

    def prepare_ai_analysis_data(self, subtitles: List[SubtitleEntry]) -> Dict:
        """
        准备 AI 分析所需的数据
        
        Returns:
            结构化的数据，包含：
            - 字幕概览
            - 分段文本（用于话题分析）
            - AI 提示词
        """
        if not subtitles:
            return {"error": "无字幕数据"}
        
        # 1. 统计信息
        total_duration = subtitles[-1].end - subtitles[0].start
        total_entries = len(subtitles)
        
        # 2. 合并为连续文本（用于长文本分析）
        full_text = " ".join([s.text for s in subtitles])
        
        # 3. 分段（每段约500字，用于话题分析）
        segments = self._create_text_segments(subtitles, max_chars=500)
        
        # 4. 高密度时段检测（基于时间间隔）
        dense_moments = self._detect_dense_moments(subtitles)
        
        # 5. 生成 AI 提示词
        ai_prompt = self._generate_analysis_prompt(
            full_text=full_text[:3000],  # 限制长度
            segments=segments,
            dense_moments=dense_moments,
            memes=self.memes,
            focus_on=self.focus_on
        )
        
        return {
            "metadata": {
                "streamer_name": self.streamer_name,
                "total_duration_seconds": total_duration,
                "total_duration_display": self.seconds_to_time(total_duration),
                "total_subtitles": total_entries,
                "analyzed_at": datetime.now().isoformat(),
                "template_focus": self.focus_on
            },
            "segments": segments,
            "dense_moments": dense_moments,
            "ai_prompt": ai_prompt,
            "full_text_preview": full_text[:1000] + ("..." if len(full_text) > 1000 else "")
        }

    def _create_text_segments(self, subtitles: List[SubtitleEntry], max_chars: int = 500) -> List[Dict]:
        """创建文本分段用于分析"""
        segments = []
        current_segment = []
        current_chars = 0
        segment_start = 0
        
        for i, sub in enumerate(subtitles):
            sub_len = len(sub.text)
            
            if current_chars + sub_len > max_chars and current_segment:
                # 保存当前段
                segment_text = " ".join([s.text for s in current_segment])
                segments.append({
                    "start_time": self.seconds_to_time(segment_start),
                    "end_time": self.seconds_to_time(current_segment[-1].end),
                    "start_seconds": segment_start,
                    "end_seconds": current_segment[-1].end,
                    "text": segment_text,
                    "text_preview": segment_text[:100] + ("..." if len(segment_text) > 100 else ""),
                    "subtitle_count": len(current_segment)
                })
                
                # 开始新段
                current_segment = [sub]
                current_chars = sub_len
                segment_start = sub.start
            else:
                current_segment.append(sub)
                current_chars += sub_len
        
        # 保存最后一段
        if current_segment:
            segment_text = " ".join([s.text for s in current_segment])
            segments.append({
                "start_time": self.seconds_to_time(segment_start),
                "end_time": self.seconds_to_time(current_segment[-1].end),
                "start_seconds": segment_start,
                "end_seconds": current_segment[-1].end,
                "text": segment_text,
                "text_preview": segment_text[:100] + ("..." if len(segment_text) > 100 else ""),
                "subtitle_count": len(current_segment)
            })
        
        return segments

    def _detect_dense_moments(self, subtitles: List[SubtitleEntry], window_seconds: float = 60.0) -> List[Dict]:
        """检测字幕密集时段"""
        if not subtitles:
            return []
        
        dense_moments = []
        total_duration = subtitles[-1].end
        
        # 计算每个时间窗口的字幕数量
        window_count = int(total_duration / window_seconds) + 1
        
        for i in range(window_count):
            window_start = i * window_seconds
            window_end = window_start + window_seconds
            
            count = sum(1 for s in subtitles if window_start <= s.start < window_end)
            
            if count >= 5:  # 至少有5条字幕
                dense_moments.append({
                    "time_range": f"{self.seconds_to_time(window_start)}-{self.seconds_to_time(window_end)}",
                    "start_seconds": window_start,
                    "end_seconds": window_end,
                    "subtitle_count": count,
                    "density": count / window_seconds  # 条/秒
                })
        
        # 按密度排序
        dense_moments.sort(key=lambda x: x["density"], reverse=True)
        
        return dense_moments[:10]  # 返回前10个密集时段

    def _generate_analysis_prompt(
        self,
        full_text: str,
        segments: List[Dict],
        dense_moments: List[Dict],
        memes: List[str],
        focus_on: List[str]
    ) -> str:
        """生成 AI 分析提示词"""
        
        prompt = f"""你是一个专业的直播切片分析师。请分析以下直播字幕数据，识别精彩片段。

## 主播信息
- 主播名称: {self.streamer_name}
- 重点关注: {', '.join(focus_on) if focus_on else '高能时刻、精彩对话'}
- 主播梗/口头禅: {', '.join(memes) if memes else '无特定梗'}

## 字幕数据概览
- 字幕段数: {len(segments)}
- 密集时段数: {len(dense_moments)}

## 密集时段（高互动区域）
"""
        
        for moment in dense_moments[:5]:
            prompt += f"- {moment['time_range']}: {moment['subtitle_count']}条字幕\n"
        
        prompt += f"""
## 字幕内容（按时间分段）

"""
        for i, seg in enumerate(segments[:10]):  # 取前10段
            prompt += f"【{seg['start_time']} - {seg['end_time']}】\n{seg['text'][:200]}\n\n"
        
        prompt += """
## 分析任务

请按以下格式输出 JSON 分析结果：

```json
{
  "highlights": [
    {
      "start_seconds": 123.0,
      "end_seconds": 189.0,
      "duration_seconds": 66,
      "title": "精彩片段标题（10-20字）",
      "reason": "为什么这是精彩片段（50字以内）",
      "score": 0.95,
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "quote": "片段中最值得引用的一句话",
      "description": "片段内容的简要描述（100字以内）"
    }
  ],
  "topics": [
    {
      "start_seconds": 0.0,
      "end_seconds": 300.0,
      "topic": "话题名称",
      "description": "话题内容描述"
    }
  ],
  "memes_detected": ["检测到的梗1", "检测到的梗2"],
  "overall_mood": "整体氛围描述（如：欢乐、技术讨论、情感交流等）"
}
```

## 要求
1. 识别 3-5 个最精彩的片段
2. 评分基于：互动密度、内容价值、情绪强度、梗的出现
3. 每个片段时长建议 60-180 秒
4. 标题要吸引人，能准确反映内容
5. 确保输出有效的 JSON 格式

请开始分析："""
        
        return prompt

    def generate_title_prompt(
        self,
        highlight: Dict,
        streamer_template: Dict = None
    ) -> str:
        """生成标题生成的 AI 提示词"""
        
        template = streamer_template or self.streamer_template
        upload_template = template.get("upload_template", {})
        title_template = upload_template.get("title_template", "[{streamer}]{topic}")
        memes = template.get("memes", [])
        
        prompt = f"""你是一个专业的社交媒体标题专家。请为以下直播片段生成吸引人的标题。

## 主播信息
- 主播: {self.streamer_name}
- 风格: {template.get('style', {}).get('tone', '幽默风趣')}
- 梗: {', '.join(memes[:5]) if memes else '无'}

## 片段信息
- 开始时间: {self.seconds_to_time(highlight['start_seconds'])}
- 结束时间: {self.seconds_to_time(highlight['end_seconds'])}
- 时长: {highlight.get('duration_seconds', '未知')}秒
- 推荐标题: {highlight.get('title', '无')}
- 精彩原因: {highlight.get('reason', '无')}
- 金句引用: {highlight.get('quote', '无')}
- 关键词: {', '.join(highlight.get('keywords', []))}
- 描述: {highlight.get('description', '无')}

## 标题模板
参考格式: {title_template}

## 输出要求
生成 3 个标题选项：

1. **悬念型**: 制造好奇，吸引点击
2. **引用型**: 直接引用金句或对话
3. **话题型**: 突出话题/事件

每个标题要求：
- 长度: 15-30 字
- 包含主播名
- 吸引人但不标题党
- 适合 Bilibili 平台

## 输出格式
```json
{{
  "titles": [
    {{
      "type": "悬念型",
      "title": "标题内容",
      "reason": "为什么这个标题有效"
    }}
  ],
  "recommended": "最佳标题",
  "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"]
}
```

请生成标题："""
        
        return prompt

    def analyze_with_ai(self, subtitle_path: str) -> Dict:
        """
        使用 AI 分析字幕（主入口）
        
        此方法会：
        1. 解析字幕文件
        2. 准备分析数据
        3. 生成 AI 提示词
        4. 输出供 AI 处理的结构化数据
        
        Returns:
            {
                'metadata': {...},
                'ai_prompt': '...',  # 用于 AI 处理的提示词
                'structured_data': {...},  # 备用规则分析结果
                'output_file': '分析结果保存路径'
            }
        """
        print(f"\n🤖 AI字幕分析模块启动")
        print(f"   主播: {self.streamer_name}")
        print(f"   文件: {Path(subtitle_path).name}")
        
        # 1. 解析字幕
        subtitles = self.parse_srt(subtitle_path)
        print(f"   字幕条目: {len(subtitles)}")
        
        if not subtitles:
            return {"error": "无法解析字幕文件"}
        
        # 2. 准备 AI 分析数据
        analysis_data = self.prepare_ai_analysis_data(subtitles)
        
        # 3. 输出分析
        print(f"\n📊 分析数据准备完成:")
        print(f"   - 总时长: {analysis_data['metadata']['total_duration_display']}")
        print(f"   - 语义分段: {len(analysis_data['segments'])}")
        print(f"   - 密集时段: {len(analysis_data['dense_moments'])}")
        
        # 4. 保存分析数据
        output_path = Path(subtitle_path).with_suffix(".ai_analysis.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": analysis_data["metadata"],
                "ai_prompt": analysis_data["ai_prompt"],
                "segments": analysis_data["segments"],
                "dense_moments": analysis_data["dense_moments"]
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 分析数据已保存: {output_path}")
        print(f"\n{'='*60}")
        print("📝 AI 提示词（复制给 AI 分析）:")
        print(f"{'='*60}\n")
        print(analysis_data["ai_prompt"])
        print(f"\n{'='*60}")
        print("💡 使用方法: 将上述提示词发送给 AI，即可获得精彩片段分析结果")
        print("   AI 返回 JSON 结果后，可用 parse_ai_result() 方法解析")
        
        return {
            "metadata": analysis_data["metadata"],
            "ai_prompt": analysis_data["ai_prompt"],
            "segments": analysis_data["segments"],
            "dense_moments": analysis_data["dense_moments"],
            "output_file": str(output_path)
        }

    def parse_ai_result(self, ai_output: str, output_path: str = None) -> Dict:
        """
        解析 AI 返回的分析结果
        
        Args:
            ai_output: AI 返回的文本（通常是 JSON 格式）
            output_path: 可选，保存解析结果
        
        Returns:
            解析后的 Dict
        """
        # 尝试提取 JSON
        json_match = re.search(r'```json\s*(.+?)\s*```', ai_output, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                result = {"raw_output": ai_output}
        else:
            # 直接尝试解析
            try:
                result = json.loads(ai_output)
            except json.JSONDecodeError:
                result = {"raw_output": ai_output}
        
        # 格式化时间
        if "highlights" in result:
            for hl in result["highlights"]:
                hl["start_time"] = self.seconds_to_time(hl["start_seconds"])
                hl["end_time"] = self.seconds_to_time(hl["end_seconds"])
        
        if "topics" in result:
            for topic in result["topics"]:
                topic["time_range"] = f"{self.seconds_to_time(topic['start_seconds'])}-{self.seconds_to_time(topic['end_seconds'])}"
        
        # 保存结果
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ AI 分析结果已保存: {output_path}")
        
        return result

    def generate_titles_for_highlight(
        self,
        highlight: Dict,
        platform: str = "bilibili"
    ) -> Dict:
        """
        为精彩片段生成标题（使用 AI）
        
        Args:
            highlight: 精彩片段信息
            platform: 目标平台
        
        Returns:
            标题生成结果
        """
        prompt = self.generate_title_prompt(highlight, self.streamer_template)
        
        # 尝试解析 AI 返回的 JSON
        # （实际使用时，prompt 发送给 AI，返回结果用 parse_ai_result 解析）
        
        return {
            "input_highlight": highlight,
            "ai_prompt": prompt,
            "streamer": self.streamer_name,
            "platform": platform
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-powered 字幕分析")
    parser.add_argument("subtitle", help="字幕文件路径(.srt/.vtt)")
    parser.add_argument("--streamer", "-s", default="Unknown", help="主播名称")
    parser.add_argument("--template", "-t", help="主播模板 YAML 文件")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 加载模板（如果有）
    streamer_template = None
    if args.template:
        import yaml
        with open(args.template, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            streamer_template = data.get(args.streamer.lower(), data.get("streamers", {}).get(args.streamer.lower()))
    
    # 创建分析器
    analyzer = SubtitleAnalyzerAI(
        streamer_name=args.streamer,
        streamer_template=streamer_template
    )
    
    # 执行分析
    result = analyzer.analyze_with_ai(args.subtitle)
    
    if "error" in result:
        print(f"❌ 错误: {result['error']}")
        return
    
    # 保存输出
    output_path = args.output or result.get("output_file")
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存: {output_path}")


if __name__ == "__main__":
    main()
