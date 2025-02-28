import os

import yaml
from pydantic_settings import BaseSettings  # type:ignore


class DigiKamScreenSaverSettings(BaseSettings):
    """
    TODO: Add class config with some reasonable prefix
    """

    pictures_path: str = ""
    database_file: str = "digikam4.db"
    target_folder: str = "Screensaver"
    font_name: str = ""
    font_size: int = 15
    limit: int = 10
    timeout: int = 5000
    filter: int = 1
    width: int = 1920
    height: int = 1080
    history_size: int = 1000

    @property
    def database_path(self) -> str:
        return os.path.join(self.pictures_path, self.database_file)

    @property
    def target_path(self) -> str:
        return os.path.join(self.pictures_path, self.target_folder)


class DigiKamScreenSaverSettingsHandler:
    def __init__(self):
        self.path = os.path.join(os.getenv("LOCALAPPDATA"), "digikam_screensaver")
        self._prepare_path()
        self.settings_file = os.path.join(self.path, "digikam_screensaver.yml")

    def _prepare_path(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def read(self) -> DigiKamScreenSaverSettings:
        if not os.path.isfile(self.settings_file):
            self.save(DigiKamScreenSaverSettings())
        else:
            with open(self.settings_file, "rb") as stream:
                data_in_file = yaml.safe_load(stream)
            if data_in_file:
                return DigiKamScreenSaverSettings(**data_in_file)
        return DigiKamScreenSaverSettings()

    def save(self, data: DigiKamScreenSaverSettings):
        with open(self.settings_file, "w") as outfile:
            data_dict = data.model_dump()
            print(data_dict)
            yaml.dump(data_dict, outfile, default_flow_style=False)
