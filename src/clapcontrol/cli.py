"""ClapControl Command Line Interface & Runner."""
import sys
import time
import argparse
import threading
import sounddevice as sd
import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import load_config, save_config, CONFIG_FILE
from .detector import ClapDetector
from .pattern import PatternRecognizer
from .actions import execute_action
from .web import run_web_server

console = Console()

def list_devices():
    """Lists all available input audio devices."""
    table = Table(title="🎤 Verfügbare Audio-Eingabegeräte")
    table.add_column("Index", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Kanäle", justify="right")
    table.add_column("Standard", justify="center")

    default_idx = sd.default.device[0]
    devices = sd.query_devices()
    for idx, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            is_def = "★" if idx == default_idx else ""
            table.add_row(str(idx), d['name'], str(d['max_input_channels']), is_def)

    console.print(table)

def run_calibrate():
    """Live acoustic gauge to tune clap sensitivity in real-time."""
    cfg = load_config()
    sr = cfg["audio"]["sample_rate"]
    chunk_size = cfg["audio"]["chunk_size"]
    dev_idx = cfg["audio"]["device_index"]
    detector = ClapDetector(sample_rate=sr, sensitivity=cfg["audio"]["sensitivity"])

    console.print(Panel.fit(
        f"[bold cyan]👏 ClapControl – Live Akustik-Kalibrierung[/bold cyan]\n"
        f"Sensitivität: [green]{detector.sensitivity}%[/green] (Threshold: {detector.peak_threshold:.3f})\n"
        f"[dim]Klatsche jetzt in die Hände oder sprich normal. Drücke Ctrl+C zum Beenden.[/dim]",
        border_style="cyan"
    ))

    def audio_callback(indata, frames, time_info, status):
        is_clap, peak, crest = detector.process_chunk(indata)
        
        # Build ASCII meter
        bar_len = 35
        fill = int(min(1.0, peak / 0.6) * bar_len)
        meter = "█" * fill + "░" * (bar_len - fill)
        thresh_pos = int(min(1.0, detector.peak_threshold / 0.6) * bar_len)

        if is_clap:
            console.print(f"\r[bold green]💥 KLATSCHEN ERKANNT! [/bold green] Pegel: {peak:.3f} | Crest: {crest:.1f} | [{meter}]")
        else:
            # Overwrite line dynamically
            status_color = "yellow" if peak > detector.peak_threshold * 0.7 else "dim"
            sys.stdout.write(f"\rPegel: [{status_color}]{meter}[/{status_color}] ({peak:.3f}) Threshold: {detector.peak_threshold:.3f}   ")
            sys.stdout.flush()

    try:
        with sd.InputStream(device=dev_idx, channels=1, samplerate=sr, blocksize=chunk_size, callback=audio_callback):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[green]Kalibrierung beendet.[/green]")

def run_daemon(web: bool = False, web_port: int = 49152):
    """Main daemon: listens for claps and triggers actions."""
    cfg = load_config()
    sr = cfg["audio"]["sample_rate"]
    chunk_size = cfg["audio"]["chunk_size"]
    dev_idx = cfg["audio"]["device_index"]

    detector = ClapDetector(sample_rate=sr, sensitivity=cfg["audio"]["sensitivity"])

    def on_double():
        action = cfg["actions"]["double_clap"]
        console.print(f"[bold green]👏 2× Klatschen erkannt![/bold green] Führe Aktion aus: [cyan]{action}[/cyan]")
        execute_action(
            action,
            custom_cmd=cfg["actions"].get("custom_double_command", ""),
            feedback=cfg["feedback"]["audio_feedback"],
            sound_path=cfg["feedback"]["feedback_sound"]
        )

    def on_triple():
        action = cfg["actions"]["triple_clap"]
        console.print(f"[bold magenta]👏👏 3× Klatschen erkannt![/bold magenta] Führe Aktion aus: [cyan]{action}[/cyan]")
        execute_action(
            action,
            custom_cmd=cfg["actions"].get("custom_triple_command", ""),
            feedback=cfg["feedback"]["audio_feedback"],
            sound_path=cfg["feedback"]["feedback_sound"]
        )

    pattern = PatternRecognizer(
        on_double_clap=on_double,
        on_triple_clap=on_triple,
        min_interval=cfg["audio"]["min_clap_interval"],
        max_interval=cfg["audio"]["max_clap_interval"],
        pattern_timeout=cfg["audio"]["pattern_timeout"],
        cooldown=cfg["audio"]["cooldown"]
    )

    console.print(Panel.fit(
        f"[bold green]👏 ClapControl Daemon gestartet[/bold green]\n"
        f"• 2× Klatschen ➔ [cyan]{cfg['actions']['double_clap']}[/cyan]\n"
        f"• 3× Klatschen ➔ [cyan]{cfg['actions']['triple_clap']}[/cyan]\n"
        f"• Empfindlichkeit: [yellow]{cfg['audio']['sensitivity']}%[/yellow]\n"
        f"• Konfigurationsdatei: [dim]{CONFIG_FILE}[/dim]",
        border_style="green"
    ))

    if web:
        console.print(f"🌐 Web Dashboard aktiv auf: [bold underline cyan]http://localhost:{web_port}[/bold underline cyan]")
        threading.Thread(target=run_web_server, args=(web_port,), daemon=True).start()

    def audio_callback(indata, frames, time_info, status):
        is_clap, peak, crest = detector.process_chunk(indata)
        if is_clap:
            pattern.record_clap()

    try:
        with sd.InputStream(device=dev_idx, channels=1, samplerate=sr, blocksize=chunk_size, callback=audio_callback):
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[yellow]ClapControl beendet.[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="👏 ClapControl – Steuere deinen Mac per Klatschen")
    subparsers = parser.add_subparsers(dest="command")

    # Start
    start_parser = subparsers.add_parser("start", help="Startet den ClapControl Daemon")
    start_parser.add_argument("--web", action="store_true", help="Startet das Web-Dashboard parallel")
    start_parser.add_argument("--port", type=int, default=49152, help="Port für das Web-Dashboard")

    # Calibrate
    subparsers.add_parser("calibrate", help="Öffnet das interaktive Akustik-Messgerät im Terminal")

    # Devices
    subparsers.add_parser("devices", help="Listet alle verfügbaren Mikrofone auf")

    # Test actions
    test_parser = subparsers.add_parser("test", help="Testet Aktionen ohne Klatschen")
    test_parser.add_argument("action", choices=["double", "triple", "mute"], help="Welche Aktion getestet werden soll")

    args = parser.parse_args()

    if args.command == "devices":
        list_devices()
    elif args.command == "calibrate":
        run_calibrate()
    elif args.command == "test":
        cfg = load_config()
        if args.action == "double":
            execute_action(cfg["actions"]["double_clap"])
        elif args.action == "triple":
            execute_action(cfg["actions"]["triple_clap"])
        elif args.action == "mute":
            execute_action("volume_mute")
        console.print(f"[green]Aktion '{args.action}' ausgeführt.[/green]")
    else:
        # Default is start
        run_daemon(web=getattr(args, "web", False), web_port=getattr(args, "port", 49152))

if __name__ == "__main__":
    main()
