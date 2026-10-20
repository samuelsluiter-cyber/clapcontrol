"""Casual Butler Briefing for Samuel Sluiter."""
import re
import datetime
import subprocess
import shutil
from pathlib import Path

VAULT_DIR = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Second Brain"
TODOS_FILE = VAULT_DIR / "Planung/Todos.md"
FOKUS_FILE = VAULT_DIR / "Leben/Tagesfokus.md"

def get_casual_briefing() -> str:
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour

    if 5 <= hour < 12:
        greeting = "Guten Morgen Samuel!"
    elif 12 <= hour < 18:
        greeting = "Hey Samuel!"
    else:
        greeting = "Guten Abend Samuel!"

    tasks = []
    
    # 1. Try reading from Tagesfokus
    if FOKUS_FILE.exists():
        try:
            content = FOKUS_FILE.read_text(encoding="utf-8")
            # Look for today or most recent section
            sections = re.split(r"^##\s+(\d{4}-\d{2}-\d{2})", content, flags=re.MULTILINE)
            if len(sections) >= 3:
                # sections[1] is date, sections[2] is body
                body = sections[2]
                for line in body.splitlines():
                    line = line.strip()
                    if line.startswith("- [ ]"):
                        # Clean task
                        clean_t = re.sub(r"^-\s*\[\s*\]\s*", "", line)
                        clean_t = re.sub(r"\(.*?\)", "", clean_t)  # strip time parentheses
                        clean_t = clean_t.replace("⭐", "").strip()
                        if clean_t and len(clean_t) > 3:
                            tasks.append(clean_t)
        except Exception:
            pass

    # 2. Try reading from Todos.md if needed
    if not tasks and TODOS_FILE.exists():
        try:
            t_content = TODOS_FILE.read_text(encoding="utf-8")
            # Look for "Heute" or tasks with today's date
            for m in re.finditer(r"-\s*\[\s*\]\s*(.*?)(?:📅|\s*🆔|$)", t_content):
                t_str = m.group(1).strip()
                if t_str and len(t_str) > 3 and not t_str.startswith("~~"):
                    tasks.append(t_str)
                    if len(tasks) >= 3:
                        break
        except Exception:
            pass

    # Assemble speech text
    if not tasks:
        speech = f"{greeting} Dein Kalender sieht heute komplett entspannt aus. Keine drängenden Termine. Perfekte Zeit zum Coden!"
    else:
        top_tasks = tasks[:3]
        if len(top_tasks) == 1:
            speech = f"{greeting} Dein Hauptding für heute: {top_tasks[0]}. Das packst du locker!"
        else:
            joined = " Zweitens: ".join(top_tasks)
            speech = f"{greeting} Hier ist dein kurzer Check für heute: Erstens: {top_tasks[0]}. Zweitens: {top_tasks[1]}."
            if len(top_tasks) > 2:
                speech += f" Und außerdem: {top_tasks[2]}."

    return speech

def speak_briefing():
    text = get_casual_briefing()
    # Find best German voice
    voice = "Anna"
    try:
        # Check if Anna exists
        check = subprocess.run(["say", "-v", "Anna", "."], capture_output=True)
        if check.returncode != 0:
            voice = ""
    except Exception:
        voice = ""

    cmd = ["say"]
    if voice:
        cmd.extend(["-v", voice])
    cmd.append(text)

    try:
        subprocess.run(cmd, capture_output=True, timeout=15)
    except Exception:
        pass

if __name__ == "__main__":
    print("Briefing Text:", get_casual_briefing())
    speak_briefing()
