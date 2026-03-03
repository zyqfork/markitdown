# -*- mode: python ; coding: utf-8 -*-
# 打包命令（在项目根目录）: pyinstaller markitdown.spec  → 生成 dist/markitdown[.exe]
# 需先安装: pip install pyinstaller "packages/markitdown[docx,xls]"

import os
import sys

block_cipher = None

# 项目根目录 = 含 markitdown.spec 的目录（请始终在项目根执行: pyinstaller markitdown.spec）
_spec_file = os.path.join(os.getcwd(), 'markitdown.spec')
if os.path.isfile(_spec_file):
    _spec_dir = os.path.dirname(os.path.abspath(_spec_file))
else:
    try:
        _spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
    except NameError:
        _spec_dir = os.getcwd()

# magika 数据目录（models + config），必须打包进 exe 否则运行时报 "model not found"
# 优先从当前已安装的 magika 包路径收集（兼容 CI 与本地）
_magika_datas = []

def _collect_magika_datas(from_dir, dest_prefix):
    out = []
    if not os.path.isdir(from_dir):
        return out
    for _root, _dirs, _files in os.walk(from_dir):
        for _f in _files:
            _full = os.path.join(_root, _f)
            _rel = os.path.relpath(_full, from_dir)
            out.append((_full, os.path.join(dest_prefix, _rel.replace(os.sep, '/'))))
    return out

# 1) 从已 import 的 magika 包路径收集（CI/本地都可靠）
try:
    import magika
    _magika_pkg = magika.__path__[0]
    _magika_datas.extend(_collect_magika_datas(os.path.join(_magika_pkg, 'models'), 'magika/models'))
    _magika_datas.extend(_collect_magika_datas(os.path.join(_magika_pkg, 'config'), 'magika/config'))
except Exception:
    pass

# 2) 若未收集到，再从 .venv 的 site-packages 路径尝试
if not _magika_datas:
    if sys.platform == 'win32':
        _site_packages = os.path.join(_spec_dir, '.venv', 'Lib', 'site-packages')
    else:
        _py = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)
        _site_packages = os.path.join(_spec_dir, '.venv', 'lib', _py, 'site-packages')
    _magika_datas.extend(_collect_magika_datas(os.path.join(_site_packages, 'magika', 'models'), 'magika/models'))
    _magika_datas.extend(_collect_magika_datas(os.path.join(_site_packages, 'magika', 'config'), 'magika/config'))

if not _magika_datas:
    sys.stderr.write(
        'WARNING: magika models/config not found. Run from project root with markitdown (and magika) installed.\n'
    )

hidden_imports = [
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
    'magika',
    'magika.magika',
]

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
