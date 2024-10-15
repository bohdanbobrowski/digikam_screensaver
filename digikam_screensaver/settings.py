import os

from pydantic_settings import BaseSettings  # type:ignore


class DigiKamScreensaverSettings(BaseSettings):
    """
    TODO: Add class config with some reasonable prefix
    """

    pictures_path: str = "D:\\Pictures"  # C:\\Users\\bohdan\\Pictures
    database_file: str = "digikam4.db"
    target_folder: str = "Screensaver"
    font_name: str = "Good_Old_DOS.ttf"  # 6809_Chargen.otf
    limit: int = 10
    timeout: int = 5000
    width: int = 1920
    height: int = 1080

    @property
    def database_path(self) -> str:
        return os.path.join(self.pictures_path, self.database_file)

    @property
    def target_path(self) -> str:
        return os.path.join(self.pictures_path, self.target_folder)
