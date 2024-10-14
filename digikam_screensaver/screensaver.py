import os
import sqlite3
from tkinter import *

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
        self.tk_images = []
        self.tk_margins = []

        self.window = Tk()
        self.window.attributes("-fullscreen", True)
        self.window.title("screen_saver!")
        self.window.configure(background="black")
        # label = Label(self.window, text=self.pictures[0])
        # label.pack()
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.canvas = Canvas(self.window, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self.show_image()
        self.window.mainloop()

    def show_image(self, i=0):
        self.canvas.delete("all")
        if i >= len(self.pictures):
            i = 0
        if i not in self.tk_images:
            image_pil = Image.open(os.path.join(self.settings.pictures_path, self.pictures[i]))
            if image_pil.height < image_pil.width:
                new_height = self.height
                new_width = int(new_height * image_pil.width / image_pil.height)
            else:
                new_width = self.width
                new_height = int(new_width * image_pil.height / image_pil.width)
            self.canvas.pack()
            resized_image_pil = image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_margins.append(int((self.width - new_width) / 2))
            self.tk_images.append(ImageTk.PhotoImage(resized_image_pil))
        self.canvas.create_image(self.tk_margins[i], 0, anchor=NW, image=self.tk_images[i])
        self.window.after(self.settings.timeout, self.show_image, i + 1)

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
