# Stream Clipper - 直播切片智能剪辑工具

> 基于弹幕密度和字幕语义分析的直播切片工具，支持主播个性化模板

## ✅ 已完成的核心功能

### 📥 1. 智能下载 (`scripts/download_stream.py`)
- ✅ 支持 Bilibili 和 YouTube 平台
- ✅ 同时下载视频、弹幕(XML)、字幕(SRT)
- ✅ 自动保存元数据
- ✅ 支持 BV 号和直播间链接

### 📊 2. 弹幕分析 (`scripts/analyze_danmaku.py`)
- ✅ 解析 B站弹幕 XML 格式
- ✅ 计算弹幕密度分布（30秒窗口）
- ✅ 识别高密度时段
- ✅ 提取高频关键词
- ✅ 输出 JSON 分析结果

### 📝 3. 语义分析 (`scripts/analyze_semantic.py`)
- ✅ 解析 SRT 字幕文件
- ✅ 按话题自动分段
- ✅ 识别兴奋度评分（1-5）
- ✅ 提取关键语录/名言
- ✅ 提取关键词

### 🧠 4. 智能切片 (`scripts/smart_clipper.py`)
- ✅ 综合评分算法：
  - 弹幕密度（30%）
  - 语义质量（40%）
  - 模板匹配（20%）
  - 时长合适（10%）
- ✅ 自动生成切片标题
- ✅ 输出推荐 JSON

### 👤 5. 主播模板 (`scripts/streamer_template.py`)
- ✅ YAML 模板配置
- ✅ 交互式模板创建
- ✅ 支持风格、梗、切片配置
- ✅ 上传模板设置

### 🎬 6. 视频剪辑 (`scripts/clip_and_burn.py`)
- ⏳ FFmpeg 精确剪辑
- ⏳ 弹幕烧录（需 ASS 转换）
- ⏳ 字幕烧录
- ⏳ 批量处理

### 🚀 7. 上传模块 (`scripts/upload_clip.py`)
- ⏳ Bilibili 上传（biliup）
- ⏳ 语义标题生成
- ⏳ 简介自动生成（含主播链接）
- ⏳ 批量上传

## 📁 文件结构

```
stream-clipper/
├── SKILL.md                          ✅ 完整工作流程文档
├── README.md                         ✅ 项目说明
├── requirements.txt                  ✅ Python依赖
├── scripts/                          ✅ 核心脚本
│   ├── download_stream.py           - 下载视频+弹幕+字幕
│   ├── analyze_danmaku.py           - 弹幕密度分析
│   ├── analyze_semantic.py          - 字幕语义分析
│   ├── smart_clipper.py             - 智能切片决策
│   ├── streamer_template.py         - 主播模板管理
│   ├── clip_and_burn.py             - 视频剪辑和烧录
│   └── upload_clip.py               - 上传到B站
└── config/                           ✅ 配置文件
    └── streamer_templates.yaml      - 主播模板配置
```

**配置说明**:
- `config/streamer_templates.yaml` - 存放所有主播模板和上传配置
stream-clipper/
├── SKILL.md                          ✅ 完整工作流程
├── README.md                         ✅ 项目说明
├── scripts/
│   ├── download_stream.py           ✅ 下载模块
│   ├── analyze_danmaku.py           ✅ 弹幕分析
│   ├── analyze_semantic.py          ✅ 语义分析
│   ├── smart_clipper.py             ✅ 智能切片
│   ├── streamer_template.py         ✅ 模板管理
│   ├── clip_and_burn.py             ⏳ 剪辑烧录
│   └── upload_clip.py               ⏳ 上传模块
├── config/
│   └── streamer_templates.yaml      ✅ 模板配置
└── requirements.txt                 ⏳ 依赖列表
```

## 🚀 快速开始

### 安装依赖

```bash
pip install yt-dlp pyyaml requests biliup xmltodict
```

### 基本使用流程

```python
# 1. 下载直播
from scripts.download_stream import StreamDownloader
downloader = StreamDownloader()
result = downloader.download("https://www.bilibili.com/video/BVxxxxx")

# 2. 分析弹幕
from scripts.analyze_danmaku import DanmakuAnalyzer
analyzer = DanmakuAnalyzer()
danmaku_result = analyzer.analyze(result['danmaku_path'])

# 3. 分析语义
from scripts.analyze_semantic import SemanticAnalyzer
semantic_analyzer = SemanticAnalyzer()
semantic_result = semantic_analyzer.analyze(result['subtitle_path'])

# 4. 智能切片
from scripts.smart_clipper import SmartClipper
clipper = SmartClipper()
recommendations = clipper.generate_recommendations(
    'danmaku_analysis.json',
    'semantic_analysis.json'
)

# 5. 后续步骤（待完成）
# clip_and_burn()
# upload()
```

## 🎯 核心特性

1. **弹幕密度分析** - 识别高互动时间点
2. **语义分析** - 理解内容结构和精彩点
3. **双维度切片** - 综合评分生成最优切片
4. **主播模板** - 个性化风格配置
5. **智能上传** - 自动生成含主播链接的标题和简介

## 📖 完整工作流程

详见 `SKILL.md`，包含7个阶段：
1. 环境检测与初始化
2. 下载直播回放（视频+弹幕+字幕）
3. 弹幕密度分析
4. 字幕语义分析
5. 智能切片决策
6. 执行切片和烧录
7. 上传到视频平台

## 📝 主播模板配置示例

```yaml
streamers:
  neurosama:
    name: "Neurosama"
    description: "AI虚拟主播"
    memes: ["Vedal修我!", "I'm an AI"]
    clip_config:
      preferred_duration: "1-3分钟"
      min_duration: 45
      max_duration: 300
    upload_template:
      title_template: "[Neuro]{topic}"
      tags: ["虚拟偶像", "AI"]
```

## ⚠️ 注意事项

- 弹幕下载仅支持 Bilibili
- 需要配置 FFmpeg（带 libass 支持）用于字幕烧录
- 上传需要配置 cookies.json
- 某些模块可能需要根据实际使用调整

## 📚 参考

- 参考项目: YouTube-clipper-skill
- B站弹幕 API
- biliup 文档

## 作者

基于 YouTube-clipper-skill 改进和扩展
