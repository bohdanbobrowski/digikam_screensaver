block_cipher = None
a = Analysis(
    ["digikam_screensaver\\screen_saver.py"],
    pathex=[
        ".",
    ],
    datas=[
        ("assets/digikam.ico", "."),
    ],
    hiddenimports=["comtypes.stream"],
    hookspath=[],
    runtime_hooks=[],
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
    name="DigiKam Screensaver",
    debug=False,
    bootloader_ignore_signals=False,
    strip=None,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="./assets/digikam.ico",
)
info_plist = {
    "NSHighResolutionCapable": True,
}
app = BUNDLE(
    exe,
    name="DigiKam Screensaver",
    icon="./assets/digikam.ico",
    bundle_identifier=None,
    info_plist=info_plist,
)
