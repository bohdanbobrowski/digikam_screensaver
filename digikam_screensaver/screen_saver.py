import json
import logging
import os
import shlex
import sqlite3
import sys
import webbrowser
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
    Radiobutton,
    S,
    StringVar,
    Tk,
    W,
    font,
)

import psutil  # type: ignore
from PIL import ExifTags, Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from digikam_screensaver.settings import DigiKamScreenSaverSettings, DigiKamScreenSaverSettingsHandler

APP_NAME: str = "DigiKam Screensaver"
VERSION: str = "1.1"
CONFIG_PATH: str = os.path.join(str(os.getenv("LOCALAPPDATA")), "digikam_screensaver")

if not os.path.exists(CONFIG_PATH):
    os.makedirs(CONFIG_PATH)

logging.basicConfig(
    filename=os.path.join(CONFIG_PATH, "debug.log"),
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(APP_NAME)
logger.info(f"Running {APP_NAME} v.{VERSION}")


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
        self.font_families = sorted(list(font.families()))
        self.file_paths: FilePaths = FilePaths()

        validate_numeric = (self.root.register(self._validate_numeric), "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")

        self.pictures_path_label = Label(self.root, text="Pictures path:")
        self.pictures_path_label.grid(row=0, column=0, sticky=E, pady=5, padx=5)
        self.pictures_path_variable = StringVar()
        self.pictures_path_entry = Entry(self.root, textvariable=self.pictures_path_variable)
        self.pictures_path_entry.grid(row=0, column=1, sticky=W, pady=5, padx=5)
        self.pictures_path_variable.set(self.settings.pictures_path)

        self.database_file_label = Label(self.root, text="Digikam database file name:")
        self.database_file_label.grid(row=1, column=0, sticky=E, pady=5, padx=5)
        self.database_file_variable = StringVar(value=self.settings.database_file)
        self.database_file_entry = Entry(self.root, textvariable=self.database_file_variable)
        self.database_file_entry.grid(row=1, column=1, sticky=W, pady=5, padx=5)

        self.font_name_label = Label(self.root, text="Caption font name:")
        self.font_name_label.grid(row=2, column=0, sticky=E, pady=5, padx=5)
        self.font_name_variable = StringVar(value=self.settings.font_name)
        self.font_name_entry = OptionMenu(self.root, self.font_name_variable, *self.font_families)
        self.font_name_entry.grid(row=2, column=1, sticky=W, pady=5, padx=5)

        self.font_size_label = Label(self.root, text="Caption font size:")
        self.font_size_label.grid(row=3, column=0, sticky=E, pady=5, padx=5)
        self.font_size_variable = IntVar(value=self.settings.font_size)
        self.font_size_entry = Entry(
            root, textvariable=self.font_size_variable, validate="key", validatecommand=validate_numeric
        )
        self.font_size_entry.grid(row=3, column=1, sticky=W, pady=5, padx=5)

        self.timeout_label = Label(self.root, text="Slideshow timeout:")
        self.timeout_label.grid(row=4, column=0, sticky=E, pady=5, padx=5)
        self.timeout_variable = IntVar(value=self.settings.timeout)
        self.timeout_entry = Entry(
            root, textvariable=self.timeout_variable, validate="key", validatecommand=validate_numeric
        )
        self.timeout_entry.grid(row=4, column=1, sticky=W, pady=5, padx=5)

        values = {
            "☆☆☆☆☆": 0,
            "★☆☆☆☆": 1,
            "★★☆☆☆": 2,
            "★★★☆☆": 3,
            "★★★★☆": 4,
            "★★★★★": 5,
        }

        self.filter_value = IntVar(self.root, self.settings.filter)
        filter_button_row = 6
        self.filter_label = Label(self.root, text="Min. picture rating:")
        self.filter_label.grid(row=filter_button_row, column=0, sticky=E, pady=5, padx=5)
        for label, value in values.items():
            filter_button = Radiobutton(
                self.root,
                text=label,
                variable=self.filter_value,
                value=value,
            )
            filter_button.grid(row=filter_button_row, column=1, sticky=W, pady=0, padx=5)
            filter_button_row += 1

        self.ok_button = Button(self.root, text="OK", command=self._okay)
        self.ok_button.grid(row=filter_button_row, column=0, sticky=E, pady=5, padx=5)

        self.cancel_button = Button(self.root, text="Cancel", command=self._cancel)
        self.cancel_button.grid(row=filter_button_row, column=1, sticky=W, pady=5, padx=5)

    @staticmethod
    def _validate_numeric(
        action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name
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
        self.settings.filter = self.filter_value.get()
        settings_handler = DigiKamScreenSaverSettingsHandler()
        settings_handler.save(self.settings)
        try:
            os.remove(self.file_paths.cache)
        except FileNotFoundError:
            pass
        self.root.destroy()

    def _cancel(self):
        self.root.destroy()


class FilePaths:
    avoid: str = os.path.join(CONFIG_PATH, "avoid.csv")
    cache: str = os.path.join(CONFIG_PATH, "cache.json")
    history: str = os.path.join(CONFIG_PATH, "history.csv")


class DigiKamScreenSaver:
    def __init__(self, target_window_handler: int | None = None):
        self._current_image: str | None = None
        self._tk_image: str | None = None
        self.file_paths: FilePaths = FilePaths()
        self.target_window_handler = target_window_handler
        self.settings_handler = DigiKamScreenSaverSettingsHandler()
        self.settings = self.settings_handler.read()
        self.pictures: list[str] = []
        self.width, self.height = (640, 480)
        self.canvas = None
        self.window = None
        self.configuration_form = None
        self._extensions: list[str] = ["JPG", "GIF", "PNG"]
        self._demo_mode: bool = False
        self.history: dict = self._read_history()
        self.avoid_images: set[str] = self._read_avoid_images()

    def _exit_scr(self, event: Event):
        """Exit screensaver."""
        if isinstance(event, Event):
            if event.keycode == 112:
                # On F1 open GitHub page in default web browser:
                webbrowser.open("https://github.com/bohdanbobrowski/digikam_screensaver")
            elif event.keycode == 123:
                # On F12 open last image in default program:
                if self._current_image is not None:
                    webbrowser.open(self._current_image)
        if self.window is not None:
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
            try:
                self._current_image = current_image
                image_pil = Image.open(self._current_image)
                image_pil = self._rotate_image(image_pil)
                image_pil = self._resize_image(image_pil)
                tk_margins = (int((self.width - image_pil.width) / 2), int((self.height - image_pil.height) / 2))
                self._tk_image = ImageTk.PhotoImage(image_pil)
                self.canvas.delete("all")
                self.canvas.create_image(tk_margins[0], tk_margins[1], anchor=NW, image=self._tk_image)
                if not self._demo_mode:
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
                    logger.info(f"Image loaded: {current_image}")
                    self._write_history(current_image)
                    memory_used = psutil.Process(os.getpid()).memory_info().rss / 1024**2
                    logger.info(f"Memory used: {memory_used}")
                self.canvas.pack()
            except (OSError, Image.DecompressionBombError) as e:
                self.avoid_images.add(current_image)
                self._write_avoid_images()
                logger.error(f"Error loading file: {current_image}")
                logger.error(f"Exception: {e}")
        else:
            logger.error(f"Image does not exist: {current_image}")
        self.window.grab_set()
        self.window.focus()
        self.window.focus_force()
        self.window.after(self.settings.timeout, self._show_image, i + 1)

    def _read_avoid_images(self) -> set[str]:
        avoid_images = set()
        if os.path.isfile(self.file_paths.avoid):
            with open(self.file_paths.avoid) as f:
                file_content = f.read()
                avoid_images = set(file_content.split("\n"))
        return avoid_images

    def _write_avoid_images(self):
        with open(self.file_paths.avoid, "w") as f:
            f.write("\n".join(self.avoid_images))

    def _read_history(self) -> dict:
        history = {}
        if os.path.isfile(self.file_paths.history):
            with open(self.file_paths.history) as f:
                file_content = f.read()
            _history_lines = file_content.split("\n")
            for _line in _history_lines:
                r = _line.split(",")
                _hk = "".join(r[:1]).strip('"')
                _hv = ",".join(r[1:]).strip('"')
                if _hk == "" or _hv == "":
                    continue
                history[_hk] = _hv
        return history

    def _write_history(self, file_name: str):
        file_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history[file_datetime] = file_name
        if len(self.history.keys()) > self.settings.history_size:
            _history_keys = list(self.history.keys())
            _too_much = len(self.history.keys()) - self.settings.history_size
            _keys_to_remove = _history_keys[:_too_much]
            for k in _keys_to_remove:
                self.history.pop(k, None)
        history_content = ""
        for ts, fn in self.history.items():
            history_content += f'"{ts}","{fn}"\n'
        with open(self.file_paths.history, "w") as f:
            f.write(history_content)

    def _get_query(self) -> str:
        sub_query = "SELECT imageid FROM ImageInformation ii WHERE "
        if self.settings.filter > 0:
            sub_query += f"ii.rating > {self.settings.filter - 1} AND "
        sub_query += f'ii.format in ("{'", "'.join(self._extensions)}") '
        sub_query += f"ORDER BY RANDOM() LIMIT {self.settings.limit} "
        query = 'SELECT a.relativePath || "/" || i.name as file_path, i.uniqueHash, i.name as hash FROM Images i '
        query += "LEFT JOIN Albums a ON a.id == i.album "
        query += f"WHERE i.id IN ({sub_query}) "
        query += "ORDER BY RANDOM();"
        logging.debug(f"QUERY: {query}")
        return query

    def _set_demo_slides(self):
        self._demo_mode = True
        self.pictures = [
            self._asset_path("default_slide_1.gif"),
            self._asset_path("default_slide_2.gif"),
        ]

    def _get_pictures(self):
        try:
            self._demo_mode = False
            con = sqlite3.connect(f"file:/{self.settings.database_path}?mode=ro", uri=True)
            cursor = con.cursor()
            self.pictures = []
            db_query = self._get_query()
            result = cursor.execute(db_query)
            for f in result.fetchall():
                if f[0] is not None:
                    file_path = f[0].replace("/", "\\")[1:]
                    source_file = os.path.join(self.settings.pictures_path, file_path)
                    if source_file in self.avoid_images:
                        logger.warning(f"Avoiding image {source_file}")
                        continue
                    if source_file not in self.history.values():
                        pass
                    if os.path.isfile(source_file):
                        self.pictures.append(file_path)
            if self.pictures:
                self._write_cache(json.dumps(self.pictures))
            else:
                logger.error("The database is configured correctly but no pictures found")
                logger.error(db_query)
                self._set_demo_slides()
        except sqlite3.OperationalError as e:
            logger.error(f"Database configuration error: {e}")
            self._set_demo_slides()

    @staticmethod
    def _asset_path(filename: str) -> str:
        try:
            base_path = sys._MEIPASS  # type: ignore
        except AttributeError:
            base_path = os.path.abspath("./assets/")
        if os.path.isfile(os.path.join(base_path, filename)):
            return os.path.join(base_path, filename)
        return os.path.join(os.path.abspath("../assets/"), filename)

    def _write_cache(self, content: str):
        with open(self.file_paths.cache, "w") as f:
            f.write(content)

    def _read_cache(self):
        try:
            with open(self.file_paths.cache) as f:
                self.pictures = json.load(f)
            shuffle(self.pictures)
        except FileNotFoundError:
            self._get_pictures()

    def screensaver(self):
        self.window = Tk()
        self.window.title(APP_NAME)
        self.window.configure(background="black", cursor="none")
        self.window.attributes("-fullscreen", True)
        self.window.attributes("-topmost", True)
        self.window.grab_set()
        self.window.focus()
        self.window.focus_force()
        self.window.bind("<Key>", self._exit_scr)
        self.window.bind("<Motion>", self._exit_scr)
        self.window.bind("<Button>", self._exit_scr)
        self._read_cache()
        self.width = self.window.winfo_screenwidth()
        self.height = self.window.winfo_screenheight()
        self.canvas = Canvas(self.window, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self._show_image()
        self.window.mainloop()

    def preview(self):
        """This function should display screensaver preview in small window of windows screensaver picker.

        But there are some problems with that:

        1. Even if I use win32gui.SetParent to put screensaver inside preview window nothing shows up there (except
           some glitches).
        2. In preview mode "Digikam Screensaver" is started and I don't know how to close it.

        I found that this functionality is often omitted in screensavers written in c/c++, but there are examples that
        it works:
        - https://github.com/rgoring/asciiquarium/tree/master
        """
        pass

    def configuration(self):
        self.window = Tk()
        self.window.iconbitmap(asset_path("digikam.ico"))
        self.window.title(APP_NAME)
        self.window.title(f"{APP_NAME} - Configuration")
        self.window.geometry("320x360")
        self.window.resizable(width=False, height=False)
        self.window.attributes("-topmost", True)
        self.configuration_form = DigiKamScreenSaverConfigurationForm(self.window, self.settings)
        self.window.mainloop()


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

    ...where 1234 is parent window handler (win32gui stuff)

    /d - additionally for debug purposes
    """

    run_mode = None
    if len(sys.argv) > 1:
        if sys.argv[len(sys.argv) - 1].lower().startswith("/c") or sys.argv[len(sys.argv) - 2].lower().startswith("/c"):
            run_mode = "configuration"
        if sys.argv[len(sys.argv) - 1].lower().startswith("/p") or sys.argv[len(sys.argv) - 2].lower().startswith("/p"):
            run_mode = "preview"
        if sys.argv[len(sys.argv) - 1].lower().startswith("/s") or sys.argv[len(sys.argv) - 2].lower().startswith("/s"):
            run_mode = "screensaver"

    # Add this argument to see all logs
    if "/d" in sys.argv:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    window_handler = None
    if len(sys.argv) > 1:
        try:
            window_handler = int(sys.argv[len(sys.argv) - 1])
            logger.info(f"Target window handler: {window_handler}")
        except ValueError:
            pass

    if run_mode:
        logger.info(f"Starting {run_mode}: " + " ".join(sys.argv))
        digikam_screensaver = DigiKamScreenSaver(target_window_handler=window_handler)
        runner = getattr(digikam_screensaver, run_mode)
        runner()


if __name__ == "__main__":
    screen_saver()
