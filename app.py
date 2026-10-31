import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
from threading import Thread

import yt_dlp

# Garante que o app encontre o ffmpeg mesmo quando executado como .app
os.environ["PATH"] += ":/opt/homebrew/bin:/usr/local/bin"


class YouTubeAudioDownloader:
    def __init__(self, root):
        self.root = root
        self.last_downloaded_file = None
        self.default_download_folder = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
        )
        self.root.title("YouTube Audio Downloader")
        self.root.geometry("700x220")
        self.root.resizable(False, False)

        tk.Label(
            root,
            text="URL do vídeo do YouTube:"
        ).pack(pady=(15, 5))

        self.url_entry = tk.Entry(root, width=90)
        self.url_entry.pack(padx=10)

        self.download_btn = tk.Button(
            root,
            text="Baixar MP3",
            command=self.start_download,
            width=20
        )
        self.download_btn.pack(pady=20)

        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")

        tk.Label(
            root,
            textvariable=self.status_var
        ).pack()

        self.show_finder_btn = tk.Button(
            root,
            text="Mostrar no Finder",
            command=self.show_in_finder,
            width=20,
            state="disabled"
        )
        self.show_finder_btn.pack(pady=(8, 0))

    def get_ffmpeg_location(self):
        # Apple Silicon (M1/M2/M3)
        if os.path.exists("/opt/homebrew/bin/ffmpeg"):
            return "/opt/homebrew/bin"

        # Intel Mac
        if os.path.exists("/usr/local/bin/ffmpeg"):
            return "/usr/local/bin"

        # Tenta localizar automaticamente
        ffmpeg = shutil.which("ffmpeg")

        if ffmpeg:
            return os.path.dirname(ffmpeg)

        return None

    def start_download(self):
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror(
                "Erro",
                "Informe a URL do vídeo."
            )
            return

        folder = self.default_download_folder

        os.makedirs(folder, exist_ok=True)

        self.download_btn.config(state="disabled")
        self.show_finder_btn.config(state="disabled")
        self.status_var.set("Baixando para Downloads...")
        self.last_downloaded_file = None

        Thread(
            target=self.download_audio,
            args=(url, folder),
            daemon=True
        ).start()

    def download_audio(self, url, folder):
        try:
            ffmpeg_location = self.get_ffmpeg_location()

            print("FFmpeg encontrado em:", ffmpeg_location)

            if not ffmpeg_location:
                raise Exception(
                    "FFmpeg não encontrado.\n"
                    "Instale com:\n\n"
                    "brew install ffmpeg"
                )

            ydl_opts = {
                "format": "bestaudio/best",
                "ffmpeg_location": ffmpeg_location,
                "outtmpl": os.path.join(
                    folder,
                    "%(title)s.%(ext)s"
                ),
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "quiet": False,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                original_path = ydl.prepare_filename(info)
                mp3_path = os.path.splitext(original_path)[0] + ".mp3"

                if not os.path.exists(mp3_path):
                    raise Exception(
                        "Download concluído, mas não foi possível localizar o arquivo MP3 final."
                    )

                self.last_downloaded_file = mp3_path

            self.root.after(
                0,
                lambda: self.status_var.set(
                    "Download concluído!"
                )
            )

            self.root.after(
                0,
                lambda: self.show_finder_btn.config(
                    state="normal"
                )
            )

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Sucesso",
                    "Áudio baixado com sucesso!"
                )
            )

        except Exception as e:
            self.root.after(
                0,
                lambda: self.status_var.set("Erro")
            )

            self.root.after(
                0,
                lambda: self.show_finder_btn.config(state="disabled")
            )

            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro",
                    str(e)
                )
            )

        finally:
            self.root.after(
                0,
                lambda: self.download_btn.config(
                    state="normal"
                )
            )

    def show_in_finder(self):
        if not self.last_downloaded_file:
            return

        if not os.path.exists(self.last_downloaded_file):
            messagebox.showerror(
                "Erro",
                "O arquivo não foi encontrado no caminho esperado."
            )
            return

        try:
            # Em macOS, "open -R" revela e seleciona o arquivo no Finder.
            subprocess.run(["open", "-R", self.last_downloaded_file], check=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível mostrar no Finder: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeAudioDownloader(root)
    root.mainloop()