#!/usr/bin/env python3
"""
markitdown 命令行入口：单文件转 Markdown（基于 Microsoft MarkItDown）。

用法:
  markitdown <文件>             在当前目录生成同名 .md
  markitdown <文件> -o out.md   指定输出路径

MarkItDown 支持的格式（需安装对应可选依赖）:
  文档: PDF, Word(.doc/.docx), PowerPoint(.ppt/.pptx), Excel(.xls/.xlsx)
  网页/结构: HTML, CSV, JSON, XML, RSS, Jupyter(.ipynb), EPUB
  媒体: 图片(EXIF + LLM描述), 音频(元数据/语音转写), YouTube URL
  其他: ZIP(遍历内容), Outlook(.msg), 纯文本
  可选: Azure Document Intelligence(-d -e <endpoint>)

LLM 图片识别（需 --llm-model 和 --llm-api-key 或环境变量）:
  识别图片内容:  markitdown image.png --llm-model gpt-4o --llm-api-key sk-xxx
  识别PDF图片:   markitdown doc.pdf   --llm-model gpt-4o --llm-api-key sk-xxx
  自定义提示词:  markitdown img.jpg   --llm-model gpt-4o --llm-prompt "描述图中的文字"
  国内/自建服务: markitdown img.jpg   --llm-model qwen-vl-plus --llm-base-url https://dashscope.aliyuncs.com/compatible-mode/v1 --llm-api-key sk-xxx

  支持任意兼容 OpenAI API 的视觉模型，如:
    OpenAI:     gpt-4o, gpt-4o-mini
    阿里云:     qwen-vl-plus, qwen-vl-max
    Azure:      gpt-4o（配合 --llm-base-url）
    本地Ollama: llava（配合 --llm-base-url http://localhost:11434/v1）

PDF + LLM 模式说明:
  传入 --llm-model 时，PDF 会逐页渲染为图片交给视觉模型识别，
  可完整理解页面布局、图表、图片等内容（需安装 pymupdf: pip install pymupdf）。
  不传 --llm-model 时，仍使用 pdfminer/pdfplumber 纯文字提取。
"""
import argparse
import base64
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="将文件转为 Markdown，默认在当前目录输出同名 .md",
        prog="markitdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    # LLM 图片识别参数
    llm_group = parser.add_argument_group(
        "LLM 图片识别",
        "使用视觉大模型识别图片/PDF内容（需安装 openai: pip install openai）",
    )
    llm_group.add_argument(
        "--llm-model",
        metavar="MODEL",
        default=None,
        help="视觉模型名称，如 gpt-4o、qwen-vl-plus、llava 等（也可设环境变量 MARKITDOWN_LLM_MODEL）",
    )
    llm_group.add_argument(
        "--llm-api-key",
        metavar="KEY",
        default=None,
        help="API Key（也可设环境变量 OPENAI_API_KEY）",
    )
    llm_group.add_argument(
        "--llm-base-url",
        metavar="URL",
        default=None,
        help="API Base URL，用于自建/国内服务（如 https://dashscope.aliyuncs.com/compatible-mode/v1）",
    )
    llm_group.add_argument(
        "--llm-prompt",
        metavar="PROMPT",
        default=None,
        help='图片描述提示词（默认："Write a detailed caption for this image."）',
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

    # 构建 LLM client
    llm_client = None
    llm_model = args.llm_model or os.environ.get("MARKITDOWN_LLM_MODEL")
    llm_api_key = args.llm_api_key or os.environ.get("OPENAI_API_KEY")
    llm_base_url = args.llm_base_url or os.environ.get("OPENAI_BASE_URL")

    if llm_model:
        try:
            from openai import OpenAI
            client_kwargs = {}
            if llm_api_key:
                client_kwargs["api_key"] = llm_api_key
            if llm_base_url:
                client_kwargs["base_url"] = llm_base_url
            llm_client = OpenAI(**client_kwargs)
        except ImportError:
            print(
                "错误：使用 --llm-model 需要安装 openai 库。\n"
                "请运行: pip install openai",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        # PDF + LLM：逐页渲染为图片，交给视觉模型识别
        if llm_client is not None and inp.suffix.lower() == ".pdf":
            markdown_text = _convert_pdf_with_llm(
                inp, llm_client, llm_model,
                prompt=args.llm_prompt,
            )
            out.write_text(markdown_text, encoding="utf-8")
            print(f"已生成: {out}")
            return

        mk_kwargs = {"enable_plugins": args.use_plugins}
        if args.use_docintel:
            if not args.endpoint:
                print("错误：使用 -d 时必须用 -e 指定 Document Intelligence endpoint。", file=sys.stderr)
                sys.exit(1)
            mk_kwargs["docintel_endpoint"] = args.endpoint
        if llm_client is not None:
            mk_kwargs["llm_client"] = llm_client
            mk_kwargs["llm_model"] = llm_model
        if args.llm_prompt:
            mk_kwargs["llm_prompt"] = args.llm_prompt

        md = MarkItDown(**mk_kwargs)
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


def _convert_pdf_with_llm(pdf_path: Path, client, model: str, prompt: str | None = None) -> str:
    """将 PDF 每页渲染为图片，逐页交给视觉 LLM 识别，返回完整 Markdown。"""
    try:
        import fitz  # pymupdf
    except ImportError:
        print(
            "错误：PDF+LLM 模式需要安装 pymupdf。\n"
            "请运行: pip install pymupdf",
            file=sys.stderr,
        )
        sys.exit(1)

    if prompt is None or not prompt.strip():
        prompt = (
            "请将这一页PDF的内容完整转换为Markdown格式。"
            "保留所有文字、表格结构、标题层级。"
            "图片用一句话描述其内容。"
            "只输出Markdown内容，不要额外解释。"
        )

    doc = fitz.open(str(pdf_path))
    total = len(doc)
    pages_md = []

    for i, page in enumerate(doc):
        print(f"  处理第 {i + 1}/{total} 页...", file=sys.stderr)
        # 渲染为 PNG（2x 分辨率，保证清晰度）
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    }
                ],
            )
            page_md = response.choices[0].message.content or ""
        except Exception as e:
            page_md = f"<!-- 第 {i + 1} 页识别失败: {e} -->"

        pages_md.append(f"<!-- Page {i + 1} -->\n\n{page_md.strip()}")

    doc.close()
    return "\n\n---\n\n".join(pages_md)


if __name__ == "__main__":
    main()
