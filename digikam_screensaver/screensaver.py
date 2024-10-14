import os
import sqlite3
import tkinter as tk

from PIL import Image, ImageTk

from digikam_screensaver.settings import DigiKamScreensaverSettings


class DigiKamScreenSaver:
    def __init__(self):
        self.settings = DigiKamScreensaverSettings()
        if os.path.isfile(self.settings.database_path):
            print(f"Digikam database {self.settings.database_path} exist.")
        else:
            print(f"Digikam database {self.settings.database_path} not found.")
            exit()
        self.con = sqlite3.connect(self.settings.database_path)
        self.crsr = self.con.cursor()

        self.pictures = self._get_pictures()

        self.window = tk.Tk()
        self.window.attributes("-fullscreen", True)
        self.window.title("screen_saver!")
        self.window.configure(background="black")
        label = tk.Label(self.window, text=self.pictures[0])
        label.pack()
        width = self.window.winfo_screenwidth()
        height = self.window.winfo_screenheight()
        canvas = tk.Canvas(self.window, width=width, height=height)
        canvas.pack()
        image_pil = Image.open(os.path.join(self.settings.pictures_path, self.pictures[0]))
        resized_image_pil = image_pil.resize((width, height))
        photo_image = ImageTk.PhotoImage(resized_image_pil)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo_image)
        self.window.mainloop()

    def _get_query(self) -> str:
        sub_query = "SELECT imageid FROM ImageInformation ii "
        sub_query += f'WHERE ii.rating > 0 AND ii.format = "JPG" ORDER BY RANDOM() LIMIT {self.settings.limit} '
        query = 'SELECT a.relativePath || "/" || i.name as file_path, i.uniqueHash, i.name as hash FROM Images i '
        query += "LEFT JOIN Albums a ON a.id == i.album "
        query += f"WHERE i.id IN ({sub_query}) "
        query += "ORDER BY RANDOM();"
        return query

    def _get_pictures(self):
        pictures = []
        result = self.crsr.execute(self._get_query())
        for f in result.fetchall():
            if f[0] is not None:
                file_path = f[0].replace("/", "\\")[1:]
                source_file = os.path.join(self.settings.pictures_path, file_path)
                if os.path.isfile(source_file):
                    pictures.append(file_path)
        return pictures


def main():
    DigiKamScreenSaver()


if __name__ == "__main__":
    main()
