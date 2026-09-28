#!/usr/bin/env python3
"""Painel local para experimentar os limites de altura do SARndbox 2.8."""

import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import tkinter as tk
from tkinter import messagebox, ttk
import projecao_visual as visual_tools
from area_scan import SensorCanvas, validate_area

ROOT = Path(__file__).resolve().parent


def find_sandbox(environ=os.environ, root=ROOT, home=None):
    """Localiza a instalação do SARndbox 2.8.

    SARNDBOX_DIR tem prioridade. Sem ela, o primeiro local testado é o da
    montagem original (pasta vizinha a Kinect-3.10), depois outros comuns.
    """
    configured = environ.get("SARNDBOX_DIR")
    if configured:
        return Path(configured).expanduser()
    home = Path.home() if home is None else home
    candidates = [root.parent / "SARndbox-2.8", root / "SARndbox-2.8",
                  root.parent.parent / "SARndbox-2.8", home / "src" / "SARndbox-2.8",
                  home / "SARndbox-2.8"]
    for candidate in candidates:
        if (candidate / "etc" / "SARndbox-2.8").is_dir():
            return candidate
    return candidates[0]


SANDBOX = find_sandbox()
CONFIG = SANDBOX / "etc" / "SARndbox-2.8"
STATE = ROOT / "ajuste_altura"
DEFAULTS = {"fundo": -40.0, "topo": 25.0, "nivel": 0.0}
PROC = Path("/proc")
# Programas que abrem o Kinect e impedem o SARndbox de usá-lo ao mesmo tempo.
KINECT_PROGRAMS = ("RawKinectViewer", "KinectViewer", "KinectUtil", "KinectServer",
                   "CalibrateProjector", "SARndbox")
STOP_TIMEOUT = 5.0
USB_DEVICES = Path("/sys/bus/usb/devices")
KINECT_VENDOR = "045e"
# Mesmos IDs de share/69-Kinect.rules: câmeras (Xbox 360, Windows, v2) e motores.
KINECT_CAMERAS = {"02ae", "02bf", "02c4"}
KINECT_MOTORS = {"02b0", "02c2"}
KINECT_MESSAGES = {
    "sem_energia": "Kinect ligado ao USB, mas a câmera não respondeu. Confira a fonte de alimentação do Kinect.",
    "ausente": "Kinect não detectado. Confira o cabo USB e a fonte de alimentação.",
}
WAITING_KINECT = "Aguardando o Kinect… a projeção abre sozinha quando ele for detectado."


def validate(values):
    bottom, top, sea = (values[k] for k in ("fundo", "topo", "nivel"))
    if not all(math.isfinite(v) for v in (bottom, top, sea)):
        raise ValueError("Use números válidos em centímetros.")
    if not bottom < sea < top:
        raise ValueError("O nível azul/verde precisa ficar entre o fundo e o topo.")


def make_palette(source, values):
    """Mantém as cores, redistribuindo as alturas em torno do nível escolhido."""
    validate(values)
    rows = [line.split() for line in source.splitlines() if line.strip()]
    heights = [float(row[0]) for row in rows]
    if not heights or not heights[0] < 0 < heights[-1]:
        raise ValueError("O mapa original precisa incluir alturas negativas e positivas.")
    if any(a >= b for a, b in zip(heights, heights[1:])):
        raise ValueError("As alturas do mapa original devem estar em ordem crescente.")
    output = []
    for height, row in zip(heights, rows):
        if len(row) != 4:
            raise ValueError("Formato inesperado no mapa de cores original.")
        if height < 0:
            mapped = values["nivel"] + height / (-heights[0]) * (
                values["nivel"] - values["fundo"])
        else:
            mapped = values["nivel"] + height / heights[-1] * (
                values["topo"] - values["nivel"])
        output.append(f"{mapped:.12g} {' '.join(row[1:])}\n")
    return "".join(output)


def external_output():
    """Usa a única tela externa ativa, se puder identificá-la sem ambiguidade."""
    try:
        result = subprocess.run(["xrandr", "--query"], capture_output=True,
                                text=True, timeout=3, check=True)
    except (OSError, subprocess.SubprocessError):
        return None
    outputs = []
    for line in result.stdout.splitlines():
        if (" connected " in line and " primary " not in line
                and re.search(r"\d+x\d+\+\d+\+\d+", line)):
            outputs.append(line.split()[0])
    return outputs[0] if len(outputs) == 1 else None


def kinect_status(devices=None):
    """Retorna "ok", "sem_energia" ou "ausente"; None se não houver como verificar."""
    devices = USB_DEVICES if devices is None else devices
    products = set()
    try:
        for device in devices.iterdir():
            try:
                if (device / "idVendor").read_text().strip() == KINECT_VENDOR:
                    products.add((device / "idProduct").read_text().strip())
            except OSError:
                continue
    except OSError:
        return None
    if products & KINECT_CAMERAS:
        return "ok"
    # Sem a fonte externa, o Kinect de Xbox 360 aparece apenas como motor.
    return "sem_energia" if products & KINECT_MOTORS else "ausente"


def kinect_users(ignore=(), proc=None):
    """Retorna {pid: programa} de outros programas que estejam usando o Kinect."""
    proc = PROC if proc is None else proc
    found = {}
    try:
        entries = list(proc.iterdir())
    except OSError:
        return found
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) in ignore:
            continue
        try:
            name = (entry / "comm").read_text().strip()
        except OSError:
            continue
        # O Linux corta o nome do processo em 15 caracteres.
        program = next((p for p in KINECT_PROGRAMS if name == p[:15]), None)
        if program:
            found[int(entry.name)] = program
    return found


def atomic_write(path, content):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def kinect_missing(log_text):
    return "3D cameras connected to local host" in log_text or "Kinect camera devices detected" in log_text


def explain_failure(log_text):
    if kinect_missing(log_text):
        return ("A câmera do Kinect não foi detectada. Confira a fonte de alimentação "
                "e reconecte o cabo USB. Depois clique em Aplicar novamente.")
    if "LIBUSB_ERROR_BUSY" in log_text or "Resource busy" in log_text:
        return "O Kinect está ocupado. Feche RawKinectViewer, CalibrateProjector ou outro SARndbox e tente novamente."
    if "LIBUSB_ERROR_ACCESS" in log_text or "Permission denied" in log_text:
        return "Acesso negado a um dispositivo ou arquivo. Consulte o registro para identificar a permissão que falta."
    fatal = next((line.strip() for line in reversed(log_text.splitlines())
                  if "Terminated Sandbox" in line), None)
    return fatal or "A projeção encerrou com erro. Consulte o registro para ver a causa."


class Panel:
    def __init__(self, window):
        self.window = window
        self.process = None
        self.log = None
        self.mode = ""
        self.applying = False
        self.kinect = kinect_status()
        self.waiting_kinect = False
        self.start_scheduled = False
        self.preview_file = STATE / "preview.ppm"
        self.preview_stamp = None
        self.preview_image = None
        self.metrics_stamp = None
        self.camera_file = STATE / "camera.ppm"
        self.camera_stamp = None
        self.camera_image = None
        self.camera_enabled = tk.BooleanVar(value=True)
        self.camera_mode = tk.StringVar(value="Profundidade (relevo)")
        try:
            saved_mode = json.loads((STATE / "valores.json").read_text()).get("camera_modo", "")
            if saved_mode in ("Profundidade (relevo)", "Colorida"):
                self.camera_mode.set(saved_mode)
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        self.active_camera = True
        self.active_camera_mode = "Profundidade (relevo)"
        self.scan_points = []
        self.scan_marking = False
        try:
            points = json.loads((STATE / "valores.json").read_text()).get("area_scan", [])
            validate_area(points)
            self.scan_points = points
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        try:
            self.camera_enabled.set(bool(json.loads((STATE / "valores.json").read_text()).get("camera", True)))
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        performance = "Resposta rápida"
        try:
            requested = json.loads((STATE / "valores.json").read_text()).get("desempenho", performance)
            if requested in visual_tools.PERFORMANCE_PROFILES:
                performance = requested
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        self.performance = tk.StringVar(value=performance)
        self.active_performance = performance
        values = dict(DEFAULTS)
        visual = dict(visual_tools.DEFAULTS)
        try:
            saved = json.loads((STATE / "valores.json").read_text())
            candidate = {k: float(saved[k]) for k in DEFAULTS}
            validate(candidate)
            values = candidate
            rotation = float(saved.get("rotacao", 0))
            visual_tools.rotation_terms(rotation)
            visual = {"rotacao": rotation, "relevo": bool(saved.get("relevo", True)),
                      "curvas": bool(saved.get("curvas", True))}
        except (OSError, ValueError, KeyError, TypeError):
            pass
        crop = dict(visual_tools.CROP_DEFAULTS)
        try:
            saved_crop = json.loads((STATE / "valores.json").read_text()).get("recorte", crop)
            visual_tools.crop_options(saved_crop)
            crop = saved_crop
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass
        self.crop = {k: tk.DoubleVar(value=float(crop[k])) for k in visual_tools.CROP_DEFAULTS}
        self.variables = {k: tk.DoubleVar(value=v) for k, v in values.items()}
        size_percent = 100.0
        try:
            requested = float(json.loads((STATE / "valores.json").read_text()).get("tamanho", 100))
            if math.isfinite(requested) and 40 <= requested <= 150:
                size_percent = requested
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        self.view_size = tk.DoubleVar(value=size_percent)
        self.rotation = tk.DoubleVar(value=visual["rotacao"])
        self.relief = tk.BooleanVar(value=visual["relevo"])
        self.contours = tk.BooleanVar(value=visual["curvas"])
        window.title("Regular areia e projeção")
        # Cabe em 800x600 mesmo se o desktop virtual incluir um monitor maior.
        window.geometry("650x480+20+40")
        window.minsize(600, 320)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(window)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        body = ttk.Frame(self.notebook)
        self.notebook.add(body, text="Ajustes")
        self.preview_page = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.preview_page, text="Prévia do projetor")
        ttk.Label(self.preview_page, text="Mesma imagem enviada ao projetor", font=("Sans", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.preview_label = tk.Label(self.preview_page, bg="black", fg="white",
                                      text="Clique em Aplicar para iniciar a projeção.")
        self.preview_label.pack(fill="both", expand=True)
        ttk.Label(self.preview_page, text="Prévia reduzida, até 5 imagens/s. A projeção tem seu próprio FPS.", wraplength=580).pack(anchor="w", pady=(8, 0))
        self.camera_page = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.camera_page, text="Câmera do Kinect")
        camera_controls = ttk.Frame(self.camera_page)
        camera_controls.pack(fill="x")
        ttk.Checkbutton(camera_controls, text="Ativar prévia", variable=self.camera_enabled).pack(side="left")
        ttk.Combobox(camera_controls, textvariable=self.camera_mode, state="readonly",
                     values=("Profundidade (relevo)", "Colorida"), width=25).pack(side="left", padx=8)
        area_buttons = ttk.Frame(self.camera_page)
        area_buttons.pack(fill="x", pady=4)
        ttk.Button(area_buttons, text="Marcar 4 cantos", command=self.mark_scan_area).pack(side="left")
        ttk.Button(area_buttons, text="Usar toda a captura", command=self.clear_scan_area).pack(side="left", padx=6)
        self.area_hint = tk.StringVar(value="Marque as bordas internas da caixa; arraste os pontos para ajustar.")
        ttk.Label(self.camera_page, textvariable=self.area_hint, wraplength=580).pack(anchor="w", pady=(0, 4))
        self.camera_label = SensorCanvas(self.camera_page, self.scan_area_changed)
        self.camera_label.points = [list(p) for p in self.scan_points]
        self.camera_label.pack(fill="both", expand=True)
        ttk.Label(self.camera_page, text="Profundidade: claro = perto; escuro = longe; preto = sem leitura.\n"
                  "Contraste automático. Selecione os cantos e clique em Aplicar.",
                  wraplength=580).pack(anchor="w", pady=(4, 0))
        self.canvas = tk.Canvas(body, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        frame = ttk.Frame(self.canvas, padding=12)
        self.content = frame
        content_id = self.canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(content_id, width=event.width))
        self.footer = ttk.Frame(window, padding=(12, 8))
        self.footer.grid(row=1, column=0, sticky="ew")
        ttk.Label(frame, text="Ajuste por tentativa", font=("Sans", 17, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Valores em cm em relação ao plano já medido da caixa.\n"
                  "Mude de 1 em 1 cm e clique em Aplicar.", wraplength=560).pack(anchor="w", pady=(6, 12))
        performance_frame = ttk.LabelFrame(frame, text="Desempenho", padding=8)
        performance_frame.pack(fill="x", pady=(0, 8))
        ttk.Combobox(performance_frame, textvariable=self.performance, state="readonly",
                     values=list(visual_tools.PERFORMANCE_PROFILES), width=24).pack(anchor="w")
        ttk.Label(performance_frame, text="Resposta rápida mantém os detalhes da água. Mais leve reduz a simulação.\n"
                  "Se a areia ficar tremendo, experimente Mais suave.", wraplength=560).pack(anchor="w", pady=(5, 0))
        specs = [("fundo", "Fundo — menor altura aceita / azul escuro", -80, 40),
                 ("nivel", "Nível azul/verde — aumentar faz o azul subir", -60, 60),
                 ("topo", "Topo — maior altura aceita / branco", -20, 80)]
        for key, label, low, high in specs:
            ttk.Label(frame, text=label).pack(anchor="w")
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=(0, 8))
            tk.Scale(row, variable=self.variables[key], from_=low, to=high,
                     resolution=0.5, orient="horizontal", showvalue=False,
                     highlightthickness=0).pack(side="left", fill="x", expand=True)
            ttk.Entry(row, textvariable=self.variables[key], width=8).pack(side="right", padx=(10, 0))
        appearance = ttk.LabelFrame(frame, text="Aparência do modo normal", padding=8)
        appearance.pack(fill="x", pady=6)
        ttk.Checkbutton(appearance, text="Sombreamento do relevo", variable=self.relief).pack(side="left")
        ttk.Checkbutton(appearance, text="Curvas de nível", variable=self.contours).pack(side="left", padx=15)
        rotation_frame = ttk.LabelFrame(frame, text="Girar imagem no sentido horário", padding=8)
        rotation_frame.pack(fill="x", pady=6)
        rotation_row = ttk.Frame(rotation_frame)
        rotation_row.pack(fill="x")
        tk.Scale(rotation_row, variable=self.rotation, from_=0, to=360, resolution=1,
                 orient="horizontal", showvalue=False, highlightthickness=0).pack(side="left", fill="x", expand=True)
        ttk.Entry(rotation_row, textvariable=self.rotation, width=8).pack(side="right")
        presets = ttk.Frame(rotation_frame)
        presets.pack(fill="x")
        for angle in (0, 90, 180, 270, 360):
            ttk.Button(presets, text=f"{angle}°", width=7,
                       command=lambda a=angle: self.rotation.set(a)).pack(side="left", padx=3)
        ttk.Label(rotation_frame, text="360° volta à posição inicial. Depois clique em Aplicar.").pack(anchor="w", pady=(5, 0))
        view_frame = ttk.LabelFrame(frame, text="Enquadramento da caixa", padding=8)
        view_frame.pack(fill="x", pady=6)
        ttk.Label(view_frame, text="Tamanho da imagem (%) — diminua para ver mais da caixa").pack(anchor="w")
        view_row = ttk.Frame(view_frame)
        view_row.pack(fill="x")
        calibrated = (CONFIG / "ProjectorMatrix.dat").is_file()
        tk.Scale(view_row, variable=self.view_size, from_=40, to=150, resolution=1,
                 state="disabled" if calibrated else "normal", orient="horizontal",
                 showvalue=True, highlightthickness=0).pack(fill="x")
        ttk.Button(view_frame, text="Afastar e remover recortes", command=self.widen_view,
                   state="disabled" if calibrated else "normal").pack(anchor="w")
        ttk.Label(view_frame, text="Com calibração, o enquadramento vem da matriz do projetor." if calibrated else
                  "Mantém as proporções. Depois confira a prévia e clique em Aplicar.",
                  wraplength=560).pack(anchor="w", pady=(5, 0))
        crop_frame = ttk.LabelFrame(frame, text="Recortar paredes (% da imagem projetada)", padding=8)
        crop_frame.pack(fill="x", pady=6)
        for column, (key, variable) in enumerate(self.crop.items()):
            crop_frame.columnconfigure(column, weight=1)
            ttk.Label(crop_frame, text=key.capitalize()).grid(row=0, column=column, sticky="w")
            ttk.Spinbox(crop_frame, from_=0, to=45, increment=0.5, textvariable=variable,
                        width=9).grid(row=1, column=column, sticky="w", pady=4)
        ttk.Button(crop_frame, text="Sugestão da foto", command=self.suggest_crop).grid(row=2, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Button(crop_frame, text="Sem recorte", command=self.clear_crop).grid(row=2, column=2, columnspan=2, sticky="w", pady=4)
        ttk.Label(crop_frame, text="Esconde as bordas sem esticar a imagem. Clique em Aplicar.").grid(row=3, column=0, columnspan=4, sticky="w")
        buttons = ttk.Frame(self.footer)
        buttons.pack(fill="x", pady=(0, 4))
        self.apply_button = ttk.Button(buttons, text="Aplicar e abrir a projeção", command=self.apply)
        self.apply_button.pack(side="left")
        self.cancel_button = ttk.Button(buttons, text="Cancelar espera", command=self.cancel_wait)
        ttk.Button(buttons, text="Restaurar valores iniciais", command=self.restore).pack(side="right")
        self.fps_status = tk.StringVar(value="Projeção: aguardando início")
        ttk.Label(self.footer, textvariable=self.fps_status).pack(anchor="w", pady=(4, 0))
        initial_status = "Pronto. Feche outros programas que estejam usando o Kinect."
        try:
            previous_log = (STATE / "sarndbox.log").read_text(errors="replace")
            if "Terminated Sandbox" in previous_log:
                initial_status = "Última tentativa: " + explain_failure(previous_log)
        except OSError:
            pass
        self.status = tk.StringVar(value=initial_status)
        self.status_label = ttk.Label(self.footer, textvariable=self.status, wraplength=600)
        self.status_label.pack(anchor="w", fill="x", pady=(4, 0))
        self.kinect_warning = tk.Label(self.footer, fg="#b00000", font=("Sans", 10, "bold"),
                                       justify="left", anchor="w", wraplength=600)
        self.show_kinect_warning()

        def footer_resized(event):
            for label in (self.status_label, self.kinect_warning):
                label.configure(wraplength=max(200, event.width - 24))
        self.footer.bind("<Configure>", footer_resized)
        ttk.Label(frame, text="Aplicar reinicia a projeção e zera a água simulada.\n"
                  "Fundo/topo também cortam leituras fora da faixa.\n"
                  "Girar ajusta a orientação; o encaixe exato exige calibração.",
                  wraplength=560).pack(anchor="w", pady=5)
        # O evento é tratado antes do comportamento padrão dos controles para
        # a roda rolar o painel sem mudar alturas ou recortes acidentalmente.
        def bind_scroll(widget):
            for event in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
                widget.bind(event, self.scroll_panel)
            for child in widget.winfo_children():
                bind_scroll(child)
        bind_scroll(body)
        window.bind("<Prior>", lambda event: self.canvas.yview_scroll(-1, "pages"))
        window.bind("<Next>", lambda event: self.canvas.yview_scroll(1, "pages"))
        window.protocol("WM_DELETE_WINDOW", self.close)
        window.after(500, self.watch)
        window.after(200, self.poll_preview)
        window.after(1000, self.watch_kinect)

    def show_kinect_warning(self):
        message = KINECT_MESSAGES.get(self.kinect)
        if message:
            self.kinect_warning.configure(text="⚠ " + message)
            self.kinect_warning.pack(anchor="w", fill="x", pady=(4, 0), before=self.status_label)
        else:
            self.kinect_warning.pack_forget()

    def set_waiting(self, waiting):
        self.waiting_kinect = waiting
        if waiting:
            self.cancel_button.pack(side="left", padx=6)
        else:
            self.cancel_button.pack_forget()

    def cancel_wait(self):
        self.set_waiting(False)
        self.status.set("Espera cancelada. Clique em Aplicar quando quiser abrir a projeção.")

    def own_pids(self):
        return {self.process.pid} if self.process is not None else set()

    def stop_process(self):
        """Pede para o SARndbox fechar e força o encerramento se ele travar (ex.: USB)."""
        process = self.process
        if process is not None and process.poll() is None:
            process.terminate()
            self.window.after(int(STOP_TIMEOUT * 1000),
                              lambda: process.poll() is None and process.kill())

    def watch_kinect(self):
        """Acompanha o USB para avisar da ausência e reabrir quando o Kinect voltar."""
        state = kinect_status()
        if state != self.kinect:
            previous, self.kinect = self.kinect, state
            self.show_kinect_warning()
            if state in KINECT_MESSAGES:
                if self.process is not None and self.process.poll() is None:
                    self.set_waiting(True)
                if self.waiting_kinect:
                    self.status.set(WAITING_KINECT)
            elif state == "ok" and previous in KINECT_MESSAGES and not self.waiting_kinect:
                self.status.set("Kinect detectado. Clique em Aplicar para abrir a projeção.")
        if (self.waiting_kinect and not self.start_scheduled
                and self.kinect not in KINECT_MESSAGES and not kinect_users(self.own_pids())):
            self.start_scheduled = True
            self.status.set("Kinect disponível. Abrindo a projeção…")
            # O dispositivo precisa de alguns instantes após ser enumerado ou liberado.
            self.window.after(2000, self.start_after_kinect)
        self.window.after(1000, self.watch_kinect)

    def start_after_kinect(self):
        self.start_scheduled = False
        if self.waiting_kinect and self.kinect not in KINECT_MESSAGES:
            self.apply(automatic=True)

    def poll_preview(self):
        if not self.applying and self.process is not None and self.process.poll() is None:
            try:
                metrics = Path(str(self.preview_file) + ".json")
                stamp = metrics.stat().st_mtime_ns
                if stamp != self.metrics_stamp:
                    data = json.loads(metrics.read_text())
                    fps = float(data["fps"])
                    if math.isfinite(fps):
                        self.fps_status.set(f"Projeção: {fps:.1f} FPS | Modo: {self.active_performance}")
                    if not data.get("preview_supported", True):
                        self.preview_label.configure(image="", text="Esta GPU não oferece a cópia da prévia.")
                    self.metrics_stamp = stamp
                if self.notebook.select() == str(self.preview_page):
                    stamp = self.preview_file.stat().st_mtime_ns
                    if stamp != self.preview_stamp:
                        photo = tk.PhotoImage(file=str(self.preview_file), format="PPM")
                        self.preview_label.configure(image=photo, text="")
                        self.preview_image = photo
                        self.preview_stamp = stamp
            except (OSError, ValueError, KeyError, tk.TclError):
                pass
            # Independent of projector telemetry: RGB works even without its JSON.
            if self.notebook.select() == str(self.camera_page):
                try:
                    if not self.active_camera:
                        self.camera_label.configure(image="", text="Prévia desativada. Marque Ativar prévia e clique em Aplicar.")
                    else:
                        info = self.camera_file.stat()
                        if time.time() - info.st_mtime > 3:
                            self.camera_label.configure(image="", text="Sem imagem recente da câmera. Confira o Kinect.")
                            self.camera_image = None
                            self.camera_stamp = None
                        elif info.st_mtime_ns != self.camera_stamp:
                            photo = tk.PhotoImage(file=str(self.camera_file), format="PPM")
                            self.camera_label.configure(image=photo, text="")
                            self.camera_image = photo
                            self.camera_stamp = info.st_mtime_ns
                except (OSError, tk.TclError):
                    self.camera_label.configure(image="", text="Aguardando imagem do sensor… Se não aparecer, confira o Kinect.")
                    self.camera_image = None
                    self.camera_stamp = None
        self.window.after(200, self.poll_preview)

    def mark_scan_area(self):
        if (self.camera_image is None or not self.active_camera
                or self.active_camera_mode != "Profundidade (relevo)"):
            self.camera_enabled.set(True)
            self.camera_mode.set("Profundidade (relevo)")
            self.status.set("Clique em Aplicar para abrir a profundidade; depois use Marcar 4 cantos.")
            return
        self.scan_marking = True
        self.scan_points = []
        self.camera_label.points = []
        self.camera_label.editable = True
        self.scan_area_changed([])
        self.camera_label.redraw()

    def scan_area_changed(self, points):
        self.scan_points = [list(p) for p in points]
        names = ("superior esquerdo", "superior direito", "inferior direito", "inferior esquerdo")
        if len(points) < 4:
            self.area_hint.set(f"Clique no canto {len(points)+1}: {names[len(points)]}.")
        else:
            try:
                validate_area(points)
                self.area_hint.set("Área marcada. Arraste os pontos para refinar e clique em Aplicar.")
            except ValueError as error:
                self.area_hint.set(str(error))

    def clear_scan_area(self):
        self.scan_marking = False
        self.scan_points = []
        self.camera_label.points = []
        self.camera_label.redraw()
        self.area_hint.set("Sem limite de captura. Clique em Aplicar para usar.")

    def scroll_panel(self, event):
        if getattr(event, "num", None) == 4:
            steps = -1
        elif getattr(event, "num", None) == 5:
            steps = 1
        elif event.delta:
            steps = -1 if event.delta > 0 else 1
        else:
            return "break"
        self.canvas.yview_scroll(steps * 3, "units")
        return "break"

    def restore(self):
        for key, value in DEFAULTS.items():
            self.variables[key].set(value)
        self.rotation.set(0)
        self.view_size.set(100)
        self.relief.set(True)
        self.contours.set(True)
        self.clear_crop()
        self.performance.set("Resposta rápida")
        self.camera_enabled.set(True)
        self.camera_mode.set("Profundidade (relevo)")
        self.clear_scan_area()
        self.status.set("Valores iniciais restaurados no painel. Clique em Aplicar para usar.")

    def widen_view(self):
        self.view_size.set(75)
        self.clear_crop()
        self.status.set("Tamanho em 75%, sem recortes. Clique em Aplicar e confira os quatro cantos na prévia.")

    def clear_crop(self):
        for variable in self.crop.values():
            variable.set(0)

    def suggest_crop(self):
        self.clear_crop()
        self.crop["esquerda"].set(17)
        self.crop["direita"].set(4)
        self.status.set("Sugestão: 17% à esquerda e 4% à direita. Clique em Aplicar e refine por tentativa.")

    def apply(self, automatic=False):
        if self.applying:
            return
        try:
            values = {k: var.get() for k, var in self.variables.items()}
            validate(values)
            visual = {"rotacao": self.rotation.get(), "relevo": self.relief.get(), "curvas": self.contours.get(), "tamanho": self.view_size.get()}
            visual_tools.rotation_terms(visual["rotacao"])
            if self.scan_marking and len(self.scan_points) != 4:
                raise ValueError("Marque os quatro cantos antes de aplicar, ou escolha Usar toda a captura.")
            validate_area(self.scan_points)
            if self.scan_points:
                # The depth selection defines the boundary; old black bands could hide it.
                self.clear_crop()
            crop = {key: variable.get() for key, variable in self.crop.items()}
            crop_args = visual_tools.crop_options(crop)
            cropped = any(crop.values())
            performance = self.performance.get()
            performance_args = visual_tools.performance_options(performance)
            executable = Path(os.environ.get("SARNDBOX_BIN") or STATE / "native/bin/SARndbox")
            if not CONFIG.is_dir():
                raise ValueError(f"Não encontrei a configuração do SARndbox em {CONFIG}.\n\n"
                                 "Defina SARNDBOX_DIR com a pasta da instalação do SARndbox-2.8 "
                                 "(veja o README).")
            palette = make_palette((CONFIG / "HeightColorMap.cpt").read_text(), values)
            if not executable.is_file():
                raise ValueError(f"Não encontrei o executável do SARndbox em {executable}.\n\n"
                                 "Compile a versão adaptada (veja o README) ou defina SARNDBOX_BIN.")
            STATE.mkdir(exist_ok=True)
            atomic_write(STATE / "HeightColorMap.cpt", palette)
            if self.scan_points:
                atomic_write(STATE / "area_scan.txt", "\n".join(" ".join(f"{v:.12g}" for v in p) for p in self.scan_points)+"\n")
            output = external_output()
            view_options, self.mode = visual_tools.orientation_options(CONFIG, STATE, visual, output)
            atomic_write(STATE / "valores.json", json.dumps({**values, **visual, "recorte": crop, "desempenho": performance, "camera": self.camera_enabled.get(), "camera_modo": self.camera_mode.get(), "area_scan": self.scan_points}, indent=2) + "\n")
        except (OSError, ValueError, tk.TclError) as error:
            messagebox.showerror("Confira os valores", str(error))
            return
        if self.kinect in KINECT_MESSAGES:
            self.set_waiting(True)
            self.stop_process()
            self.status.set(WAITING_KINECT)
            return
        users = kinect_users(self.own_pids())
        if users:
            names = ", ".join(sorted(set(users.values())))
            if not automatic:
                if not messagebox.askyesno("Kinect em uso", f"{names} está usando o Kinect.\n\n"
                                           "Fechar e abrir a projeção?"):
                    self.status.set(f"O Kinect está sendo usado por {names}. Feche-o e clique em Aplicar.")
                    return
                for pid in users:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except OSError:
                        pass
            self.set_waiting(True)
            self.status.set(f"Aguardando {names} liberar o Kinect… a projeção abre sozinha em seguida.")
            return
        self.set_waiting(False)
        command = [str(executable), "-s", "100", "-uhm",
                   str(STATE / "HeightColorMap.cpt"), "-er", str(values["fundo"]), str(values["topo"])]
        command += visual_tools.appearance_options(visual) + view_options
        self.active_performance = performance
        command += performance_args
        command += ["-panelPreview", str(self.preview_file), "-previewRate", "5"]
        if self.scan_points:
            command += ["-scanArea", str(STATE / "area_scan.txt"), "-scanView", str(visual["rotacao"]), str(visual["tamanho"])]
            self.mode += " Área de profundidade limitada aos quatro cantos."
        self.active_camera = self.camera_enabled.get()
        self.active_camera_mode = self.camera_mode.get()
        self.camera_label.editable = self.active_camera_mode == "Profundidade (relevo)"
        self.scan_marking = False
        if self.active_camera:
            command += ["-cameraDepthPreview" if self.camera_mode.get() == "Profundidade (relevo)" else "-cameraPreview", str(self.camera_file)]
        if cropped:
            command += crop_args
        if output:
            command += ["-rootSection", "Desktop", "-setConfig", f"Window/outputName={output}",
                        "-setConfig", "Window/windowFullscreen=true"]
        else:
            self.mode += " Leve a janela ao projetor e pressione F11."
        self.applying = True
        self.apply_button.state(["disabled"])
        self.status.set("Abrindo a projeção com os novos valores…")
        self.stop_process()
        self.window.after(100, lambda: self.start_when_stopped(command))

    def start_when_stopped(self, command):
        if self.process is not None and self.process.poll() is None:
            self.window.after(100, lambda: self.start_when_stopped(command))
            return
        if self.log:
            self.log.close()
        try:
            for path in (self.preview_file, Path(str(self.preview_file) + ".json"), self.camera_file):
                path.unlink(missing_ok=True)
            self.preview_stamp = None
            self.metrics_stamp = None
            self.preview_label.configure(image="", text="Aguardando imagem do projetor…")
            self.preview_image = None
            self.camera_stamp = None
            self.camera_image = None
            self.camera_label.configure(image="", text="Aguardando imagem do sensor…" if self.active_camera else "Câmera desativada.")
            self.fps_status.set("Projeção: medindo FPS…")
            self.log = (STATE / "sarndbox.log").open("w")
            self.process = subprocess.Popen(command, cwd=SANDBOX, stdout=self.log, stderr=subprocess.STDOUT)
            self.status.set(self.mode)
        except OSError as error:
            self.status.set(f"Não foi possível abrir a projeção: {error}")
        finally:
            self.applying = False
            self.apply_button.state(["!disabled"])

    def watch(self):
        if not self.applying and self.process is not None and self.process.poll() is not None:
            code = self.process.returncode
            self.process = None
            self.fps_status.set("Projeção encerrada")
            self.camera_label.configure(image="", text="Câmera encerrada. Clique em Aplicar para abrir novamente.")
            self.camera_image = None
            self.camera_stamp = None
            self.preview_label.configure(image="", text="Projeção encerrada. Clique em Aplicar para abrir novamente.")
            self.preview_image = None
            if self.log:
                self.log.close()
                self.log = None
            if code:
                try:
                    details = (STATE / "sarndbox.log").read_text(errors="replace")
                except OSError:
                    details = ""
                # Só espera se o USB confirmar a ausência; senão tentaria reabrir sem parar.
                if kinect_missing(details) and self.kinect in KINECT_MESSAGES:
                    self.set_waiting(True)
                self.status.set(WAITING_KINECT if self.waiting_kinect else explain_failure(details))
            else:
                self.status.set("Projeção fechada. Seus últimos ajustes ficaram salvos.")
        self.window.after(500, self.watch)

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.log:
            self.log.close()
        for timer in self.window.tk.call("after", "info"):
            self.window.after_cancel(timer)
        self.window.destroy()


if __name__ == "__main__":
    import sys
    window = tk.Tk()
    panel = Panel(window)
    if "--abrir" in sys.argv or "--camera" in sys.argv:
        panel.notebook.select(panel.camera_page if "--camera" in sys.argv else panel.preview_page)
        window.after(300, panel.apply)
    window.mainloop()
