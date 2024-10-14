import tkinter as tk


def screen_saver():
    window = tk.Tk()
    window.attributes("-fullscreen", True)
    window.title("screen_saver!")

    label = tk.Label(window, text="Screen saver!")
    label.pack()

    window.mainloop()


def main():
    screen_saver()


if __name__ == "__main__":
    main()
