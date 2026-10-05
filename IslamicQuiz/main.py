"""
Islamic Quiz — заманбап исламий викторина (CustomTkinter)

Орнотуу:   pip install customtkinter
Иштетүү:   python main.py
"""

import json
import math
import os
import random
import sys
import time
import tkinter as tk
from collections import Counter
from datetime import datetime
from tkinter import messagebox

try:
    import customtkinter as ctk
except ImportError:
    _r = tk.Tk()
    _r.withdraw()
    messagebox.showerror(
        "Islamic Quiz",
        "CustomTkinter китепканасы табылган жок.\n\n"
        "Буйрук сабында төмөнкүнү аткарыңыз:\n\npip install customtkinter",
    )
    sys.exit(1)

# =====================================================================
# 1. КОНСТАНТАЛАР
# =====================================================================
APP_TITLE = "Islamic Quiz"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
RESULTS_FILE = os.path.join(BASE_DIR, "results.json")
LOGO_FILE = os.path.join(BASE_DIR, "assets", "logo.png")

MSG_NO_FILE = "questions.json файлы табылган жок"
MSG_BAD_FORMAT = "Суроолор файлынын форматы туура эмес"
MSG_CANNOT_READ = "questions.json файлын окуу мүмкүн болгон жок"

LETTERS = "ABCD"

# (суроо саны, аталышы)
MODES = [
    (10, "Тез тест"),
    (25, "Орто тест"),
    (50, "Чоң тест"),
    (100, "Толук марафон ★"),
]

FONT = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"
MONO = "Consolas" if sys.platform.startswith("win") else "Courier"

# Түстөр: кочкул жашыл + ак + алтын
C = {
    "bg": "#0b1512",
    "card": "#12231d",
    "card_alt": "#183228",
    "option": "#17302a",
    "option_hover": "#1f3f35",
    "option_dim": "#10211c",
    "border": "#2a4a3c",
    "green": "#1f6f4a",
    "green_hover": "#27885c",
    "gold": "#d4af37",
    "gold_hover": "#e8c95a",
    "gold_dim": "#6b5a24",
    "line": "#1c3a2e",
    "text": "#f4f1e8",
    "muted": "#9fb5aa",
    "ok": "#1f8f58",
    "ok_border": "#2fbf7a",
    "bad": "#a8403c",
    "bad_border": "#e0605b",
    "track": "#1e3a2f",
    "dark_text": "#0b1512",
}

ctk.set_appearance_mode("dark")


# =====================================================================
# 2. ЖАРДАМЧЫ ФУНКЦИЯЛАР
# =====================================================================
def mix(c1, c2, t):
    """Эки HEX түстүн ортосундагы түстү кайтарат (анимация үчүн)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def fmt_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def grade_text(percent):
    if percent >= 90:
        return "Мааша Аллах! Эң сонун жыйынтык"
    if percent >= 75:
        return "Абдан жакшы! Ушинтип улантыңыз"
    if percent >= 50:
        return "Жакшы башталыш. Дагы бир аракет кылыңыз"
    return "Кам санабаңыз — окуп, кайра аракет кылыңыз"


# =====================================================================
# 3. МААЛЫМАТ КАТМАРЫ (questions.json жана results.json)
# =====================================================================
class QuestionFileError(Exception):
    """Суроолор файлы менен байланышкан ката (экранга түшүнүктүү билдирүү чыгат)."""


def _validate_question(item):
    """Бир суроонун түзүлүшүн текшерет. Туура эмес болсо None кайтарат."""
    if not isinstance(item, dict):
        return None
    text = item.get("question")
    options = item.get("options")
    answer = item.get("answer")
    if not isinstance(text, str) or not text.strip() or not isinstance(options, list):
        return None
    clean = [str(o).strip() for o in options if isinstance(o, (str, int, float)) and str(o).strip()]
    clean = list(dict.fromkeys(clean))  # кайталанмаларды алып салуу
    if not 2 <= len(clean) <= 4:
        return None
    answer = str(answer).strip() if answer is not None else ""
    if answer not in clean:
        return None
    return {
        "question": text.strip(),
        "options": clean,
        "answer": answer,
        "category": str(item.get("category", "")).strip(),
    }


def load_questions(path=QUESTIONS_FILE):
    """questions.json окуп, туура суроолордун тизмесин кайтарат."""
    if not os.path.isfile(path):
        raise QuestionFileError(MSG_NO_FILE)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise QuestionFileError(MSG_BAD_FORMAT)
    except OSError:
        raise QuestionFileError(MSG_CANNOT_READ)

    if isinstance(data, dict):
        data = data.get("questions")
    if not isinstance(data, list):
        raise QuestionFileError(MSG_BAD_FORMAT)

    valid = [q for q in (_validate_question(i) for i in data) if q]
    if not valid:
        raise QuestionFileError(MSG_BAD_FORMAT)
    return valid


def build_session(bank, count):
    """
    Тест сессиясын түзөт.
    Туура жооптордун орду (A/B/C/D) ар бир иштетүүдө кокустан аныкталат жана
    мүмкүн болушунча тең бөлүштүрүлөт (100 суроодо 25/25/25/25).
    """
    count = min(count, len(bank))
    picked = random.sample(bank, count)

    base, extra = divmod(count, 4)
    slots = [pos for pos in range(4) for _ in range(base)]
    slots += random.sample(range(4), extra)
    random.shuffle(slots)

    session = []
    for q, slot in zip(picked, slots):
        opts = q["options"]
        if slot >= len(opts):                    # 2-3 варианттуу суроолор үчүн
            slot = random.randrange(len(opts))
        ordered = [o for o in opts if o != q["answer"]]
        random.shuffle(ordered)
        ordered.insert(slot, q["answer"])
        session.append({
            "question": q["question"],
            "category": q["category"],
            "options": ordered,
            "correct": slot,
            "selected": None,
        })
    return session


def save_results(results):
    """results.json'го атайын (атомдук) жазат. Ийгиликтүү болсо True."""
    tmp = RESULTS_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        os.replace(tmp, RESULTS_FILE)
        return True
    except OSError:
        return False


def load_results():
    """results.json окуйт. Жок болсо түзөт, бузулган болсо .bak кылып жаңыдан баштайт."""
    if not os.path.isfile(RESULTS_FILE):
        save_results([])
        return []
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("results", [])
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        pass
    try:
        os.replace(RESULTS_FILE, RESULTS_FILE + ".bak")
    except OSError:
        pass
    return []


# =====================================================================
# 4. ИСЛАМИЙ ОРНАМЕНТТЕР (Canvas менен чийилет)
# =====================================================================
def draw_star(canvas, cx, cy, r, color, width=1):
    """8 бурчтуу геометриялык жылдыз (эки квадраттын кесилиши)."""
    for offset in (0, 45):
        pts = []
        for k in range(4):
            a = math.radians(offset + 90 * k)
            pts.extend((cx + r * math.cos(a), cy + r * math.sin(a)))
        canvas.create_polygon(pts, outline=color, fill="", width=width)


def draw_mosque(canvas, cx, base, s):
    """Жөнөкөй мечит силуэти. s — масштаб."""
    body, roof, gold = "#1d4d3b", "#236049", C["gold"]
    lw = max(1, int(2 * s))
    for side in (-1, 1):  # минареттер
        x = cx + side * 105 * s
        canvas.create_rectangle(x - 9 * s, base - 130 * s, x + 9 * s, base, fill=body, outline="")
        canvas.create_rectangle(x - 13 * s, base - 102 * s, x + 13 * s, base - 95 * s, fill=roof, outline="")
        canvas.create_polygon(x - 12 * s, base - 130 * s, x + 12 * s, base - 130 * s,
                              x, base - 166 * s, fill=roof, outline="")
        canvas.create_oval(x - 3 * s, base - 175 * s, x + 3 * s, base - 166 * s, fill=gold, outline="")
    canvas.create_rectangle(cx - 85 * s, base - 55 * s, cx + 85 * s, base, fill=body, outline="")
    for side in (-1, 1):  # кичи гумбездер
        x = cx + side * 58 * s
        canvas.create_arc(x - 26 * s, base - 81 * s, x + 26 * s, base - 29 * s,
                          start=0, extent=180, fill=roof, outline="")
    canvas.create_arc(cx - 48 * s, base - 103 * s, cx + 48 * s, base - 7 * s,
                      start=0, extent=180, fill=roof, outline="")
    top = base - 103 * s
    canvas.create_line(cx, top, cx, top - 22 * s, fill=gold, width=lw)
    canvas.create_oval(cx - 8 * s, top - 42 * s, cx + 8 * s, top - 26 * s, fill=gold, outline="")
    canvas.create_oval(cx - 4 * s, top - 45 * s, cx + 9 * s, top - 29 * s, fill=C["bg"], outline="")
    canvas.create_rectangle(cx - 14 * s, base - 30 * s, cx + 14 * s, base, fill=C["bg"], outline="")
    canvas.create_arc(cx - 14 * s, base - 44 * s, cx + 14 * s, base - 16 * s,
                      start=0, extent=180, fill=C["bg"], outline="")
    for x in (-62 * s, 62 * s):  # терезелер
        canvas.create_rectangle(cx + x - 6 * s, base - 42 * s, cx + x + 6 * s, base - 14 * s,
                                fill=C["gold_dim"], outline="")
    canvas.create_line(cx - 145 * s, base, cx + 145 * s, base, fill=C["gold_dim"])


def draw_ornament(canvas):
    """Башкы беттин оң жагындагы орнамент: жылдыздар + мечит."""
    canvas.delete("all")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    if w < 60 or h < 60:
        return
    cx, cy = w / 2, h * 0.46
    r = min(w, h) * 0.40
    for k, f in enumerate((1.0, 0.82, 0.64, 0.46)):
        draw_star(canvas, cx, cy, r * f, C["gold_dim"] if k % 2 == 0 else C["line"], 1)
    canvas.create_oval(cx - r * 1.12, cy - r * 1.12, cx + r * 1.12, cy + r * 1.12,
                       outline=C["line"], width=1)
    for k in range(8):
        a = math.radians(45 * k)
        draw_star(canvas, cx + r * 1.12 * math.cos(a), cy + r * 1.12 * math.sin(a),
                  r * 0.07, C["gold"], 1)
    draw_mosque(canvas, cx, cy + r * 0.62, r / 230)


# =====================================================================
# 5. НЕГИЗГИ ТИРКЕМЕ
# =====================================================================
class IslamicQuizApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(fg_color=C["bg"])
        self.minsize(900, 640)
        self.center_window(1100, 700)

        # --- шрифттер ---
        self.f_hero = ctk.CTkFont(family=FONT, size=34, weight="bold")
        self.f_h2 = ctk.CTkFont(family=FONT, size=20, weight="bold")
        self.f_q = ctk.CTkFont(family=FONT, size=24, weight="bold")
        self.f_opt = ctk.CTkFont(family=FONT, size=17)
        self.f_btn = ctk.CTkFont(family=FONT, size=15, weight="bold")
        self.f_body = ctk.CTkFont(family=FONT, size=15)
        self.f_small = ctk.CTkFont(family=FONT, size=13)
        self.f_small_bold = ctk.CTkFont(family=FONT, size=13, weight="bold")
        self.f_tiny = ctk.CTkFont(family=FONT, size=12)

        # --- абал ---
        self.bank = []
        self.session = []
        self.index = 0
        self.mode_count = 25
        self.start_time = 0.0
        self.elapsed = 0
        self.stopped = False
        self.result_saved = False
        self.screen = ""
        self.logo_img = None
        self.mode_buttons = {}
        self._timer_id = None
        self._slide_id = None
        self._prog_id = None

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.bind("<Key>", self.on_key)

        self.reload_bank()

    # ------------------------------------------------------------------
    # Жалпы жардамчылар
    # ------------------------------------------------------------------
    def center_window(self, w, h):
        self.update_idletasks()
        x = max((self.winfo_screenwidth() - w) // 2, 0)
        y = max((self.winfo_screenheight() - h) // 2 - 20, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def clear_screen(self):
        self.stop_timer()
        for attr in ("_slide_id", "_prog_id"):
            after_id = getattr(self, attr)
            if after_id:
                try:
                    self.after_cancel(after_id)
                except (tk.TclError, ValueError):
                    pass
                setattr(self, attr, None)
        for child in self.container.winfo_children():
            child.destroy()

    def load_logo(self, size):
        """assets/logo.png бар болсо CTkImage кайтарат, болбосо None."""
        if not os.path.isfile(LOGO_FILE):
            return None
        try:
            from PIL import Image
            img = Image.open(LOGO_FILE)
            self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
            return self.logo_img
        except Exception:
            return None

    def make_button(self, parent, text, command, kind="secondary", width=160, height=48):
        styles = {
            "gold": dict(fg_color=C["gold"], hover_color=C["gold_hover"],
                         text_color=C["dark_text"], border_width=0),
            "primary": dict(fg_color=C["green"], hover_color=C["green_hover"],
                            text_color=C["text"], border_width=0),
            "secondary": dict(fg_color="transparent", hover_color=C["card_alt"],
                              text_color=C["text"], border_width=2, border_color=C["border"]),
        }
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=height,
                             corner_radius=14, font=self.f_btn, **styles[kind])

    def make_text_view(self, parent):
        """Окулуучу гана текст талаасы (жоопторду көрүү жана тарых үчүн)."""
        holder = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=20,
                              border_width=1, border_color=C["border"])
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)
        text = tk.Text(holder, bg=C["card"], fg=C["text"], bd=0, highlightthickness=0,
                       wrap="word", padx=22, pady=16, font=(FONT, 12), insertwidth=0,
                       relief="flat", cursor="arrow", spacing1=2, spacing3=2)
        bar = ctk.CTkScrollbar(holder, command=text.yview)
        text.configure(yscrollcommand=bar.set)
        text.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=8)
        bar.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=10)
        text.tag_configure("num", foreground=C["gold"], font=(FONT, 13, "bold"), spacing1=10)
        text.tag_configure("q", foreground=C["text"], font=(FONT, 13, "bold"), spacing1=10)
        text.tag_configure("plain", foreground=C["muted"])
        text.tag_configure("ok", foreground="#5ddc98")
        text.tag_configure("bad", foreground="#ff7b72")
        text.tag_configure("gold", foreground=C["gold"])
        text.tag_configure("mono", font=(MONO, 12), foreground=C["text"])
        text.tag_configure("head", foreground=C["gold"], font=(MONO, 12, "bold"))
        return holder, text

    # ------------------------------------------------------------------
    # Суроолорду жүктөө жана ката экраны
    # ------------------------------------------------------------------
    def reload_bank(self):
        try:
            self.bank = load_questions()
        except QuestionFileError as e:
            self.bank = []
            self.show_error(str(e))
            return
        self.show_home()

    def show_error(self, message):
        self.screen = "error"
        self.clear_screen()
        box = ctk.CTkFrame(self.container, fg_color=C["card"], corner_radius=28,
                           border_width=1, border_color=C["border"])
        box.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(padx=50, pady=36)
        ctk.CTkLabel(inner, text="⚠", font=ctk.CTkFont(family=FONT, size=44),
                     text_color=C["gold"]).pack()
        ctk.CTkLabel(inner, text=message, font=self.f_h2, text_color=C["text"],
                     wraplength=520).pack(pady=(10, 6))
        ctk.CTkLabel(inner, text=f"Файл: {QUESTIONS_FILE}", font=self.f_tiny,
                     text_color=C["muted"], wraplength=520).pack(pady=(0, 20))
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack()
        self.make_button(row, "Кайра текшерүү", self.reload_bank, "gold", 190).pack(side="left", padx=6)
        self.make_button(row, "Чыгуу", self.destroy, "secondary", 130).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # БАШКЫ БЕТ
    # ------------------------------------------------------------------
    def show_home(self):
        self.screen = "home"
        self.clear_screen()

        results = load_results()
        percents = [r["percent"] for r in results if isinstance(r.get("percent"), (int, float))]
        best = max(percents) if percents else None

        wrap = ctk.CTkFrame(self.container, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=40, pady=28)
        wrap.grid_columnconfigure(0, weight=5)
        wrap.grid_columnconfigure(1, weight=4)
        wrap.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(wrap, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        inner = ctk.CTkFrame(left, fg_color="transparent")
        inner.place(relx=0, rely=0.5, anchor="w")

        brand = ctk.CTkFrame(inner, fg_color="transparent")
        brand.pack(anchor="w")
        logo = self.load_logo((34, 34))
        if logo:
            ctk.CTkLabel(brand, image=logo, text="").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(brand, text="☪  ISLAMIC QUIZ", font=self.f_small_bold,
                     text_color=C["gold"]).pack(side="left")

        ctk.CTkLabel(inner, text="Исламий билим сынагы", font=self.f_hero,
                     text_color=C["text"], anchor="w").pack(anchor="w", pady=(16, 8))
        ctk.CTkLabel(inner, text="Ыйман, Куран, намаз, пайгамбарлар жана ислам тарыхы боюнча "
                                 "суроолор. Билимиңизди сынап, ар бир жолу жаңы нерсе үйрөнүңүз.",
                     font=self.f_body, text_color=C["muted"], wraplength=420,
                     justify="left", anchor="w").pack(anchor="w")

        ctk.CTkLabel(inner, text="Тесттин түрүн тандаңыз", font=self.f_small_bold,
                     text_color=C["text"]).pack(anchor="w", pady=(22, 8))

        grid = ctk.CTkFrame(inner, fg_color="transparent")
        grid.pack(anchor="w")
        self.mode_buttons = {}
        for i, (count, title) in enumerate(MODES):
            shown = min(count, len(self.bank))
            btn = ctk.CTkButton(grid, text=f"{shown} суроо\n{title}", width=204, height=62,
                                corner_radius=16, border_width=2, font=self.f_btn,
                                command=lambda c=count: self.select_mode(c))
            btn.grid(row=i // 2, column=i % 2, padx=3, pady=3)
            self.mode_buttons[count] = btn
        if self.mode_count not in self.mode_buttons:
            self.mode_count = MODES[1][0]
        self.select_mode(self.mode_count)

        self.make_button(inner, "▶   Тестти баштоо", self.start_test, "gold", 420, 56).pack(
            anchor="w", pady=(16, 10))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(anchor="w")
        self.make_button(row, "Натыйжалардын тарыхы", self.show_history, "secondary", 250, 44).pack(
            side="left", padx=(0, 10))
        self.make_button(row, "Чыгуу", self.destroy, "secondary", 160, 44).pack(side="left")

        stats = f"✦  Суроо базасы: {len(self.bank)}   ✦   Аракеттер: {len(results)}"
        if best is not None:
            stats += f"   ✦   Эң мыкты: {best:g}%"
        ctk.CTkLabel(inner, text=stats, font=self.f_tiny, text_color=C["muted"]).pack(
            anchor="w", pady=(14, 0))

        canvas = tk.Canvas(wrap, bg=C["bg"], highlightthickness=0)
        canvas.grid(row=0, column=1, sticky="nsew")
        canvas.bind("<Configure>", lambda e: draw_ornament(canvas))

    def select_mode(self, count):
        self.mode_count = count
        for c, btn in self.mode_buttons.items():
            active = c == count
            btn.configure(
                fg_color=C["green"] if active else C["option"],
                hover_color=C["green_hover"] if active else C["option_hover"],
                border_color=C["gold"] if active else C["border"],
                text_color=C["text"],
            )

    # ------------------------------------------------------------------
    # ТЕСТТИ БАШТОО ЖАНА СУРОО ЭКРАНЫ
    # ------------------------------------------------------------------
    def start_test(self):
        if not self.bank:
            self.reload_bank()
            return
        self.session = build_session(self.bank, self.mode_count)
        self.index = 0
        self.stopped = False
        self.result_saved = False
        self.start_time = time.time()
        self.show_quiz()

    def show_quiz(self):
        self.screen = "quiz"
        self.clear_screen()

        page = ctk.CTkFrame(self.container, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=36, pady=(18, 14))
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        # --- жогорку панель ---
        top = ctk.CTkFrame(page, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(2, weight=1)
        brand = ctk.CTkFrame(top, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w")
        logo = self.load_logo((28, 28))
        if logo:
            ctk.CTkLabel(brand, image=logo, text="").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(brand, text="☪  Islamic Quiz", font=self.f_small_bold,
                     text_color=C["gold"]).pack(side="left")
        self.counter_label = ctk.CTkLabel(top, text="", font=self.f_h2, text_color=C["text"])
        self.counter_label.grid(row=0, column=1)
        self.timer_label = ctk.CTkLabel(top, text="⏱ 00:00", font=self.f_small, text_color=C["muted"])
        self.timer_label.grid(row=0, column=2, sticky="e")

        # --- progress bar ---
        prog = ctk.CTkFrame(page, fg_color="transparent")
        prog.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        prog.grid_columnconfigure(0, weight=1)
        self.progress = ctk.CTkProgressBar(prog, height=14, corner_radius=7,
                                           fg_color=C["track"], progress_color=C["gold"])
        self.progress.grid(row=0, column=0, sticky="ew")
        self.progress.set(0)
        self.percent_label = ctk.CTkLabel(prog, text="0%", width=52, font=self.f_small_bold,
                                          text_color=C["gold"])
        self.percent_label.grid(row=0, column=1, padx=(12, 0))
        self.answered_label = ctk.CTkLabel(prog, text="", font=self.f_tiny,
                                           text_color=C["muted"], anchor="w")
        self.answered_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # --- суроо картасы ---
        self.holder = ctk.CTkFrame(page, fg_color="transparent", corner_radius=0)
        self.holder.grid(row=2, column=0, sticky="nsew", pady=14)
        self.card = ctk.CTkFrame(self.holder, fg_color=C["card"], corner_radius=24,
                                 border_width=1, border_color=C["border"])
        self.card.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_rowconfigure(2, weight=1)

        self.category_label = ctk.CTkLabel(self.card, text="", font=self.f_small_bold,
                                           text_color=C["gold"], anchor="w")
        self.category_label.grid(row=0, column=0, sticky="w", padx=36, pady=(22, 0))
        self.question_label = ctk.CTkLabel(self.card, text="", font=self.f_q,
                                           text_color=C["text"], justify="left",
                                           anchor="w", wraplength=600)
        self.question_label.grid(row=1, column=0, sticky="ew", padx=36, pady=(8, 14))

        opts = ctk.CTkFrame(self.card, fg_color="transparent")
        opts.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 22))
        opts.grid_columnconfigure(0, weight=1)
        self.option_buttons = []
        for i in range(4):
            opts.grid_rowconfigure(i, weight=1)
            btn = ctk.CTkButton(opts, text="", height=52, corner_radius=16, border_width=2,
                                anchor="w", font=self.f_opt,
                                command=lambda i=i: self.on_select(i))
            btn.grid(row=i, column=0, sticky="nsew", pady=5)
            self.option_buttons.append(btn)
        self.holder.bind("<Configure>", self.on_holder_resize, add="+")

        # --- төмөнкү навигация ---
        nav = ctk.CTkFrame(page, fg_color="transparent")
        nav.grid(row=3, column=0, sticky="ew")
        nav.grid_columnconfigure(2, weight=1)
        self.prev_btn = self.make_button(nav, "←  Мурунку", self.go_prev, "secondary", 150)
        self.prev_btn.grid(row=0, column=0, padx=(0, 10))
        self.make_button(nav, "↻  Кайра баштоо", self.restart_test, "secondary", 165).grid(row=0, column=1)
        self.make_button(nav, "Тестти токтотуу", self.stop_test, "secondary", 165).grid(
            row=0, column=3, padx=(0, 10))
        self.next_btn = self.make_button(nav, "Кийинки  →", self.go_next, "gold", 190)
        self.next_btn.grid(row=0, column=4)
        ctk.CTkLabel(page, text="Кыска баскычтар:  1–4 — жооп тандоо   ·   ← → — суроолор аралыгында өтүү",
                     font=self.f_tiny, text_color=C["muted"]).grid(row=4, column=0, pady=(8, 0))

        self.render_question(direction=0)
        self.tick()

    def on_holder_resize(self, event):
        """Терезенин өлчөмүнө жараша текстти жана шрифтти адаптациялайт."""
        try:
            self.question_label.configure(wraplength=max(260, event.width - 110))
            size_q = 20 if event.width < 760 else (24 if event.width < 1000 else 28)
            size_o = 15 if event.width < 760 else (17 if event.width < 1000 else 19)
            if self.f_q.cget("size") != size_q:
                self.f_q.configure(size=size_q)
            if self.f_opt.cget("size") != size_o:
                self.f_opt.configure(size=size_o)
        except (tk.TclError, AttributeError):
            pass

    def render_question(self, direction=1):
        q = self.session[self.index]
        total = len(self.session)
        pct = (self.index + 1) / total

        self.counter_label.configure(text=f"Суроо {self.index + 1} / {total}")
        self.percent_label.configure(text=f"{round(pct * 100)}%")
        self.animate_progress(pct)
        self.update_answered()
        self.category_label.configure(text=f"✦  {q['category'].upper()}" if q["category"] else "✦")
        self.question_label.configure(text=q["question"])

        for i, btn in enumerate(self.option_buttons):
            if i < len(q["options"]):
                btn.grid()
                btn.configure(text=f"   {LETTERS[i]}    {q['options'][i]}")
            else:
                btn.grid_remove()
        self.style_options()

        self.prev_btn.configure(state="normal" if self.index > 0 else "disabled")
        last = self.index == total - 1
        self.next_btn.configure(text="Аяктоо  ✓" if last else "Кийинки  →")
        if direction:
            self.slide_card(direction)

    def style_options(self):
        """Тандалган/туура/ката жоопторго жараша кнопкалардын түсүн коёт."""
        q = self.session[self.index]
        sel = q["selected"]
        for i, btn in enumerate(self.option_buttons):
            if i >= len(q["options"]):
                continue
            if sel is None:
                btn.configure(fg_color=C["option"], hover_color=C["option_hover"],
                              border_color=C["border"], text_color=C["text"], hover=True)
            elif i == q["correct"]:
                btn.configure(fg_color=C["ok"], border_color=C["ok_border"],
                              text_color="#ffffff", hover=False)
            elif i == sel:
                btn.configure(fg_color=C["bad"], border_color=C["bad_border"],
                              text_color="#ffffff", hover=False)
            else:
                btn.configure(fg_color=C["option_dim"], border_color=C["line"],
                              text_color=C["muted"], hover=False)

    def update_answered(self):
        done = sum(1 for q in self.session if q["selected"] is not None)
        self.answered_label.configure(text=f"Жооп берилген: {done} / {len(self.session)}")

    # ------------------------------------------------------------------
    # Жооп тандоо жана анимациялар
    # ------------------------------------------------------------------
    def on_select(self, i):
        if self.screen != "quiz":
            return
        q = self.session[self.index]
        if q["selected"] is not None or i >= len(q["options"]):
            return
        q["selected"] = i
        self.update_answered()

        if i == q["correct"]:
            self.tween_color(self.option_buttons[i], C["option"], C["ok"])
        else:
            self.tween_color(self.option_buttons[i], C["option"], C["bad"])
            self.tween_color(self.option_buttons[q["correct"]], C["option"], C["ok"])
        idx = self.index
        self.after(230, lambda: self.settle(idx))

    def settle(self, idx):
        if self.screen == "quiz" and self.index == idx:
            self.style_options()

    def tween_color(self, widget, c1, c2, steps=8, delay=18):
        """Кнопканын түсүн жылмакай өзгөртөт."""
        def step(n=0):
            try:
                widget.configure(fg_color=mix(c1, c2, (n + 1) / steps))
            except tk.TclError:
                return
            if n + 1 < steps:
                self.after(delay, step, n + 1)
        step()

    def slide_card(self, direction):
        """Суроо алмашканда картаны жылмакай жылдырат."""
        if self._slide_id:
            try:
                self.after_cancel(self._slide_id)
            except (tk.TclError, ValueError):
                pass
        steps, shift = 8, 0.06 * direction

        def step(n=0):
            try:
                t = (n + 1) / steps
                ease = 1 - (1 - t) ** 3
                self.card.place(relx=shift * (1 - ease), rely=0, relwidth=1, relheight=1)
            except tk.TclError:
                return
            self._slide_id = self.after(16, step, n + 1) if n + 1 < steps else None
        step()

    def animate_progress(self, target, steps=8):
        if self._prog_id:
            try:
                self.after_cancel(self._prog_id)
            except (tk.TclError, ValueError):
                pass
        start = self.progress.get()

        def step(n=0):
            try:
                self.progress.set(start + (target - start) * (n + 1) / steps)
            except tk.TclError:
                return
            self._prog_id = self.after(16, step, n + 1) if n + 1 < steps else None
        step()

    # ------------------------------------------------------------------
    # Таймер
    # ------------------------------------------------------------------
    def tick(self):
        try:
            self.timer_label.configure(text=f"⏱ {fmt_time(time.time() - self.start_time)}")
        except tk.TclError:
            return
        self._timer_id = self.after(1000, self.tick)

    def stop_timer(self):
        if self._timer_id:
            try:
                self.after_cancel(self._timer_id)
            except (tk.TclError, ValueError):
                pass
            self._timer_id = None

    # ------------------------------------------------------------------
    # Навигация жана башкаруу
    # ------------------------------------------------------------------
    def on_key(self, event):
        if self.screen != "quiz":
            return
        key = event.keysym
        if key in ("1", "2", "3", "4"):
            self.on_select(int(key) - 1)
        elif key in ("Left", "BackSpace"):
            self.go_prev()
        elif key in ("Right", "Return"):
            self.go_next()

    def go_prev(self):
        if self.index > 0:
            self.index -= 1
            self.render_question(direction=-1)

    def go_next(self):
        total = len(self.session)
        if self.index < total - 1:
            self.index += 1
            self.render_question(direction=1)
            return
        left = sum(1 for q in self.session if q["selected"] is None)
        if left and not messagebox.askyesno(
                "Тестти аяктоо", f"{left} суроого жооп берилген жок.\nТестти аяктайсызбы?", parent=self):
            return
        self.finish_test()

    def stop_test(self):
        if messagebox.askyesno("Тестти токтотуу",
                               "Тестти токтотуп, азыркы натыйжаны көрөсүзбү?", parent=self):
            self.finish_test(stopped=True)

    def restart_test(self):
        if messagebox.askyesno("Кайра баштоо",
                               "Тест кайра башталат, азыркы жооптор өчөт.\nУлантасызбы?", parent=self):
            self.start_test()

    def finish_test(self, stopped=False):
        self.stop_timer()
        self.elapsed = int(time.time() - self.start_time)
        self.stopped = stopped
        self.result_saved = False
        self.show_result()

    # ------------------------------------------------------------------
    # НАТЫЙЖА ЭКРАНЫ
    # ------------------------------------------------------------------
    def compute_stats(self):
        total = len(self.session)
        answered = sum(1 for q in self.session if q["selected"] is not None)
        correct = sum(1 for q in self.session if q["selected"] == q["correct"])
        return {
            "total": total,
            "answered": answered,
            "correct": correct,
            "wrong": answered - correct,
            "unanswered": total - answered,
            "percent": round(correct * 100 / total, 1) if total else 0.0,
        }

    def show_result(self):
        self.screen = "result"
        self.clear_screen()
        st = self.compute_stats()

        card = ctk.CTkFrame(self.container, fg_color=C["card"], corner_radius=28,
                            border_width=1, border_color=C["border"])
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=56, pady=28)

        title = "Тест токтотулду" if self.stopped else "Тест аяктады"
        ctk.CTkLabel(inner, text=f"✦  {title}  ✦", font=self.f_small_bold,
                     text_color=C["gold"]).pack()

        size, pad = 200, 14
        cv = tk.Canvas(inner, width=size, height=size, bg=C["card"], highlightthickness=0)
        cv.pack(pady=12)
        cv.create_oval(pad, pad, size - pad, size - pad, outline=C["track"], width=14)
        arc = cv.create_arc(pad, pad, size - pad, size - pad, start=90, extent=0,
                            style="arc", outline=C["gold"], width=14)
        txt = cv.create_text(size / 2, size / 2 - 8, text="0%", fill=C["text"],
                             font=(FONT, 34, "bold"))
        cv.create_text(size / 2, size / 2 + 28, text=f"{st['correct']} / {st['total']}",
                       fill=C["muted"], font=(FONT, 13))
        self.animate_ring(cv, arc, txt, st["percent"])

        ctk.CTkLabel(inner, text=grade_text(st["percent"]), font=self.f_h2,
                     text_color=C["text"]).pack(pady=(0, 6))
        ctk.CTkLabel(inner, text=f"Туура: {st['correct']}   ·   Ката: {st['wrong']}   ·   "
                                 f"Жооп берилген эмес: {st['unanswered']}",
                     font=self.f_small, text_color=C["muted"]).pack()
        ctk.CTkLabel(inner, text=f"Убакыт: {fmt_time(self.elapsed)}   ·   Тест: {st['total']} суроо",
                     font=self.f_small, text_color=C["muted"]).pack(pady=(2, 18))

        grid = ctk.CTkFrame(inner, fg_color="transparent")
        grid.pack()
        self.make_button(grid, "Жоопторду көрүү", self.show_review, "gold", 230).grid(
            row=0, column=0, padx=5, pady=5)
        self.save_btn = self.make_button(grid, "Натыйжаны сактоо", self.save_current_result, "primary", 230)
        self.save_btn.grid(row=0, column=1, padx=5, pady=5)
        self.make_button(grid, "Тестти кайра тапшыруу", self.start_test, "secondary", 230).grid(
            row=1, column=0, padx=5, pady=5)
        self.make_button(grid, "Башкы меню", self.show_home, "secondary", 230).grid(
            row=1, column=1, padx=5, pady=5)
        if self.result_saved:
            self.save_btn.configure(text="✓ Сакталды", state="disabled")

    def animate_ring(self, canvas, arc, txt, percent, steps=24):
        def step(n=0):
            try:
                t = (n + 1) / steps
                value = percent * (1 - (1 - t) ** 3)
                canvas.itemconfigure(arc, extent=-min(359.9, 360 * value / 100))
                canvas.itemconfigure(txt, text=f"{value:.0f}%" if n + 1 < steps else f"{percent:g}%")
            except tk.TclError:
                return
            if n + 1 < steps:
                self.after(16, step, n + 1)
        step()

    def save_current_result(self):
        if self.result_saved:
            return
        st = self.compute_stats()
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mode": st["total"],
            "total": st["total"],
            "answered": st["answered"],
            "correct": st["correct"],
            "percent": st["percent"],
            "duration_sec": self.elapsed,
            "stopped": self.stopped,
        }
        results = load_results()
        results.append(entry)
        if save_results(results):
            self.result_saved = True
            self.save_btn.configure(text="✓ Сакталды", state="disabled")
        else:
            messagebox.showerror("Ката", "results.json файлына жазуу мүмкүн болгон жок.", parent=self)

    # ------------------------------------------------------------------
    # ЖООПТОРДУ КӨРҮҮ
    # ------------------------------------------------------------------
    def show_review(self):
        self.screen = "review"
        self.clear_screen()

        page = ctk.CTkFrame(self.container, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=36, pady=22)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        head.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(head, text="Жоопторду көрүү", font=self.f_h2, text_color=C["text"]).grid(
            row=0, column=0, sticky="w")
        seg = ctk.CTkSegmentedButton(
            head, values=["Баары", "Каталар", "Туура"], command=self.render_review,
            fg_color=C["card_alt"], selected_color=C["green"], selected_hover_color=C["green_hover"],
            unselected_color=C["card_alt"], unselected_hover_color=C["option_hover"],
            text_color=C["text"], font=self.f_small_bold)
        seg.set("Баары")
        seg.grid(row=0, column=1, sticky="e", padx=(0, 12))
        self.make_button(head, "←  Натыйжага кайтуу", self.show_result, "secondary", 200, 40).grid(
            row=0, column=2)

        counts = Counter(q["correct"] for q in self.session)
        dist = "   ·   ".join(f"{LETTERS[i]} — {counts.get(i, 0)}" for i in range(4))
        ctk.CTkLabel(page, text=f"Туура жооптордун таралышы:   {dist}", font=self.f_tiny,
                     text_color=C["muted"], anchor="w").grid(row=1, column=0, sticky="w", pady=(6, 8))

        holder, self.review_text = self.make_text_view(page)
        holder.grid(row=2, column=0, sticky="nsew")
        self.render_review("Баары")

    def render_review(self, mode):
        t = self.review_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        shown = 0
        for n, q in enumerate(self.session, 1):
            sel = q["selected"]
            is_ok = sel == q["correct"]
            if mode == "Каталар" and is_ok:
                continue
            if mode == "Туура" and not is_ok:
                continue
            shown += 1
            t.insert("end", f"{n}.  ", "num")
            t.insert("end", q["question"] + "\n", "q")
            for i, opt in enumerate(q["options"]):
                if i == q["correct"]:
                    tag, mark = "ok", "✔"
                elif i == sel:
                    tag, mark = "bad", "✘"
                else:
                    tag, mark = "plain", " "
                t.insert("end", f"      {mark}  {LETTERS[i]})  {opt}\n", tag)
            if sel is None:
                t.insert("end", "      ➜ Жооп берилген жок\n", "gold")
        if shown == 0:
            t.insert("end", "Көрсөтүүгө эч нерсе жок.", "plain")
        t.configure(state="disabled")
        t.yview_moveto(0)

    # ------------------------------------------------------------------
    # НАТЫЙЖАЛАРДЫН ТАРЫХЫ
    # ------------------------------------------------------------------
    def show_history(self):
        self.screen = "history"
        self.clear_screen()

        page = ctk.CTkFrame(self.container, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=40, pady=26)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="Натыйжалардын тарыхы", font=self.f_h2, text_color=C["text"]).grid(
            row=0, column=0, sticky="w")
        self.make_button(head, "Тарыхты тазалоо", self.clear_history, "secondary", 170, 40).grid(
            row=0, column=1, padx=(0, 10))
        self.make_button(head, "←  Башкы меню", self.show_home, "secondary", 160, 40).grid(row=0, column=2)

        holder, self.history_text = self.make_text_view(page)
        holder.grid(row=1, column=0, sticky="nsew")
        self.fill_history()

    def fill_history(self):
        t = self.history_text
        results = load_results()
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not results:
            t.insert("end", "Азырынча сакталган натыйжа жок.\n"
                            "Тестти аяктап, «Натыйжаны сактоо» баскычын басыңыз.", "plain")
        else:
            t.insert("end", f"{'Күнү':<18}{'Суроо':<8}{'Туура':<10}{'Жыйынтык':<11}Убакыт\n", "head")
            for r in reversed(results[-100:]):
                date = str(r.get("date", "—"))
                total = r.get("total", "?")
                correct = r.get("correct", "?")
                percent = r.get("percent", "?")
                dur = fmt_time(r["duration_sec"]) if isinstance(r.get("duration_sec"), (int, float)) else "—"
                t.insert("end", f"{date:<18}{str(total):<8}{f'{correct}/{total}':<10}"
                                f"{f'{percent}%':<11}{dur}\n", "mono")
        t.configure(state="disabled")
        t.yview_moveto(0)

    def clear_history(self):
        if messagebox.askyesno("Тарыхты тазалоо", "Бардык сакталган натыйжалар өчүрүлөт.\nУлантасызбы?",
                               parent=self):
            if not save_results([]):
                messagebox.showerror("Ката", "results.json файлына жазуу мүмкүн болгон жок.", parent=self)
            self.fill_history()


# =====================================================================
# 6. ПРОГРАММАНЫ БАШТОО
# =====================================================================
if __name__ == "__main__":
    app = IslamicQuizApp()
    app.mainloop()