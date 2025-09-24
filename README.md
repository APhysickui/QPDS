# QPDS - Quantitative Poker Decision System
## 量化扑克决策系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

QPDS 旨在把量化投资思维引入德州扑克决策：实时整理底牌、公共牌、底池与筹码信息，计算关键因子，给出带解释的行动建议。前端提供简洁的双语交互界面，后端由 Flask 驱动，核心算法模块独立封装，便于扩展与复用。

## 🎯 项目亮点
- **交互式 UI**：在浏览器中直接选择牌面、调整底池/筹码与风险偏好，实时查看输入摘要。
- **多因子决策引擎**：整合胜率、底池赔率、SPR、听牌与位置等指标，产出包含信心度与解释的推荐动作。
- **双语支持**：界面、提示与错误信息可在中文/英文之间即时切换。
- **模块化核心**：`backend/core` 拆分为评估器、因子引擎、决策引擎等组件，可单独在脚本或测试中调用。
- **快速启动脚本**：`run.py` 自动创建虚拟环境、安装依赖并启动后端，适合即开即用。

## 🏗️ 系统结构
```text
QPDS/
├── backend/
│   ├── api/                 # Flask 入口与路由
│   ├── core/                # 牌力评估、权益计算、因子/决策引擎
│   ├── models/              # 结构体与序列化模型
│   ├── utils/               # 辅助函数与工具
│   └── config/              # 配置与常量
├── frontend/
│   ├── index.html           # 纯 HTML/JS 前端界面
│   └── package.json         # 未来重构 Vue/Vite 的占位配置
├── data/                    # 示例数据与手牌记录
├── docs/                    # 需求、设计与笔记
├── tests/                   # pytest 单元测试
├── run.py                   # 快速启动脚本
└── requirements.txt         # Python 依赖
```

## ⚙️ 快速开始
### 方式一：使用一键脚本（推荐）
```bash
python3 run.py
```
脚本会：
1. 检查/创建虚拟环境 `venv/`
2. 自动安装 `requirements.txt`
3. 启动后端 API（默认 http://localhost:5000 ）

随后在浏览器打开 `frontend/index.html` 即可使用界面。脚本运行的终端窗口保持开启，按 `Ctrl+C` 可随时停止。

### 方式二：手动操作
```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
python -m pip install -r requirements.txt
python -m backend.api.app         # 启动后端（默认端口 8080）
```
前端仍然通过直接打开 `frontend/index.html` 访问。

## 💡 核心功能
### 前端交互
- 牌堆选择器支持自动灰化已用卡牌、点击移除等操作。
- 阶段（翻前/翻牌/转牌/河牌）切换会限制公共牌数量。
- 底池、需要跟注、双方筹码、风险滑块等输入实时汇总展示。
- 错误提示本地化，指导用户补全必需信息。

### 后端服务
- `POST /api/get_recommendation`：基于当前局面返回行动、金额、期望值与解释。
- `POST /api/get_equity`：对给定牌面与范围进行胜率模拟。
- `GET /health`：健康检查。
- 响应中附带完整因子明细，便于前端或其他系统展示。

### 因子体系（部分）
| 因子 | 含义 | 取值范围 |
| ---- | ---- | -------- |
| `hand_strength` | 当前牌力强度 | 0 ~ 1 |
| `equity` | 对手范围下的胜率 | 0 ~ 1 |
| `pot_odds` | 跟注所需胜率 | 0 ~ 1 |
| `stack_to_pot_ratio` | 有效筹码 / 底池 | 0 ~ ∞ |
| `fold_equity` | 估计对手弃牌率 | 0 ~ 1 |
| `pot_commitment` | 底池投入度 | 0 ~ 1 |

## 🧪 测试
```bash
source venv/bin/activate
pytest
```
测试目录覆盖因子引擎、权益计算等核心逻辑。可使用 `pytest -k factor` 等子集命令按需运行。

## 🛠️ 常见问题
- **依赖安装失败（例如 LightGBM 构建错误）**：脚本会自动升级 pip 并安装最新版二进制轮子；若仍失败，可手动执行 `python -m pip install lightgbm` 查看详细日志。
- **前端看不到结果**：确认后端已启动，浏览器 Console 无跨域/网络错误，或检查 `frontend/index.html` 内的 `API_URL` 是否与后端端口一致。

## 🗺️ Roadmap
- [x] 双语静态前端 & 交互式牌局输入
- [x] 因子计算 + 决策引擎 REST API
- [ ] 手牌历史解析与回放
- [ ] 对手建模参数输入
- [ ] 数据持久化与回测模块
- [ ] 前端框架化（Vue/Vite）与组件重构

## 📄 License
本项目基于 MIT 协议开源，详情参见 [LICENSE](LICENSE)。

## 🙏 Acknowledgments
- Poker hand evaluator algorithms based on Cactus Kev's evaluator
- Monte Carlo methods inspired by PokerStove
- Quantitative framework adapted from modern portfolio theory

## 📧 Contact

For questions or suggestions, please open an issue on GitHub.

or contact with me ，my blog website address is
https://akuiro24.xyz/

---

**Disclaimer**: This tool is for educational purposes. Always check platform policies before using poker assistance tools.
