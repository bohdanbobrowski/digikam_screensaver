import os
import shutil
import sqlite3

from progress.bar import Bar
from pydantic_settings import BaseSettings


class DigiKamScreensaverSettings(BaseSettings):
    """
    TODO: Add class config with some reasonable prefix
    """

    pictures_path: str = "C:\\Users\\bohdan\\Pictures"
    database_file: str = "digikam4.db"
    target_folder: str = "Screensaver"
    limit: int = 100
    width: int = 1920
    height: int = 1080

    @property
    def database_path(self) -> str:
        return os.path.join(self.pictures_path, self.database_file)

    @property
    def target_path(self) -> str:
        return os.path.join(self.pictures_path, self.target_folder)


class DigiKamScreensaver:
    def __init__(self):
        self.settings = DigiKamScreensaverSettings()
        self.con = sqlite3.connect(self.settings.database_path)
        self.crsr = self.con.cursor()

    def _get_query(self) -> str:
        sub_query = "SELECT imageid FROM ImageInformation ii "
        sub_query += f'WHERE ii.rating > 0 AND ii.format = "JPG" ORDER BY RANDOM() LIMIT {self.settings.limit} '
        query = 'SELECT CONCAT(a.relativePath, "/" , i.name) as file_path, i.uniqueHash, i.name as hash FROM Images i '
        query += "LEFT JOIN Albums a ON a.id == i.album "
        query += f"WHERE i.id IN ({sub_query}) "
        query += "ORDER BY RANDOM();"
        return query

    def copy_pictures(self):
        result = self.crsr.execute(self._get_query())
        bar = Bar(
            f"Copying starred pictures to {self.settings.target_path}:",
            max=self.settings.limit,
        )
        for f in result.fetchall():
            bar.next()
            file_path = f[0].replace("/", "\\")[1:]
            file_album_name = file_path.split("\\")[-2:-1]
            try:
                file_album_name = file_album_name[0]
                file_path = file_path
                file_name = f[2]
                source_file = os.path.join(self.settings.pictures_path, file_path)
                target_file = os.path.join(
                    self.settings.target_path, f"{file_album_name}_{file_name}.jpg"
                )
                if os.path.isfile(source_file) and not os.path.isfile(target_file):
                    shutil.copy(source_file, target_file)
            except IndexError:
                pass


def copy_pictures():
    screensaver = DigiKamScreensaver()
    screensaver.copy_pictures()


def main():
    pass


if __name__ == "__main__":
    main()
