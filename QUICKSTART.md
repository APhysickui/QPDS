# QPDS 快速启动指南

## 🚀 5分钟快速开始

### 前提条件
- Python 3.8+
- Node.js 14+ (可选，用于前端)
- Git

### 方法一：本地运行（推荐初学者）

1. **克隆项目**
```bash
git clone https://github.com/yourusername/QPDS.git
cd QPDS
```

2. **安装Python依赖**
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

3. **启动后端API**
```bash
python backend/api/app.py
```
API将在 http://localhost:5000 启动

4. **打开前端界面**
直接在浏览器中打开 `frontend/index.html` 文件

### 方法二：使用Docker（推荐生产环境）

1. **安装Docker和Docker Compose**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **启动所有服务**
```bash
docker-compose up
```

3. **访问应用**
   - API: http://localhost:5000
   - 前端: http://localhost:3000

### 方法三：开发模式

1. **后端开发**
```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8

# 运行测试
pytest tests/

# 代码格式化
black backend/

# 代码检查
flake8 backend/
```

2. **前端开发**
```bash
cd frontend
npm install
npm run dev
```

## 🎮 使用示例

### 1. 计算手牌胜率

```python
import requests

response = requests.post('http://localhost:5000/api/get_equity', json={
    'hero_cards': ['As', 'Kh'],
    'board': ['Qd', 'Jc', 'Ts'],
    'villain_range': 'AA,KK,QQ,AKs',
    'iterations': 10000
})

print(f"胜率: {response.json()['win_percentage']:.1f}%")
```

### 2. 获取决策建议

```python
response = requests.post('http://localhost:5000/api/get_recommendation', json={
    'hero_cards': ['As', 'Kh'],
    'board': ['Qd', 'Jc', 'Ts'],
    'pot_size': 100,
    'to_call': 20,
    'hero_stack': 500,
    'villain_stack': 450,
    'position': 'BTN',
    'street': 'FLOP',
    'risk_preference': 5
})

data = response.json()
print(f"建议动作: {data['action']}")
print(f"解释: {data['explanation']}")
```

## 🔧 配置说明

### 环境变量
创建 `.env` 文件：
```
DEBUG=false
PORT=5000
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/qpds
```

### 风险偏好设置
- 0 = 极度保守（只在极高胜率时行动）
- 5 = 中性（标准GTO策略）
- 10 = 极度激进（频繁诈唬和激进打法）

## 📊 核心功能

### 1. 手牌评估
- 7张牌快速评估
- 手牌强度百分位
- 听牌识别

### 2. 胜率计算
- 蒙特卡洛模拟
- 对手范围分析
- 多人底池支持

### 3. 因子分析
- 底池赔率（Pot Odds）
- 隐含赔率（Implied Odds）
- 位置优势（Position Factor）
- 筹码深度比（SPR）

### 4. 决策引擎
- 基于EV的决策
- 风险偏好调整
- 决策解释系统

## 🐛 常见问题

### Q: 后端无法启动
A: 确保已激活虚拟环境并安装所有依赖：
```bash
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### Q: 前端无法连接后端
A: 检查：
1. 后端是否在运行（http://localhost:5000/health）
2. 浏览器控制台是否有CORS错误
3. 防火墙设置

### Q: 计算速度慢
A: 可以：
1. 减少蒙特卡洛迭代次数（iterations参数）
2. 使用Redis缓存
3. 升级到更快的CPU

## 📈 性能优化

### 缓存配置
```python
# 使用Redis缓存
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
}
```

### 并行计算
```python
# 启用多线程
EQUITY_CALCULATOR_CONFIG = {
    'USE_MULTIPROCESSING': True,
    'MAX_WORKERS': 4
}
```

## 🤝 获取帮助

- 📖 [完整文档](./docs/)
- 🐛 [报告问题](https://github.com/yourusername/QPDS/issues)
- 💬 [讨论区](https://github.com/yourusername/QPDS/discussions)
- 📧 联系作者：[https://akuiro24.xyz/](https://akuiro24.xyz/)

## 📝 开发路线图

### 已完成 ✅
- [x] 核心手牌评估器
- [x] 胜率计算器
- [x] 因子引擎
- [x] 决策引擎
- [x] REST API
- [x] 基础Web界面

### 进行中 🚧
- [ ] 手牌历史解析器
- [ ] 回测框架
- [ ] 对手建模

### 计划中 📋
- [ ] 机器学习集成
- [ ] GTO求解器
- [ ] 实时适应系统
- [ ] 移动应用

---

**祝你在牌桌上好运！** 🍀

*记住：QPDS是教育工具，使用前请查看平台政策。*