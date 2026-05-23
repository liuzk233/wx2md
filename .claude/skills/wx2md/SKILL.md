---
name: wx2md
description: 将微信公众号文章转换为 Markdown 文档。用户粘贴微信文章链接后自动执行转换。
allowed-tools: Bash(python wx2md.py:*) Bash(python:*)
---

# wx2md - 微信公众号文章转 Markdown

## 前置条件

- 已安装 Python 3.8+
- 已安装 Google Chrome 浏览器（Playwright 依赖）
- 已安装依赖：`pip install -r requirements.txt`

## 使用方法

当用户提供微信公众号文章链接（`mp.weixin.qq.com`）时，执行转换：

```bash
python wx2md.py "<url>"
```

用户可以指定输出目录：

```bash
python wx2md.py "<url>" -o "<output_dir>"
```

## 执行流程

1. 验证用户提供的 URL 包含 `mp.weixin.qq.com`
2. 运行 `python wx2md.py "<url>"`，如果用户指定了输出目录则加上 `-o "<output_dir>"`
3. 将执行结果汇报给用户，包括：标题、作者、日期、图片数量、输出路径

## 输出结构

```
<output_dir>/
└── <文章标题>/
    ├── article.md      # 带 frontmatter 的 Markdown 文件
    └── images/         # 文章中的图片
        ├── 1.jpg
        ├── 2.png
        └── ...
```

## 注意事项

- 需要已安装 Google Chrome 浏览器（Playwright 依赖）
- 转换过程中会显示进度信息
- 默认输出目录为 `output`
