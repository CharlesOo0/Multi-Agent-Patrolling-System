from __future__ import annotations

from typing import Optional, Callable, Dict, Any, List
import pygame
import numpy as np
import csv
from datetime import datetime

from ui.components.button import Button
from ui.components.utils import viz_utils
from ui.routes.base import Page
import json
import os
import sys
import subprocess
import socket
import shutil
import webbrowser


class StatsPage(Page):
    """Simulation statistics display page with graphs.

    Expected: receive a 'results' dictionary via set_results() containing
    - 'algorithm_name': str
    - 'steps': int
    - 'average_idleness_history': List[float]
    - 'event_count': int
    - 'map_shape': tuple[int, int]
    """

    def __init__(self, go_home: Callable[[], None], go_sim: Callable[[], None]):
        self.utils = viz_utils()
        self.go_home = go_home
        self.go_sim = go_sim
        self.font = pygame.font.SysFont(None, 38)
        self.small = pygame.font.SysFont(None, 24)
        self._btn_home: Button | None = None
        self._btn_rerun: Button | None = None
        self._btn_export: Button | None = None
        self._streamlit_process = None
        self._ready = False
        self.results: Dict[str, Any] | None = None

    def set_results(self, results: Dict[str, Any]) -> None:
        self.results = results

    def on_enter(self, prev: Optional[str] = None) -> None:
        self._ready = False

    def on_exit(self, next: Optional[str] = None) -> None:
        pass

    def _export_to_json(self) -> None:

        if not self.results:
            return
        # Save exports into project `src/streamlit/saves` directory so
        # the Streamlit app can load them directly.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       
        algo_name = str(self.results.get("algorithm_name", "unknown")).lower().replace(" ", "_")
        filename = f"{algo_name}_{timestamp}_stats.json"

        export_data = {
            "general_information": {
                "algorithm": self.results.get("algorithm_name", "?"),
                "steps": self.results.get("steps", 0),
                "events": self.results.get("event_count", 0),
                "map_shape": self.results.get("map_shape", (0, 0)),
            },
            "average_idleness_history": self.results.get("average_idleness_history", [])
            or [],
            "maximum_idleness_history": self.results.get("maximum_idleness_history", [])
            or [],
            "total_coverage_history": self.results.get("total_coverage_history", [])
            or [],
            "coverage_by_agent_history": self.results.get(
                "coverage_by_agent_history", []
            )
            or [],
            "agentswork_history": self.results.get("agentswork_history", []) or [],
        }

        # Compute project root and target saves directory
        proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        saves_dir = os.path.join(proj, "src", "streamlit", "saves")
        try:
            os.makedirs(saves_dir, exist_ok=True)
        except Exception:
            # fallback to current dir if mkdir fails for some reason
            saves_dir = os.path.abspath(os.path.join(os.getcwd()))

        filepath = os.path.join(saves_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            print(f"Statistics exported to {filepath}")
        except Exception as e:
            # last-resort: write to cwd
            try:
                with open(filename, "w", encoding="utf-8") as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                print(f"Statistics exported to {filename} (fallback). Error: {e}")
            except Exception:
                print("Failed to export statistics:", e)

    def _open_in_browser(self, url) -> None:
        """ Open URL in Google Chrome if available, else default browser. """
        chrome_bins = []
        try:
            c = shutil.which("chrome")
            if c:
                chrome_bins.append(c)
            c2 = shutil.which("chrome.exe")
            if c2 and c2 not in chrome_bins:
                chrome_bins.append(c2)
        except Exception:
            pass

        if os.name == "nt":
            pf = os.environ.get("ProgramFiles", r"C:\Program Files")
            pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
            for pth in [
                os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            ]:
                if os.path.exists(pth) and pth not in chrome_bins:
                    chrome_bins.append(pth)

        opened = False
        for ch in chrome_bins:
            try:
                subprocess.Popen(
                    [ch, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                opened = True
                break
            except Exception:
                continue

        if not opened:
            try:
                webbrowser.open(url)
            except Exception:
                pass

    def _launch_streamlit(self, port = 8501) -> None:
        """Launch Streamlit UI:

        - Do nothing if a Streamlit process started by this instance is already running
        - Ensure Streamlit is available in the project venv (if present), else fall back to current Python
        - Write minimal ~/.streamlit configs to bypass email + disable usage stats
        - If port 8501 is used, kill the process using it
        - Start Streamlit on port 8501 and open it in Google Chrome (fallback to default web browser)
        - Additionally: send empty input to stdin to bypass any email prompt
        """
        url = f"http://localhost:{port}"

        self._export_to_json()

        # 1) If we already started a Streamlit process and it's still alive then reopening the UI
        try:
            if getattr(self, "_streamlit_process", None) is not None and self._streamlit_process.poll() is None:
                print("Streamlit already running")
                self._open_in_browser(url)
                return
        except Exception:
            self._streamlit_process = None

        # 2) Locate the Streamlit script
        base = os.path.dirname(__file__)
        candidate_paths = [
            os.path.abspath(os.path.join(base, "..", "..", "..", "streamlit", "stats.py")),
            os.path.abspath(os.path.join(base, "..", "..", "..", "..", "streamlit", "stats.py")),
        ]

        script: Optional[str] = None
        for cand in candidate_paths:
            if os.path.exists(cand):
                script = cand
                break

        if script is None:
            print("streamlit script not found")
            return

        # 3) Prefer project venv's Python if available
        proj = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        p_venv = os.path.join(proj, "venv", "Scripts", "python.exe")
        p_alt = os.path.join(proj, ".venv", "Scripts", "python.exe")

        py = sys.executable
        if os.path.exists(p_venv):
            py = p_venv
        elif os.path.exists(p_alt):
            py = p_alt

        # 4) Check that Streamlit is importable in that Python
        try:
            ok = subprocess.run(
                [py, "-c", "import streamlit"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if ok.returncode != 0:
                print("streamlit not installed for", py)
                return
        except Exception:
            print("failed to check streamlit")
            return

        # 5) Write minimal Streamlit config to bypass email + usage stats
        try:
            cfg_dir = os.path.join(os.path.expanduser("~"), ".streamlit")
            os.makedirs(cfg_dir, exist_ok=True)

            with open(os.path.join(cfg_dir, "credentials.toml"), "w", encoding="utf-8") as f:
                f.write('email = ""\n')

            with open(os.path.join(cfg_dir, "config.toml"), "w", encoding="utf-8") as f:
                f.write("[browser]\n")
                f.write("gatherUsageStats = false\n")
        except Exception:
            # Non-fatal
            pass

        # 6) Port handling
        def port_used(p: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(0.3)
                    s.connect(("127.0.0.1", p))
                    return True
                except Exception:
                    return False

        def kill_port(p: int) -> None:
            out = subprocess.check_output(["netstat", "-ano"], encoding="utf-8", errors="ignore")
            for line in out.splitlines():
                if f":{p} " in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

        if port_used(port):
            kill_port(port)

        # 7) Launch Streamlit (with PIPE stdin so we can send an empty line)
        log = open("streamlit_run.log", "a", encoding="utf-8")
        cmd = [
            py,
            "-m",
            "streamlit",
            "run",
            script,
            "--server.headless", "true",
            "--server.port", str(port),
        ]

        try:
            self._streamlit_process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                stdin=subprocess.PIPE,   # <<< changed from DEVNULL
            )
        except Exception as e:
            print("failed to launch streamlit:", e)
            try:
                log.close()
            except Exception:
                pass
            return

        # 7bis) Send empty "email" + Enter to stdin to bypass prompt (if any)
        try:
            if self._streamlit_process.stdin:
                # One or two newlines, in case Streamlit asks more than once
                self._streamlit_process.stdin.write(b"\n\n")
                self._streamlit_process.stdin.flush()
        except Exception:
            # If this fails, Streamlit will still run; worst case prompt remains
            pass

        # 8) Open in browser
        self._open_in_browser(url)

        print(f"Streamlit launched on {url}")

    def _ensure_ui(self, screen: pygame.Surface) -> None:
        if self._ready:
            return
        w, h = screen.get_size()
        bw, bh, gap = 160, 46, 12
        self._btn_home = Button(
            20, 20, 160, 46, "Accueil", self.utils.GRAY, self.utils.LIGHT_GRAY
        )
        self._btn_rerun = Button(
            20 + 160 + gap,
            20,
            bw,
            bh,
            "Relancer",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self._btn_export = Button(
            20 + 2 * (160 + gap),
            20,
            bw,
            bh,
            "Streamlit",
            self.utils.GRAY,
            self.utils.LIGHT_GRAY,
        )
        self._ready = True

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in (self._btn_home, self._btn_rerun, self._btn_export):
            if b:
                b.hover_property(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self._btn_home and self._btn_home.is_clicked(pos, event):
                self.go_home()
            if self._btn_rerun and self._btn_rerun.is_clicked(pos, event):
                self.go_sim()
            if self._btn_export and self._btn_export.is_clicked(pos, event):
                self._launch_streamlit()

    def update(self, dt: float) -> None:
        pass

    # --- Simple graph helpers (pygame-based) ---
    def _draw_axes(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, self.utils.BLACK, rect, 1)
        # Axes
        pygame.draw.line(
            surface,
            self.utils.BLACK,
            (rect.left + 40, rect.bottom - 30),
            (rect.right - 10, rect.bottom - 30),
            2,
        )
        pygame.draw.line(
            surface,
            self.utils.BLACK,
            (rect.left + 40, rect.top + 10),
            (rect.left + 40, rect.bottom - 30),
            2,
        )

    def _plot_line(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: List[float],
        color=(30, 144, 255),
    ) -> None:
        if not data:
            return
        vals = np.array(data, dtype=float)
        if len(vals) == 1:
            vals = np.concatenate([vals, vals])
        ymin, ymax = float(np.min(vals)), float(np.max(vals))
        if ymax - ymin < 1e-9:
            ymax = ymin + 1.0
        xs = np.linspace(rect.left + 50, rect.right - 14, num=len(vals))
        ys = rect.bottom - 30 - (vals - ymin) / (ymax - ymin) * (rect.height - 50)
        points = list(zip(xs.astype(int), ys.astype(int)))
        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, 2)

    def _plot_bars(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        bars: List[float],
        color=(100, 149, 237),
    ) -> None:
        if not bars:
            return
        n = len(bars)
        vals = np.array(bars, dtype=float)
        ymax = float(np.max(vals)) if np.max(vals) > 0 else 1.0
        # Compute bar geometry
        gap = 8
        available_w = rect.width - 60 - gap * (n + 1)
        bw = max(10, available_w // max(1, n))
        x = rect.left + 50 + gap
        base_y = rect.bottom - 30
        for v in vals:
            h = int((v / ymax) * (rect.height - 50))
            pygame.draw.rect(surface, color, (x, base_y - h, bw, h))
            x += bw + gap

    def render(self, screen: pygame.Surface) -> None:
        self._ensure_ui(screen)
        screen.fill(self.utils.WHITE)

        title = self.font.render(
            "Simulation Statistic", True, self.utils.BLACK
        )
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 20))

        # Boutons
        if self._btn_home:
            self._btn_home.draw(screen)
        if self._btn_rerun:
            self._btn_rerun.draw(screen)
        if self._btn_export:
            self._btn_export.draw(screen)

        if not self.results:
            msg = self.small.render(
                "No simulation data", True, self.utils.BLACK
            )
            screen.blit(msg, (50, 100))
            return

        # Informations générales
        algo = str(self.results.get("algorithm_name", "?"))
        steps = int(self.results.get("steps", 0))
        events = int(self.results.get("event_count", 0))
        map_shape = self.results.get("map_shape", (0, 0))

        info_y = 90
        info_lines = [
            f"Algorithm: {algo}",
            f"Steps done: {steps}",
            f"Events: {events}",
            f"Map Size: {map_shape}",
        ]
        for i, line in enumerate(info_lines):
            txt = self.small.render(line, True, self.utils.BLACK)
            screen.blit(txt, (50, info_y + i * 22))

        # Graph 1 : average idleness across history
        avg = self.results.get("average_idleness_history", []) or []
        g1_rect = pygame.Rect(50, 250, (screen.get_width() - 100) / 2, 180)
        self._draw_axes(screen, g1_rect)
        self._plot_line(screen, g1_rect, avg)
        # labels
        x_lbl = self.small.render("Steps done", True, self.utils.BLACK)
        screen.blit(
            x_lbl,
            (
                g1_rect.left + g1_rect.width // 2 - x_lbl.get_width() // 2,
                g1_rect.bottom - 18,
            ),
        )
        y_lbl_surf = self.small.render("Value", True, self.utils.BLACK)
        y_lbl = pygame.transform.rotate(y_lbl_surf, 90)
        screen.blit(
            y_lbl,
            (
                g1_rect.left + 8,
                g1_rect.top + g1_rect.height // 2 - y_lbl.get_height() // 2,
            ),
        )
        last_avg = f"{avg[-1]:.2f}" if avg else "n/a"
        g1_label = self.small.render(
            f"Average Idleness: {last_avg} points", True, self.utils.BLACK
        )
        screen.blit(g1_label, (g1_rect.left, g1_rect.top - 20))

        # Graph 2: Max idlness in history
        max_hist = self.results.get("maximum_idleness_history", []) or []
        g2_rect = pygame.Rect(
            50 + (screen.get_width() - 100) / 2,
            250,
            (screen.get_width() - 100) / 2,
            180,
        )
        self._draw_axes(screen, g2_rect)
        # use a different color for the max line
        self._plot_line(screen, g2_rect, max_hist, color=(220, 20, 60))
        # labels
        x_lbl2 = self.small.render("Steps done", True, self.utils.BLACK)
        screen.blit(
            x_lbl2,
            (
                g2_rect.left + g2_rect.width // 2 - x_lbl2.get_width() // 2,
                g2_rect.bottom - 18,
            ),
        )
        y_lbl2_surf = self.small.render("Value", True, self.utils.BLACK)
        y_lbl2 = pygame.transform.rotate(y_lbl2_surf, 90)
        screen.blit(
            y_lbl2,
            (
                g2_rect.left + 8,
                g2_rect.top + g2_rect.height // 2 - y_lbl2.get_height() // 2,
            ),
        )
        last_max = f"{max_hist[-1]:.2f}" if max_hist else "n/a"
        g2_label = self.small.render(
            f"Max Idleness: {last_max} points", True, self.utils.BLACK
        )
        screen.blit(g2_label, (g2_rect.left, g2_rect.top - 20))

        #Graph 3: total coverage in history
        total_cov = self.results.get("total_coverage_history", []) or []
        g3_rect = pygame.Rect(
            50, g2_rect.bottom + 50, (screen.get_width() - 100) / 2, 180
        )
        self._draw_axes(screen, g3_rect)
        # use a different color for the total coverage line
        self._plot_line(screen, g3_rect, total_cov, color=(220, 20, 60))
        # labels
        x_lbl3 = self.small.render("Steps done", True, self.utils.BLACK)
        screen.blit(
            x_lbl3,
            (
                g3_rect.left + g3_rect.width // 2 - x_lbl3.get_width() // 2,
                g3_rect.bottom - 18,
            ),
        )
        y_lbl3_surf = self.small.render("Coverage", True, self.utils.BLACK)
        y_lbl3 = pygame.transform.rotate(y_lbl3_surf, 90)
        screen.blit(
            y_lbl3,
            (
                g3_rect.left + 8,
                g3_rect.top + g3_rect.height // 2 - y_lbl3.get_height() // 2,
            ),
        )
        last_total = f"{total_cov[-1]:.2f}" if total_cov else "n/a"
        g3_label = self.small.render(
            f"Total coverage: {last_total}", True, self.utils.BLACK
        )
        screen.blit(g3_label, (g3_rect.left, g3_rect.top - 20))

        # Graph 4: Coverage per agent in history
        cov_hist = self.results.get("coverage_by_agent_history", []) or []
        g4_rect = pygame.Rect(
            50 + (screen.get_width() - 100) / 2,
            g2_rect.bottom + 50,
            (screen.get_width() - 100) / 2,
            180,
        )
        g4_label = self.small.render("Coverage by agent", True, self.utils.BLACK)
        screen.blit(g4_label, (g4_rect.left, g4_rect.top - 20))
        self._draw_axes(screen, g4_rect)
        # labels
        x_lbl4 = self.small.render("Steps done", True, self.utils.BLACK)
        screen.blit(
            x_lbl4,
            (
                g4_rect.left + g4_rect.width // 2 - x_lbl4.get_width() // 2,
                g4_rect.bottom - 18,
            ),
        )
        y_lbl4_surf = self.small.render("Coverage", True, self.utils.BLACK)
        y_lbl4 = pygame.transform.rotate(y_lbl4_surf, 90)
        screen.blit(
            y_lbl4,
            (
                g4_rect.left + 8,
                g4_rect.top + g4_rect.height // 2 - y_lbl4.get_height() // 2,
            ),
        )
        # Palette of colors to cycle through for each agent
        palette = [
            (30, 144, 255),  # dodger blue
            (220, 20, 60),  # crimson
            (34, 139, 34),  # forest green
            (255, 140, 0),  # dark orange
            (148, 0, 211),  # dark violet
            (255, 105, 180),  # hot pink
            (70, 130, 180),  # steel blue
        ]
        for i, agent_hist in enumerate(cov_hist):
            color = palette[i % len(palette)]
            self._plot_line(screen, g4_rect, agent_hist or [], color=color)
            # draw a small legend for each agent above the graph
