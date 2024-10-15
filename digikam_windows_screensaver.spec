# -*- mode: python ; coding: utf-8 -*-
# block_cipher = None
a = Analysis(
    ['digikam_screensaver\\screen_saver.py'],
    pathex=[
        '.',
    ],
    datas=[
        ('./assets/6809_Chargen.otf', '.'),
        ('./assets/Good_Old_DOS.ttf', '.'),
    ],
    hookspath=[],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    **get_deps_minimal(video=None, audio=None)
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='digikam_windows_screensaver.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=None,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    # icon='./assets/blog2epub_256px.png'
)
info_plist = {
    "NSHighResolutionCapable": True,
}
app = BUNDLE(
    exe,
    name='digikam_windows_screensaver.exe',
    # icon='./assets/blog2epub.ico',
    bundle_identifier=None,
    info_plist=info_plist
)
