# -*- mode: python ; coding: utf-8 -*-
# 打包命令（在项目根目录）: pyinstaller markdow.spec  → 生成 dist/markdow.exe
# 需先安装: pip install pyinstaller "packages/markitdown[docx,xls]"

import os
import sys

block_cipher = None

# 项目根目录 = 含 markdow.spec 的目录（请始终在项目根执行: pyinstaller markdow.spec）
_spec_file = os.path.join(os.getcwd(), 'markdow.spec')
if os.path.isfile(_spec_file):
    _spec_dir = os.path.dirname(os.path.abspath(_spec_file))
else:
    try:
        _spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
    except NameError:
        _spec_dir = os.getcwd()

# magika 数据目录（models + config），必须存在否则运行时会报错
# Windows: .venv/Lib/site-packages；Linux/macOS: .venv/lib/pythonX.Y/site-packages
if sys.platform == 'win32':
    _site_packages = os.path.join(_spec_dir, '.venv', 'Lib', 'site-packages')
else:
    _py = 'python%d.%d' % (sys.version_info.major, sys.version_info.minor)
    _site_packages = os.path.join(_spec_dir, '.venv', 'lib', _py, 'site-packages')
_magika_models = os.path.join(_site_packages, 'magika', 'models')
_magika_config = os.path.join(_site_packages, 'magika', 'config')
_magika_datas = []
if os.path.isdir(_magika_models):
    for _root, _dirs, _files in os.walk(_magika_models):
        for _f in _files:
            _full = os.path.join(_root, _f)
            _rel = os.path.relpath(_full, _magika_models)
            _magika_datas.append((_full, os.path.join('magika', 'models', _rel.replace(os.sep, '/'))))
if os.path.isdir(_magika_config):
    for _root, _dirs, _files in os.walk(_magika_config):
        for _f in _files:
            _full = os.path.join(_root, _f)
            _rel = os.path.relpath(_full, _magika_config)
            _magika_datas.append((_full, os.path.join('magika', 'config', _rel.replace(os.sep, '/'))))

if not _magika_datas:
    sys.stderr.write(
        'WARNING: magika models/config not found at %s\n'
        '  Run from project root with .venv created and markitdown installed.\n' % _spec_dir
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
    ['markdow_cli.py'],
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
    name='markdow',
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
