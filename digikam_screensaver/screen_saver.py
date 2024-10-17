import json
import os
import shlex
import sqlite3
import subprocess
import sys
import winreg
from datetime import datetime
from random import shuffle
from tkinter import (
    NW,
    Button,
    Canvas,
    E,
    Entry,
    Event,
    IntVar,
    Label,
    OptionMenu,
    S,
    StringVar,
    Tk,
    W,
    font,
    messagebox,
)

import psutil
from PIL import ExifTags, Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from digikam_screensaver.settings import DigiKamScreenSaverSettings, DigiKamScreenSaverSettingsHandler

APP_NAME = "DigiKam Screensaver"


def write_debug_log(message: str):
    f_path = os.path.join(os.getenv("LOCALAPPDATA"), "digikam_screensaver", "debug.log")  # type: ignore
    with open(f_path, "a") as f:
        date = datetime.now()
        f.write(f"{date.strftime("%Y-%m-%d %H:%M:%S")} {message}\n")


def write_history(file_name: str):
    f_path = os.path.join(os.getenv("LOCALAPPDATA"), "digikam_screensaver", "history.csv")  # type: ignore
    with open(f_path, "a") as f:
        date = datetime.now()
        f.write(f"\"{date.strftime("%Y-%m-%d %H:%M:%S")}\",\"{file_name}\"\n")


def get_default_windows_app(suffix):
    """https://stackoverflow.com/a/48121945"""
    class_root = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, suffix)
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf"{class_root}\shell\open\command") as key:
        command = winreg.QueryValueEx(key, "")[0]
        return shlex.split(command)[0]


def asset_path(filename: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath("./assets/")
    if os.path.isfile(os.path.join(base_path, filename)):
        return os.path.join(base_path, filename)
    return os.path.join(os.path.abspath("../assets/"), filename)


class DigiKamScreenSaverConfigurationForm:
    def __init__(self, root: Tk, settings: DigiKamScreenSaverSettings):
        self.root = root
        self.settings = settings

        validate_numeric = (self.root.register(self._validate_numeric), "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")

        self.pictures_path_label = Label(self.root, text="Pictures path:")
        self.pictures_path_label.grid(row=0, column=0, sticky=E, pady=5, padx=5)
        self.pictures_path_variable = StringVar()
        self.pictures_path_entry = Entry(self.root, textvariable=self.pictures_path_variable)
        self.pictures_path_entry.grid(row=0, column=1, sticky=W, pady=5, padx=5)
        self.pictures_path_variable.set(self.settings.pictures_path)

        self.database_file_label = Label(self.root, text="Digikam database file name:")
        self.database_file_label.grid(row=1, column=0, sticky=E, pady=5, padx=5)
        self.database_file_variable = StringVar()
        self.database_file_entry = Entry(self.root, textvariable=self.database_file_variable)
        self.database_file_variable.set(self.settings.database_file)
        self.database_file_entry.grid(row=1, column=1, sticky=W, pady=5, padx=5)

        self.font_name_label = Label(self.root, text="Caption font name:")
        self.font_name_label.grid(row=2, column=0, sticky=E, pady=5, padx=5)
        self.font_name_variable = StringVar()
        self.font_name_variable.set(self.settings.font_name)
        self.font_name_entry = OptionMenu(self.root, self.font_name_variable, *font.families())
        self.font_name_entry.grid(row=2, column=1, sticky=W, pady=5, padx=5)

        self.font_size_label = Label(self.root, text="Caption font size:")
        self.font_size_label.grid(row=3, column=0, sticky=E, pady=5, padx=5)
        self.font_size_variable = IntVar()
        self.font_size_entry = Entry(
            root, textvariable=self.font_size_variable, validate="key", validatecommand=validate_numeric
        )
        self.font_size_variable.set(self.settings.font_size)
        self.font_size_entry.grid(row=3, column=1, sticky=W, pady=5, padx=5)

        self.timeout_label = Label(self.root, text="Slideshow timeout:")
        self.timeout_label.grid(row=4, column=0, sticky=E, pady=5, padx=5)
        self.timeout_variable = IntVar()
        self.timeout_entry = Entry(
            root, textvariable=self.timeout_variable, validate="key", validatecommand=validate_numeric
        )
        self.timeout_variable.set(self.settings.timeout)
        self.timeout_entry.grid(row=4, column=1, sticky=W, pady=5, padx=5)

        self.ok_button = Button(self.root, text="OK", command=self._okay)
        self.ok_button.grid(row=5, column=0, sticky=E, pady=5, padx=5)

        self.cancel_button = Button(self.root, text="Cancel", command=self._cancel)
        self.cancel_button.grid(row=5, column=1, sticky=W, pady=5, padx=5)

    def _validate_numeric(
        self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name
    ):
        if str.isdigit(value_if_allowed):
            return True
        else:
            return False

    def _okay(self):
        self.settings.pictures_path = self.pictures_path_variable.get()
        self.settings.database_file = self.database_file_variable.get()
        self.settings.font_name = self.font_name_variable.get()
        self.settings.font_size = self.font_size_variable.get()
        self.settings.timeout = self.timeout_variable.get()
        settings_handler = DigiKamScreenSaverSettingsHandler()
        settings_handler.save(self.settings)
        self.root.destroy()

    def _cancel(self):
        self.root.destroy()


class DigiKamScreenSaver:
    def __init__(self, target_window_handler: int | None = None):
        self.target_window_handler = target_window_handler
        self.settings_handler = DigiKamScreenSaverSettingsHandler()
        self.settings = self.settings_handler.read()
        self._current_image = self._tk_image = None
        self.pictures: list[str] = []
        self.width = 640
        self.height = 480
        self.canvas = None
        self.window = None
        self.configuration_form = None
        self.cache_file = os.path.join(os.getenv("LOCALAPPDATA"), "digikam_screensaver", "cache.json")  # type: ignore

    def screensaver(self):
        self.window = Tk()
        self.window.title(APP_NAME)
        # windows = Desktop(backend="uia").windows()
        # for w in windows:
        #     write_debug_log(f'Handler {w.handle} is for "{w.window_text()}".')
        self.window.configure(background="black", cursor="none")
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-topmost", True)
        self.window.grab_set()
        self.window.focus()
        self.window.focus_force()
        self.window.bind("<Key>", self._exit_scr)
        self.window.bind("<Motion>", self._exit_scr)
        self.window.bind("<Button>", self._exit_scr)
        if not os.path.isfile(self.settings.database_path):
            messagebox.showinfo(
                f"Digikam database {self.settings.database_path} not found.",
                f"{APP_NAME} needs some configuration.",
            )
            exit()
        self._read_cache()
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.canvas = Canvas(self.window, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self._show_image()
        self.window.mainloop()

    def preview(self):
        """TODO: this part needs reimplementation"""
        pass

    def configuration(self):
        self.window = Tk()
        self.window.iconbitmap(asset_path("digikam.ico"))
        self.window.title(APP_NAME)
        self.window.title(f"{APP_NAME} - Configuration")
        self.window.geometry("400x300")
        self.configuration_form = DigiKamScreenSaverConfigurationForm(self.window, self.settings)
        self.window.mainloop()

    @staticmethod
    def open_image(path):
        image_viewer = {"linux": "xdg-open", "win32": "explorer", "darwin": "open"}[sys.platform]
        subprocess.run([image_viewer, path])

    def _exit_scr(self, event: Event):
        """Exit screensaver but when F12 pressed open last image in default program."""
        if isinstance(event, Event) and event.keycode == 123:
            self.open_image(self._current_image)
        self.window.destroy()

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
            self._get_pictures()
        current_image = os.path.join(self.settings.pictures_path, self.pictures[i])
        if os.path.isfile(current_image):
            self._current_image = current_image
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
            write_debug_log(f"Image loaded: {current_image}")
            write_history(current_image)
            memory_used = psutil.Process(os.getpid()).memory_info().rss / 1024**2
            write_debug_log(f"Memory used: {memory_used}")
            self.canvas.pack()
        else:
            write_debug_log(f"Image does not exist: {current_image}")
        self.window.grab_set()
        self.window.focus()
        self.window.focus_force()
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
        con = sqlite3.connect(f"file:/{self.settings.database_path}?mode=ro", uri=True)
        cursor = con.cursor()
        self.pictures = []
        result = cursor.execute(self._get_query())
        for f in result.fetchall():
            if f[0] is not None:
                file_path = f[0].replace("/", "\\")[1:]
                source_file = os.path.join(self.settings.pictures_path, file_path)
                if os.path.isfile(source_file):
                    self.pictures.append(file_path)
        self._write_cache(json.dumps(self.pictures))

    def _write_cache(self, content: str):
        with open(self.cache_file, "w") as f:
            f.write(content)

    def _read_cache(self):
        try:
            with open(self.cache_file) as f:
                self.pictures = json.load(f)
            shuffle(self.pictures)
        except FileNotFoundError:
            self._get_pictures()


def screen_saver():
    """
    /p - Show the screensaver in the screensaver selection dialog box
    /s - Show the screensaver full-screen
    /c - Show the screensaver configuration dialog box

    Possible syntax:

    /p:1234
    /s:1234
    /p 1234
    /s 1234

    ...where 1234 is (I guess) parent Windows handler.

    """

    run_mode = None
    if len(sys.argv) > 1:
        if sys.argv[len(sys.argv) - 1].startswith("/c") or sys.argv[len(sys.argv) - 2].startswith("/c"):
            run_mode = "configuration"
        if sys.argv[len(sys.argv) - 1].startswith("/s") or sys.argv[len(sys.argv) - 2].startswith("/s"):
            run_mode = "screensaver"
        if sys.argv[len(sys.argv) - 1].startswith("/p") or sys.argv[len(sys.argv) - 2].startswith("/p"):
            run_mode = "preview"

    window_handler = None
    if len(sys.argv) > 1:
        try:
            window_handler = int(sys.argv[len(sys.argv) - 1])
            write_debug_log(f"Target window handler: {window_handler}")
        except ValueError:
            pass

    if run_mode:
        digikam_screensaver = DigiKamScreenSaver(target_window_handler=window_handler)
        write_debug_log(f"Started {run_mode}: " + " ".join(sys.argv))
        runner = getattr(digikam_screensaver, run_mode)
        runner()


if __name__ == "__main__":
    screen_saver()
