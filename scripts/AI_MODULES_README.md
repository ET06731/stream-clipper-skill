# AI-powered 字幕分析模块

基于 AI 语义理解的字幕分析工具。

## 使用方法

```bash
# 基本分析
python scripts/analyze_subtitles_ai.py video.srt --streamer 主播名

# 指定模板
python scripts/analyze_subtitles_ai.py video.srt -s 主播名 -t config/streamer_templates.yaml
```

## 输出

1. **AI 提示词文件** - 复制发送给 AI
2. **分析数据文件** - 包含分段、密集时段等信息
3. **控制台输出** - 快速预览

## AI 返回结果处理

将 AI 返回的 JSON 结果保存后，使用 `parse_ai_result()` 方法解析：

```python
from analyze_subtitles_ai import SubtitleAnalyzerAI

analyzer = SubtitleAnalyzerAI(streamer_name="Neurosama")
result = analyzer.parse_ai_result(ai_output_json)
```

---

# AI-powered 标题生成模块

基于 AI 语义理解的标题生成工具。

## 使用方法

```bash
# 为精彩片段生成标题
python scripts/generate_title_ai.py highlight.json --streamer 主播名

# 使用模板
python scripts/generate_title_ai.py highlight.json -s 主播名 -t config/streamer_templates.yaml
```

## 标题类型

- **悬念型** - 制造好奇，吸引点击
- **引用型** - 直接引用金句
- **话题型** - 突出核心话题
- **搞笑型** - 强调翻车/搞笑
- **锐评型** - 突出毒舌观点
- **互动型** - 突出弹幕互动

## 输出

- **AI 提示词** - 发送给 AI
- **多版本标题** - 3-5 个选项
- **推荐标题** - AI 评分最高
- **标签建议** - 5-10 个标签
- **描述文案** - 视频简介

---

# AI-powered 智能切片脚本

整合完整工作流。

## 使用方法

### 方式1：完整流程

```bash
python scripts/smart_clipper_ai.py --subtitle video.srt --streamer Neurosama
```

### 方式2：继续流程（AI 分析后）

```bash
# 1. 将 AI 分析结果保存为 JSON
# 2. 继续生成标题
python scripts/smart_clipper_ai.py --subtitle video.srt --ai-result ai_output.json
```

### 方式3：一键完成

```bash
python scripts/smart_clipper_ai.py \
    --subtitle video.srt \
    --ai-result ai_output.json \
    --output ./clips \
    --clips 5
```

## 输出

- `*_ai_prompt.txt` - AI 分析提示词
- `*_clip_plan.json` - 最终切片方案
- 每个片段独立的标题提示词

## 切片方案结构

```json
{
  "streamer": "Neurosama",
  "total_clips": 5,
  "clips": [
    {
      "index": 1,
      "time_range": "00:15:00 - 00:18:30",
      "start_seconds": 900,
      "end_seconds": 1110,
      "highlight_title": "Vedal 修我！",
      "reason": "编程翻车名场面",
      "score": 0.95,
      "keywords": ["编程", "翻车", "Python"],
      "quote": "Vedal 修我！",
      "generated_titles": [...],
      "recommended_title": "【Neurosama】\"Vedal修我！\" AI编程翻车现场",
      "tags": ["neurosama", "编程", "翻车", "AI"],
      "description": "..."
    }
  ]
}
```

---

# 与 Claude Code 集成

在 Claude Code 中使用这些模块：

## 1. 分析字幕

```python
from scripts.analyze_subtitles_ai import SubtitleAnalyzerAI

analyzer = SubtitleAnalyzerAI(
    streamer_name="Neurosama",
    streamer_template=get_streamer_template("neurosama")
)

result = analyzer.analyze_with_ai("video.srt")
print(result["ai_prompt"])  # 复制给 AI
```

## 2. 生成标题

```python
from scripts.generate_title_ai import AITitleGenerator

generator = AITitleGenerator(
    streamer_name="Neurosama",
    streamer_template=get_streamer_template("neurosama")
)

result = generator.generate_titles(highlight, platform="bilibili")
print(result.description)  # 复制给 AI
```

## 3. 完整流程

```python
from scripts.smart_clipper_ai import SmartClipperAI

clipper = SmartClipperAI(
    streamer_name="Neurosama",
    template_path="config/streamer_templates.yaml"
)

# 完整流程
result = clipper.run_full_pipeline(
    subtitle_path="video.srt",
    num_highlights=5
)

# AI 分析后继续
result = clipper.continue_pipeline(
    subtitle_path="video.srt",
    ai_result_path="ai_output.json"
)
```

---

# AI 提示词示例

## 字幕分析提示词

```
你是一个专业的直播切片分析师。请分析以下直播字幕数据...

## 主播信息
- 主播名称: Neurosama
- 重点关注: 编程翻车、游戏高光、经典梗
- 主播梗: Vedal修我!, 我是AI不是人类, 足球梗

## 字幕内容
【00:00 - 00:05】Hello everyone, welcome to the stream...
【00:05 - 00:10】Okay, let's start coding...

## 分析任务
请识别 3-5 个最精彩的片段...
```

## 标题生成提示词

```
你是一个专业的社交媒体标题专家...

## 片段信息
- 金句引用: "Vedal 修我！"
- 关键词: 编程, 翻车, Python
- 描述: Neurosama 写代码时遭遇 bug，呼唤 Vedal 修理

## 输出要求
生成 3 个标题选项...
```

---

# 与旧版对比

| 特性 | 旧版 (规则) | 新版 (AI) |
|------|-------------|-----------|
| 话题检测 | 关键词匹配 | 语义理解 |
| 情绪分析 | 词频统计 | 深度情感理解 |
| 精彩片段 | 阈值规则 | 内容价值评估 |
| 标题生成 | 模板填充 | 创意生成 |
| 梗识别 | 预设列表 | 上下文理解 |

## 推荐使用场景

- **AI 推荐**: 质量优先，创意标题
- **规则 fallback**: 快速处理，简单场景
