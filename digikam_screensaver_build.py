from pathlib import Path

import PyInstaller.__main__

HERE = Path(__file__).parent.absolute()
digikam_windows_screensaver_spec = str(HERE / "digikam_windows_screensaver.spec")


if __name__ == "__main__":
    PyInstaller.__main__.run([digikam_windows_screensaver_spec])
