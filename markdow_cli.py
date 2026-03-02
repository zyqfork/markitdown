#!/usr/bin/env python3
"""
markdow.exe 入口：单文件转 Markdown（基于 Microsoft MarkItDown）。

用法:
  markdow.exe <文件>             在当前目录生成同名 .md
  markdow.exe <文件> -o out.md   指定输出路径

MarkItDown 支持的格式（需安装对应可选依赖）:
  文档: PDF, Word(.doc/.docx), PowerPoint(.ppt/.pptx), Excel(.xls/.xlsx)
  网页/结构: HTML, CSV, JSON, XML, RSS, Jupyter(.ipynb), EPUB
  媒体: 图片(EXIF/OCR), 音频(元数据/语音转写), YouTube URL
  其他: ZIP(遍历内容), Outlook(.msg), 纯文本
  可选: Azure Document Intelligence(-d -e <endpoint>)
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="将文件转为 Markdown，默认在当前目录输出同名 .md",
        prog="markdow",
        epilog=__doc__.split("MarkItDown 支持的格式")[-1].strip(),
    )
    parser.add_argument(
        "file",
        type=Path,
        nargs="?",
        default=None,
        help="要转换的文件路径",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="输出文件路径（默认：当前目录下 同名.md）",
    )
    parser.add_argument(
        "-x", "--extension",
        help="文件扩展名提示（如从 stdin 读取时使用）",
    )
    parser.add_argument(
        "-m", "--mime-type",
        help="MIME 类型提示",
    )
    parser.add_argument(
        "-c", "--charset",
        help="字符集提示（如 UTF-8）",
    )
    parser.add_argument(
        "-p", "--use-plugins",
        action="store_true",
        help="启用第三方插件转换",
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="列出已安装的插件后退出",
    )
    parser.add_argument(
        "--keep-data-uris",
        action="store_true",
        help="保留 data URI（如 base64 图片），默认会截断",
    )
    parser.add_argument(
        "-d", "--use-docintel",
        action="store_true",
        help="使用 Azure Document Intelligence 提取（需 -e 指定 endpoint）",
    )
    parser.add_argument(
        "-e", "--endpoint",
        help="Azure Document Intelligence 的 endpoint（与 -d 配合使用）",
    )
    args = parser.parse_args()

    if args.list_plugins:
        try:
            from importlib.metadata import entry_points
            eps = list(entry_points(group="markitdown.plugin"))
            print("已安装的 MarkItDown 插件:")
            print("  " + "\n  ".join(f"{e.name}" for e in eps) if eps else "  （无）")
        except Exception as e:
            print(f"列出插件失败: {e}", file=sys.stderr)
        sys.exit(0)

    if args.file is None:
        parser.print_help()
        sys.exit(1)

    inp = args.file.resolve()
    if not inp.is_file():
        print(f"错误：文件不存在: {inp}", file=sys.stderr)
        sys.exit(1)

    out = args.output
    if out is None:
        out = Path.cwd() / (inp.stem + ".md")
    else:
        out = out.resolve()

    try:
        from markitdown import MarkItDown, StreamInfo
    except ImportError:
        print("错误：未找到 markitdown，请先安装。", file=sys.stderr)
        sys.exit(1)

    stream_info = None
    if args.extension or args.mime_type or args.charset:
        ext = (args.extension or "").strip().lower()
        if ext and not ext.startswith("."):
            ext = "." + ext
        stream_info = StreamInfo(
            extension=ext or None,
            mimetype=(args.mime_type or "").strip() or None,
            charset=(args.charset or "").strip() or None,
        )

    try:
        if args.use_docintel:
            if not args.endpoint:
                print("错误：使用 -d 时必须用 -e 指定 Document Intelligence endpoint。", file=sys.stderr)
                sys.exit(1)
            md = MarkItDown(enable_plugins=args.use_plugins, docintel_endpoint=args.endpoint)
        else:
            md = MarkItDown(enable_plugins=args.use_plugins)
        result = md.convert(
            str(inp),
            stream_info=stream_info,
            keep_data_uris=args.keep_data_uris,
        )
        out.write_text(result.markdown, encoding="utf-8")
        print(f"已生成: {out}")
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
