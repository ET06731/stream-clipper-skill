#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-powered 智能切片脚本
整合字幕分析、精彩片段识别、标题生成全流程
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_subtitles_ai import SubtitleAnalyzerAI
from generate_title_ai import AITitleGenerator


class SmartClipperAI:
    """
    AI-powered 智能切片器
    
    完整工作流：
    1. 解析字幕文件
    2. AI 分析精彩片段
    3. AI 生成标题
    4. 输出切片方案
    """

    def __init__(self, streamer_name: str = "Unknown", template_path: str = None):
        """
        初始化智能切片器
        
        Args:
            streamer_name: 主播名称
            template_path: 主播模板文件路径
        """
        self.streamer_name = streamer_name
        self.streamer_template = self._load_template(template_path)
        
        # 初始化子模块
        self.analyzer = SubtitleAnalyzerAI(
            streamer_name=streamer_name,
            streamer_template=self.streamer_template
        )
        
        self.title_generator = AITitleGenerator(
            streamer_name=streamer_name,
            streamer_template=self.streamer_template
        )

    def _load_template(self, template_path: str = None) -> Dict:
        """加载主播模板"""
        if not template_path:
            # 尝试默认路径
            default_path = Path(__file__).parent.parent / "config" / "streamer_templates.yaml"
            if default_path.exists():
                template_path = str(default_path)
            else:
                return {}
        
        if not Path(template_path).exists():
            return {}
        
        import yaml
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # 尝试获取主播模板
                streamers = data.get("streamers", {})
                # 尝试精确匹配
                key = self.streamer_name.lower().replace(" ", "_")
                return streamers.get(key, streamers.get(self.streamer_name, {}))
        except Exception:
            return {}

    def run_full_pipeline(
        self,
        subtitle_path: str,
        output_dir: str = None,
        num_highlights: int = 5,
        platform: str = "bilibili"
    ) -> Dict:
        """
        运行完整 AI 切片流程
        
        Args:
            subtitle_path: 字幕文件路径
            output_dir: 输出目录
            num_highlights: 生成的精彩片段数量
            platform: 目标平台
        
        Returns:
            完整分析结果
        """
        subtitle_path = Path(subtitle_path)
        
        print(f"\n{'='*60}")
        print(f"🤖 AI 智能切片流程启动")
        print(f"{'='*60}")
        print(f"   主播: {self.streamer_name}")
        print(f"   字幕: {subtitle_path.name}")
        print(f"   平台: {platform}")
        print(f"   目标: {num_highlights} 个精彩片段")
        
        output_dir = Path(output_dir) if output_dir else subtitle_path.parent / "ai_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: AI 字幕分析
        print(f"\n📊 Step 1: AI 字幕分析")
        print("-" * 40)
        
        analysis_result = self.analyzer.analyze_with_ai(str(subtitle_path))
        
        if "error" in analysis_result:
            return {"error": analysis_result["error"]}
        
        # 保存分析提示词
        prompt_file = output_dir / f"{subtitle_path.stem}_ai_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(analysis_result["ai_prompt"])
        print(f"   💾 AI 提示词已保存: {prompt_file}")
        
        # Step 2: 等待 AI 分析结果
        print(f"\n📝 Step 2: AI 分析结果输入")
        print("-" * 40)
        print(f"   ⚠️  请将 Step 1 生成的提示词发送给 AI")
        print(f"   📄 AI 返回分析结果后，保存到文件")
        print(f"\n   使用以下命令继续：")
        print(f"   python {Path(__file__).name} --subtitle {subtitle_path}")
        print(f"                 --ai-result <ai_output_json>")
        print(f"                 --output {output_dir}")
        
        # 生成继续命令示例
        continue_script = output_dir / "continue_pipeline.sh"
        with open(continue_script, "w", encoding="utf-8") as f:
            f.write(f'''#!/bin/bash
# 继续 AI 切片流程
# 1. 将 AI 返回的分析结果保存为 ai_result.json
# 2. 运行以下命令：

python "{Path(__file__).name}" \\
    --subtitle "{subtitle_path}" \\
    --ai-result ./ai_result.json \\
    --output ./
''')
        print(f"   📜 继续脚本已生成: {continue_script}")
        
        return {
            "step": "analysis_complete",
            "subtitle_file": str(subtitle_path),
            "ai_prompt_file": str(prompt_file),
            "output_dir": str(output_dir),
            "next_step": "请将 AI 返回的分析结果保存为 JSON 文件，然后运行继续命令"
        }

    def continue_pipeline(
        self,
        subtitle_path: str,
        ai_result_path: str = None,
        ai_result_json: str = None,
        output_dir: str = None,
        num_highlights: int = 5,
        platform: str = "bilibili"
    ) -> Dict:
        """
        继续切片流程（Step 2）
        
        Args:
            subtitle_path: 字幕文件路径
            ai_result_path: AI 分析结果文件路径
            ai_result_json: AI 分析结果 JSON 字符串
            output_dir: 输出目录
            num_highlights: 生成的精彩片段数量
            platform: 目标平台
        """
        subtitle_path = Path(subtitle_path)
        
        # Step 3: 解析 AI 分析结果
        print(f"\n📊 Step 3: 解析 AI 分析结果")
        print("-" * 40)
        
        if ai_result_path and Path(ai_result_path).exists():
            with open(ai_result_path, "r", encoding="utf-8") as f:
                ai_output = f.read()
        elif ai_result_json:
            ai_output = ai_result_json
        else:
            # 尝试从 .ai_analysis 目录读取
            analysis_dir = subtitle_path.parent / "ai_analysis"
            ai_result_file = analysis_dir / "ai_result.json"
            if ai_result_file.exists():
                with open(ai_result_file, "r", encoding="utf-8") as f:
                    ai_output = f.read()
            else:
                return {"error": "未找到 AI 分析结果"}
        
        # 解析 AI 返回的结果
        highlights = []
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'```json\s*(.+?)\s*```', ai_output, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(ai_output)
            
            highlights = result.get("highlights", [])[:num_highlights]
            
        except json.JSONDecodeError:
            # 手动解析（如果 AI 返回的是文本描述）
            print(f"   ⚠️  AI 返回格式不是标准 JSON")
            print(f"   📄 返回内容预览: {ai_output[:500]}...")
            
            # 尝试从文本中提取信息
            highlights = self._parse_text_result(ai_output)
        
        if not highlights:
            return {"error": "无法解析 AI 分析结果"}
        
        print(f"   ✅ 解析到 {len(highlights)} 个精彩片段")
        
        # Step 4: 生成标题
        print(f"\n📝 Step 4: AI 标题生成")
        print("-" * 40)
        
        output_dir = Path(output_dir) if output_dir else subtitle_path.parent / "ai_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        clips = []
        for i, highlight in enumerate(highlights, 1):
            print(f"\n   [{i}/{len(highlights)}] 处理片段...")
            
            # 确保时间格式正确
            if isinstance(highlight.get("start_seconds"), str):
                highlight["start_seconds"] = self._parse_time_to_seconds(highlight.get("start_time", "0:00"))
            if isinstance(highlight.get("end_seconds"), str):
                highlight["end_seconds"] = self._parse_time_to_seconds(highlight.get("end_time", "0:00"))
            
            # 生成标题
            title_result = self.title_generator.generate_titles(
                highlight,
                platform=platform,
                use_ai=True
            )
            
            # 输出标题生成提示词
            title_prompt_file = output_dir / f"clip_{i}_title_prompt.txt"
            with open(title_prompt_file, "w", encoding="utf-8") as f:
                f.write(title_result.description)
            
            print(f"       🎯 推荐标题: {title_result.recommended or '（请查看提示词文件）'}")
            print(f"       💾 标题提示词: {title_prompt_file}")
            
            clips.append({
                "index": i,
                "highlight": highlight,
                "title_result": {
                    "titles": [t.__dict__ for t in title_result.titles] if title_result.titles else [],
                    "recommended": title_result.recommended,
                    "prompt_file": str(title_prompt_file)
                },
                "tags": title_result.tags,
                "description": title_result.description
            })
        
        # Step 5: 生成切片方案
        print(f"\n📋 Step 5: 生成切片方案")
        print("-" * 40)
        
        # 构建最终方案
        final_plan = {
            "streamer": self.streamer_name,
            "subtitle_file": str(subtitle_path),
            "generated_at": datetime.now().isoformat(),
            "platform": platform,
            "total_clips": len(clips),
            "clips": []
        }
        
        for clip in clips:
            hl = clip["highlight"]
            final_plan["clips"].append({
                "index": clip["index"],
                "time_range": f"{self._format_time(hl.get('start_seconds', 0))} - {self._format_time(hl.get('end_seconds', 0))}",
                "start_seconds": hl.get("start_seconds"),
                "end_seconds": hl.get("end_seconds"),
                "duration_seconds": hl.get("end_seconds", 0) - hl.get("start_seconds", 0),
                "highlight_title": hl.get("title', '精彩片段"),
                "reason": hl.get("reason', ''),
                "score": hl.get("score', 0),
                "keywords": hl.get('keywords', []),
                "quote": hl.get('quote'),
                "generated_titles": clip["title_result"]["titles"],
                "recommended_title": clip["title_result"]["recommended"],
                "tags": clip["tags"],
                "description": clip["description"]
            })
        
        # 保存方案
        plan_file = output_dir / f"{subtitle_path.stem}_clip_plan.json"
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(final_plan, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ 切片方案已保存: {plan_file}")
        
        # 打印摘要
        print(f"\n{'='*60}")
        print(f"🎬 AI 智能切片完成!")
        print(f"{'='*60}")
        print(f"\n📊 生成 {final_plan['total_clips']} 个切片方案:")
        
        for clip in final_plan["clips"]:
            print(f"\n   [{clip['index']}] {clip['time_range']}")
            print(f"       ⭐ 推荐标题: {clip['recommended_title'] or '（查看标题提示词）'}")
            print(f"       📝 精彩原因: {clip['reason'][:50]}..." if len(clip['reason']) > 50 else f"       📝 精彩原因: {clip['reason']}")
            print(f"       🏷️  标签: {', '.join(clip['tags'][:3])}")
            print(f"       📂 详情: {plan_file}")
        
        print(f"\n💡 下一步:")
        print(f"   1. 查看切片方案文件: {plan_file}")
        print(f"   2. 使用标题提示词文件生成最终标题")
        print(f"   3. 运行 clip_and_burn.py 执行实际剪辑")
        
        return final_plan

    def _parse_time_to_seconds(self, time_str: str) -> float:
        """解析时间字符串为秒"""
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        parts = time_str.split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return float(parts[0])
        except:
            return 0

    def _format_time(self, seconds: float) -> str:
        """格式化秒为时间字符串"""
        if seconds is None:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _parse_text_result(self, text: str) -> List[Dict]:
        """从文本解析 AI 分析结果（fallback）"""
        highlights = []
        
        # 尝试提取时间信息
        time_patterns = [
            r"(\d{1,2}:\d{2})[-~–](\d{1,2}:\d{2})",
            r"(\d{1,2}:\d{2}:\d{2})[-~–](\d{1,2}:\d{2}:\d{2})",
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                highlights.append({
                    "start_time": match[0],
                    "end_time": match[1],
                    "title": "AI识别的精彩片段",
                    "reason": text[:100]
                })
        
        return highlights[:5]


def main():
    parser = argparse.ArgumentParser(description="AI-powered 智能切片")
    parser.add_argument("--subtitle", "-s", help="字幕文件路径")
    parser.add_argument("--ai-result", "-a", help="AI 分析结果 JSON 文件")
    parser.add_argument("--ai-json", help="AI 分析结果 JSON 字符串")
    parser.add_argument("--streamer", default="Unknown", help="主播名称")
    parser.add_argument("--template", "-t", help="主播模板文件")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--clips", "-c", type=int, default=5, help="生成切片数量")
    parser.add_argument("--platform", "-p", default="bilibili", help="目标平台")
    
    args = parser.parse_args()
    
    # 创建切片器
    clipper = SmartClipperAI(
        streamer_name=args.streamer,
        template_path=args.template
    )
    
    if args.subtitle:
        if args.ai_result or args.ai_json:
            # 继续流程
            result = clipper.continue_pipeline(
                subtitle_path=args.subtitle,
                ai_result_path=args.ai_result,
                ai_result_json=args.ai_json,
                output_dir=args.output,
                num_highlights=args.clips,
                platform=args.platform
            )
        else:
            # 开始流程
            result = clipper.run_full_pipeline(
                subtitle_path=args.subtitle,
                output_dir=args.output,
                num_highlights=args.clips,
                platform=args.platform
            )
    else:
        parser.print_help()
        print("\n💡 使用方法:")
        print("   1. 开始完整流程:")
        print("      python smart_clipper_ai.py --subtitle video.srt --streamer 主播名")
        print("\n   2. 继续流程（AI 分析后）:")
        print("      python smart_clipper_ai.py --subtitle video.srt --ai-result ai_output.json")
        print("\n   3. 一键完成（已有 AI 分析结果）:")
        print("      python smart_clipper_ai.py --subtitle video.srt --ai-result ai_output.json --output ./")
    
    if "error" in result:
        print(f"\n❌ 错误: {result['error']}")


if __name__ == "__main__":
    main()
