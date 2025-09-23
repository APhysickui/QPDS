# 📋 GitHub上传步骤

## 1. 创建GitHub仓库

1. 打开浏览器，访问 https://github.com/APhysickui
2. 点击绿色的 **"New"** 按钮或访问 https://github.com/new
3. 填写仓库信息：
   - **Repository name**: `QPDS`
   - **Description**: `Quantitative Poker Decision System - AI-powered poker analytics using quantitative investment strategies`
   - **选择**: Public（公开）
   - **不要勾选** "Initialize this repository with a README"（因为我们已经有了）
4. 点击 **"Create repository"**

## 2. 推送代码到GitHub

创建仓库后，GitHub会显示一些命令。在终端中运行以下命令：

```bash
# 添加远程仓库（用你看到的地址）
git remote add origin https://github.com/APhysickui/QPDS.git

# 推送代码
git push -u origin main
```

如果提示输入用户名和密码：
- 用户名：APhysickui
- 密码：使用你的GitHub Personal Access Token（不是GitHub密码）

## 3. 创建Personal Access Token（如果需要）

如果你还没有Personal Access Token：

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 给token起个名字（比如"QPDS"）
4. 选择权限，至少勾选：
   - `repo`（完整的仓库权限）
5. 点击 "Generate token"
6. **立即复制token**（它只显示一次！）

## 4. 验证上传成功

上传完成后，访问 https://github.com/APhysickui/QPDS 查看你的项目！

## 5. 项目已经运行

- **后端API**: http://localhost:8080
- **健康检查**: http://localhost:8080/health
- **前端界面**: 在浏览器中打开 `frontend/index.html`

## 可选：添加项目标签

在GitHub仓库页面，点击齿轮图标（Settings旁边），添加topics：
- `poker`
- `texas-holdem`
- `quantitative-analysis`
- `python`
- `flask`
- `ai`
- `decision-system`

---

**祝贺！你的QPDS项目即将上线！** 🎉