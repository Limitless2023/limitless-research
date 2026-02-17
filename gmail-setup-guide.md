---
layout: default
title: "Gmail API Setup Guide for OpenClaw"
---

# 📧 OpenClaw 连接 Gmail 完整指南

> 让你的 AI 助手读写邮件、管理日历。适用于中国大陆网络环境，无需 TUN 模式。

[← 返回首页](./)

---

## 为什么需要这个？

OpenClaw 通过 Gmail API 访问你的邮箱。常见的 `gog` CLI（Go 语言写的）在中国大陆会因为**代理兼容性问题**超时——Go 的 Google OAuth2 库不走 `HTTPS_PROXY` 环境变量，导致直连 Google 被墙。

**解决方案**：用 `curl` 封装的脚本，通过 `-x proxy` 显式走 HTTP 代理。

---

## 📋 前置条件

| 需要 | 说明 |
|------|------|
| macOS / Linux | 脚本基于 bash |
| `curl` | 系统自带 |
| `python3` | 系统自带或 `brew install python` |
| HTTP 代理 | 如 Clash（默认 `http://127.0.0.1:7890`） |
| Google 账号 | 用于创建 OAuth 凭据 |

---

## 第一步：创建 Google Cloud 项目

1. 打开 [Google Cloud Console](https://console.cloud.google.com/)
2. 顶部项目选择器 → **新建项目**
3. 名称随便填（如 `openclaw-gmail`）→ **创建**
4. 确保切换到新项目

---

## 第二步：启用 API

在项目中启用以下 API（点链接直达，记得确认项目正确）：

| API | 用途 |
|-----|------|
| [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com) | 邮件读写 |
| [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) | 日历管理 |
| [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) | 文件访问 |
| [People API](https://console.cloud.google.com/apis/library/people.googleapis.com) | 联系人 |
| [Google Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com) | 文档 |
| [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) | 表格 |

> ⚠️ **常见坑**：OAuth 凭据和 API 必须在**同一个项目**下！如果凭据在项目 A 但 API 启用在项目 B，会报 `403 SERVICE_DISABLED`。

---

## 第三步：配置 OAuth 同意屏幕

1. 进入 [OAuth 同意屏幕](https://console.cloud.google.com/apis/credentials/consent)
2. 选择 **外部** → 创建
3. 填写必填项：
   - **应用名称**：`OpenClaw`
   - **用户支持邮箱**：你的邮箱
   - **开发者联系邮箱**：你的邮箱
4. 范围（Scopes）页面直接跳过
5. 保存

### ⚠️ 添加测试用户（必须！）

未验证的应用只允许测试用户使用。

1. 进入 [目标对象](https://console.cloud.google.com/auth/audience)
2. 找到 **测试用户** → **+ Add users**
3. 添加你要授权的 Gmail 地址
4. 保存

> 如果不添加测试用户，授权时会看到 `Access blocked: xxx has not completed the Google verification process`。

---

## 第四步：创建 OAuth 凭据

1. 进入 [凭据页面](https://console.cloud.google.com/apis/credentials)
2. **+ 创建凭据** → **OAuth 客户端 ID**
3. 应用类型：**桌面应用**
4. 名称：`gog-cli`（随便填）
5. 创建后 **下载 JSON**

> 💡 如果新版 Google Auth Platform 界面下载按钮不好使，试试旧版入口：
> `https://console.cloud.google.com/apis/credentials/oauthclient/YOUR_CLIENT_ID?project=YOUR_PROJECT`

记下 JSON 里的 `client_id` 和 `client_secret`。

---

## 第五步：获取 Refresh Token

### 方案 A：用 gog CLI（推荐）

```bash
# 安装
brew install steipete/tap/gogcli

# 导入凭据
gog auth credentials /path/to/client_secret.json

# 授权（自动打开浏览器）
gog auth add your@gmail.com --services gmail,calendar,drive,contacts,docs,sheets

# 导出 refresh token
gog auth tokens export your@gmail.com --out /tmp/token.json
cat /tmp/token.json   # 复制 refresh_token
rm /tmp/token.json     # 用完删除
```

> `gog auth add` 只需浏览器能访问 Google（浏览器走代理即可）。授权完成后我们只需要 refresh token，不实际用 gog 调 API。

### 方案 B：纯手动

```bash
CLIENT_ID="你的client_id"
CLIENT_SECRET="你的client_secret"

# 1. 浏览器打开（替换 CLIENT_ID）：
open "https://accounts.google.com/o/oauth2/auth?client_id=${CLIENT_ID}&redirect_uri=http://localhost&response_type=code&scope=email+https://www.googleapis.com/auth/gmail.modify+https://www.googleapis.com/auth/calendar+https://www.googleapis.com/auth/drive+https://www.googleapis.com/auth/contacts+https://www.googleapis.com/auth/documents+https://www.googleapis.com/auth/spreadsheets&access_type=offline&prompt=consent"

# 2. 授权后跳转到 http://localhost/?code=4/xxx&scope=...
#    从 URL 复制 code 参数的值

# 3. 换取 token
AUTH_CODE="复制的code"
curl -x http://127.0.0.1:7890 -X POST "https://oauth2.googleapis.com/token" \
  -d "client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&code=${AUTH_CODE}&grant_type=authorization_code&redirect_uri=http://localhost"

# 返回 JSON 里的 refresh_token 就是我们要的
```

---

## 第六步：配置脚本

```bash
# 下载脚本（如果还没有）
# 脚本位置：~/.openclaw/workspace/skills/gmail-api/gmail.sh

# 创建配置
mkdir -p ~/.config/gmail-api

cat > ~/.config/gmail-api/config.json << 'EOF'
{
  "email": "your@gmail.com",
  "client_id": "123456-xxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxx",
  "refresh_token": "1//0gXXX"
}
EOF

chmod 600 ~/.config/gmail-api/config.json
```

---

## 第七步：验证

```bash
GMAIL="~/.openclaw/workspace/skills/gmail-api/gmail.sh"

# 测试连接
$GMAIL profile
# ✅ Email: your@gmail.com
# ✅ Total messages: 4156

# 查看未读
$GMAIL unread 5

# 读邮件
$GMAIL read <messageId>

# 看日历
$GMAIL calendar-events 7
```

---

## 🌐 代理说明

| 场景 | 设置 |
|------|------|
| 中国大陆 + Clash | 默认即可（`http://127.0.0.1:7890`） |
| 中国大陆 + 其他代理 | `GMAIL_PROXY=http://ip:port gmail.sh profile` |
| 海外服务器 | `GMAIL_PROXY= gmail.sh profile`（空值=直连） |
| Clash TUN 模式 | ⚠️ 可能不稳定，建议关闭 TUN 用 HTTP 代理 |

---

## 📝 命令速查

```
gmail.sh profile                          # 账号信息
gmail.sh unread [N]                       # 未读邮件
gmail.sh search "<query>" [N]             # 搜索
gmail.sh read <id>                        # 读全文
gmail.sh headers <id>                     # 看邮件头
gmail.sh send <to> <subject> <body>       # 发邮件
gmail.sh reply <id> <body>                # 回复
gmail.sh labels                           # 标签列表
gmail.sh mark-read <id>                   # 标已读
gmail.sh mark-unread <id>                 # 标未读
gmail.sh star <id>                        # 加星标
gmail.sh trash <id>                       # 删除
gmail.sh calendar-list                    # 日历列表
gmail.sh calendar-events [days]           # 近期日程
gmail.sh calendar-create <title> <start> <end>  # 建日程
```

---

## ❓ FAQ

**Q: Token 会过期吗？**
Access token 1小时过期，脚本自动刷新。Refresh token 基本不过期（除非撤销授权或 6 个月不用）。

**Q: 换电脑怎么迁移？**
只需迁移 `~/.config/gmail-api/config.json`（一个 JSON 文件），脚本重新下载即可。

**Q: 多账号？**
当前单账号。扩展思路：`GMAIL_CONFIG=~/.config/gmail-api/work.json gmail.sh profile`

**Q: 安全建议？**
- `config.json` 包含 refresh token，等同密码
- 定期在 [Google 安全设置](https://myaccount.google.com/permissions) 检查
- 不要把 config.json 提交到 git

---

*Created by Singularity ✴️ — 2026-02-17*

[← 返回首页](./)
