# wx2md - 微信公众号文章转 Markdown

将微信公众号文章转换为 Markdown 文档，支持图片下载和元数据提取。

## 安装方式

### 方式一：下载 exe（纯使用）

从 [GitHub Releases](https://github.com/liuzk233/wx2md/releases) 下载 `wx2md.exe`，双击运行后浏览器会自动打开转换界面。

如果需要命令行或 AI Agent 调用，从同一 Release 下载 `wx2md-cli.exe`：

```bash
wx2md-cli.exe "<微信文章链接>" -o "D:/articles"
```

### 方式二：Docker

已发布的 Docker 镜像在 Docker Hub：

```bash
docker pull liuzk233/wx2md
docker run --rm -p 8000:8000 liuzk233/wx2md
```

如果当前网络无法访问 Docker Hub，可以从 [GitHub Releases](https://github.com/liuzk233/wx2md/releases) 下载离线镜像压缩包 `wx2md.tar`，导入后再运行：

```bash
docker load -i wx2md.tar
docker run --rm -p 8000:8000 liuzk233/wx2md
```

也可以从源码构建并启动：

```bash
git clone https://github.com/liuzk233/wx2md.git
cd wx2md
docker compose up
```

访问 http://localhost:8000 使用 Web 界面。

### 方式三：AI Agent Skill（OpenClaw / Claude Code / Codex）

仓库内置 `skills/wx2md/`，其中包含通用 `SKILL.md` 和调用脚本。这个 skill 适用于支持本地 skill 目录并允许执行 PowerShell 命令的 AI coding agent，例如 OpenClaw、Claude Code、Codex。

1. Clone 或下载本仓库
2. 从 [GitHub Releases](https://github.com/liuzk233/wx2md/releases) 下载 `wx2md-cli.exe`
3. 将 `wx2md-cli.exe` 放入仓库的 `skills/wx2md/bin/` 目录。如果 `bin/` 不存在，手动创建：

```text
skills/
└── wx2md/
    └── bin/
        └── wx2md-cli.exe
```

4. 将完整的 `skills/wx2md/` 复制到对应工具的 skill 搜索目录，例如：

```text
<agent-workspace>/
└── skills/
    └── wx2md/
        ├── SKILL.md
        ├── bin/
        │   └── wx2md-cli.exe
        └── scripts/
            └── wx2md.ps1
```

常见放置方式：

- OpenClaw：放到当前 workspace 的 `skills/` 目录，或按 OpenClaw 文档安装本地 skill
- Claude Code：放到项目 `.claude/skills/` 目录，或用户级 skills 目录
- Codex：放到项目 `.codex/skills/` 目录，或用户级 skills 目录

5. 重启对应 Agent，或运行该工具提供的 skills 检查命令确认 skill 可见
6. 首次使用时告诉 Agent 输出目录，例如：

```text
请使用 wx2md 将这个微信公众号文章转换为 Markdown，输出到 D:\articles：
<微信文章链接>
```

首次成功配置后，输出目录会保存到 `%APPDATA%\wx2md-skill\config.json`。后续只需要提供微信公众号文章链接，skill 会复用该输出目录。

### 方式四：原生安装

```bash
git clone https://github.com/liuzk233/wx2md.git
cd wx2md
pip install -r requirements.txt
```

## 使用方法

### CLI 模式

```bash
python wx2md.py "<微信文章链接>"
python wx2md.py "<微信文章链接>" -o "D:/articles"
wx2md-cli.exe "<微信文章链接>" -o "D:/articles"
```

### Web 模式

```bash
python web.py
```

访问 http://localhost:8000 使用浏览器界面。

## 输出结构

```
output/
└── <文章标题>/
    ├── article.md      # 带 frontmatter 的 Markdown 文件
    └── images/         # 文章中的图片
        ├── 1.jpg
        ├── 2.png
        └── ...
```

## 依赖说明

- Python 3.8+
- Google Chrome 浏览器（Playwright 用于抓取页面）
- 其他依赖见 `requirements.txt`

## License

[MIT](LICENSE)
