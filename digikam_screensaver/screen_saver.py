import os
import sqlite3
import sys
from tkinter import NW, Canvas, Tk, messagebox

from PIL import ExifTags, Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from digikam_screensaver.settings import DigiKamScreensaverSettings


class DigiKamScreenSaver:
    def __init__(self):
        self.settings = DigiKamScreensaverSettings()
        self.con = self.cursor = None
        self.pictures = self.tk_images = self.tk_margins = []
        self.width = self.height = self.canvas = None
        self.window = Tk()

    def screensaver(self):
        if os.path.isfile(self.settings.database_path):
            print(f"Digikam database {self.settings.database_path} exist.")
        else:
            print(f"Digikam database {self.settings.database_path} not found.")
            exit()
        self.con = sqlite3.connect(self.settings.database_path)
        self.cursor = self.con.cursor()
        self.pictures = self._get_pictures()
        self.tk_images = []
        self.tk_margins = []
        self.window.attributes("-fullscreen", True)
        self.window.title("screen_saver!")
        self.window.configure(background="black")
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.canvas = Canvas(self.window, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self._show_image()
        self.window.mainloop()

    def configuration(self):
        messagebox.showinfo("showinfo", "Not implemented yet LOL")
        self.window.mainloop()

    @staticmethod
    def _rotate_image(image_pil: Image) -> Image:
        orientation_tag = None
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                orientation_tag = orientation
                break
        try:
            if orientation_tag:
                exif = image_pil._getexif()
                if exif[orientation_tag] == 3:
                    image_pil = image_pil.rotate(180, expand=True)
                elif exif[orientation_tag] == 6:
                    image_pil = image_pil.rotate(270, expand=True)
                elif exif[orientation_tag] == 8:
                    image_pil = image_pil.rotate(90, expand=True)
        except KeyError:
            pass
        return image_pil

    def _resize_image(self, image_pil: Image) -> Image:
        new_height = self.height
        new_width = int(new_height * image_pil.width / image_pil.height)
        if new_width > self.width:
            new_width = self.width
            new_height = int(new_width * image_pil.height / image_pil.width)
        return image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _add_caption(self, image_pil: Image, caption: str) -> Image:
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
        my_font = ImageFont.truetype(os.path.join(assets_dir, self.settings.font_name), 20)
        blurred = Image.new("RGBA", image_pil.size)
        draw = ImageDraw.Draw(blurred)
        draw.text((10, image_pil.height - 30), caption, font=my_font, fill="black")
        blurred = blurred.filter(ImageFilter.BoxBlur(7))
        image_pil.paste(blurred, blurred)
        image_draw = ImageDraw.Draw(image_pil)
        image_draw.text((10, image_pil.height - 30), caption, font=my_font, fill="white")
        return image_pil

    def _show_image(self, i=0):
        self.canvas.delete("all")
        if i >= len(self.pictures):
            i = 0
        if i not in self.tk_images:
            image_pil = Image.open(os.path.join(self.settings.pictures_path, self.pictures[i]))
            image_pil = self._rotate_image(image_pil)
            image_pil = self._resize_image(image_pil)
            image_pil = self._add_caption(image_pil, self.pictures[i])
            self.tk_margins.append((int((self.width - image_pil.width) / 2), int((self.height - image_pil.height) / 2)))
            self.tk_images.append(ImageTk.PhotoImage(image_pil))
        self.canvas.create_image(self.tk_margins[i][0], self.tk_margins[i][1], anchor=NW, image=self.tk_images[i])
        self.canvas.pack()
        self.window.after(self.settings.timeout, self._show_image, i + 1)

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
        result = self.cursor.execute(self._get_query())
        for f in result.fetchall():
            if f[0] is not None:
                file_path = f[0].replace("/", "\\")[1:]
                source_file = os.path.join(self.settings.pictures_path, file_path)
                if os.path.isfile(source_file):
                    pictures.append(file_path)
        return pictures


def screen_saver():
    """
    /p - Show the screensaver in the screensaver selection dialog box
    /c - Show the screensaver configuration dialog box
    /s - Show the screensaver full-screen
    """

    digikam_screensaver = DigiKamScreenSaver()
    if "/c" in sys.argv:
        digikam_screensaver.configuration()
    else:
        digikam_screensaver.screensaver()


if __name__ == "__main__":
    screen_saver()
