from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decoder import decode_payload
from encoder import encode_payload
from utils import (
    AuthenticationError,
    InvalidImageError,
    PayloadPackage,
    SteganographyError,
    ensure_directories,
    format_bytes,
    image_summary,
    log_operation,
    read_file_payload,
    read_text_payload,
    save_extracted_package,
    serialize_preview,
    timestamped_output_path,
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


class SecureSteganographyApp:
    def __init__(self) -> None:
        ensure_directories()
        self.root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
        self.root.title("Secure Steganography System")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(max(int(screen_w * 0.88), 920), 1400)
        height = min(max(int(screen_h * 0.88), 680), 960)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(820, 620)
        self.root.configure(bg="#101418")

        self.mode_var = tk.StringVar(value="text")
        self.source_image_var = tk.StringVar()
        self.payload_file_var = tk.StringVar()
        self.output_image_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.extract_image_var = tk.StringVar()
        self.extract_password_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.text_payload = tk.Text
        self.last_encoded_path = ""
        self.hero = None
        self.hero_copy_label = None
        self.hero_stats = None
        self.encode_pane = None
        self.decode_pane = None
        self.footer_links = None

        self._build_style()
        self._build_ui()
        self.root.bind("<Configure>", self._on_resize)

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        palette = {
            "bg": "#05080a",
            "panel": "#0a1110",
            "panel_alt": "#0f1917",
            "fg": "#d8ffe4",
            "muted": "#6ee7a8",
            "accent": "#00ff85",
            "accent_2": "#00c96b",
            "danger": "#ff5f56",
            "line": "#123126",
        }
        self.colors = palette

        style.configure(".", background=palette["bg"], foreground=palette["fg"], fieldbackground=palette["panel_alt"])
        style.configure("Card.TFrame", background=palette["panel"])
        style.configure("Surface.TFrame", background=palette["panel_alt"])
        style.configure("Hero.TFrame", background=palette["panel"])
        style.configure("Title.TLabel", background=palette["bg"], foreground=palette["fg"], font=("Consolas", 24, "bold"))
        style.configure("Sub.TLabel", background=palette["bg"], foreground=palette["muted"], font=("Consolas", 10))
        style.configure("HeroTitle.TLabel", background=palette["panel"], foreground=palette["accent"], font=("Consolas", 22, "bold"))
        style.configure("HeroSub.TLabel", background=palette["panel"], foreground=palette["fg"], font=("Consolas", 10))
        style.configure("CardTitle.TLabel", background=palette["panel"], foreground=palette["fg"], font=("Consolas", 13, "bold"))
        style.configure("Body.TLabel", background=palette["panel"], foreground=palette["fg"], font=("Consolas", 10))
        style.configure("SurfaceTitle.TLabel", background=palette["panel_alt"], foreground=palette["accent"], font=("Consolas", 13, "bold"))
        style.configure("SurfaceBody.TLabel", background=palette["panel_alt"], foreground=palette["muted"], font=("Consolas", 10))
        style.configure("TNotebook", background=palette["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=palette["panel_alt"], foreground=palette["muted"], padding=(16, 10), font=("Consolas", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", palette["accent_2"])], foreground=[("selected", "#02170b")])
        style.configure("Accent.Horizontal.TProgressbar", troughcolor=palette["panel_alt"], bordercolor=palette["panel_alt"], background=palette["accent"])
        style.configure("Accent.TButton", background=palette["accent"], foreground="#02170b", padding=(12, 10), borderwidth=0, focusthickness=0, font=("Consolas", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#5cffad")])
        style.configure("Ghost.TButton", background=palette["panel_alt"], foreground=palette["fg"], padding=(12, 10), borderwidth=1, focusthickness=0, font=("Consolas", 10))
        style.map("Ghost.TButton", background=[("active", "#163024")], foreground=[("active", palette["accent"])])
        style.configure("Footer.TLabel", background=palette["bg"], foreground=palette["fg"], font=("Consolas", 9, "bold"))
        style.configure("FooterBrand.TLabel", background=palette["bg"], foreground=palette["fg"], font=("Consolas", 10, "bold"))
        style.configure("FooterLink.TLabel", background=palette["panel_alt"], foreground=palette["fg"], font=("Consolas", 9, "bold"), padding=(10, 5))
        style.configure("TRadiobutton", background=palette["panel_alt"], foreground=palette["fg"], font=("Consolas", 10))
        style.map("TRadiobutton", foreground=[("selected", palette["accent"])])
        style.configure("TEntry", fieldbackground="#06100c", foreground=palette["fg"], insertcolor=palette["accent"], bordercolor=palette["line"], lightcolor=palette["line"], darkcolor=palette["line"], padding=8)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="Card.TFrame", padding=18)
        outer.pack(fill="both", expand=True)

        hero = ttk.Frame(outer, style="Hero.TFrame", padding=20)
        hero.pack(fill="x", pady=(0, 14))
        hero.columnconfigure(0, weight=1)
        hero.columnconfigure(1, weight=1)
        self.hero = hero
        ttk.Label(hero, text="[ SECURE STEGANOGRAPHY SYSTEM ]", style="HeroTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.hero_copy_label = ttk.Label(
            hero,
            text="Hide text or files inside images with AES-256 protection, randomized LSB embedding, and authenticated recovery.",
            style="HeroSub.TLabel",
            wraplength=620,
            justify="left",
        )
        self.hero_copy_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

        hero_stats = ttk.Frame(hero, style="Surface.TFrame", padding=14)
        hero_stats.grid(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0))
        self.hero_stats = hero_stats
        ttk.Label(hero_stats, text=":: SYSTEM STATUS ::", style="SurfaceTitle.TLabel").pack(anchor="w")
        ttk.Label(
            hero_stats,
            text="crypto: AES-256-GCM\nkdf: PBKDF2-SHA256\ncarrier: PNG-safe output\nmode: drag and drop ready",
            style="SurfaceBody.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        notebook = ttk.Notebook(outer)
        notebook.pack(fill="both", expand=True)

        encode_tab = ttk.Frame(notebook, style="Card.TFrame", padding=18)
        decode_tab = ttk.Frame(notebook, style="Card.TFrame", padding=18)
        notebook.add(encode_tab, text="Encode")
        notebook.add(decode_tab, text="Decode")

        self._build_encode_tab(encode_tab)
        self._build_decode_tab(decode_tab)

        footer = ttk.Frame(outer, style="Card.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        credits = ttk.Frame(footer, style="Card.TFrame")
        credits.pack(fill="x", pady=(0, 6))
        ttk.Label(credits, text="Developed By Rishabh dev Singh", style="FooterBrand.TLabel").pack(side="left", padx=(2, 14))
        self._footer_link(credits, "[ Portfolio ]", "https://rishabhadevsingh.netlify.app/").pack(side="left", padx=4)
        self._footer_link(credits, "[ LinkedIn ]", "https://www.linkedin.com/in/rishabhadevsingh/").pack(side="left", padx=4)
        self._footer_link(credits, "[ GitHub ]", "https://github.com/Bhatirishabhdevsingh").pack(side="left", padx=4)
        ttk.Progressbar(footer, variable=self.progress_var, maximum=100, style="Accent.Horizontal.TProgressbar").pack(fill="x")
        ttk.Label(footer, textvariable=self.status_var, style="Sub.TLabel").pack(anchor="w", pady=(6, 0))

    def _build_encode_tab(self, parent: ttk.Frame) -> None:
        pane = tk.PanedWindow(parent, orient=tk.HORIZONTAL, sashwidth=8, bd=0, bg=self.colors["bg"], relief="flat")
        pane.pack(fill="both", expand=True)
        self.encode_pane = pane

        left = ttk.Frame(pane, style="Surface.TFrame", padding=18)
        right = ttk.Frame(pane, style="Surface.TFrame", padding=18)
        pane.add(left, minsize=420, stretch="always")
        pane.add(right, minsize=360, stretch="always")

        self._section_title(left, "Carrier Image")
        self._path_picker(left, "Image", self.source_image_var, self.pick_source_image, accept_drop=True)
        ttk.Label(
            left,
            text="Tip: High-resolution PNG images give the best capacity and the safest output quality.",
            style="SurfaceBody.TLabel",
            wraplength=440,
        ).pack(anchor="w", pady=(0, 14))

        self._section_title(left, "Hidden Content")
        mode_row = ttk.Frame(left, style="Surface.TFrame")
        mode_row.pack(fill="x", pady=(0, 8))
        ttk.Radiobutton(mode_row, text="Hide Text", value="text", variable=self.mode_var, command=self._toggle_mode).pack(side="left")
        ttk.Radiobutton(mode_row, text="Hide File", value="file", variable=self.mode_var, command=self._toggle_mode).pack(side="left", padx=(14, 0))

        self.text_payload = tk.Text(
            left,
            height=11,
            wrap="word",
            bg="#06100c",
            fg="#d8ffe4",
            insertbackground="#00ff85",
            relief="flat",
            font=("Consolas", 11),
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground="#123126",
            highlightcolor="#00ff85",
        )
        self.text_payload.pack(fill="both", expand=True, pady=(4, 8))

        self.file_picker_frame = ttk.Frame(left, style="Surface.TFrame")
        self._path_picker(self.file_picker_frame, "Payload File", self.payload_file_var, self.pick_payload_file)
        self._toggle_mode()

        left_actions = ttk.Frame(left, style="Surface.TFrame")
        left_actions.pack(fill="x", pady=(4, 0))
        ttk.Button(
            left_actions,
            text="Choose Save Location",
            style="Ghost.TButton",
            command=self.pick_output_image,
        ).pack(side="left")

        self._section_title(right, "Security & Output")
        self._password_entry(right, "Password", self.password_var)
        self._path_picker(right, "Output Image", self.output_image_var, self.pick_output_image)
        quick_actions = ttk.Frame(right, style="Surface.TFrame")
        quick_actions.pack(fill="x", pady=(0, 12))
        ttk.Button(
            quick_actions,
            text="Auto Output Path",
            style="Ghost.TButton",
            command=lambda: self.output_image_var.set(timestamped_output_path("stego_image", ".png")),
        ).pack(side="left")
        ttk.Button(
            quick_actions,
            text="Clear Form",
            style="Ghost.TButton",
            command=self._reset_encode_form,
        ).pack(side="left", padx=(8, 0))
        ttk.Label(
            right,
            text="PNG output is enforced for integrity. JPG or JPEG carriers can be loaded, but stego data must be saved losslessly.",
            style="SurfaceBody.TLabel",
            wraplength=420,
        ).pack(anchor="w", pady=(0, 14))

        self.encode_meta = tk.Text(
            right,
            height=12,
            wrap="word",
            bg="#06100c",
            fg="#86f7b3",
            relief="flat",
            state="disabled",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground="#123126",
            highlightcolor="#00ff85",
        )
        self.encode_meta.pack(fill="both", expand=True, pady=(0, 10))
        action_bar = ttk.Frame(right, style="Surface.TFrame")
        action_bar.pack(fill="x", pady=(0, 4))
        action_bar.columnconfigure(0, weight=1)
        action_bar.columnconfigure(1, weight=1)
        ttk.Button(
            action_bar,
            text="Done",
            style="Ghost.TButton",
            command=self._reset_encode_form,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            action_bar,
            text="Submit Encryption",
            style="Accent.TButton",
            command=self.start_encode,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _build_decode_tab(self, parent: ttk.Frame) -> None:
        pane = tk.PanedWindow(parent, orient=tk.HORIZONTAL, sashwidth=8, bd=0, bg=self.colors["bg"], relief="flat")
        pane.pack(fill="both", expand=True)
        self.decode_pane = pane

        left = ttk.Frame(pane, style="Surface.TFrame", padding=18)
        right = ttk.Frame(pane, style="Surface.TFrame", padding=18)
        pane.add(left, minsize=380, stretch="always")
        pane.add(right, minsize=420, stretch="always")

        self._section_title(left, "Stego Image")
        self._path_picker(left, "Image", self.extract_image_var, self.pick_extract_image, accept_drop=True, drop_target="decode")
        self._password_entry(left, "Password", self.extract_password_var)
        ttk.Label(
            left,
            text="Use the same password used at encode time. Wrong passwords are rejected through authenticated decryption.",
            style="SurfaceBody.TLabel",
            wraplength=360,
        ).pack(anchor="w", pady=(0, 12))
        actions = ttk.Frame(left, style="Surface.TFrame")
        actions.pack(fill="x", pady=(0, 8))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="Clear Decode Form", style="Ghost.TButton", command=self._reset_decode_form).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text="Decode Hidden Payload", style="Accent.TButton", command=self.start_decode).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self._section_title(right, "Recovered Content")
        self.decode_output = tk.Text(
            right,
            height=24,
            wrap="word",
            bg="#06100c",
            fg="#86f7b3",
            relief="flat",
            state="disabled",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground="#123126",
            highlightcolor="#00ff85",
        )
        self.decode_output.pack(fill="both", expand=True)

    def _section_title(self, parent: ttk.Frame, title: str) -> None:
        ttk.Label(parent, text=title, style="SurfaceTitle.TLabel").pack(anchor="w", pady=(0, 10))

    def _path_picker(self, parent, label, variable, command, accept_drop=False, drop_target="encode") -> None:
        ttk.Label(parent, text=label, style="Body.TLabel").pack(anchor="w")
        row = ttk.Frame(parent, style="Surface.TFrame")
        row.pack(fill="x", pady=(6, 12))
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse", style="Ghost.TButton", command=command).pack(side="left", padx=(8, 0))

        if accept_drop and TkinterDnD:
            entry.drop_target_register(DND_FILES)
            entry.dnd_bind("<<Drop>>", lambda event: self._handle_drop(event, variable, drop_target))

    def _password_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Body.TLabel").pack(anchor="w")
        ttk.Entry(parent, textvariable=variable, show="*").pack(fill="x", pady=(6, 12))

    def _footer_link(self, parent: ttk.Frame, text: str, url: str) -> ttk.Label:
        label = ttk.Label(parent, text=text, style="FooterLink.TLabel", cursor="hand2")
        label.bind("<Button-1>", lambda _event: self._open_url(url))
        return label

    def _open_url(self, url: str) -> None:
        self.root.after(0, lambda: __import__("webbrowser").open_new_tab(url))

    def _on_resize(self, event) -> None:
        if event.widget is not self.root:
            return

        width = self.root.winfo_width()

        if self.hero and self.hero_stats and self.hero_copy_label:
            if width < 1040:
                self.hero_stats.grid_configure(row=2, column=0, rowspan=1, sticky="ew", padx=(0, 0), pady=(14, 0))
                self.hero.grid_columnconfigure(1, weight=0)
                self.hero_copy_label.configure(wraplength=max(width - 160, 320))
            else:
                self.hero_stats.grid_configure(row=0, column=1, rowspan=2, sticky="e", padx=(16, 0), pady=(0, 0))
                self.hero.grid_columnconfigure(1, weight=1)
                self.hero_copy_label.configure(wraplength=620)

        if self.encode_pane:
            self.encode_pane.configure(orient=tk.VERTICAL if width < 1100 else tk.HORIZONTAL)

        if self.decode_pane:
            self.decode_pane.configure(orient=tk.VERTICAL if width < 1100 else tk.HORIZONTAL)


    def _toggle_mode(self) -> None:
        if self.mode_var.get() == "file":
            self.text_payload.pack_forget()
            self.file_picker_frame.pack(fill="x", pady=(4, 8))
        else:
            self.file_picker_frame.pack_forget()
            self.text_payload.pack(fill="both", expand=True, pady=(4, 8))

    def _reset_encode_form(self) -> None:
        self.source_image_var.set("")
        self.payload_file_var.set("")
        self.output_image_var.set("")
        self.password_var.set("")
        self.last_encoded_path = ""
        self.mode_var.set("text")
        self.text_payload.delete("1.0", "end")
        self._toggle_mode()
        self._set_text_widget(self.encode_meta, "Choose a carrier image to see image details and encoding results.")
        self._set_status(0, "Ready")

    def _reset_decode_form(self) -> None:
        self.extract_image_var.set("")
        self.extract_password_var.set("")
        self._set_text_widget(self.decode_output, "Recovered content details will appear here after decoding.")
        self._set_status(0, "Ready")

    def _handle_drop(self, event, variable: tk.StringVar, target: str) -> None:
        path = event.data.strip("{}")
        variable.set(path)
        if target == "encode":
            self._update_encode_summary()

    def pick_source_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if path:
            self.source_image_var.set(path)
            if not self.output_image_var.get():
                self.output_image_var.set(timestamped_output_path(Path(path).stem, ".png"))
            self._update_encode_summary()

    def pick_payload_file(self) -> None:
        path = filedialog.askopenfilename()
        if path:
            self.payload_file_var.set(path)
            self._update_encode_summary()

    def pick_output_image(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.output_image_var.set(path)

    def pick_extract_image(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if path:
            self.extract_image_var.set(path)

    def _update_encode_summary(self) -> None:
        path = self.source_image_var.get()
        if not path:
            return
        try:
            summary = image_summary(path)
            width, height = summary["size"]
            capacity_bytes = max((((width * height * 3) - (57 * 8)) // 8), 0)
            text = (
                f"Carrier image\n"
                f"Format: {summary['format']}\n"
                f"Mode: {summary['mode']}\n"
                f"Dimensions: {width} x {height}\n"
                f"Approx payload capacity: {format_bytes(capacity_bytes)}\n"
            )
            self._set_text_widget(self.encode_meta, text)
        except Exception as exc:
            self._set_text_widget(self.encode_meta, f"Unable to inspect image: {exc}")

    def _set_text_widget(self, widget: tk.Text, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")

    def _set_status(self, percent: float, message: str) -> None:
        styled_message = f"> {message}"
        self.root.after(0, lambda: self.progress_var.set(percent * 100))
        self.root.after(0, lambda: self.status_var.set(styled_message))

    def start_encode(self) -> None:
        threading.Thread(target=self._encode_worker, daemon=True).start()

    def start_decode(self) -> None:
        threading.Thread(target=self._decode_worker, daemon=True).start()

    def _build_payload(self) -> PayloadPackage:
        if self.mode_var.get() == "file":
            if not self.payload_file_var.get():
                raise SteganographyError("Choose a file to hide.")
            return read_file_payload(self.payload_file_var.get())

        text = self.text_payload.get("1.0", "end").strip()
        if not text:
            raise SteganographyError("Enter the message you want to hide.")
        return read_text_payload(text)

    def _encode_worker(self) -> None:
        try:
            image_path = self.source_image_var.get().strip()
            password = self.password_var.get()
            output_path = self.output_image_var.get().strip()
            if not image_path:
                raise SteganographyError("Choose a carrier image first.")
            if not password:
                raise SteganographyError("Enter a password for encryption.")
            if not output_path:
                output_path = timestamped_output_path("stego_image", ".png")
                self.output_image_var.set(output_path)
            if not output_path.lower().endswith(".png"):
                raise SteganographyError("Output must use the PNG format to preserve hidden data.")

            package = self._build_payload()
            result = encode_payload(image_path, package, password, output_path, progress_callback=self._set_status)
            preview = (
                f"Encoding successful\n\n"
                f"Saved to: {result['output_path']}\n"
                f"Payload size: {format_bytes(len(package.data))}\n"
                f"Encrypted bytes: {format_bytes(result['ciphertext_bytes'])}\n"
                f"Usable carrier capacity: {format_bytes(result['carrier_capacity_bytes'])}\n"
                f"Payload type: {package.payload_type}\n"
                f"Original name: {package.file_name or 'message.txt'}\n"
            )
            self.last_encoded_path = result["output_path"]
            self._set_text_widget(self.encode_meta, preview)
            log_operation("encode", image_path, "success", len(package.data), f"output={result['output_path']}")
        except Exception as exc:
            self._set_status(0, "Encoding failed")
            log_operation("encode", self.source_image_var.get(), "failed", 0, str(exc))
            self.root.after(0, lambda err=str(exc): messagebox.showerror("Encoding Error", err))

    def _decode_worker(self) -> None:
        try:
            image_path = self.extract_image_var.get().strip()
            password = self.extract_password_var.get()
            if not image_path:
                raise SteganographyError("Choose a stego image to decode.")
            if not password:
                raise SteganographyError("Enter the password used during encoding.")

            package = decode_payload(image_path, password, progress_callback=self._set_status)
            saved_path = save_extracted_package(package)
            preview = (
                f"Decoding successful\n\n"
                f"Saved to: {saved_path}\n"
                f"{serialize_preview(package)}"
            )
            self._set_text_widget(self.decode_output, preview)
            log_operation("decode", image_path, "success", len(package.data), f"saved={saved_path}")
        except (AuthenticationError, InvalidImageError, SteganographyError) as exc:
            self._set_status(0, "Decoding failed")
            log_operation("decode", self.extract_image_var.get(), "failed", 0, str(exc))
            self.root.after(0, lambda err=str(exc): messagebox.showerror("Decoding Error", err))
        except Exception as exc:
            self._set_status(0, "Unexpected error")
            log_operation("decode", self.extract_image_var.get(), "failed", 0, str(exc))
            self.root.after(0, lambda err=str(exc): messagebox.showerror("Decoding Error", err))

    def run(self) -> None:
        self.root.mainloop()


def run() -> None:
    app = SecureSteganographyApp()
    app.run()
