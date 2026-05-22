"""wx2md - 微信公众号文章转 Markdown 工具"""

import os
import re
import sys

import frontmatter
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from playwright.sync_api import sync_playwright


def fetch_article(url: str, on_progress=None) -> tuple[str, str]:
    """抓取微信文章，返回 (正文 HTML, 完整页面 HTML)"""
    if on_progress:
        on_progress("正在启动浏览器...")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            raise RuntimeError(
                "未检测到 Google Chrome 浏览器。请先安装 Chrome 后再使用本工具。"
            )
        page = browser.new_page()

        if on_progress:
            on_progress("正在加载页面...")
        page.goto(url, wait_until="domcontentloaded")

        # 等待正文容器可见
        page.wait_for_selector("#js_content", state="visible", timeout=15000)

        # 滚动触发图片懒加载
        if on_progress:
            on_progress("正在滚动加载图片...")
        page_height = page.evaluate("document.body.scrollHeight")
        for y in range(0, page_height, 800):
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(300)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        content_html = page.inner_html("#js_content")
        full_html = page.content()
        browser.close()

    return content_html, full_html


def extract_metadata(full_html: str, url: str) -> dict:
    """从完整页面 HTML 中提取元数据"""
    soup = BeautifulSoup(full_html, "html.parser")

    title = ""
    title_el = soup.select_one("#activity-name")
    if title_el:
        title = title_el.get_text(strip=True)

    author = ""
    author_el = soup.select_one("#js_name")
    if author_el:
        author = author_el.get_text(strip=True)

    date = ""
    date_el = soup.select_one("#publish_time")
    if date_el:
        date = date_el.get_text(strip=True)

    return {"title": title, "author": author, "date": date, "url": url}


def sanitize_filename(name: str) -> str:
    """清理文件名，移除非法字符"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "", name)
    name = name.strip()
    return name[:80] if name else "untitled"


def guess_extension(url: str) -> str:
    """从 URL 推断图片扩展名"""
    if "wx_fmt=png" in url:
        return "png"
    if "wx_fmt=gif" in url:
        return "gif"
    if "wx_fmt=svg" in url:
        return "svg"
    if "wx_fmt=webp" in url:
        return "webp"
    return "jpg"


def preprocess_html(html: str) -> BeautifulSoup:
    """预处理微信文章 HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # 移除微信特有标签
    for tag in soup.find_all(["mpvoice", "mpvideosnap", "mp-miniprogram"]):
        tag.decompose()

    # 移除空 section 和无内容元素
    for tag in soup.find_all(["section", "span"]):
        if not tag.get_text(strip=True) and not tag.find("img"):
            tag.decompose()

    # 处理图片: data-src → src
    for img in soup.find_all("img"):
        data_src = img.get("data-src")
        if data_src:
            img["src"] = data_src
        # 移除无用属性
        for attr in [
            "data-src", "data-w", "data-ratio", "data-type", "data-s",
            "data-before-oversubscription-url", "data-fail", "data-backw",
            "data-backh", "data-before-oversubscription-src", "class",
            "style", "width", "height",
        ]:
            img.attrs.pop(attr, None)

    # 移除所有 style 属性
    for tag in soup.find_all(style=True):
        del tag["style"]

    # 移除注释
    from bs4 import Comment
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    return soup


def download_images(soup: BeautifulSoup, images_dir: str, on_progress=None) -> int:
    """下载所有图片到本地，返回下载数量"""
    os.makedirs(images_dir, exist_ok=True)
    count = 0
    client = httpx.Client(
        headers={"Referer": "https://mp.weixin.qq.com/"},
        follow_redirects=True,
        timeout=30,
    )

    all_imgs = [img for img in soup.find_all("img")
                if img.get("src", "") and not img.get("src", "").startswith("data:")]
    total = len(all_imgs)

    for idx, img in enumerate(all_imgs, 1):
        src = img.get("src", "")
        ext = guess_extension(src)
        filename = f"{idx}.{ext}"
        filepath = os.path.join(images_dir, filename)

        try:
            resp = client.get(src)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            img["src"] = f"images/{filename}"
            count += 1
            if on_progress:
                on_progress(f"正在下载图片 ({idx}/{total})...")
            print(f"  图片 {idx}: 已下载 ({len(resp.content) // 1024}KB)")
        except Exception as e:
            print(f"  图片 {idx}: 下载失败 - {e}")
            continue

    client.close()
    return count


def convert_to_markdown(soup: BeautifulSoup) -> str:
    """将预处理后的 HTML 转换为 Markdown"""
    content = md(
        str(soup),
        heading_style="atx",
        bullets="-",
        strip=["script", "style", "noscript"],
    )
    # 清理多余空行
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def build_output(meta: dict, md_content: str) -> str:
    """组装带 frontmatter 的最终输出"""
    post = frontmatter.Post(md_content)
    post["title"] = meta["title"]
    post["author"] = meta["author"]
    if meta["date"]:
        post["date"] = meta["date"]
    post["source"] = meta["url"]
    return frontmatter.dumps(post)


def convert(url: str, output_dir: str = "output", on_progress=None) -> dict:
    """完整转换流程，返回结果信息字典。CLI 和 GUI 共用。"""
    if on_progress:
        on_progress("正在抓取文章...")
    content_html, full_html = fetch_article(url, on_progress=on_progress)

    meta = extract_metadata(full_html, url)

    if on_progress:
        on_progress("正在处理内容...")
    soup = preprocess_html(content_html)

    article_dir = sanitize_filename(meta["title"])
    base_dir = os.path.join(output_dir, article_dir)
    images_dir = os.path.join(base_dir, "images")

    if on_progress:
        on_progress("正在下载图片...")
    img_count = download_images(soup, images_dir, on_progress=on_progress)

    if on_progress:
        on_progress("正在转换为 Markdown...")
    md_content = convert_to_markdown(soup)
    output = build_output(meta, md_content)

    output_path = os.path.join(base_dir, "article.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    return {
        "title": meta["title"],
        "author": meta["author"],
        "date": meta["date"],
        "img_count": img_count,
        "output_path": output_path,
        "images_dir": images_dir,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="wx2md - 微信公众号文章转 Markdown")
    parser.add_argument("url", nargs="?", help="微信文章链接")
    parser.add_argument("-o", "--output", default="output", help="输出目录 (默认: output)")
    args = parser.parse_args()

    print("wx2md - 微信公众号文章转 Markdown")
    print("=" * 40)

    url = args.url or input("请输入微信文章链接: ").strip()

    if "mp.weixin.qq.com" not in url:
        print("错误: 不是有效的微信公众号文章链接")
        return

    def cli_progress(msg):
        print(f"  {msg}")

    result = convert(url, output_dir=args.output, on_progress=cli_progress)

    print(f"\n完成!")
    print(f"  标题: {result['title']}")
    print(f"  作者: {result['author']}")
    print(f"  日期: {result['date']}")
    print(f"  图片: {result['img_count']} 张")
    print(f"  输出: {result['output_path']}")


if __name__ == "__main__":
    main()
