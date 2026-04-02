import json
import math
import os
import platform
import subprocess
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
        self.load.create_rectangle(0, 520, int(self.percentage / 100 * self.winfo_width()), 540, outline="green",
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
        if messagebox.askyesno(message=f'Tem certeza que quer remover o anime "{self.anime_.name}"?'):
            main.remove_anime(self.anime_)
            try:
                os.remove(os.path.join(os.path.expanduser('~'), f"Animes/Thumbs/{self.anime_.name}.png"))
            except OSError:
                pass
            messagebox.showinfo(message=f'Anime "{self.anime_.name}" deletado com sucesso! ' +
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
                messagebox.showinfo(message="Anime renomeado com sucesso!")

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
        messagebox.showinfo(message="Favorito Adicionado! O programa será reiniciado.")
        self.parent.root.destroy()
        return MainWindow()

    def remove_fav(self):
        directory = os.path.join(os.path.expanduser("~"), "Animes")
        try:
            os.rename(os.path.join(directory, f"Favorites/{self.anime_.name}.json"),
                      os.path.join(directory, f"{self.anime_.name}.json"))
            self.anime_.file_name = os.path.join(directory, f"{self.anime_.name}.json")
            messagebox.showinfo(message="Favorito Removido! O programa será reiniciado.")
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
        def _on_canvas_configure(e):
            self.canvas.itemconfig("scroller_window", width=e.width)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind("<Configure>", _on_canvas_configure)
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


class VideoDialog(tk.Toplevel):
    _PLAYERS = [
        'vlc',
        r'C:\Program Files\VideoLAN\VLC\vlc.exe',
        r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
        'mpv',
        r'C:\Program Files\mpv\mpv.exe',
    ]

    def __init__(self, root, anime_, ep_num, ep_url):
        tk.Toplevel.__init__(self, root)
        self.root = root
        self.anime_ = anime_
        self.ep_num = ep_num
        self.ep_url = ep_url

        self.title(f"{anime_.name} — Episódio {ep_num + 1}")
        self.configure(bg="#363636")
        self.resizable(False, False)

        btn_color = root.config_screen.config_info["button_color"]

        tk.Label(self, text="O que deseja fazer?", bg="#363636", fg="white",
                 font=button_font(s=14)).pack(pady=(15, 8), padx=20)

        btn_frame = tk.Frame(self, bg="#363636")
        btn_frame.pack(pady=5, padx=20)

        self.watch_btn = tk.Button(btn_frame, text="Assistir", width=14,
                                   bg=btn_color, fg="black", font=button_font(),
                                   activebackground=highlight(btn_color), activeforeground="black",
                                   command=self._start_watch)
        self.watch_btn.pack(side=tk.LEFT, padx=5)

        self.dl_btn = tk.Button(btn_frame, text="Baixar", width=14,
                                bg=btn_color, fg="black", font=button_font(),
                                activebackground=highlight(btn_color), activeforeground="black",
                                command=self._start_download)
        self.dl_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Abrir no navegador", width=18,
                  bg=btn_color, fg="black", font=button_font(),
                  activebackground=highlight(btn_color), activeforeground="black",
                  command=self._open_browser).pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(self, text="", bg="#363636", fg="white", font=button_font(s=11))
        self.status.pack(pady=(8, 4), padx=20)

        self.progress = ttk.Progressbar(self, length=540, mode='determinate')

        w, h = 620, 155
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _set_status(self, text):
        def _do(t=text):
            try:
                if self.winfo_exists():
                    self.status.configure(text=t)
            except Exception:
                pass
        self.after(0, _do)

    def _disable_buttons(self):
        self.watch_btn.configure(state="disabled")
        self.dl_btn.configure(state="disabled")

    def _show_progress(self):
        self.progress.pack(pady=(0, 10), padx=40, fill=tk.X)
        self.geometry("620x190")

    def _show_browser_fallback(self):
        self.progress.pack_forget()
        btn = tk.Button(self, text="Abrir no navegador", bg="#3CB371", fg="black",
                        font=button_font(), activebackground=highlight("#3CB371"),
                        activeforeground="black", command=self._open_browser)
        btn.pack(pady=(4, 10))
        self.geometry("620x185")

    def _open_browser(self):
        webbrowser.open(self.ep_url)
        self.destroy()

    # ── extração via Playwright ───────────────────────────────────────────────

    def _extract_video_url(self, ep_url):
        """Retorna (video_url, user_agent) via Blogger batchexecute interceptado."""
        import json as _json
        from playwright.sync_api import sync_playwright

        # {itag: url} — coletamos todos os formatos e escolhemos o melhor
        formats = {}

        def parse_batch(body):
            idx = body.find('[')
            if idx == -1:
                return
            try:
                outer, _ = _json.JSONDecoder().raw_decode(body, idx)
                for item in outer:
                    if isinstance(item, list) and len(item) > 2 and isinstance(item[2], str):
                        try:
                            inner = _json.loads(item[2])
                            if not isinstance(inner, list):
                                continue
                            entries = inner[2] if len(inner) > 2 and isinstance(inner[2], list) else []
                            for entry in entries:
                                if not (isinstance(entry, list) and entry
                                        and isinstance(entry[0], str)
                                        and 'googlevideo' in entry[0]):
                                    continue
                                # entry[1] é [itag] ou [[itag, ...]]
                                itag = 0
                                if len(entry) > 1:
                                    tag_field = entry[1]
                                    if isinstance(tag_field, list) and tag_field:
                                        itag = tag_field[0] if isinstance(tag_field[0], int) else 0
                                    elif isinstance(tag_field, int):
                                        itag = tag_field
                                formats[itag] = entry[0]
                        except (_json.JSONDecodeError, TypeError, IndexError):
                            continue
            except Exception:
                pass

        def on_response(response):
            if 'batchexecute' in response.url and 'WcwnYd' in response.url:
                try:
                    parse_batch(response.body().decode('utf-8', errors='replace'))
                except Exception:
                    pass

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            chromium_ua = page.evaluate('navigator.userAgent')
            page.on('response', on_response)
            page.goto(ep_url, timeout=30000)
            page.wait_for_timeout(8000)
            browser.close()

        if not formats:
            return None, None

        # Preferência: 22 (720p) > 18 (360p) > qualquer outro
        preferred = [22, 18]
        best_url = next((formats[t] for t in preferred if t in formats),
                        formats[max(formats)])
        return best_url, chromium_ua

    # ── watch ─────────────────────────────────────────────────────────────────

    def _start_watch(self):
        self._disable_buttons()
        threading.Thread(target=self._watch_thread, daemon=True).start()

    def _watch_thread(self):
        self._set_status("Abrindo navegador para extrair vídeo...")
        try:
            video_url, ua = self._extract_video_url(self.ep_url)
        except Exception as e:
            self._set_status(f"Erro ao extrair: {e}")
            return

        if not video_url:
            self._set_status("Vídeo indisponível para extração. Tente abrir no navegador.")
            self.after(0, self._show_browser_fallback)
            return

        for player in self._PLAYERS:
            try:
                subprocess.Popen([player, video_url])
                self._set_status("Abrindo no player...")
                self.after(1500, self.destroy)
                return
            except (FileNotFoundError, OSError):
                continue

        # Nenhum player — baixar para temp e abrir com player padrão
        self._set_status("Baixando para reprodução local...")
        self._show_progress()
        self._download_url(video_url, ua, tempfile.mkdtemp(prefix="animan_"), "temp", open_after=True)

    # ── download ──────────────────────────────────────────────────────────────

    def _start_download(self):
        self._disable_buttons()
        self._show_progress()
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        self._set_status("Extraindo vídeo...")
        try:
            video_url, ua = self._extract_video_url(self.ep_url)
        except Exception as e:
            self._set_status(f"Erro ao extrair: {e}")
            return

        if not video_url:
            self._set_status("Vídeo indisponível para extração. Tente abrir no navegador.")
            self.after(0, self._show_browser_fallback)
            return

        dest = os.path.join(os.path.expanduser("~"), "Videos", "Animes", self.anime_.name)
        os.makedirs(dest, exist_ok=True)
        ep_label = str(self.ep_num + 1).zfill(2)
        self._download_url(video_url, ua, dest, ep_label, open_after=True)

    def _download_url(self, video_url, ua, dest, ep_label, open_after=False):
        """Baixa MP4 em partes paralelas (cada parte em arquivo temp próprio) e concatena."""
        import math
        filepath = os.path.join(dest, f"Episodio {ep_label}.mp4")
        CONNECTIONS = 3
        MAX_RETRIES = 5

        try:
            req_headers = {'User-Agent': ua or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                           'Referer': 'https://www.blogger.com/'}

            head = requests.head(video_url, headers=req_headers, timeout=15,
                                 allow_redirects=True)
            total = int(head.headers.get('content-length', 0))
            accepts_ranges = head.headers.get('accept-ranges', '') == 'bytes'

            start_time = time.time()

            if not total or not accepts_ranges:
                # Fallback: conexão única
                with requests.get(video_url, headers=req_headers, stream=True,
                                  timeout=30, allow_redirects=True) as r:
                    r.raise_for_status()
                    total = int(r.headers.get('content-length', 0))
                    done = 0
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024 * 512):
                            if chunk:
                                f.write(chunk)
                                done += len(chunk)
                                if total:
                                    pct = done / total * 100
                                    elapsed = time.time() - start_time or 0.001
                                    speed = done / elapsed
                                    self.after(0, lambda v=pct: self.progress.configure(value=v) if self.winfo_exists() else None)
                                    self._set_status(
                                        f"Baixando... {done/1024/1024:.1f} / {total/1024/1024:.1f} MB"
                                        f"  ({pct:.0f}%)  {speed/1024/1024:.1f} MB/s")
            else:
                chunk_size = math.ceil(total / CONNECTIONS)
                downloaded = [0] * CONNECTIONS
                lock = threading.Lock()
                tmp_dir = tempfile.mkdtemp(prefix="animan_dl_")
                part_files = [os.path.join(tmp_dir, f"part_{i:03d}") for i in range(CONNECTIONS)]
                errors = [None] * CONNECTIONS

                def fetch_part(idx, start, end):
                    current = start
                    for attempt in range(MAX_RETRIES):
                        try:
                            h = {**req_headers, 'Range': f'bytes={current}-{end}'}
                            mode = 'ab' if current > start else 'wb'
                            with requests.get(video_url, headers=h, stream=True,
                                              timeout=60, allow_redirects=True) as r:
                                r.raise_for_status()
                                with open(part_files[idx], mode) as f:
                                    for chunk in r.iter_content(chunk_size=1024 * 256):
                                        if chunk:
                                            f.write(chunk)
                                            with lock:
                                                downloaded[idx] += len(chunk)
                                            current += len(chunk)
                            return  # sucesso
                        except Exception as e:
                            if attempt < MAX_RETRIES - 1:
                                time.sleep(1.5 * (attempt + 1))
                            else:
                                errors[idx] = e

                threads = [threading.Thread(
                    target=fetch_part,
                    args=(i, i * chunk_size, min((i + 1) * chunk_size - 1, total - 1)),
                    daemon=True) for i in range(CONNECTIONS)]
                for t in threads:
                    t.start()

                while any(t.is_alive() for t in threads):
                    with lock:
                        done = sum(downloaded)
                    pct = done / total * 100
                    elapsed = (time.time() - start_time) or 0.001
                    speed = done / elapsed
                    self.after(0, lambda v=pct: self.progress.configure(value=v) if self.winfo_exists() else None)
                    self._set_status(
                        f"Baixando... {done/1024/1024:.1f} / {total/1024/1024:.1f} MB"
                        f"  ({pct:.0f}%)  {speed/1024/1024:.1f} MB/s  [{CONNECTIONS}x]")
                    time.sleep(0.25)

                for t in threads:
                    t.join()

                failed = [e for e in errors if e is not None]
                if failed:
                    raise failed[0]

                # Concatenar partes em ordem
                self._set_status("Juntando partes...")
                with open(filepath, 'wb') as out:
                    for pf in part_files:
                        if os.path.isfile(pf):
                            with open(pf, 'rb') as pf_:
                                out.write(pf_.read())
                            os.remove(pf)
                try:
                    os.rmdir(tmp_dir)
                except OSError:
                    pass

            self._set_status(f"Concluído! Salvo em:\n{dest}")
            if open_after:
                self.after(500, lambda: os.startfile(filepath))
            self.after(3000, self.destroy)
        except Exception as e:
            self._set_status(f"Erro no download: {e}")


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
        self.configure(bg="grey")

        self.anime_.last_episode = self.num
        with open(self.anime_.file_name, 'w') as file:
            self.anime_info['last_episode'] = self.num
            json.dump(self.anime_info, file, indent=4)

        ep_url = list(self.anime_.episodes.values())[self.num]
        root = self.ep_window.master.master.master.root
        VideoDialog(root, self.anime_, self.num, ep_url)

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
            eps = self.anime_.get_episodes()
            season_breaks = getattr(self.anime_, 'season_breaks', {})
            show_seasons = len(season_breaks) > 1
            n = 0
            for ep in eps:
                if show_seasons and n in season_breaks:
                    snum = season_breaks[n]
                    tk.Label(self.scroller.sec_frame,
                             text=f"  Temporada {snum}",
                             bg="#222222", fg="white",
                             font=button_font(s=13), anchor='w',
                             height=1).pack(fill=tk.X, pady=(6, 0))
                self.button_list.append(EpButton(n, self.scroller.sec_frame, ep, self.anime_, self.tooltip))
                n += 1
        else:
            self.root.configure(cursor="arrow")
            self.destroy()
            messagebox.showerror(message="Erro: verifique sua conexão com a internet.")

        width = int(screen_width / 1.52)

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
        self.text = anime_.name
        width = int(root.winfo_screenwidth() // 5.333)
        height = int(root.winfo_screenheight() // 4.5)
        self.root = root.master.master.master
        if anime_ in self.root.fav_anime_list:
            self.text += " \U00002605"
        if anime_.new_episode:
            self.text += "\n(Novo Episódio!)"
        show_name = self.root.config_screen.config_info.get("show_name", 1)
        display_text = self.text if show_name else ""
        compound_mode = tk.TOP if show_name else tk.NONE
        if show_name:
            height += 50
        tk.Button.__init__(self, root, image=picture, borderwidth=10, text=display_text,
                           compound=compound_mode, width=width, height=height, background="#337ED7", font=anime_font(anime_),
                           activebackground='#6690D0', foreground="black", activeforeground="yellow",
                           wraplength=width - 20)

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
        self.canvas.create_rectangle(10, 30, self.width - 10, 70, fill="#1C1C1C")
        self.canvas.create_text(120, 50, font=button_font(), fill="#3CB371", text="Checar Episódios:")

        self.values_list = ["Checar Todos", "Checar Apenas Favoritos", "Nunca Checar"]

        self.check_episode_config = ttk.Combobox(self.canvas, values=self.values_list, state="readonly",
                                                 font=button_font(s=10), foreground="black", width=21)
        self.check_episode_config.current(self.config_info["check_episodes"])
        self.canvas.create_window(self.width - 15, 50, anchor="e", window=self.check_episode_config)

        self.canvas.create_rectangle(10, 80, self.width - 10, 120, fill="#1C1C1C")
        self.canvas.create_text(113, 100, font=button_font(), fill="#3CB371", text="Cor dos animes:")
        self.canvas.create_text(self.width - 110, 100, font=button_font(s=16), fill=self.config_info["anime_color"],
                                text=self.config_info["anime_color"], tags="anime_color_text")
        self.canvas.create_rectangle(self.width - 50, 85, self.width - 20, 115, fill=self.config_info["anime_color"])

        self.canvas.create_rectangle(10, 130, self.width - 10, 170, fill="#1C1C1C")
        self.canvas.create_text(113, 150, font=button_font(), fill="#3CB371", text="Cor dos botões:")
        self.canvas.create_text(self.width - 110, 150, font=button_font(s=16), fill=self.config_info["button_color"],
                                text=self.config_info["button_color"], tags="button_color_text")
        self.canvas.create_rectangle(self.width - 50, 135, self.width - 20, 165, fill=self.config_info["button_color"])

        self.canvas.create_rectangle(10, 180, self.width - 10, 220, fill="#1C1C1C")
        self.canvas.create_text(104, 200, font=button_font(), fill="#3CB371", text="Cor de fundo:")
        self.canvas.create_text(self.width - 110, 200, font=button_font(s=16), fill=self.config_info["bg_color"],
                                text=self.config_info["bg_color"], tags="bg_color_text")
        self.canvas.create_rectangle(self.width - 50, 185, self.width - 20, 215, fill=self.config_info["bg_color"])

        self.canvas.create_rectangle(10, 230, self.width - 10, 270, fill="#1C1C1C")
        self.canvas.create_text(145, 250, font=button_font(), fill="#3CB371", text="Mostrar Nomes dos Animes:")
        self.show_name_values = ["Mostrar Nomes", "Ocultar Nomes"]
        self.show_name_config = ttk.Combobox(self.canvas, values=self.show_name_values, state="readonly",
                                             font=button_font(s=10), foreground="black", width=21)
        self.show_name_config.current(1 - self.config_info.get("show_name", 1))
        self.canvas.create_window(self.width - 15, 250, anchor="e", window=self.show_name_config)

        self.reset_button = tk.Button(self.canvas, text="Redefinir", bg=self.config_info["button_color"], fg="black",
                                      activeforeground="red", font=button_font(),
                                      activebackground=highlight(self.config_info["button_color"]),
                                      command=self.redefine)
        self.canvas.create_window(self.width // 4, 510, anchor="center", window=self.reset_button)

        self.reload_button = tk.Button(self.canvas, text="Recarregar", bg=self.config_info["button_color"], fg="black",
                                       activeforeground="black", font=button_font(),
                                       activebackground=highlight(self.config_info["button_color"]),
                                       command=lambda: self.root.reload_b_list())
        self.canvas.create_window(3 * self.width // 4, 510, anchor="center", window=self.reload_button)

        self.bind("<ButtonRelease-1>", self.local_event)
        self.bind("<B1-Motion>", self.move)
        self.check_episode_config.bind("<<ComboboxSelected>>", lambda e: self.write_config(
            {"check_episodes": self.values_list.index(self.check_episode_config.get())}))
        def _apply_show_name(_e):
            self.write_config({"show_name": 1 - self.show_name_values.index(self.show_name_config.get())})
            self.root.reload_b_list()
        self.show_name_config.bind("<<ComboboxSelected>>", _apply_show_name)
        self.root.bind("<Unmap>", lambda e: self.withdraw())

    def write_config(self, config):
        with open(os.path.join(os.path.expanduser("~"), "Animes/Config/config.json"), 'w') as file:
            for n in range(len(config)):
                self.config_info[list(config.keys())[n]] = list(config.values())[n]
            json.dump(self.config_info, file, indent=4)
        self.read_config()

    def read_config(self):
        if not os.path.isdir(os.path.join(os.path.expanduser("~"), "Animes/Config")):
            os.mkdir(os.path.join(os.path.expanduser("~"), "Animes/Config"))
        if os.path.isfile(os.path.join(os.path.expanduser("~"), "Animes/Config/config.json")):
            with open(os.path.join(os.path.expanduser("~"), "Animes/Config/config.json"), 'r') as file:
                self.config_info = json.load(file)
            if "show_name" not in self.config_info:
                self.write_config({"show_name": 1})
        else:
            self.write_config({"check_episodes": 0, "anime_color": "#337ED7",
                               "button_color": "#3CB371", "bg_color": "#123456", "show_name": 1})

    def change_color(self, item, color):
        if color is not None:
            if item == "anime":
                self.write_config({"anime_color": color})
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
                self.write_config({"button_color": color})
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
                self.root.canvas.rec_button.configure(bg=color, activebackground=highlight(color))
            if item == "background":
                self.write_config({"bg_color": color})
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
        if event.x in range(self.width - 50, self.width - 20) and event.y in range(85, 116):
            self.withdraw()
            color = askcolor(color=self.config_info["anime_color"])[1]
            self.change_color("anime", color)
            self.deiconify()
        if event.x in range(self.width - 50, self.width - 20) and event.y in range(135, 166):
            self.withdraw()
            color = askcolor(color=self.config_info["button_color"])[1]
            self.change_color("button", color)
            self.deiconify()
        if event.x in range(self.width - 50, self.width - 20) and event.y in range(185, 216):
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
        if messagebox.askokcancel(message="Tem certeza que deseja redefinir as configurações?"):
            self.write_config({"check_episodes": 0, "show_name": 1})
            self.change_color("anime", "#337ED7")
            self.change_color("button", "#3CB371")
            self.change_color("background", "#123456")
            self.check_episode_config.current(0)
            self.show_name_config.current(0)
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
                                     command=lambda: webbrowser.open("https://animesonlinecc.to"),
                                     activebackground='#8FBC8F', font=button_font(), foreground="black",
                                     activeforeground="black")
        self.site_button.pack(anchor="sw", side=tk.LEFT, padx=8, pady=5)

        self.rec_button = tk.Button(self, text="Recomendações", width=14, height=0, background='#3CB371',
                                    command=download_recommendations, activebackground='#8FBC8F',
                                    font=button_font(), foreground="black", activeforeground="black")
        self.rec_button.pack(anchor="sw", side=tk.LEFT, padx=8, pady=5)

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
        if self.screen_width >= 1600:
            self.screen_width -= 20
        if self.screen_width <= 1400:
            self.screen_width += 20
        self.screen_height = self.winfo_screenheight()
        if self.screen_height >= 900:
            self.screen_height -= 16
        if self.screen_height <= 768:
            self.screen_height += 16
        _btn_w = int(self.screen_width // 5.333)
        _w = 4 * (_btn_w + 20) + 30   # 4 buttons (width + 2×borderwidth) + scrollbar/padding
        _h = int(self.screen_height // 1.13)
        _x = (self.winfo_screenwidth() - _w) // 2
        _y = (self.winfo_screenheight() - _h) // 2
        self.geometry(f"{_w}x{_h}+{_x}+{_y}")
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
        self.canvas.rec_button.configure(bg=self.config_screen.config_info["button_color"],
                                         activebackground=highlight(self.config_screen.config_info["button_color"]))
        self.canvas.tooltip = tk.Label(self.canvas, bg="#363636", fg="white", font=button_font(s=14))
        self.canvas.tooltip.pack(anchor="s", fill=tk.BOTH, expand=1)

        self.scroller = Scroller(self, background=self.config_screen.config_info["bg_color"],
                                 objects=(MainWindow, AniButton))

        self.splash = Splash(self)

        if len(self.get_anime_list()) <= 12:
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

    def get_anime_list(self):
        directory = os.path.join(os.path.expanduser("~"), "Animes")

        if not os.path.isdir(directory):
            os.mkdir(directory)
        if not os.path.isdir(os.path.join(directory, "Favorites")):
            os.mkdir(os.path.join(directory, "Favorites"))

        if self.config_screen.config_info["check_episodes"] == 2:
            main.already_searched = True

        for file in os.listdir(os.path.join(directory, "Favorites")):
            if os.path.isfile(os.path.join(directory, f"Favorites/{file}")) and file != "anime_dict.json" \
                    and file[len(file) - 5:] == ".json":
                anime = main.Anime(os.path.join(directory, f"Favorites/{file}"))
                if anime.last_search[0] < time.localtime()[2] or anime.last_search[1] < time.localtime()[1] \
                        and not main.already_searched:
                    step = math.ceil(100 / len([i for i in os.listdir(os.path.join(directory, "Favorites")) if
                                                os.path.isfile(os.path.join(directory, f"Favorites/{i}"))
                                                and i[len(i) - 5:] == ".json"]))
                    try:
                        self.splash.load_bar(text=f"Checando por novos episódios de {anime.name}", step=step,
                                             small_font=True)
                    except tk.TclError:
                        pass
                self.fav_anime_list.append(anime)

        if self.config_screen.config_info["check_episodes"] == 1:
            main.already_searched = True

        for file in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, file)) and file != "anime_dict.json" \
                    and file[len(file) - 5:] == ".json":
                anime = main.Anime(os.path.join(directory, file))
                if anime.last_search[0] < time.localtime()[2] or anime.last_search[1] < time.localtime()[1] \
                        and not main.already_searched:
                    step = math.ceil(100 / len([i for i in os.listdir(directory) if
                                                os.path.isfile(os.path.join(directory, i))
                                                and i[len(i) - 5:] == ".json"]))
                    try:
                        self.splash.load_bar(text=f"Checando por novos episódios de {anime.name}", step=step,
                                             small_font=True)
                    except tk.TclError:
                        pass
                self.anime_list.append(anime)

        return self.fav_anime_list + self.anime_list

    def get_b_list(self):
        n = 0
        self.fav_anime_list.sort(key=lambda x: x.name)
        self.anime_list.sort(key=lambda x: x.name)
        try:
            raw_sw = self.winfo_screenwidth()
            raw_sh = self.winfo_screenheight()

            for ani in self.fav_anime_list:
                try:
                    self.splash.load_bar(text="Carregando " + ani.name, step=self.step)
                    if self.splash.percentage == 100:
                        self.splash.finish()
                except tk.TclError:
                    pass
                success = download_thumb(ani, raw_sw, raw_sh)
                if not success:
                    continue
                img = tk.PhotoImage(file=os.path.join(os.path.expanduser("~"), f"Animes/Thumbs/{ani.name}.png"))

                b = AniButton(self.scroller.sec_frame, img, n // 4, n % 4, ani)
                self.b_list.append([b, img])

                n += 1

            for ani in self.anime_list:
                try:
                    self.splash.load_bar(text="Carregando " + ani.name, step=self.step)
                    if self.splash.percentage == 100:
                        self.splash.finish()
                except tk.TclError:
                    pass
                success = download_thumb(ani, raw_sw, raw_sh)
                if not success:
                    continue
                img = tk.PhotoImage(file=os.path.join(os.path.expanduser("~"), f"Animes/Thumbs/{ani.name}.png"))

                b = AniButton(self.scroller.sec_frame, img, n // 4, n % 4, ani)
                self.b_list.append([b, img])

                n += 1
        except IndexError:
            messagebox.showerror("Erro: Um erro inesperado aconteceu, por favor reinicie a aplicação.")
            sys.exit()

        for col in range(4):
            self.scroller.sec_frame.grid_columnconfigure(col, weight=1, uniform="col")

    def reload_b_list(self):
        for b, _ in self.b_list:
            b.destroy()
        self.b_list = []
        self.get_b_list()


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

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        soup = BeautifulSoup(requests.get(self.link, headers=headers).content, "html.parser")

        h1 = soup.find('h1')
        self.title = h1.text.strip() if h1 else title

        info_items = []
        genres = [a.text.strip() for a in soup.find_all('a', href=lambda h: h and '/generos/' in h)]
        if genres:
            info_items.append('Gêneros: ' + ', '.join(genres))
        desc_meta = soup.find('meta', {'name': 'description'})
        if desc_meta:
            info_items.append(desc_meta.get('content', ''))
        self.info_list = info_items

        try:
            task = threading.Thread(target=self.get_info)
            task.start()
        except RuntimeError:
            self.get_info()

        if self.n == 2:
            self.root.scroller.bind_wheel()

    def output(self):
        self.root.withdraw()
        add_dialog = AddAnimeDialog(self.root.root)
        add_dialog.name_text.delete(0, "end")
        add_dialog.link_text.delete(0, "end")
        add_dialog.name_text.insert(0, self.title)
        add_dialog.link_text.insert(0, self.link)

        def destroy_event():
            try:
                self.root.deiconify()
            except tk.TclError:
                pass

        add_dialog.bind("<Destroy>", lambda e: destroy_event())

    def get_info(self):
        text = '\n'.join(self.info_list)
        self.configure(text=text if text else self.title, anchor="w")


class SearchAnimeDialog(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root)
        self.title("Pesquisar Animes")
        self.configure(bg="#1C1C1C")
        self.overrideredirect(True)

        self.root = root

        self.top_canvas = tk.Canvas(self, bg="#363636")
        self.top_canvas.pack(side=tk.TOP)

        self.top_label = tk.Label(self.top_canvas, text="Procurar Animes:", font=button_font(s=18), bg="#363636")
        self.top_label.pack(pady=1)

        self.search_field = tk.Entry(self.top_canvas, width=69, bg="grey", font=button_font(), fg="white")
        self.search_field.pack(side=tk.LEFT, fill=tk.BOTH)

        def search_animes_threaded():
            try:
                threading.Thread(target=self.search_animes).start()
            except RuntimeError:
                self.search_animes()

        self.search_button = tk.Button(self.top_canvas, text='\U000023CE',
                                       command=search_animes_threaded, bg="#363636", fg="white")
        self.search_button.pack(side=tk.RIGHT)

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
        self.configure(cursor="watch")
        self.progress_bar["value"] = 0

        for button in [(x[0], x[1]) for x in self.button_list]:
            button[0].destroy()
            button[1].destroy()

        self.button_list.clear()

        self.scroller.unbind_wheel()

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        keywords = self.search_field.get().split()
        soup = BeautifulSoup(requests.get(f"https://animesonlinecc.to/?s={'+'.join(keywords)}", headers=headers)
                             .content, "html.parser")

        result_list = []
        link_list = []
        for item in soup.find_all("article"):
            a_tag = item.select_one("div.poster a")
            if not a_tag:
                a_tag = item.select_one("a")
            if not a_tag:
                continue
            img_tag = item.select_one("div.poster img") or a_tag.find("img")
            title_text = img_tag.get('alt', '').strip() if img_tag else ''
            img_src = img_tag.get('src', '') if img_tag else ''
            link = a_tag.get('href', '')
            if not title_text:
                h = item.select_one('h2, h3, .title')
                title_text = h.get_text(strip=True) if h else ''
            if title_text and link and link.startswith('http'):
                result_list.append((title_text, img_src))
                link_list.append(link)

        n = 0
        for title in result_list:
            label = tk.Label(self.frame, text=title[0] + ':', anchor="center", font=button_font(),
                             bg=highlight(highlight(self.root.config_screen.config_info["bg_color"])), fg="black")
            label.pack(pady=5, anchor="w")

            with tempfile.TemporaryFile() as image:
                try:
                    image.write(requests.get(title[1], headers=headers).content)
                    img = Image.open(image).convert("RGB") \
                        .resize((150, 150), Image.LANCZOS)
                    img.save(image, format="png")
                except (requests.exceptions.InvalidSchema, Exception):
                    pass
                else:
                    img = PIL.ImageTk.PhotoImage(img)

                    button = ResultButton(self, img, title[0], n, link_list)

                    self.button_list.append((button, label, img, title[0]))

                    label.configure(text=button.title + ':')

                if self.winfo_height() == self.height:
                    self.geometry(f"{self.width}x{self.height + 1}"
                                  f"+{self.winfo_x()}+{self.winfo_y()}")
                else:
                    self.geometry(f"{self.width}x{self.height}"
                                  f"+{self.winfo_x()}+{self.winfo_y()}")

            n += 1
            self.progress_bar["value"] += 100/len(result_list)

        self.configure(cursor="arrow")

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
        self.link_text.insert(0, "https://animesonlinecc.to/anime/")
        self.link_text.grid(row=2, column=1)

        self.bottom_frame = tk.Frame(self, bg="#808080")
        self.bottom_frame.pack()

        self.site_button = tk.Button(self.bottom_frame, text="Ir para o site", width=40, fg="black",
                                     activeforeground="black",
                                     command=lambda: webbrowser.open("https://animesonlinecc.to"),
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        def test_link():
            try:
                r = requests.get(link, headers=headers)
            except requests.exceptions.MissingSchema:
                messagebox.showwarning(message="URL inválido, por favor tente novamente.")
                return False
            if r.status_code == 200:
                return True
            messagebox.showerror(message="Não é possível conectar a este URL, por favor " +
                                         "cheque sua conexão com a internet e tente novamente.")
            return False

        if test_link() and name:
            self.withdraw()
            messagebox.showinfo(message=f'Anime "{name}" adicionado com sucesso!' +
                                        f'\nO aplicativo será reiniciado!')
            main.add_anime(name, link)
            self.master.destroy()
            return MainWindow()
        elif not name:
            return messagebox.showwarning(message="Por favor insira um nome!")

    def search_link(self, name):
        self.configure(cursor="watch")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        link = f"https://animesonlinecc.to/anime/{'-'.join(name.lower().split())}/"
        r = requests.get(link, headers=headers)
        if r.status_code == 200 and BeautifulSoup(r.content, "html.parser").select_one('ul.episodios'):
            self.link_text.delete(0, "end")
            self.link_text.insert(0, link)
            self.configure(cursor="arrow")
        else:
            self.get_link_button.configure(fg="red", activeforeground="red")
            self.configure(cursor="arrow")


def download_thumb(ani, screen_width, screen_height):
    thumb_w = int(screen_width // 5.333)
    thumb_h = int(screen_height // 4.5)
    thumbs_dir = os.path.join(os.path.expanduser("~"), "Animes/Thumbs")
    thumb_path = os.path.join(thumbs_dir, f"{ani.name}.png")
    fail_path = os.path.join(thumbs_dir, f"{ani.name}.fail")
    if os.path.isfile(fail_path):
        return False
    if os.path.isfile(thumb_path):
        try:
            existing = Image.open(thumb_path)
            if existing.size == (thumb_w, thumb_h):
                return True
            existing.close()
        except Exception:
            pass
        os.remove(thumb_path)
    try:
        if not os.path.isdir(thumbs_dir):
            os.mkdir(thumbs_dir)

        font_path = os.path.join(os.path.expanduser("~"), "Animes/font.ttf")
        if not os.path.isfile(font_path):
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            font_data = requests.get(
                "https://drive.usercontent.google.com/u/0/uc?id=1DO7Eqo01NGHWTSMFWxuYKS1p4PFmd_wc&export=download",
                headers=headers).content
            with open(font_path, "wb") as f:
                f.write(font_data)

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get(ani.link, headers=headers)
        if r.status_code != 200:
            open(fail_path, 'w').close()
            return False
        soup = BeautifulSoup(r.content, "html.parser")
        if not soup.select_one('ul.episodios'):
            open(fail_path, 'w').close()
            return False
        poster_div = (soup.find('div', class_='poster') or
                      soup.find('div', class_='imagen') or
                      soup.find('div', class_='thumb'))
        if poster_div:
            img_tag = poster_div.find('img')
        else:
            imgs = [i for i in soup.find_all('img') if i.get('src') and 'uploads' in i.get('src', '')]
            img_tag = imgs[0] if imgs else None
        if not img_tag:
            return False
        img_link = img_tag.get('src')

        raw_path = os.path.join(thumbs_dir, ani.name)
        with open(raw_path, "wb") as image:
            image.write(requests.get(img_link, headers=headers).content)

        img = Image.open(raw_path).convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
        img.save(thumb_path)
        os.remove(raw_path)

        enhance_image(thumb_path)

        img = Image.open(thumb_path)
        draw = ImageDraw.Draw(img)
        try:
            fnt = ImageFont.truetype(font_path, size=max(10, 180 // max(len(ani.name), 1)))
        except (OSError, IOError):
            fnt = ImageFont.load_default()
        text_pos = (4, img.height - fnt.size - 6)
        draw.text(text_pos, ani.name, font=fnt, fill="white", stroke_width=1, stroke_fill="black")
        img.save(thumb_path)

        return True
    except Exception as e:
        print(f"Erro: Falha ao adicionar thumb do anime {ani.name}: {e}")
        try:
            open(fail_path, 'w').close()
        except Exception:
            pass
        return False


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
            if length <= 15:
                return 20
            if length <= 25:
                return 16
            if length <= 35:
                return 13
            if length <= 50:
                return 11
            return 9
        except ValueError:
            return 9

    return font.Font(family="Comic Sans MS", size=font_size(), weight=font.BOLD)


def enhance_image(image):
    enh_image = Image.open(image)

    enh_col = ImageEnhance.Color(enh_image)
    color = 1.25
    enh_image = enh_col.enhance(color)

    enh_con = ImageEnhance.Contrast(enh_image)
    contrast = 1.25
    enh_image = enh_con.enhance(contrast)

    enh_sha = ImageEnhance.Sharpness(enh_image)
    sharpness = 2.0
    enh_image = enh_sha.enhance(sharpness)

    enh_image.save(image)


def check_internet():
    """ Checar conexão de ‘internet’ """
    url = 'https://www.google.com'
    timeout = 5
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.exceptions.ConnectionError:
        return False


def download_recommendations():
    if not messagebox.askyesno(message="Baixar animes recomendados?"):
        return
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        data = requests.get(
            "https://drive.usercontent.google.com/download?id=1tbCWhpSpKqdUSNTqFJWCACX6FlGPFgL6&export=download&authuser=0",
            headers=headers).content
        config_dir = os.path.join(os.path.expanduser("~"), "Animes/Config")
        if not os.path.isdir(config_dir):
            os.mkdir(config_dir)
        with open(os.path.join(config_dir, "animes recomendados.json"), "wb") as f:
            f.write(data)
        messagebox.showinfo(message="Recomendações baixadas com sucesso!")
    except requests.exceptions.ConnectionError:
        messagebox.showerror(message="Erro: verifique sua conexão com a internet.")


if __name__ == '__main__':
    try:
        if not os.path.isdir(os.path.join(os.path.expanduser('~'), "Animes")):
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes"))
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes/Thumbs"))
            os.mkdir(os.path.join(os.path.expanduser('~'), "Animes/Favorites"))
        window = MainWindow()
        window.mainloop()
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erro: Verifique sua conexão com a internet.")
