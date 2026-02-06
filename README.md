# Stream Clipper - 直播录制与切片智能剪辑工具

> 支持两种模式：1) 实时直播录制（30分钟自动分段 + 弹幕录制）；2) 录播回放切片（弹幕密度 + 语义分析）。基于主播个性化模板的高质量切片工具。

## 🎬 两种工作模式

### 模式一：直播实时录制 ⭐ 推荐

适合录制正在进行的直播，自动分段防止硬盘溢出。

```bash
# 完整工作流：录制 + 自动切片
python scripts/record_workflow.py "https://live.bilibili.com/55"

# 仅录制（30分钟分段）
python scripts/smart_record.py "https://live.bilibili.com/55" -t 30

# 录制完成后切片
python scripts/auto_clipper.py --list ./recordings/recorded_list_xxx.json
```

**核心特性**:
- ✅ **30分钟自动分段** - 防止硬盘溢出，方便管理
- ✅ **实时弹幕录制** - 同时保存弹幕内容和配置
- ✅ **优雅停止** - Ctrl+C 立即停止，不丢失数据
- ✅ **自动精彩片段切片** - 录制完成后自动生成3个推荐片段

### 模式二：录播回放切片

适合下载已结束的直播回放进行分析和切片。

```bash
# 下载回放
python scripts/download_stream.py "https://www.bilibili.com/video/BVxxxxx"

# 分析弹幕
python scripts/analyze_danmaku.py ./downloads/BVxxxxx.danmaku.xml

# 智能切片
python scripts/clip_and_burn.py --video ./downloads/BVxxxxx.mp4 --recommendations ./recommendations.json
```

---

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
- ✅ Bilibili 上传（biliup）
- ✅ 语义标题生成
- ✅ 简介自动生成（含主播链接）
- ✅ 批量上传

### 📺 8. 直播录制 (`scripts/smart_record.py`) ⭐ 新功能
- ✅ **30分钟自动分段** - 防止硬盘溢出
- ✅ **实时弹幕录制** - 同时保存弹幕配置
- ✅ **优雅停止** - Ctrl+C 不丢失数据
- ✅ **显示录制进度** - 实时百分比
- ✅ **生成录制列表** - JSON格式

### ✂️ 9. 自动切片 (`scripts/auto_clipper.py`) ⭐ 新功能
- ✅ **自动分析精彩片段** - 每段生成3个推荐
- ✅ **自动调用剪辑** - 无需手动操作
- ✅ **批量处理** - 处理所有录制分段
- ✅ **分类推荐** - 高能/搞笑/团战

### 🎯 10. 完整工作流 (`scripts/record_workflow.py`) ⭐ 新功能
- ✅ **一键录制+切片** - 完整自动化流程
- ✅ **交互式确认** - 录制完成后询问是否切片
- ✅ **状态保存** - 记录所有操作日志

## 📁 文件结构

```
stream-clipper/
├── SKILL.md                          ✅ 完整工作流程文档
├── README.md                         ✅ 项目说明
├── requirements.txt                  ✅ Python依赖
├── package.json                      ✅ npm配置（可选）
├── bin/
│   └── cli.js                        ✅ npm CLI入口
├── scripts/                          ✅ 核心脚本
│   ├── download_stream.py           ✅ 下载视频+弹幕+字幕
│   ├── analyze_danmaku.py           ✅ 弹幕密度分析
│   ├── analyze_semantic.py          ✅ 字幕语义分析
│   ├── smart_clipper.py             ✅ 智能切片决策
│   ├── streamer_template.py         ✅ 主播模板管理
│   ├── clip_and_burn.py             ✅ 视频剪辑和烧录
│   ├── upload_clip.py               ✅ 上传到B站
│   ├── smart_record.py              ✅ 🆕 智能分段录制
│   ├── auto_clipper.py              ✅ 🆕 自动精彩片段切片
│   ├── record_workflow.py           ✅ 🆕 完整录制工作流
│   ├── record_live.py               ✅ 🆕 基础直播录制
│   └── query_video_stats.py         ✅ 🆕 视频数据查询
├── config/                           ✅ 配置文件
│   └── streamer_templates.yaml      ✅ 主播模板配置
└── .gitignore                        ✅ Git忽略配置
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

### 安装

```bash
# 方式1: Python直接安装
pip install yt-dlp pyyaml requests biliup xmltodict

# 方式2: npm全局安装
npm install -g ET06731/stream-clipper-skill
```

### 使用方式

#### 方式A: 直播录制（推荐新手）

```bash
# 一键录制 + 自动切片
python scripts/record_workflow.py "https://live.bilibili.com/55"

# 录制过程:
# 1. 每30分钟自动分段
# 2. 同时录制弹幕
# 3. 显示实时进度
# 4. 录制完成后询问是否切片
```

#### 方式B: 录播切片

```bash
# 1. 下载回放
python scripts/download_stream.py "https://www.bilibili.com/video/BVxxxxx"

# 2. 分析弹幕
python scripts/analyze_danmaku.py ./downloads/BVxxxxx.danmaku.xml

# 3. 剪辑视频
python scripts/clip_and_burn.py \
    --video ./downloads/BVxxxxx.mp4 \
    --recommendations ./recommendations.json \
    --danmaku ./downloads/BVxxxxx.danmaku.xml

# 4. 上传到B站
python scripts/upload_clip.py ./clips --batch --template evil_neuro
```

#### 方式C: Python API

```python
# 直播录制
from scripts.smart_record import LiveRecorder
recorder = LiveRecorder(output_dir="./recordings", segment_minutes=30)
recorded_files = recorder.smart_record("https://live.bilibili.com/55")

# 自动切片
from scripts.auto_clipper import AutoClipper
clipper = AutoClipper("./clips_output")
clipper.process_all_segments(video_files=recorded_files)

# 录播下载
from scripts.download_stream import StreamDownloader
downloader = StreamDownloader()
result = downloader.download("https://www.bilibili.com/video/BVxxxxx")
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
