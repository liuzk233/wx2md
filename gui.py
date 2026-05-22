"""wx2md GUI - 微信公众号文章转 Markdown 图形界面"""

import os
import threading
from tkinter import filedialog

import customtkinter as ctk

from wx2md import convert


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("wx2md - 微信文章转 Markdown")
        self.geometry("520x460")
        self.resizable(False, False)
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # URL 输入
        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="请输入微信文章链接...", height=36
        )
        self.url_entry.pack(padx=20, pady=(20, 10), fill="x")

        # 输出目录选择
        dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        dir_frame.pack(padx=20, pady=5, fill="x")

        self.dir_entry = ctk.CTkEntry(
            dir_frame, placeholder_text="输出目录...", height=36
        )
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.dir_entry.insert(0, os.path.join(os.getcwd(), "output"))

        self.browse_btn = ctk.CTkButton(
            dir_frame, text="浏览", width=60, height=36,
            command=self.browse_dir
        )
        self.browse_btn.pack(side="right")

        # 转换按钮
        self.convert_btn = ctk.CTkButton(
            self, text="开始转换", command=self.start_convert, height=36
        )
        self.convert_btn.pack(padx=20, pady=5)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(padx=20, pady=(10, 5), fill="x")
        self.progress_bar.set(0)

        # 状态标签
        self.status_label = ctk.CTkLabel(self, text="就绪", anchor="w")
        self.status_label.pack(padx=20, fill="x")

        # 结果展示
        self.result_box = ctk.CTkTextbox(self, height=200, state="disabled")
        self.result_box.pack(padx=20, pady=(10, 20), fill="both", expand=True)

    def browse_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, path)

    def update_status(self, msg: str):
        self.after(0, lambda: self.status_label.configure(text=msg))

    def update_progress(self, value: float):
        self.after(0, lambda: self.progress_bar.set(value))

    def show_result(self, title: str, content: str):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", f"{title}\n{'─' * 40}\n{content}")
        self.result_box.configure(state="disabled")

    def start_convert(self):
        url = self.url_entry.get().strip()
        if "mp.weixin.qq.com" not in url:
            self.show_result("错误", "不是有效的微信公众号文章链接")
            return
        self.convert_btn.configure(state="disabled", text="转换中...")
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")
        output_dir = self.dir_entry.get().strip() or "output"
        threading.Thread(
            target=self.do_convert, args=(url, output_dir), daemon=True
        ).start()

    def do_convert(self, url: str, output_dir: str):
        try:
            self.update_progress(0.05)
            result = convert(url, output_dir=output_dir, on_progress=self.update_status)

            self.update_progress(1.0)
            self.update_status("完成!")
            text = (
                f"标题: {result['title']}\n"
                f"作者: {result['author']}\n"
                f"日期: {result['date']}\n"
                f"图片: {result['img_count']} 张\n"
                f"输出: {result['output_path']}"
            )
            self.after(0, lambda: self.show_result("转换成功", text))

        except Exception as e:
            error_msg = str(e)
            self.update_progress(0)
            self.update_status("出错了")
            self.after(0, lambda: self.show_result("转换失败", error_msg))
        finally:
            self.after(
                0, lambda: self.convert_btn.configure(
                    state="normal", text="开始转换"
                )
            )


if __name__ == "__main__":
    App().mainloop()
