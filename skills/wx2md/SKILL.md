---
name: wx2md
description: 将微信公众号文章（mp.weixin.qq.com）转换为 Markdown，通过在 Windows 上运行自带的 wx2md-cli.exe 实现。当用户要求 OpenClaw、Claude Code、Codex 等 AI 编码代理转换微信公众号文章链接、下载文章图片，或从公众号 URL 生成 article.md 时使用。
compatibility: Requires Windows, Google Chrome (Playwright channel), and PowerShell 5.1+.
allowed-tools: Bash(powershell:*)
---

# wx2md

本 skill 仅适用于 `mp.weixin.qq.com` 文章 URL。**仅在 Windows 上可用**，依赖 Google Chrome（Playwright 通道）。

## 使用方法

`{baseDir}` 是 Claude Code 加载 skill 时自动填入的绝对路径。若使用其他 AI 工具，请将其替换为 `skills/wx2md/` 实际所在目录。

```powershell
powershell -ExecutionPolicy Bypass -File "{baseDir}\scripts\wx2md.ps1" -Url "<article_url>"
```

### 输入示例

```powershell
powershell -ExecutionPolicy Bypass -File "{baseDir}\scripts\wx2md.ps1" -Url "https://mp.weixin.qq.com/s/AbCdEfGh1234" -OutputDir "D:\articles"
```

### 首次使用

如果包装脚本提示尚未配置输出目录，请向用户询问一个绝对的 Windows 输出路径，然后重新运行并加上 `-OutputDir`：

```powershell
powershell -ExecutionPolicy Bypass -File "{baseDir}\scripts\wx2md.ps1" -Url "<article_url>" -OutputDir "<absolute_output_dir>"
```

首次成功配置后省略 `-OutputDir`；包装脚本会复用保存在 `%APPDATA%\wx2md-skill\config.json` 中的路径。

## 输出结构

转换完成后会在 `-OutputDir` 下生成（基于 `wx2md.py` 的行为；若 `wx2md-cli.exe` 实际输出与之不同，以实际为准）：

```
<output_dir>/
└── <sanitized-title>/          # 文章标题清洗后：去 \ / : * ? " < > | \r \n \t，截 80 字，空标题回退为 "untitled"
    ├── article.md              # 带 YAML frontmatter（title / author / date / source）
    └── images/
        ├── 1.<ext>             # 扩展名按 URL 中 wx_fmt=png|gif|svg|webp 推断；默认 jpg
        ├── 2.<ext>
        └── ...
```

`article.md` 中的图片引用统一为相对路径 `images/<n>.<ext>`。

## 验证结果

**直接打开并读取 `article.md` 文件**来确认标题、作者等元信息是否符合预期。**不要依赖控制台输出**来判断结果 —— 控制台输出可能截断、丢失字段或与最终文件内容不一致。
