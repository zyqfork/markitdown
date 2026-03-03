---
name: markitdown-convert
description: 使用本地 markitdown 命令行工具将不支持的文件格式转换为 Markdown，然后再读取内容。当需要读取 PDF、Word(.docx/.doc)、PowerPoint(.pptx)、Excel(.xlsx/.xls)、Outlook邮件(.msg)、EPUB、ZIP等文件，但无法直接读取时，先调用 markitdown 转换为 .md 文件再处理。Use when the user asks to read, analyze, or extract content from unsupported file formats like PDF, docx, pptx, xlsx, xls, msg, epub.
---

# markitdown-convert

调用系统已安装的 `markitdown` 工具将不支持的文件转为 Markdown，再读取内容。

## 支持的格式

| 格式 | 扩展名 |
|------|--------|
| PDF | `.pdf` |
| Word | `.docx`, `.doc` |
| PowerPoint | `.pptx`, `.ppt` |
| Excel | `.xlsx`, `.xls` |
| Outlook 邮件 | `.msg` |
| 电子书 | `.epub` |
| 网页 | `.html`, `.htm` |
| 数据 | `.csv`, `.json`, `.xml` |
| Notebook | `.ipynb` |
| 压缩包 | `.zip`（遍历内部文件） |
| 图片 | `.jpg`, `.png` 等（提取 EXIF，无 OCR） |

## 工作流程

1. **判断是否需要转换**：如果用户要读取的文件是上述格式之一，则调用 markitdown 转换
2. **执行转换命令**：
   ```bash
   markitdown "<文件路径>" -o "<输出路径>.md"
   ```
3. **读取转换结果**：用 Read 工具读取生成的 `.md` 文件
4. **清理临时文件**（可选）：如果是临时转换，任务完成后可删除 `.md` 文件

## 命令格式

```bash
# 基本用法（输出到当前目录同名 .md）
markitdown "<文件路径>"

# 指定输出路径
markitdown "<文件路径>" -o "<输出文件>.md"

# 路径含空格时必须加引号
markitdown "C:\path\with spaces\file.pdf" -o "C:\output\file.md"
```

## 注意事项

- **路径含空格或中文必须用引号包裹**
- 输出的 `.md` 文件默认在**命令执行时的当前目录**（不是文件所在目录）
- 推荐用 `-o` 明确指定输出路径，避免混淆
- 设计稿/扫描版 PDF 转换质量较差（基于文字坐标提取，非 OCR）
- 执行转换后用 Shell 工具运行命令，再用 Read 工具读取结果

## 示例

**读取一个 Word 文档：**
```
Shell: markitdown "C:\Users\user\doc.docx" -o "C:\Users\user\doc.md"
Read:  C:\Users\user\doc.md
```

**读取带空格路径的 PDF：**
```
Shell: markitdown "C:\Users\user\My Documents\report.pdf" -o "C:\Temp\report.md"
Read:  C:\Temp\report.md
```
