import os
import sqlite3
import sys
from tkinter import NW, Canvas, Event, S, Tk, messagebox

from PIL import ExifTags, Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from digikam_screensaver.settings import DigiKamScreensaverSettings

APP_NAME = "DigiKam Screensaver"


class DigiKamScreenSaver:
    def __init__(self):
        self.settings = DigiKamScreensaverSettings()
        self.con = self.cursor = None
        self._current_image = self._tk_image = None
        self.pictures = []
        self.width = self.height = self.canvas = None
        self.window = Tk()
        self.window.title(APP_NAME)

    def screensaver(self):
        self.window.attributes("-fullscreen", True)
        if not os.path.isfile(self.settings.database_path):
            messagebox.showinfo(
                f"Digikam database {self.settings.database_path} not found.",
                f"{APP_NAME} needs some configuration.",
            )
            exit()
        self.con = sqlite3.connect(self.settings.database_path)
        self.cursor = self.con.cursor()
        self.pictures = self._get_pictures()
        self.window.configure(background="black", cursor="none")
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.canvas = Canvas(self.window, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self._show_image()
        self.window.bind_all("<Key>", self._exit_scr)
        self.window.bind_all("<Motion>", self._exit_scr)
        self.window.bind_all("<Button>", self._exit_scr)
        self.window.mainloop()

    def _exit_scr(self, event: Event):
        """Exit screensaver but when F12 pressed open last image in default program."""
        if isinstance(event, Event) and event.keycode == 123:
            os.startfile(self._current_image)
        exit()

    def configuration(self):
        """TODO: Implement configuration window and save/load configuration into yaml."""
        messagebox.showinfo("showinfo", "Not implemented yet LOL")
        self.window.mainloop()

    @staticmethod
    def _rotate_image(image_pil: Image.Image) -> Image.Image:
        orientation_tag = None
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                orientation_tag = orientation
                break
        try:
            if orientation_tag:
                exif = image_pil.getexif()
                if exif[orientation_tag] == 3:
                    image_pil = image_pil.rotate(180, expand=True)
                elif exif[orientation_tag] == 6:
                    image_pil = image_pil.rotate(270, expand=True)
                elif exif[orientation_tag] == 8:
                    image_pil = image_pil.rotate(90, expand=True)
        except KeyError:
            pass
        return image_pil

    def _resize_image(self, image_pil: Image.Image) -> Image.Image:
        new_height = self.height
        new_width = int(new_height * image_pil.width / image_pil.height)
        if new_width > self.width:
            new_width = self.width
            new_height = int(new_width * image_pil.height / image_pil.width)
        return image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _add_caption(self, image_pil: Image.Image, caption: str) -> Image.Image:
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
        my_font = ImageFont.truetype(os.path.join(assets_dir, self.settings.font_name), 20)
        blurred = Image.new("RGBA", image_pil.size)
        draw = ImageDraw.Draw(blurred)
        draw.text((10, image_pil.height - 30), caption, font=my_font, fill="black")
        blurred = blurred.filter(ImageFilter.BoxBlur(7))
        image_pil.paste(blurred, blurred)  # type: ignore
        image_draw = ImageDraw.Draw(image_pil)
        image_draw.text((10, image_pil.height - 30), caption, font=my_font, fill="white")
        return image_pil

    def _show_image(self, i=0):
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
        if i >= len(self.pictures):
            i = 0
            self.pictures = self._get_pictures()
        self._current_image = os.path.join(self.settings.pictures_path, self.pictures[i])
        if os.path.isfile(self._current_image):
            image_pil = Image.open(self._current_image)
            image_pil = self._rotate_image(image_pil)
            image_pil = self._resize_image(image_pil)
            tk_margins = (int((self.width - image_pil.width) / 2), int((self.height - image_pil.height) / 2))
            self._tk_image = ImageTk.PhotoImage(image_pil)
            self.canvas.delete("all")
            self.canvas.create_image(tk_margins[0], tk_margins[1], anchor=NW, image=self._tk_image)
            self.canvas.create_text(
                self.width / 2 + 1,
                self.height - 9,
                text=self.pictures[i],
                fill="black",
                font=(self.settings.font_name, self.settings.font_size),
                anchor=S,
            )
            self.canvas.create_text(
                self.width / 2,
                self.height - 10,
                text=self.pictures[i],
                fill="white",
                font=(self.settings.font_name, self.settings.font_size),
                anchor=S,
            )
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
