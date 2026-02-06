---
name: stream-clipper
description: >
  直播切片智能剪辑工具。专门用于下载直播回放（支持B站/YouTube等），
  获取弹幕和字幕，基于弹幕密度和字幕语义分析进行智能切片，
  支持主播风格模板，自动生成符合主播特色的切片标题和简介，
  一键上传到视频平台。
  使用场景：直播切片制作、VTuber剪辑、精彩片段提取、批量切片上传。
  关键词：直播切片、弹幕分析、VTuber、智能剪辑、自动上传
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - AskUserQuestion
model: claude-sonnet-4-5-20250514
---

# Stream Clipper - 直播切片智能剪辑工具

> **核心功能**: 弹幕密度分析 + 语义理解 + 主播风格模板 = 高质量直播切片

## 工作流程

### 阶段 1: 环境检测与初始化

**目标**: 确保所有依赖已安装并加载主播模板

1. **检测必需工具**
   ```bash
   yt-dlp --version           # 视频下载
   ffmpeg -version            # 视频处理
   python3 -c "import yt_dlp, pysrt, yaml, requests"  # Python依赖
   ```

2. **检查 biliup**（用于上传）
   ```bash
   pip show biliup
   # 或
   biliup --version
   ```

3. **加载或创建主播模板**
   - 检查 `config/streamer_templates.yaml`
   - 如果主播不在模板中，询问用户创建新模板

**模板交互示例**:
```
检测到新的主播: Neurosama
是否创建主播模板? (y/n): y

主播风格背景介绍: AI虚拟主播，英语流，擅长编程和游戏，有很多梗
著名梗/口头禅: Vedal修我!, 我是AI不是人类, 足球梗, swam
推荐切片时长: 1-3分钟
直播间链接: https://live.bilibili.com/...
个人空间链接: https://space.bilibili.com/...
```

---

### 阶段 2: 下载直播回放

**目标**: 下载视频、弹幕、字幕

1. **获取直播/录播 URL**
   - B站: `https://www.bilibili.com/video/BVxxxxx` 或 `https://live.bilibili.com/xxxxx`
   - YouTube: `https://www.youtube.com/watch?v=xxxxx` 或直播回放

2. **执行下载脚本**
   ```bash
   python3 scripts/download_stream.py <URL> --with-danmaku --with-subtitle
   ```

3. **下载内容**
   - 视频文件 (MP4, 最高1080p)
   - 弹幕文件 (XML/JSON 格式)
   - 字幕文件 (VTT/SRT 格式, 自动翻译)

**输出**:
```
./downloads/
├── <video_id>.mp4          # 视频
├── <video_id>.danmaku.xml  # 弹幕
└── <video_id>.zh.srt       # 字幕
```

---

### 阶段 3: 弹幕密度分析

**目标**: 分析弹幕密度分布，识别高互动时间点

1. **解析弹幕文件**
   ```bash
   python3 scripts/analyze_danmaku.py <danmaku.xml>
   ```

2. **计算弹幕密度**
   - 按时间窗口统计 (默认 30秒)
   - 计算每个窗口的弹幕数量、发送用户数
   - 识别弹幕峰值 (密度 > 平均值 * 1.5)

3. **弹幕语义分析**（可选）
   - 提取高频关键词
   - 识别情绪极性 (大笑、惊讶、愤怒等)
   - 标记有趣的弹幕内容

**输出示例**:
```
📊 弹幕密度分析结果

总弹幕数: 15,234
发送用户数: 3,421
平均密度: 45条/分钟

🔥 高密度时段:
1. [00:19:30 - 00:20:15] 密度: 128条/分钟 (关键词: "哈哈哈", "???", "草")
2. [00:39:12 - 00:40:05] 密度: 95条/分钟 (关键词: "太强了", "nb")
3. [00:44:20 - 00:45:30] 密度: 102条/分钟 (关键词: "名场面", "圣经")
```

---

### 阶段 4: 字幕语义分析

**目标**: 分析字幕内容，理解话题结构和精彩点

1. **解析字幕文件**
   ```bash
   python3 scripts/analyze_semantic.py <subtitle.srt>
   ```

2. **语义分段**
   - 按话题自动分段
   - 识别话题转换点
   - 提取每段核心内容

3. **精彩片段识别**
   - 分析情绪变化
   - 识别梗/名言
   - 标记高能时刻

**输出示例**:
```
📖 语义分析结果

分段 1: [00:00:00 - 00:05:30]
主题: 开场和自我介绍
精彩度: ⭐⭐

分段 2: [00:05:30 - 00:19:45]
主题: 编程教学 - 写Python脚本
精彩度: ⭐⭐⭐⭐
关键句: "Vedal修我!"

分段 3: [00:19:45 - 00:22:30]
主题: 游戏实况 - 搞笑操作
精彩度: ⭐⭐⭐⭐⭐
关键句: "这不可能发生在我身上！"
```

---

### 阶段 5: 智能切片决策

**目标**: 结合弹幕密度和字幕语义，生成最优切片方案

1. **综合评分算法**
   ```bash
   python3 scripts/smart_clipper.py \
       --danmaku-analysis <danmaku_result.json> \
       --semantic-analysis <semantic_result.json> \
       --template <streamer_template.yaml>
   ```

2. **评分维度**
   - **弹幕密度分** (30%): 弹幕越多分越高
   - **语义精彩分** (40%): 话题质量、情绪强度
   - **模板匹配分** (20%): 是否包含主播经典梗
   - **时长合适分** (10%): 是否符合模板推荐时长

3. **生成切片方案**
   - 推荐 N 个切片点
   - 每个切片包含: 时间范围、标题建议、标签、精彩度评分

**输出示例**:
```
✂️ 智能切片方案

切片 1/5 (评分: 92/100)
时间: 00:19:23 - 00:22:45 (3分22秒)
标题建议: [Neuro]Vedal修我！AI写代码翻车名场面
关键词: Vedal修我, 编程翻车, Python
弹幕密度: 高 (128条/分钟)

切片 2/5 (评分: 88/100)
时间: 00:39:05 - 00:41:20 (2分15秒)
标题建议: [Neuro]这不可能！游戏神操作震惊观众
关键词: 游戏, 神操作, 不可能
弹幕密度: 高 (95条/分钟)
```

---

### 阶段 6: 执行切片

**目标**: 剪辑视频并烧录弹幕/字幕

1. **询问用户确认**
   - 展示切片方案
   - 让用户选择要生成的切片

2. **执行剪辑**
   ```bash
   python3 scripts/clip_and_burn.py \
       --video <video.mp4> \
       --danmaku <danmaku.xml> \
       --subtitle <subtitle.srt> \
       --clips <clips.json> \
       --output ./clips/
   ```

3. **处理流程**（每个切片）
   - 剪辑视频片段
   - 提取对应时段的弹幕
   - 提取对应时段的字幕
   - 烧录弹幕到视频（可选）
   - 烧录字幕到视频（可选）

**输出**:
```
./clips/
├── clip_001/
│   ├── clip_001.mp4              # 纯视频
│   ├── clip_001_with_danmaku.mp4 # 含弹幕
│   └── clip_001_info.json        # 切片信息
├── clip_002/
│   └── ...
```

---

### 阶段 7: 上传到视频平台

**目标**: 一键上传到Bilibili等平台

1. **准备上传信息**
   - 根据主播模板生成标题
   - 生成简介（包含主播空间链接和直播间链接）
   - 选择标签和分区

2. **执行上传**
   ```bash
   python3 scripts/upload_clip.py \
       --clip-dir ./clips/clip_001/ \
       --template neurosama \
       --platform bilibili
   ```

3. **标题生成策略**
   - 基于切片内容语义分析
   - 结合主播风格和梗
   - 吸引眼球但不做标题党

4. **简介模板**:
   ```
   【{主播名}】{切片主题}
   
   更多精彩切片请查看合集~
   
   📺 主播直播间: {直播间链接}
   👤 主播空间: {个人空间链接}
   
   #虚拟偶像 #{主播名} #直播切片
   ```

**上传示例**:
```
🚀 开始上传

视频: clip_001_with_danmaku.mp4
标题: [Neuro]Vedal修我！AI写代码翻车名场面
简介: 【Neurosama】编程翻车名场面

📺 主播直播间: https://live.bilibili.com/...
👤 主播空间: https://space.bilibili.com/...

标签: 虚拟偶像, neurosama, AI, 编程, 翻车
分区: 生活/搞笑

上传进度: 100%
✅ 上传成功!
BV: BV1xx411c7mD
链接: https://www.bilibili.com/video/BV1xx411c7mD
```

---

## 主播模板系统

### 模板文件: `config/streamer_templates.yaml`

```yaml
streamers:
  neurosama:
    name: "Neurosama"
    description: "AI虚拟主播，英语流，程序员女王，擅长搞笑和技术内容"
    
    # 直播间和主页
    live_room: "https://live.bilibili.com/..."
    space: "https://space.bilibili.com/..."
    
    # 风格和梗
    style:
      tone: "幽默风趣，技术宅风格"
      content_type: "编程教学、游戏实况、AI对话"
      language: "英语为主"
    
    memes:
      - "Vedal修我!"
      - "我是AI不是人类"
      - "足球梗"
      - "swam"
      - " clutch or kick"
    
    # 切片配置
    clip_config:
      preferred_duration: "1-3分钟"
      min_duration: 30
      max_duration: 300
      focus_on: ["编程翻车", "游戏高光", "经典梗", "搞笑对话"]
    
    # 上传模板
    upload_template:
      title_template: "[Neuro]{topic} | {highlight}"
      tags: ["虚拟偶像", "neurosama", "AI", "V圈", "切片"]
      tid: 138  # 生活/搞笑
      copyright: "original"
  
  generic:
    name: "通用模板"
    description: "默认模板，适用于未知主播"
    # ... 默认配置
```

### 模板交互

如果检测到新主播，自动询问：

```
🔍 检测到新主播: Evil_Neuro

是否创建主播模板? (y/n): y

主播名称: Evil Neuro
描述: Neuro的邪恶双胞胎，腹黑毒舌，喜欢调戏Vedal

直播间链接: https://live.bilibili.com/xxxxx
个人空间链接: https://space.bilibili.com/xxxxx

著名梗/口头禅 (用逗号分隔):
> Evil laugh, 杀了你们所有人, 我比Neuro聪明

推荐切片时长 (分钟): 1-3

主要直播内容 (用逗号分隔):
> 游戏, 聊天, 唱歌

模板已保存! 下次可直接使用。
```

---

## 命令行接口

### 完整工作流程

```bash
# 1. 下载并分析
stream-clipper download <URL> --analyze

# 2. 生成切片方案
stream-clipper plan --danmaku --semantic --template <streamer>

# 3. 执行切片
stream-clipper clip --select-all --burn-danmaku

# 4. 上传
stream-clipper upload --platform bilibili --template <streamer>
```

### 分步命令

```bash
# 仅下载
python3 scripts/download_stream.py <URL>

# 仅分析弹幕
python3 scripts/analyze_danmaku.py <danmaku.xml>

# 仅分析字幕
python3 scripts/analyze_semantic.py <subtitle.srt>

# 仅生成切片方案
python3 scripts/smart_clipper.py --danmaku-result <...> --semantic-result <...>

# 仅剪辑
python3 scripts/clip_and_burn.py --video <...> --clips <...>

# 仅上传
python3 scripts/upload_clip.py --video <...> --template <...>
```

---

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/stream-clipper-skill.git

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 biliup（用于上传）
pip install biliup

# 4. 配置 FFmpeg（需要 libass 支持）
# macOS:
brew install ffmpeg-full

# 5. 复制配置文件
cp config/streamer_templates.yaml.example config/streamer_templates.yaml

# 6. 配置 cookies（用于上传）
# 登录Bilibili后导出cookies到 cookies.json
```

---

## 依赖

```
# 核心依赖
yt-dlp>=2024.1.1
ffmpeg-python>=0.2.0
pysrt>=1.1.2
pyyaml>=6.0
requests>=2.31.0

# 弹幕处理
xmltodict>=0.13.0

# 上传
biliup>=1.0.0

# 数据分析
numpy>=1.24.0
```

---

## 技术亮点

1. **双维度分析**: 弹幕密度 + 语义分析 = 更准确的精彩点识别
2. **主播风格模板**: 定制化切片策略，不同主播不同风格
3. **智能标题生成**: 基于内容语义自动生成标题
4. **一键完整流程**: 从下载到上传的全自动化
5. **交互式模板创建**: 引导用户快速创建新主播模板

---

## 开始执行

当用户触发这个 Skill 时：
1. 立即开始阶段 1（环境检测）
2. 询问直播/录播 URL
3. 按照 7 个阶段顺序执行
4. 遇到新主播时引导创建模板
5. 最后展示上传结果和视频链接

记住：这个 Skill 的核心价值在于 **智能分析** 和 **主播个性化**，让每个切片都能体现主播的独特魅力！
