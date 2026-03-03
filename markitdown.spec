# -*- mode: python ; coding: utf-8 -*-
# 打包命令（在项目根目录，使用 venv 里的 pyinstaller）:
#   .venv\Scripts\pyinstaller.exe markitdown.spec        （Windows）
#   .venv/bin/pyinstaller markitdown.spec                （Linux / macOS）

import os
import sys
import subprocess

block_cipher = None

# ── 定位 magika 包路径 ────────────────────────────────────────────────────────
# 不依赖 spec 进程的 import，而是通过「当前 Python 可执行文件」问 venv 里的 Python
# PyInstaller 执行 spec 时 sys.executable 就是 venv 里的 Python，最可靠
_magika_pkg = subprocess.check_output(
    [sys.executable, '-c', 'import magika, os; print(magika.__path__[0])'],
    text=True
).strip()

print(f"[spec] magika package path: {_magika_pkg}")

_magika_models_src = os.path.join(_magika_pkg, 'models')
_magika_config_src = os.path.join(_magika_pkg, 'config')

assert os.path.isdir(_magika_models_src), f"magika models dir not found: {_magika_models_src}"
assert os.path.isdir(_magika_config_src), f"magika config dir not found: {_magika_config_src}"

# 检查 model.onnx 是否存在
_onnx = os.path.join(_magika_models_src, 'standard_v3_3', 'model.onnx')
assert os.path.isfile(_onnx), f"model.onnx not found: {_onnx}"
print(f"[spec] model.onnx OK: {_onnx}")

# ── 收集 magika 数据文件（models + config）──────────────────────────────────
# PyInstaller datas 元组：(源文件完整路径, 目标目录路径)
# 目标目录是相对于 _MEIPASS 的目录，不是文件路径
def _walk_datas(src_dir, dest_prefix):
    out = []
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            full = os.path.join(root, f)
            # 该文件相对于 src_dir 的目录部分（不含文件名）
            rel_dir = os.path.relpath(root, src_dir)
            if rel_dir == '.':
                dest_dir = dest_prefix
            else:
                dest_dir = os.path.join(dest_prefix, rel_dir).replace(os.sep, '/')
            out.append((full, dest_dir))
    return out

_magika_datas = (
    _walk_datas(_magika_models_src, 'magika/models') +
    _walk_datas(_magika_config_src, 'magika/config')
)
print(f"[spec] magika datas collected: {len(_magika_datas)} files")

# ── Hidden imports ────────────────────────────────────────────────────────────
hidden_imports = [
    # markitdown core
    'markitdown',
    'markitdown._markitdown',
    'markitdown.converters',
    'markitdown.converters._plain_text_converter',
    'markitdown.converters._html_converter',
    'markitdown.converters._docx_converter',
    'markitdown.converters._xlsx_converter',
    'markitdown.converters._pptx_converter',
    'markitdown.converters._pdf_converter',
    'markitdown.converters._csv_converter',
    'markitdown.converters._image_converter',
    'markitdown.converters._zip_converter',
    'markitdown.converters._ipynb_converter',
    'markitdown.converters._rss_converter',
    'markitdown.converters._epub_converter',
    'markitdown.converters._outlook_msg_converter',
    'markitdown.converters._audio_converter',
    'markitdown.converters._markdownify',
    # magika
    'magika',
    'magika.magika',
    # xlsx
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.cell',
    # xls
    'xlrd',
    # pdf
    'pdfminer',
    'pdfminer.high_level',
    'pdfminer.layout',
    'pdfplumber',
    # docx
    'mammoth',
    'lxml',
    'lxml.etree',
    # pptx
    'pptx',
    # outlook
    'olefile',
    # pandas (used by xlsx/xls converters)
    'pandas',
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['markitdown_cli.py'],
    pathex=[],
    binaries=[],
    datas=_magika_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='markitdown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
