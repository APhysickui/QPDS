# GitHub Pages + Render 部署全流程教学

借助 GitHub Pages 托管前端静态站点、Render 托管 Flask 后端，就能把 QPDS 变成一个在线可访问的系统。本文提供从零开始的完整步骤，确保你在部署过程中不会漏掉关键环节。

---

## 0. 前置准备
在开始之前，请确认：

- 拥有一个 GitHub 账号，并已经 fork/克隆了本项目。
- 本地已经完成所有需要的代码修改，并且可以在本地成功运行（`python3 run.py` + 打开 `frontend/index.html`）。
- 了解基础的 Git 操作（提交、推送）。
- 拥有一个 Render 账户（免费注册即可，https://render.com）。

> **提示**：部署前务必将本地修改推送到 GitHub 仓库，否则 Render 和 GitHub Pages 无法获取最新代码。

---

## 1. 准备并推送代码仓库

1. **Fork 或创建仓库**：如果尚未 fork，请在 GitHub 上点击 “Fork” 将仓库复制到自己的账号下。
2. **克隆到本地**：
   ```bash
   git clone https://github.com/<你的用户名>/QPDS.git
   cd QPDS
   ```
3. **确认分支**：默认分支建议使用 `main`。若你使用其它分支，请在后续 GitHub Actions 配置中同步修改分支名。
4. **提交更改**：将改动提交并推送到远程仓库。
   ```bash
   git add .
   git commit -m "chore: prepare deployment"
   git push origin main
   ```

---

## 2. 在 Render 上部署后端 API
Render 会根据项目根目录的 `render.yaml` 自动创建服务。

1. 登录 Render 后，在控制台点击 **New +** → **Blueprint**。
2. 选择关联刚才推送代码的 GitHub 仓库，并选定部署分支（默认为 `main`）。
3. Render 会读取 `render.yaml`，展示预配置：
   - 服务类型：Web Service
   - 构建命令：`pip install --upgrade pip && pip install -r requirements.txt`
   - 启动命令：`gunicorn backend.api.app:app`
   - 健康检查路径：`/health`
4. 保留默认区域（如 `Oregon`）和免费服务计划，点击 **Create Blueprint**。
5. 首次部署通常需要几分钟：
   - 在 “Events”/“Logs” 里可以看到依赖安装、构建、启动的过程。
   - 如果失败，可根据日志定位问题（例如依赖安装失败、Python 版本不支持等）。
6. 部署成功后，Render 会给出一个 HTTPS 域名，例如 `https://qpds-backend.onrender.com`。复制该地址，供后续前端调用。

> **可选环境变量**：如需调整 Flask 行为，可在 Render → Service → Environment 页面添加变量（例如 `DEBUG=false`）。`render.yaml` 已指定 `PYTHON_VERSION=3.10.13`，通常无需再改。

---

## 3. 配置 GitHub Pages 发布前端
仓库中已包含 GitHub Actions 工作流 `.github/workflows/deploy-frontend.yml`，它会将 `frontend/` 文件夹原样上传到 GitHub Pages。

1. 进入 GitHub 仓库页面，确认 `.github/workflows/deploy-frontend.yml` 存在且分支条件与实际一致（默认监听 `main`）。如需改为其它分支，编辑该文件中的 `branches` 配置。
2. 打开 **Settings → Pages**：
   - 在 “Build and deployment” 中，将 Source 选择为 **GitHub Actions**。
3. 推送代码后，Actions 会自动触发。如果需要立即执行，可在 GitHub 仓库的 **Actions** 标签页手动触发 `Deploy Frontend to GitHub Pages` 工作流（菜单中选择 “Run workflow”）。
4. 工作流分为两个 Job：
   - `build`：复制 `frontend/` 的静态文件到 `public/`，并打包成 artifact。
   - `deploy`：将 artifact 发布到 GitHub Pages。
5. 工作流执行成功后，返回 **Settings → Pages**，即可看到公开访问地址，例如：
   ```
   https://<你的用户名>.github.io/QPDS/
   ```
   首次部署需要几分钟，请耐心等待 “Your site is live” 提示出现。

> **注意**：GitHub Pages 会强制使用 HTTPS。如果你访问时提示 404 或尚未生效，稍等片刻再刷新；如果多次触发仍失败，检查 Actions 日志是否报错。

---

## 4. 连接前端页面与后端 API
线上前端默认会尝试连接 `https://qpds-backend.onrender.com`。你可以在页面内动态修改：

1. 访问 GitHub Pages 提供的站点地址。
2. 页面右上角点击 `⚙️ API配置` 按钮。
3. 在弹出的输入框输入 Render 返回的 HTTPS 地址（例如 `https://qpds-backend.onrender.com`）。
4. 点击确认：
   - 前端会立即对 `/health` 发起检测，并在右侧状态标签显示 “已连接/无法连接”。
   - 配置会保存到浏览器 `localStorage`，刷新页面后仍然生效。
5. 如果想恢复默认配置，再次点击按钮，留空提交即可。

还有两种快捷设置方式：
- **URL 查询参数**：首次访问时可在地址后加上 `?api=https://your-service.onrender.com`，页面会自动保存该地址并移除查询参数。
- **本地开发**：如果在本地直接打开 `frontend/index.html`，默认仍然指向 `http://localhost:8080`，方便调试。

---

## 5. 验证部署结果
1. 在浏览器访问 Render 后端的 `/health`，确认返回：
   ```json
   {"status": "healthy", "service": "QPDS API"}
   ```
2. 打开 GitHub Pages 前端：
   - 在页面中选择底牌、公共牌、筹码等信息。
   - 点击 “获取决策建议” 或 “仅计算胜率”，确保能收到返回结果。
3. 若前端顶部显示红色错误提示 “无法连接后端服务”，请确认：
   - Render 服务是否正在运行（状态是否为 “Live”）。
   - 输入的 API 地址是否正确且带有 https:// 前缀。
   - 网络环境是否允许访问外部站点。

---

## 6. 常见问题排查

| 问题 | 排查思路 |
| ---- | ---- |
| Render 构建失败 | 查看 Render 日志，检查 `requirements.txt` 是否过旧、依赖安装是否报错，可先手动在本地升级依赖再提交。 |
| Render 启动成功但健康检查失败 | 确认 `backend/api/app.py` 可在本地正常启动；检查是否忘记开放 `/health` 路由或端口被占用。 |
| GitHub Pages 工作流失败 | 在 Actions 日志中查看 `build` 步骤的错误（通常是路径不一致或权限问题），必要时在仓库设置中重新授权 GitHub Pages。 |
| 前端显示“无法连接后端服务” | 确认 API 地址填写正确且可通过 HTTPS 访问；也可在浏览器控制台查看具体的网络错误。 |
| 需要多环境配置（测试/生产） | 可以在 Render 中创建多个服务，前端通过 `⚙️ API配置` 分别切换，或在地址栏使用不同的 `?api=` 参数。 |

---

## 7. 附录：相关文件说明
- `render.yaml`：Render Blueprint，定义后端如何构建与启动。
- `.github/workflows/deploy-frontend.yml`：GitHub Actions 工作流，把 `frontend/` 发布到 Pages。
- `frontend/index.html`：前端页面；右上角的 `⚙️ API配置` 按钮、健康检查状态等逻辑都在此文件中实现。
- `README.md`：总览文档，含本地启动指引和部署入口。

完成以上步骤后，你的 QPDS 将同时具备线上可访问的前端页面与可远程调用的后端 API，适合分享给团队或朋友体验。祝部署顺利！
