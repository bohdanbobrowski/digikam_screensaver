import os
import sqlite3
import tkinter as tk

from digikam_screensaver.settings import DigiKamScreensaverSettings


class DigiKamScreenSaver:
    def __init__(self):
        self.settings = DigiKamScreensaverSettings()
        self.con = sqlite3.connect(self.settings.database_path)
        self.crsr = self.con.cursor()

        self.pictures = self._get_pictures()

        self.window = tk.Tk()
        self.window.attributes("-fullscreen", True)
        self.window.title("screen_saver!")
        self.window.configure(background="black")
        for p in self.pictures:
            label = tk.Label(self.window, text=p)
            label.pack()
        self.window.mainloop()

    def _get_query(self) -> str:
        sub_query = "SELECT imageid FROM ImageInformation ii "
        sub_query += f'WHERE ii.rating > 0 AND ii.format = "JPG" ORDER BY RANDOM() LIMIT {self.settings.limit} '
        query = 'SELECT CONCAT(a.relativePath, "/" , i.name) as file_path, i.uniqueHash, i.name as hash FROM Images i '
        query += "LEFT JOIN Albums a ON a.id == i.album "
        query += f"WHERE i.id IN ({sub_query}) "
        query += "ORDER BY RANDOM();"
        return query

    def _get_pictures(self):
        pictures = []
        result = self.crsr.execute(self._get_query())
        for f in result.fetchall():
            file_path = f[0].replace("/", "\\")[1:]
            source_file = os.path.join(self.settings.pictures_path, file_path)
            if os.path.isfile(source_file):
                pictures.append(file_path)
        return pictures

def main():
    DigiKamScreenSaver()


if __name__ == "__main__":
    main()
