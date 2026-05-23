# wx2md - 微信公众号文章转 Markdown

将微信公众号文章转换为 Markdown 文档，支持图片下载和元数据提取。

## 安装方式

### 方式一：下载 exe（推荐新手）

从 [GitHub Releases](https://github.com/your-username/wx2md/releases) 下载 `wx2md.exe`，双击运行后浏览器会自动打开转换界面。

### 方式二：Docker（推荐开发者）

```bash
git clone https://github.com/your-username/wx2md.git
cd wx2md
docker compose up
```

访问 http://localhost:8000 使用 Web 界面。

### 方式三：Claude Code Skill（推荐 AI 用户）

1. Clone 仓库到本地
2. 在 Claude Code 中打开项目目录
3. 直接粘贴微信文章链接，Claude 会自动执行转换

### 方式四：原生安装（推荐 Python 开发者）

```bash
git clone https://github.com/your-username/wx2md.git
cd wx2md
pip install -r requirements.txt
```

## 使用方法

### CLI 模式

```bash
python wx2md.py "<微信文章链接>"
python wx2md.py "<微信文章链接>" -o "D:/articles"
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
