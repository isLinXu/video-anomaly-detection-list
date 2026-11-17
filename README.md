# 🎬 Awesome Video Anomaly Detection

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
![Auto Update](https://img.shields.io/badge/Auto_Updated-Daily-blue)
![arXiv Papers](https://img.shields.io/badge/papers-0-green)
![Last Update](https://img.shields.io/badge/last_update-2026-11-18-orange)

> **自动跟踪视频异常检测（Video Anomaly Detection）领域的开源情报站。**

聚焦多条主线——**弱监督 VAD**、**半监督 VAD**、**全监督 VAD**、**开放世界 VAD**、**视频异常检索**、**视频异常理解（大模型方向）**—— 每天由 GitHub Actions 从 arXiv 与 GitHub 抓取、打分、去重、归类，自动更新论文清单、项目增速榜和周报。

<!-- stats:start -->
- **收录论文**: 26 篇
- **近 7 天新论文**: 0 篇
- **跟踪仓库**: 0 个
- **累计 star**: 0
<!-- stats:end -->

> 最后自动更新：2026-11-18

---

## 赛道地图

```
Video Anomaly Detection
├── 👁️ 弱监督 VAD (Weakly-Supervised)
│   └── 仅用视频级标签训练，检测帧/区域级异常
├── 🔍 半监督 VAD (Semi-Supervised)
│   └── 仅用正常视频训练，检测异常
├── 📊 全监督 VAD (Fully-Supervised)
│   └── 使用标注的异常+正常视频训练
├── 🌍 开放世界 VAD (Open-World)
│   └── 检测和描述未见过的异常类型
├── 🔎 视频异常检索 (Retrieval)
│   └── 基于自然语言查询检索异常片段
├── 🧠 视频异常理解 (Understanding)
│   └── 使用大视觉语言模型进行异常检测和解释
├── 🦴 基于骨架 VAD (Skeleton-based)
│   └── 利用人体骨架信息检测异常
├── 💬 提示学习 VAD (Prompt-based)
│   └── 使用 prompt learning 进行异常检测
├── 🔄 自监督 VAD (Self-Supervised)
│   └── 通过自监督预训练学习正常模式
├── 📚 综述论文 (Surveys)
│   └── 领域综述与调研
└── 🏋 数据集与基准 (Benchmarks)
    └── 新的数据集和基准
```

## 怎么用

你想…… | 去哪
- | -
30 秒知道最近在发生什么 | [📬 自动周报](docs/digest.md)
搞懂某条赛道的核心问题 | 各赛道文档，每篇开头有"必读"清单
找能直接跑的项目 | [🚀 项目雷达](docs/projects.md)，按 7 日 star 增速排
追最新论文 | 各赛道文档的论文表，按发布日期倒序

## 现在什么情况

（图表将在首次抓取后自动生成）

## 自动化是怎么跑的

```
        ┌──────────────────────────────────────────────────────────────┐
        │  GitHub Actions · 每天 01:30 UTC（也可手动触发）               │
        └───────────────────────────┬──────────────────────────────────┘
                                    ▼
   ┌────────────────┐   ┌────────────────────┐   ┌────────────────────┐
   │ fetch_arxiv.py │   │  track_github.py   │   │ update_metadata.py │
   │  arXiv 检索     │   │  仓库搜索 + star    │   │  统计 / 徽章 / 周报 │
   │  HF Daily 热度  │   │  快照 + 增速计算    │   │  跨文档计数         │
   └───────┬────────┘   └─────────┬──────────┘   └─────────┬──────────┘
           │  打分·归类·去重        │  历史累积              │
           ▼                      ▼                       ▼
   docs/*.md 标记表格        data/repos.json          README 数字
   data/papers.json         (每日 star 快照)          docs/digest.md
           │                      │
           └──────────┬───────────┘
                      ▼
          ┌───────────────────────┐
          │   render_charts.py    │  ← 把 JSON 直接画成 SVG
          │   横幅 / 趋势 / 占比 /  │     不截图、不存位图
          │   各赛道 sparkline     │     浅色深色各一套
          └───────────┬───────────┘
                      ▼
                 assets/*.svg
                      │
                      ▼
        有变更才 commit（幂等，重跑无副作用）
```

## 快速开始

```bash
git clone https://github.com/isLinXu/awesome-video-anomaly-detection.git
cd awesome-video-anomaly-detection
pip install -r requirements.txt

# 1) 抓取论文（首次建库建议回填半年）
python scripts/fetch_arxiv.py --days 180
#    日常增量：python scripts/fetch_arxiv.py

# 2) 跟踪仓库（建议带 token，未认证搜索限流 10 次/分钟）
GITHUB_TOKEN=ghp_xxx python scripts/track_github.py

# 3) 刷新统计、徽章与周报
python scripts/update_metadata.py

# 4) 重画图表
python scripts/render_charts.py

# 5) 自检
python scripts/check_md.py
```

## 想加一条赛道 / 换个方向？

全部逻辑由 [`config/taxonomy.yml`](config/taxonomy.yml) 驱动，改配置不用改代码。

## 贡献

欢迎三类贡献：**补经典论文**（带 arXiv ID）、**加仓库到种子列表**、**修分类关键词**。

## 免责声明

论文标题、作者、摘要来自 arXiv API，仓库 star 数来自 GitHub API，均保留原始来源链接。
自动归类基于关键词打分，**不保证每条都归到最优赛道**。
分数仅代表关键词相关度，不代表论文质量。

## License

MIT · 内容版权归各论文与项目作者所有。
