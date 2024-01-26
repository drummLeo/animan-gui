import json
import math
import os
import platform
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk, font

import requests
from PIL import Image, UnidentifiedImageError, ImageTk, ImageEnhance, ImageDraw, ImageFont
import PIL
from bs4 import BeautifulSoup
from tkinter.colorchooser import askcolor

import main


class Splash(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent, takefocus=True)
        self.root = parent

        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()

        self.geometry(f"{int(width / 1.8)}x540+{int(width / 4)}+{int(height / 4.2)}")

        if not os.path.isdir(os.path.join(os.path.expanduser('~'), "Animes/Thumbs")):
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes/Thumbs"))

        if not os.path.isfile(os.path.join(os.path.expanduser('~'), "Animes/Thumbs/splash.png")):
            image = requests.get("https://drive.google.com/u/0/uc?id=1UUo9u-TWCChxGlELXtPTf65JW2EfwxWb&export=download"
                                 ).content
            with open(os.path.join(os.path.expanduser('~'), "Animes/Thumbs/splash.png"), "wb") as file:
                file.write(image)

        self.img = tk.PhotoImage(file=os.path.join(os.path.expanduser('~'), "Animes/Thumbs/splash.png"))
        self.load = tk.Canvas(self, bg="#574d4c")
        self.load.create_image(0, 35, anchor="nw", image=self.img)
        self.load.create_text(int(width / 1.6) // 2, 20, text="Inicializando...",
                              font=anime_font(s=28), tags="text")
        self.load.create_oval(int(width / 1.24) // 2, 74, int(width / 3.9), 209,
                              fill="purple", outline="blue")
        self.load.create_text(int(width / 1.55) // 2, 142, text="  Anime\nManager", font=anime_font(s=52))
        self.load.pack(fill=tk.BOTH, expand=1)
        self.overrideredirect(True)
        self.configure(background='#0048FF')
        self.percentage = 0

        self.update()

    def load_bar(self, text='Finalizando', step=5, small_font=False):
        self.percentage += step
        self.load.delete("text")
        self.load.create_rectangle(0, 520, int(self.percentage * (self.winfo_width() / 100)), 540, outline="green",
                                   fill="purple", tags="rect")
        if not small_font:
            self.load.create_text(self.winfo_width() // 2, 20, text=f"{text}... {self.percentage}%",
                                  font=anime_font(s=28), tags="text")
        else:
            self.load.create_text(self.winfo_width() // 2, 20, text=f"{text}... {self.percentage}%",
                                  font=anime_font(), tags="text")
        self.load.update()

    def finish(self):
        self.destroy()
        self.root.deiconify()
        return


class ContextMenu(tk.Listbox):
    def __init__(self, parent, anime_=None, command=None, label='', *args, **kwargs):
        tk.Listbox.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        self.anime_ = anime_

        self.popup_menu = tk.Menu(self, tearoff=0, background='#808080')
        if self.anime_ is not None:
            if self.anime_ not in self.parent.root.fav_anime_list:
                self.popup_menu.add_command(label="Favoritar",
                                            command=self.add_to_fav)
            else:
                self.popup_menu.add_command(label="Remover fav.",
                                            command=self.remove_fav)
            self.popup_menu.add_command(label="Renomear",
                                        command=self.rename_anime)
            self.popup_menu.add_command(label="Remover Anime",
                                        command=self.remove_anime)
            self.popup_menu.add_command(label="Ver no site",
                                        command=self.anime_.call)
        else:
            self.popup_menu.add_command(label=label,
                                        command=command)

        parent.bind("<Button-3>", self.popup)

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root)
            self.popup_menu.after(2000, self.popup_menu.unpost)
        finally:
            self.popup_menu.grab_release()

    def remove_anime(self):
        if messagebox.askyesno(title="Remover Anime",
                               message=f'Tem certeza que quer remover o anime "{self.anime_.name}"?'):
            main.remove_anime(self.anime_)
            try:
                os.remove(os.path.join(os.path.expanduser('~'), f"Animes/Thumbs/{self.anime_.name}.png"))
            except OSError:
                pass
            messagebox.showinfo(title="Remover Anime", message=f'Anime "{self.anime_.name}" removido com sucesso! ' +
                                                               f'O aplicativo será reiniciado!')
            self.parent.master.master.master.master.destroy()
            return MainWindow()

    def rename_anime(self):
        root = tk.Toplevel(self.parent.root)
        root.title("Renomear")
        root.configure(background='#808080')

        label = tk.Label(root, text="Digite o novo nome:", bg='#808080', fg="black", font=button_font())
        label.pack(anchor='n', pady=10)

        new_name = tk.Entry(root, width=root.winfo_width() + 40, font=button_font())
        new_name.insert(0, self.anime_.name)
        new_name.pack(anchor='center', padx=10)

        new_name.bind("<Return>", lambda e: rename())

        def rename():
            if new_name.get().rstrip():
                name = new_name.get().rstrip()
                anime_info = dict()
                with open(self.anime_.file_name, 'r') as file:
                    anime_info.update(json.load(file))
                    anime_info['name'] = name
                with open(self.anime_.file_name, 'w') as file:
                    json.dump(anime_info, file)
                os.rename(self.anime_.file_name, os.path.join(os.path.expanduser('~'), f"Animes/{name}.json"))
                try:
                    os.rename(os.path.join(os.path.expanduser('~'), f"Animes/Thumbs/{self.anime_.name}.png"),
                              os.path.join(os.path.expanduser('~'), f"Animes/Thumbs/{name}.png"))
                except OSError:
                    pass
                if self.anime_ in self.parent.root.fav_anime_list:
                    if self.anime_.new_episode:
                        self.parent.configure(text=name + " \U00002605" + "\n(Novo Episódio!)")
                    else:
                        self.parent.configure(text=name + " \U00002605")
                else:
                    if self.anime_.new_episode:
                        self.parent.configure(text=name + "\n(Novo Episódio!)")
                    else:
                        self.parent.configure(text=name)

                self.anime_.name = name
                self.parent.configure(font=anime_font(self.anime_))

                self.anime_.file_name = os.path.join(os.path.expanduser('~'), f"Animes/{name}.json")

                root.destroy()
                messagebox.showinfo(title="Renomear Anime", message="Anime renomeado com sucesso!")

        button = tk.Button(root, text="Renomear", command=rename, font=button_font(),
                           background='#3CB371', activebackground='#8FBC8F', fg="black")
        button.pack(anchor='s', pady=10, side=tk.BOTTOM)

    def add_to_fav(self):
        directory = os.path.join(os.path.expanduser("~"), "Animes")
        if not os.path.isdir(os.path.join(directory, "Favorites")):
            os.mkdir(os.path.join(directory, "Favorites"))
        os.rename(os.path.join(directory, f"{self.anime_.name}.json"),
                  os.path.join(directory, f"Favorites/{self.anime_.name}.json"))
        self.anime_.file_name = os.path.join(directory, f"Favorites/{self.anime_.name}.json")
        if self.parent.show_name:
            self.parent.configure(text=self.anime_.name + " \U00002605")
        messagebox.showinfo(title="Adicionar Favorito", message="Favorito Adicionado! O programa será reiniciado.")
        self.parent.root.destroy()
        return MainWindow()

    def remove_fav(self):
        directory = os.path.join(os.path.expanduser("~"), "Animes")
        try:
            os.rename(os.path.join(directory, f"Favorites/{self.anime_.name}.json"),
                      os.path.join(directory, f"{self.anime_.name}.json"))
            self.anime_.file_name = os.path.join(directory, f"{self.anime_.name}.json")
            if self.parent.show_name:
                self.parent.configure(text=self.anime_.name)
            messagebox.showinfo(title="Remover Favorito", message="Favorito Removido! O programa será reiniciado.")
            self.parent.root.destroy()
            return MainWindow()
        except OSError:
            messagebox.showerror(message="Erro: Anime não encontrado nos favoritos.")


class Scroller:
    def __init__(self, root, background='white', objects=None):
        if objects is None:
            objects = (Scroller, root.__class__)
        self.objects = objects
        self.root = root
        self.frame = tk.Frame(self.root, background=background)
        self.frame.pack(fill=tk.BOTH, expand=1)

        self.canvas = tk.Canvas(self.frame, background=background)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.bind_wheel()

        self.sec_frame = tk.Frame(self.canvas, background=background)

        self.canvas.create_window((0, 0), window=self.sec_frame, anchor="nw", tags="scroller_window")

        self.must_scroll = True

    def mouse_wheel_handler(self, event):
        if self.must_scroll:
            if isinstance(event.widget, self.objects) or event.widget is self.sec_frame or event.widget is self.canvas:
                if event.num == 5 or event.delta < 0:
                    return 1
                return -1
            else:
                return 0
        else:
            return 0

    def bind_wheel(self):
        self.must_scroll = True
        if platform.system() == "Linux":
            self.root.bind("<Button-4>", lambda e: self.canvas.yview_scroll(self.mouse_wheel_handler(e), "units"))
            self.root.bind("<Button-5>", lambda e: self.canvas.yview_scroll(self.mouse_wheel_handler(e), "units"))
        else:
            self.root.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(self.mouse_wheel_handler(e), "units"))

    def unbind_wheel(self):
        self.must_scroll = False
        if platform.system() == "Linux":
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind("<MouseWheel>")


class EpButton(tk.Button):
    def __init__(self, num, ep_window, ep, anime_, tooltip):
        self.anime_ = anime_
        self.num = num
        self.anime_info = dict()
        self.ep = ep

        if '. "ep"' in self.ep:
            self.ep = self.ep[:self.ep.find('"')] + '"Nenhum titulo oficial ainda."'

        with open(self.anime_.file_name, 'r') as file:
            self.anime_info.update(json.load(file))

        self.ep_window = ep_window
        tk.Button.__init__(self, self.ep_window, text=self.ep, height=1, width=100, command=self.call_anime,
                           bg="#337ED7", activebackground="#6690D0", font=button_font(),
                           fg='black', activeforeground='yellow', borderwidth=5, anchor='w', cursor="hand2")
        self.configure(bg=self.ep_window.master.master.master.root.config_screen.config_info["anime_color"],
                       activebackground=highlight(self.ep_window.master.master.master
                                                  .root.config_screen.config_info["anime_color"]))

        self.bind("<Enter>", lambda e: tooltip.configure(text=self.ep))

        if self.is_last():
            self.configure(background='grey')
        self.pack(fill=tk.X, expand=1)

    def call_anime(self):
        self.ep_window.configure(cursor="watch")
        self.configure(bg="grey")

        self.anime_.last_episode = self.num
        with open(self.anime_.file_name, 'w') as file:
            self.anime_info['last_episode'] = self.num
            json.dump(self.anime_info, file, indent=4)

        self.anime_.call(self.num)

        self.ep_window.configure(cursor="arrow")

    def is_last(self):
        if self.anime_info['last_episode'] == self.num:
            return True
        return False


class EpisodesWindow(tk.Toplevel):
    def __init__(self, root, anime_):
        tk.Toplevel.__init__(self, root, takefocus=True, bg="#363636")

        self.root = root
        self.root.configure(cursor="watch")

        screen_width = self.winfo_screenwidth()
        self.resizable(width=True, height=False)

        self.anime_ = anime_
        self.title(self.anime_.name)

        self.button_list = []

        self.ep_label = tk.Label(self, text="Episódios:", font=button_font(s=20),
                                 bg="#363636", fg="white")
        self.ep_label.pack(pady=5)

        self.scroller = Scroller(self, background=root.config_screen.config_info["bg_color"],
                                 objects=(EpisodesWindow, EpButton))

        self.canvas = tk.Canvas(self, bg="#363636")
        self.canvas.pack(side=tk.BOTTOM, anchor="sw", fill=tk.BOTH)

        self.tooltip = tk.Label(self.canvas, bg="#363636", fg="white", anchor='w')
        self.tooltip.pack(side=tk.LEFT, padx=12, pady=8)

        self.canvas.exit_button = tk.Button(self.canvas, text="Sair", width=14, height=0,
                                            background=self.root.config_screen.config_info["button_color"],
                                            command=self.destroy, foreground="black", activeforeground="black",
                                            activebackground=highlight(
                                                self.root.config_screen.config_info["button_color"]),
                                            font=button_font())
        self.canvas.exit_button.pack(side=tk.RIGHT, anchor="e", padx=12, pady=8)

        if check_internet():
            n = 0
            for ep in self.anime_.get_episodes():
                self.button_list.append(EpButton(n, self.scroller.sec_frame, ep, self.anime_, self.tooltip))
                n += 1
            self.iconphoto(False, tk.PhotoImage(file=os.path.join(
                os.path.expanduser("~"), f"Animes/Thumbs/animan-gui.png")))
        else:
            self.root.configure(cursor="arrow")
            self.destroy()
            messagebox.showerror(message="Erro: verifique sua conexão com a internet.")

        width = int(screen_width / 1.55)

        height = (len(self.button_list) + 3) * 45
        if height > 620:
            height = 620
        else:
            self.scroller.unbind_wheel()

        self.geometry(f"{width}x{height}")

        root.configure(cursor="arrow")


def highlight(color):
    output = '#'
    for n in color[1:]:
        if n in ['0', '1', '2', '3', '4', '5', '6', '7', '8']:
            output += str(int(n) + 1)
        elif n == '9':
            output += 'a'
        elif n == 'a':
            output += 'b'
        elif n == 'b':
            output += 'c'
        elif n == 'c':
            output += 'd'
        elif n == 'd':
            output += 'e'
        else:
            output += 'f'

    return output


class AniButton(tk.Button):
    def __init__(self, root, picture, row, column, anime_):
        width = int(root.winfo_screenwidth() // (16 / 3))
        height = root.winfo_screenheight() // 4
        self.root = root.master.master.master

        self.show_name = not self.root.config_screen.config_info["show_name"]

        self.text = anime_.name if self.show_name else ''

        self.picture = picture

        if anime_ in self.root.fav_anime_list:
            if self.show_name:
                self.text += " \U00002605"
        if anime_.new_episode:
            if self.show_name:
                self.text += "\n(Novo Episódio!)"
        if len(self.text) > 25:
            self.text = self.text[:25] + "..."
        tk.Button.__init__(self, root, image=self.picture, borderwidth=10,
                           text=self.text,
                           compound=tk.TOP, width=width, height=height, background="#337ED7", font=anime_font(anime_),
                           activebackground='#6690D0', foreground="black", activeforeground="yellow")

        self.configure(bg=self.root.config_screen.config_info["anime_color"])
        self.configure(activebackground=highlight(self.root.config_screen.config_info["anime_color"]))

        self.grid(row=row, column=column, padx=3, pady=4)

        self.bind("<Enter>", lambda e: self.root.canvas.tooltip.configure(text=f'"{self.anime_.name}"'))
        self.bind("<ButtonRelease-1>", self.call_episodes)

        self.anime_ = anime_
        self.picture = picture
        self.context_menu = ContextMenu(self, self.anime_)

    def call_episodes(self, event):
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            return EpisodesWindow(self.root, self.anime_)


class Config(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root, bg="#363636")
        self.root = root
        self.overrideredirect(True)

        self.config_info = dict()
        self.read_config()

        self.title("Configurações")
        self.configure(bg="#363636")

        self.width = int(self.winfo_screenwidth() / 3.6)
        self.height = self.winfo_screenheight()

        self.geometry(f"{self.width}x540+{self.width}+{int(self.height / 4.2)}")

        self.canvas = tk.Canvas(self, bg="#363636")
        self.canvas.pack(fill=tk.BOTH, expand=1)

        self.canvas.create_text(self.width - 12, 12, font=button_font(), fill="white", text="X")

        self.canvas.create_rectangle(10, 25, self.width - 10, 65, fill="#1C1C1C")
        self.canvas.create_text(120, 45, font=button_font(), fill="#3CB371", text="Checar Episódios:")

        self.check_episodes_values = ["Checar Todos", "Checar Apenas Favoritos", "Nunca Checar"]

        self.check_episode_config = ttk.Combobox(self.canvas, values=self.check_episodes_values, state="readonly",
                                                 font=button_font(s=10), foreground="black", width=21)
        self.check_episode_config.current(self.config_info["check_episodes"])
        self.check_episode_config.pack(pady=30, padx=15, anchor="e")

        self.canvas.create_rectangle(10, 75, self.width - 10, 115, fill="#1C1C1C")
        self.canvas.create_text(160, 95, font=button_font(), fill="#3CB371", text="Mostrar Nome dos Animes:")

        self.show_name_values = ["Sim", "Não"]

        self.show_name_config = ttk.Combobox(self.canvas, values=self.show_name_values, state="readonly",
                                             font=button_font(s=10), foreground="black", width=21)
        self.show_name_config.current(self.config_info["show_name"])
        self.show_name_config.pack(padx=15, pady=0, anchor="e")

        self.canvas.create_rectangle(10, 125, self.width - 10, 165, fill="#1C1C1C")
        self.canvas.create_text(113, 145, font=button_font(), fill="#3CB371", text="Cor dos animes:")
        self.canvas.create_text(self.width - 110, 145, font=button_font(s=16), fill=self.config_info["anime_color"],
                                text=self.config_info["anime_color"], tags="anime_color_text")
        self.canvas.create_rectangle(self.width - 50, 130, self.width - 20, 160, fill=self.config_info["anime_color"])

        self.canvas.create_rectangle(10, 175, self.width - 10, 215, fill="#1C1C1C")
        self.canvas.create_text(113, 195, font=button_font(), fill="#3CB371", text="Cor dos botões:")
        self.canvas.create_text(self.width - 110, 195, font=button_font(s=16), fill=self.config_info["button_color"],
                                text=self.config_info["button_color"], tags="button_color_text")
        self.canvas.create_rectangle(self.width - 50, 180, self.width - 20, 210, fill=self.config_info["button_color"])

        self.canvas.create_rectangle(10, 225, self.width - 10, 265, fill="#1C1C1C")
        self.canvas.create_text(104, 245, font=button_font(), fill="#3CB371", text="Cor de fundo:")
        self.canvas.create_text(self.width - 110, 245, font=button_font(s=16), fill=self.config_info["bg_color"],
                                text=self.config_info["bg_color"], tags="bg_color_text")
        self.canvas.create_rectangle(self.width - 50, 230, self.width - 20, 260, fill=self.config_info["bg_color"])

        self.reset_button = tk.Button(self.canvas, text="Redefinir", bg=self.config_info["button_color"], fg="black",
                                      activeforeground="red", font=button_font(),
                                      activebackground=highlight(self.config_info["button_color"]),
                                      command=self.redefine)
        self.reset_button.pack(side=tk.BOTTOM, pady=20)

        self.bind("<ButtonRelease-1>", self.local_event)
        self.bind("<B1-Motion>", self.move)
        self.check_episode_config.bind("<<ComboboxSelected>>", lambda e: self.write_config(
            check_episodes=self.check_episodes_values.index(self.check_episode_config.get())
        ))

        def show_name():
            value = self.show_name_values.index(self.show_name_config.get())
            self.write_config(show_name=value)

            if messagebox.askyesno(title="Mostrar Nomes dos Animes",
                                   message="Para alterar esta configuração "
                                           "é necessário reiniciar o programa, reiniciar agora?"):
                self.root.destroy()
                return MainWindow()

        self.show_name_config.bind("<<ComboboxSelected>>", lambda e: show_name())
        self.root.bind("<Unmap>", lambda e: self.withdraw())

    def write_config(self, **kwargs):
        with open(os.path.join(os.path.expanduser("~"), "Animes/Config/config.json"), 'w') as file:
            for n in range(len(kwargs)):
                self.config_info[list(kwargs.keys())[n]] = list(kwargs.values())[n]
            json.dump(self.config_info, file, indent=4)
        self.read_config()

    def read_config(self):
        if not os.path.isdir(os.path.join(os.path.expanduser("~"), "Animes/Config")):
            os.mkdir(os.path.join(os.path.expanduser("~"), "Animes/Config"))
        if os.path.isfile(os.path.join(os.path.expanduser("~"), "Animes/Config/config.json")):
            with open(os.path.join(os.path.expanduser("~"), "Animes/Config/config.json"), 'r') as file:
                self.config_info = json.load(file)
        else:
            self.write_config(check_episodes=0, show_name=1, anime_color="#337ED7",
                              button_color="#3CB371", bg_color="#123456")
        if (not len(os.listdir(os.path.join(os.path.expanduser('~'), "Animes"))) > 3 and
                messagebox.askokcancel(title="Baixar Recomendações", message="Baixar animes recomendados?")):
            if not os.path.isfile(os.path.join(os.path.expanduser('~'), "Animes/Config/animes recomendados.json")):
                with open(os.path.join(os.path.expanduser('~'), "Animes/Config/animes recomendados.json"),
                          "wb") as file:
                    file.write(requests.get("https://drive.usercontent.google.com"
                                            "/download?id=1tbCWhpSpKqdUSNTqFJWCACX6FlGPFgL6&export=download&authuser=0")
                               .content)
            with open(os.path.join(os.path.expanduser("~"), "Animes/Config/animes recomendados.json"), 'r') as file:
                animes = json.load(file)
                for anime, link in animes.items():
                    main.add_anime(anime, link)

    def change_color(self, item, color):
        if color is not None:
            if item == "anime":
                self.write_config(anime_color=color)
                self.canvas.delete("anime_color_text")
                self.canvas.create_text(self.width - 110, 100, font=button_font(s=16),
                                        fill=self.config_info["anime_color"],
                                        text=self.config_info["anime_color"], tags="anime_color_text")
                self.canvas.create_rectangle(self.width - 50, 85, self.width - 20, 115,
                                             fill=self.config_info[f"anime_color"])
                for button in self.root.b_list:
                    button[0].configure(bg=self.config_info["anime_color"])
                    button[0].configure(activebackground=highlight(self.config_info["anime_color"]))
            if item == "button":
                self.write_config(button_color=color)
                self.canvas.delete("button_color_text")
                self.canvas.create_text(self.width - 110, 150, font=button_font(s=16),
                                        fill=self.config_info["button_color"],
                                        text=self.config_info["button_color"], tags="button_color_text")
                self.canvas.create_rectangle(self.width - 50, 135, self.width - 20, 165,
                                             fill=self.config_info[f"button_color"])
                self.reset_button.configure(bg=color, activebackground=highlight(color))
                self.root.canvas.add_button.configure(bg=color, activebackground=highlight(color))
                self.root.canvas.site_button.configure(bg=color, activebackground=highlight(color))
                self.root.canvas.config_button.configure(bg=color, activebackground=highlight(color))
                self.root.canvas.add_button.configure(bg=color, activebackground=highlight(color))
                self.root.canvas.exit_button.configure(bg=color, activebackground=highlight(color))
            if item == "background":
                self.write_config(bg_color=color)
                self.canvas.delete("bg_color_text")
                self.canvas.create_text(self.width - 110, 200, font=button_font(s=16),
                                        fill=self.config_info["bg_color"],
                                        text=self.config_info["bg_color"], tags="bg_color_text")
                self.canvas.create_rectangle(self.width - 50, 185, self.width - 20, 215,
                                             fill=self.config_info[f"bg_color"])
                self.root.scroller.sec_frame.configure(bg=color)
                self.root.scroller.canvas.configure(bg=color)

    def local_event(self, event):
        self.configure(cursor="arrow")
        if event.x in range(self.width - 20, self.width) and event.y in range(21):
            self.withdraw()
        if event.x in range(self.width - 50, self.width - 20) and event.y in range(130, 160):
            self.withdraw()
            color = askcolor(color=self.config_info["anime_color"])[1]
            self.change_color("anime", color)
            self.deiconify()
        if event.x in range(self.width - 50, self.width - 20) and event.y in range(180, 210):
            self.withdraw()
            color = askcolor(color=self.config_info["button_color"])[1]
            self.change_color("button", color)
            self.deiconify()
        if event.x in range(self.width - 50, self.width - 20) and event.y in range(230, 260):
            self.withdraw()
            color = askcolor(color=self.config_info["bg_color"])[1]
            self.change_color("background", color)
            self.deiconify()

    def move(self, event):
        if event.y < 30 and event.x < self.width - 25 and event.widget is self.canvas:
            self.configure(cursor="fleur")
            if event.x_root <= self.winfo_x() + int(event.x + self.width / 2):
                self.geometry(f"{self.width}x540+{event.x_root - int(self.width / 2)}"
                              f"+{event.y_root - 10}")
            else:
                self.geometry(f"{self.width}x540+{event.x_root - int(event.x / 1.005)}"
                              f"+{event.y_root + 10}")
            self.update()

    def redefine(self):
        self.withdraw()
        if messagebox.askokcancel(title="Redefinir Configurações",
                                  message="Tem certeza que deseja redefinir as configurações?"):
            self.write_config(check_episodes=0)
            self.change_color("anime", "#337ED7")
            self.change_color("button", "#3CB371")
            self.change_color("background", "#123456")
            self.check_episode_config.current(0)
            self.show_name_config.current(1)
        self.deiconify()


class ButtonCanvas(tk.Canvas):
    def __init__(self, root):
        tk.Canvas.__init__(self, root, bg="#363636")

        self.root = root

        self.pack(side=tk.BOTTOM, anchor="sw", padx=12, pady=8, fill=tk.X)

        self.add_button = tk.Button(self, text="Adicionar Anime", width=14, height=0, background='#3CB371',
                                    command=lambda: SearchAnimeDialog(root), activebackground='#8FBC8F',
                                    font=button_font(), foreground="black", activeforeground="black")
        self.add_button.pack(anchor="sw", side=tk.LEFT, padx=8, pady=5)

        self.site_button = tk.Button(self, text="Animes Orion", width=14, height=0, background='#3CB371',
                                     command=lambda: webbrowser.open("https://animesorionvip.com"),
                                     activebackground='#8FBC8F', font=button_font(), foreground="black",
                                     activeforeground="black")
        self.site_button.pack(anchor="sw", side=tk.LEFT, padx=8, pady=5)

        self.exit_button = tk.Button(self, text="Sair", width=14, height=0, background='#3CB371',
                                     command=self.master.destroy, foreground="black", activeforeground="black",
                                     activebackground='#8FBC8F', font=button_font())
        self.exit_button.pack(anchor="se", side=tk.RIGHT, padx=8, pady=5)

        self.config_button = tk.Button(self, text="Config.", width=14, height=0, background="#3CB371",
                                       activebackground="#8FBC8F", foreground="black", activeforeground="black",
                                       font=button_font(), command=self.root.config_screen.deiconify)
        self.config_button.pack(anchor="se", side=tk.RIGHT, padx=8, pady=5)


class MainWindow(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.withdraw()

        self.config_screen = Config(self)
        self.config_screen.withdraw()

        self.anime_list = []
        self.fav_anime_list = []

        self.title("Animan")

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        self.geometry(f"{int(self.screen_width // (4 / 3) + 135)}x{int(self.screen_height // 1.13)}")
        self.resizable(width=False, height=False)
        self.configure(background='#1C1C1C')

        self.canvas = ButtonCanvas(self)
        self.canvas.add_button.configure(bg=self.config_screen.config_info["button_color"],
                                         activebackground=highlight(self.config_screen.config_info["button_color"]))
        self.canvas.site_button.configure(bg=self.config_screen.config_info["button_color"],
                                          activebackground=highlight(self.config_screen.config_info["button_color"]))
        self.canvas.config_button.configure(bg=self.config_screen.config_info["button_color"],
                                            activebackground=highlight(self.config_screen.config_info["button_color"]))
        self.canvas.exit_button.configure(bg=self.config_screen.config_info["button_color"],
                                          activebackground=highlight(self.config_screen.config_info["button_color"]))
        self.canvas.tooltip = tk.Label(self.canvas, bg="#363636", fg="white", font=button_font(s=14))
        self.canvas.tooltip.pack(anchor="s", fill=tk.BOTH, expand=1)

        self.scroller = Scroller(self, background=self.config_screen.config_info["bg_color"],
                                 objects=(MainWindow, AniButton))

        self.splash = Splash(self)

        if len(self.get_anime_lists()) <= 12:
            self.scroller.unbind_wheel()
        try:
            self.splash.percentage = 0
            self.splash.load.delete("rect")
            self.step = math.floor((100 - self.splash.percentage) /
                                   (len(self.anime_list) + len(self.fav_anime_list)))
        except ZeroDivisionError:
            self.step = 2
        except tk.TclError:
            self.step = 1

        if not os.path.isdir(os.path.join(os.path.expanduser("~"), "Animes/Thumbs")):
            os.mkdir(os.path.join(os.path.expanduser("~"), "Animes/Thumbs"))

        try:
            self.iconphoto(False, tk.PhotoImage(file=os.path.join(
                os.path.expanduser("~"), "Animes/Thumbs/animan-gui.png")))
        except tk.TclError:
            try:
                with open(os.path.join(os.path.expanduser("~"), "Animes/Thumbs/animan-gui.png"), 'wb') as file:
                    file.write(requests.get("https://drive.google.com/u/0/" +
                                            "uc?id=1bDKMG7CCN7yfmdJY5Z8VNqS1e6oID5gl&export=download").content)
                self.iconphoto(False, tk.PhotoImage(file=os.path.join(
                    os.path.expanduser("~"), "Animes/Thumbs/animan-gui.png")))
                self.splash.load_bar(text="Ícone", step=0)
            except tk.TclError:
                pass

        self.b_list = []
        self.get_b_list()

        try:
            self.splash.finish()
        except tk.TclError:
            pass

    def get_anime_lists(self):
        directory = os.path.join(os.path.expanduser("~"), "Animes")

        if not os.path.isdir(directory):
            os.mkdir(directory)
        if not os.path.isdir(os.path.join(directory, "Favorites")):
            os.mkdir(os.path.join(directory, "Favorites"))

        if self.config_screen.config_info["check_episodes"] == 2:
            main.already_searched = True

        anime_number = len([i for i in os.listdir(os.path.join(directory, "Favorites")) if
                            os.path.isfile(os.path.join(directory, f"Favorites/{i}"))
                            and i[len(i) - 5:] == ".json"])
        anime_number += len([i for i in os.listdir(directory) if
                             os.path.isfile(os.path.join(directory, i))
                             and i[len(i) - 5:] == ".json"])

        def get_anime_list(fav=False):
            path = os.path.join(directory, "Favorites" if fav else '')
            for file in os.listdir(path):
                if os.path.isfile(os.path.join(path, f"{file}")) and file != "anime_dict.json" \
                        and file[len(file) - 5:] == ".json":
                    anime = main.Anime(os.path.join(path, f"{file}"))
                    if anime.last_search[0] < time.localtime()[2] or anime.last_search[1] < time.localtime()[1] \
                            and not main.already_searched:
                        step = math.ceil(100 / anime_number)
                        try:
                            self.splash.load_bar(text=f"Checando por novos episódios de {anime.name}", step=step,
                                                 small_font=True)
                        except tk.TclError:
                            pass
                    self.fav_anime_list.append(anime) if fav else self.anime_list.append(anime)

        get_anime_list(True)

        if self.config_screen.config_info["check_episodes"] == 1:
            main.already_searched = True

        get_anime_list()

        return self.fav_anime_list + self.anime_list

    def draw_thumb(self, ani):
        filename = os.path.join(os.path.expanduser("~"), f"Animes/Thumbs/{ani.name}.png")
        try:
            img = Image.open(filename).convert("RGB") \
                .resize((int(self.screen_width / 1920 * 360),
                         (int(self.screen_height / 1080 * (280 if self.config_screen.config_info["show_name"]
                                                           else 240)))))
            if ani in self.fav_anime_list:
                draw = ImageDraw.Draw(img)
                font_path = os.path.join(os.path.expanduser('~'), f"Animes/font.ttf")
                if not os.path.isfile(font_path) and check_internet():
                    with open(font_path, "wb") as file:
                        file.write(requests.get("https://drive.usercontent.google.com/u/"
                                                "0/uc?id=1DO7Eqo01NGHWTSMFWxuYKS1p4PFmd_wc&export=download").content)
                font_ = ImageFont.truetype(font_path, 48)
                draw.text((0, 0), u"\u2605", font=font_, fill=(0, 255, 0))
            return enhance_image(img)
        except UnidentifiedImageError:
            print(f"Erro: Falha ao adicionar thumb do anime {ani.name}.")

    def load_anime_list(self, anime_list, n):
        for ani in anime_list:
            error = False
            try:
                self.splash.load_bar(text="Carregando " + ani.name, step=self.step)
                if self.splash.percentage == 100:
                    self.splash.finish()
            except tk.TclError:
                pass
            if not (os.path.isfile(os.path.join(os.path.expanduser("~"), f"Animes/Thumbs/{ani.name}.png"))):
                download_thumb(ani)
            img = self.draw_thumb(ani) if not error else (
                tk.PhotoImage(file=os.path.join(os.path.expanduser("~"), f"Animes/Thumbs/animan-gui.png")))

            b = AniButton(self.scroller.sec_frame, img, n // 4, n % 4, ani)
            self.b_list.append([b, img])

            n += 1

    def get_b_list(self):
        n = 0
        self.fav_anime_list.sort(key=lambda x: x.name)
        self.anime_list.sort(key=lambda x: x.name)
        try:
            self.load_anime_list(self.fav_anime_list, n)
            n = len(self.fav_anime_list)
            self.load_anime_list(self.anime_list, n)
        except IndexError:
            messagebox.showerror("Erro: Um erro inesperado aconteceu, por favor reinicie a aplicação.")
            sys.exit()


class ResultButton(tk.Button):
    def __init__(self, root, img, title, n, link_list):
        tk.Button.__init__(self, root.frame, image=img, compound=tk.LEFT, text=title, font=anime_font(s=12),
                           command=self.output, bg=root.root.config_screen.config_info["anime_color"],
                           activebackground=highlight(root.root.config_screen.config_info["anime_color"]),
                           fg="black", anchor="w", width=root.winfo_width() - 60, borderwidth=10, relief="ridge",
                           activeforeground="black")
        self.pack(pady=10, anchor="w", expand=1)
        self.root = root
        self.n = n
        self.link = link_list[n]

        soup = BeautifulSoup(requests.get(self.link, headers=headers).content, "html.parser")

        self.info_list = soup.find("section", {"class": "capaInfo"}).find_all("li")

        try:
            task = threading.Thread(target=self.get_info())
            task.start()
        except RuntimeError:
            self.get_info()

        self.title = self.info_list[0].find("span").text

        if self.n == 2:
            self.root.scroller.bind_wheel()

    def output(self):
        self.root.withdraw()
        add_dialog = AddAnimeDialog(self.root.root)
        add_dialog.name_text.delete(0, "end")
        add_dialog.link_text.delete(0, "end")

        if ':' in self.title:
            self.title = self.title.replace(':', '')

        add_dialog.name_text.insert(0, self.title)
        add_dialog.link_text.insert(0, self.link)

        def destroy_event():
            try:
                self.root.deiconify()
            except tk.TclError:
                pass

        add_dialog.bind("<Destroy>", lambda e: destroy_event())

    def get_info(self):
        text = ''
        for info in self.info_list[1:]:
            text += info.text + '\n'

        text = text[:len(text) - 1]
        self.configure(text=text, anchor="w")


class SearchAnimeDialog(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root, takefocus=True)
        self.title("Pesquisar Animes")
        self.configure(bg="#1C1C1C")
        self.iconphoto(False, tk.PhotoImage(file=os.path.join(
            os.path.expanduser("~"), "Animes/Thumbs/animan-gui.png")))

        self.root = root

        self.top_canvas = tk.Canvas(self, bg="#363636")
        self.top_canvas.pack(side=tk.TOP, fill=tk.X)

        self.top_label = tk.Label(self.top_canvas, text="Procurar Animes:", font=button_font(s=18), bg="#363636")
        self.top_label.pack(pady=1)

        self.search_field = tk.Entry(self.top_canvas, width=83, bg="grey", font=button_font(), fg="white")
        self.search_field.pack(side=tk.LEFT, fill=tk.BOTH)

        def search_animes_threaded():
            try:
                threading.Thread(target=self.search_animes).start()
            except RuntimeError:
                self.search_animes()

        self.search_button = tk.Button(self.top_canvas, text='\U000023CE', width=5,
                                       command=search_animes_threaded, bg="#363636", fg="white")
        self.search_button.pack(side=tk.LEFT, fill=tk.X, padx=1)

        self.button_list = []

        self.scroller = Scroller(self, background=root.config_screen.config_info["bg_color"],
                                 objects=(SearchAnimeDialog, ResultButton, tk.Label))
        self.scroller.unbind_wheel()

        self.canvas = self.scroller.canvas
        self.frame = self.scroller.sec_frame

        self.bottom_canvas = tk.Canvas(self)
        self.bottom_canvas.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(self.bottom_canvas, mode="determinate")
        self.progress_bar["value"] = 0
        self.progress_bar.pack(fill=tk.X)

        self.exit_button = tk.Button(self.bottom_canvas, text="Sair", width=14, height=0, background='#3CB371',
                                     command=self.destroy, foreground="black", activeforeground="black",
                                     activebackground=highlight("#3CB371"), font=button_font())
        self.exit_button.pack(anchor="se", side=tk.RIGHT, padx=8, pady=5)

        def add_command():
            self.withdraw()
            add_dialog = AddAnimeDialog(self.root)
            add_dialog.bind("<Destroy>", lambda e: self.deiconify())
            return

        self.add_button = tk.Button(self.bottom_canvas, text="Adc. Manualmente", width=14, height=0, bg="#3CB371",
                                    command=add_command, fg="black", activeforeground="black",
                                    activebackground=highlight("#3CB371"), font=button_font())
        self.add_button.pack(anchor="sw", side=tk.LEFT, padx=8, pady=5)

        self.search_field.bind("<Return>", lambda e: search_animes_threaded())

        self.width = int(self.winfo_screenwidth() / 2)
        self.height = int(self.winfo_screenheight() / (6 / 5))

        self.geometry(f"{self.width}x{self.height}"
                      f"+{self.width // 2}+{self.height // 16}")

        self.top_canvas.bind_all("<B1-Motion>", self.move)

        def arrow_event(event):
            if event.widget in (self.top_canvas, self.top_label):
                self.configure(cursor="arrow")

        try:
            self.bind_all("<ButtonRelease-1>", arrow_event)
        except tk.TclError:
            pass

        self.root.bind("<Unmap>", lambda e: self.withdraw())
        self.root.bind("<Visibility>", lambda e: self.deiconify())

    def search_animes(self):
        try:
            self.configure(cursor="watch")
            self.progress_bar["value"] = 0
            for button in [(x[0], x[1]) for x in self.button_list]:
                button[0].destroy()
                button[1].destroy()

            self.button_list.clear()

            self.scroller.unbind_wheel()

            keywords = self.search_field.get().split()
            soup = BeautifulSoup(requests.get(f"https://animesorionvip.com/?s={'+'.join(keywords)}", headers=headers)
                                 .content, "html.parser")

            images = soup.find("div", {"id": "sliderHome"}).find_all("img")
            titles = soup.find("div", {"id": "sliderHome"}).find_all("a")

            result_list = []
            link_list = []
            for result in zip(titles, images[1::2]):
                result_list.append((result[0].get("title"), result[1].get("src")))
                link_list.append(result[0].get("href"))

            n = 0
            for title in result_list:
                label = tk.Label(self.frame, text=title[0] + ':', anchor="center", font=button_font(),
                                 bg=highlight(highlight(self.root.config_screen.config_info["bg_color"])), fg="black")
                label.pack(pady=5, anchor="w")

                with tempfile.TemporaryFile() as image:
                    try:
                        image.write(requests.get(title[1], headers=headers).content)
                        img = Image.open(image).convert("RGB") \
                            .resize((150, 150))
                        img.save(image, format="png")
                    except requests.exceptions.InvalidSchema:
                        pass
                    except PIL.UnidentifiedImageError:
                        pass
                    else:
                        img = PIL.ImageTk.PhotoImage(img)

                        button = ResultButton(self, img, title[0], n, link_list)

                        self.button_list.append((button, label, img, title[0]))

                        label.configure(text=button.info_list[0].find("span").text + ':')

                    if self.winfo_height() == self.height:
                        self.geometry(f"{self.width}x{self.height + 1}"
                                      f"+{self.winfo_x()}+{self.winfo_y()}")
                    else:
                        self.geometry(f"{self.width}x{self.height}"
                                      f"+{self.winfo_x()}+{self.winfo_y()}")

                n += 1
                self.progress_bar["value"] += 100 / len(result_list)

            self.configure(cursor="arrow")

        except RuntimeError:
            messagebox.showerror("Erro, por favor tente novamente.")
            self.destroy()

    def move(self, event):
        if event.widget is self.top_canvas or event.widget is self.top_label:
            self.configure(cursor="fleur")
            if event.x_root <= self.winfo_x() + int(event.x + self.width / 2):
                self.geometry(f"{self.width}x{self.height}+{event.x_root - int(self.width / 2)}"
                              f"+{event.y_root - 10}")
            else:
                self.geometry(f"{self.width}x{self.height}+{event.x_root - int(event.x / 1.005)}"
                              f"+{event.y_root + 10}")
            self.update()


class AddAnimeDialog(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root)

        self.root = root

        self.title("Adicionar Anime")
        self.configure(background="#808080")

        self.middle_frame = tk.Frame(self, bg="#808080")
        self.middle_frame.pack(pady=10)

        self.name_label = tk.Label(self.middle_frame, text="Nome:", background="#808080", font=button_font())
        self.name_label.grid(row=1, column=0, padx=5)

        self.get_link_button = tk.Button(self.middle_frame, text="\u29C8", width=1, fg="black",
                                         activeforeground="black",
                                         command=lambda: self.search_link(self.name_text.get().strip()),
                                         font=button_font(), bg=root.config_screen.config_info["button_color"],
                                         activebackground=highlight(root.config_screen.config_info["button_color"]))
        self.get_link_button.grid(row=1, column=2, padx=5)

        self.get_link_button.tooltip = ContextMenu(self.get_link_button, label="Procurar link pelo nome",
                                                   command=lambda: self.search_link(self.name_text.get().strip()))
        self.get_link_button.tooltip.configure(bg="green")
        self.get_link_button.unbind("<Button-3>")

        def get_link_threaded(e):
            try:
                threading.Thread(target=self.get_link_button.tooltip.popup(e)).start()
            except RuntimeError:
                self.get_link_button.tooltip.popup(e)

        self.get_link_button.bind("<Motion>", get_link_threaded)
        self.get_link_button.bind("<ButtonRelease-1>", lambda e: self.search_link(self.name_text.get().strip()))

        self.name_text = tk.Entry(self.middle_frame, width=int(self.winfo_screenwidth() / 20 - 10), font=button_font())
        self.name_text.grid(row=1, column=1)

        self.link_label = tk.Label(self.middle_frame, text="Link:", background="#808080", font=button_font())
        self.link_label.grid(row=2, column=0)

        self.link_text = tk.Entry(self.middle_frame, width=int(self.winfo_screenwidth() / 20 - 10), font=button_font())
        self.link_text.insert(0, "https://animesorionvip.com/animes/")
        self.link_text.grid(row=2, column=1)

        self.bottom_frame = tk.Frame(self, bg="#808080")
        self.bottom_frame.pack()

        self.site_button = tk.Button(self.bottom_frame, text="Ir para o site", width=40, fg="black",
                                     activeforeground="black",
                                     command=lambda: webbrowser.open("https://animesorionvip.com"),
                                     font=button_font(), bg=root.config_screen.config_info["button_color"],
                                     activebackground=highlight(root.config_screen.config_info["button_color"]))
        self.site_button.pack(side=tk.LEFT)

        self.add_button = tk.Button(self.bottom_frame, text="Adicionar Anime", width=40, fg="black",
                                    activeforeground="black",
                                    command=lambda: self.process_input(self.name_text.get().strip(),
                                                                       self.link_text.get().strip()),
                                    font=button_font(), bg=root.config_screen.config_info["button_color"],
                                    activebackground=highlight(root.config_screen.config_info["button_color"]))
        self.add_button.pack(side=tk.RIGHT)

        self.exit_frame = tk.Frame(self, bg="#808080")
        self.exit_frame.pack()

        self.exit_button = tk.Button(self.exit_frame, text="Voltar", width=83, fg="black", activeforeground="black",
                                     bg=root.config_screen.config_info["button_color"], font=button_font(),
                                     activebackground=highlight(root.config_screen.config_info["button_color"]),
                                     command=self.destroy)
        self.exit_button.pack()

        self.bind("<Return>", lambda e: self.process_input(self.name_text.get().strip(), self.link_text.get().strip()))

    def process_input(self, name, link):

        def test_link():
            try:
                r = requests.get(link, headers=headers)
            except requests.exceptions.MissingSchema:
                messagebox.showwarning(title="URL Inválido", message="URL inválido, por favor tente novamente.")
                return False
            if r.status_code == 200:
                return True
            messagebox.showerror(title="Erro de Conexão", message="Não é possível conectar a este URL, por favor " +
                                                                  "cheque sua conexão com a internet e "
                                                                  "tente novamente.")
            return False

        if test_link() and name:
            self.withdraw()
            messagebox.showinfo(title="Adicionar Anime", message=f'Anime "{name}" adicionado com sucesso!' +
                                                                 f'\nO aplicativo será reiniciado!')
            main.add_anime(name, link)
            self.master.destroy()
            return MainWindow()
        elif not name:
            return messagebox.showwarning(title="Anime sem Nome", message="Por favor insira um nome!")

    def search_link(self, name):
        self.configure(cursor="watch")
        link = f"https://animesorionvip.com/animes/{'-'.join(name.lower().split())}/i"
        r = requests.get(link, headers=headers)
        if r.status_code == 200 and BeautifulSoup(r.content, "html.parser").find('div', {"id": "episodio_box"}):
            self.link_text.delete(0, "end")
            self.link_text.insert(0, link)
            self.configure(cursor="arrow")
        else:
            self.get_link_button.configure(fg="red", activeforeground="red")
            self.configure(cursor="arrow")


def button_font(anime_=None, s=14):
    def font_size():
        if anime_ is None:
            return s
        length = len(anime_.name)
        try:
            size = 16 - (length // 9)
            if length >= 27:
                size -= 1
            return size
        except ValueError:
            return 6

    return font.Font(family="Ubuntu Medium", size=font_size(), weight=font.BOLD)


def anime_font(anime_=None, s=24):
    def font_size():
        if anime_ is None:
            return s
        length = len(anime_.name)
        try:
            size = 20 - (length // 9)
            if length >= 27:
                size -= 1
            return size
        except ValueError:
            return 6

    return font.Font(family="Comic Sans MS", size=font_size(), weight=font.BOLD)


def download_thumb(ani):
    soup = BeautifulSoup(requests.get(ani.link, headers=headers).content, "html.parser")
    img_link = soup.find_all('img')[1].get('src')
    if not os.path.isdir(os.path.join(os.path.expanduser("~"), f"Animes/Thumbs")):
        os.mkdir(os.path.join(os.path.expanduser("~"), f"Animes/Thumbs"))

    filename = os.path.join(os.path.expanduser("~"), f"Animes/Thumbs/{ani.name}.png")

    with open(filename, "wb") as image:
        try:
            image.write(requests.get(img_link, headers=headers).content)
        except UnidentifiedImageError:
            print(f"Erro: Falha ao adicionar thumb do anime {ani.name}.")

    return img_link, filename


def enhance_image(enh_image):
    enh_col = ImageEnhance.Color(enh_image)
    color = 1.25
    enh_image = enh_col.enhance(color)

    enh_con = ImageEnhance.Contrast(enh_image)
    contrast = 1.25
    enh_image = enh_con.enhance(contrast)

    enh_sha = ImageEnhance.Sharpness(enh_image)
    sharpness = 2.0
    enh_image = enh_sha.enhance(sharpness)

    return ImageTk.PhotoImage(enh_image)


def check_internet():
    """ Checar conexão de ‘internet’ """
    url = 'https://www.google.com'
    timeout = 5
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.exceptions.ConnectionError:
        return False


if __name__ == '__main__':
    headers = {'User-Agent': 'Mozilla/5.0 (Windows'}
    try:
        if not os.path.isdir(os.path.join(os.path.expanduser('~'), "Animes")):
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes"))
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes/Thumbs"))
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes/Favorites"))
        window = MainWindow()
        window.mainloop()
    except requests.exceptions.ConnectionError:
        messagebox.showerror(title="Erro de Conexão", message="Erro: Verifique sua conexão com a internet.")
