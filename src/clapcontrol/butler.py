"""Casual Butler Briefing for Samuel Sluiter."""
import re
import datetime
import subprocess
from pathlib import Path

VAULT_DIR = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Second Brain"
TODOS_FILE = VAULT_DIR / "Planung/Todos.md"
FOKUS_FILE = VAULT_DIR / "Leben/Tagesfokus.md"

def clean_task_text(text: str) -> str:
    # Remove markdown formatting, IDs, tags, and unicode math subscripts
    t = re.sub(r"^-\s*\[\s*\]\s*", "", text)
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"\[\[(.*?)\]\]", r"\1", t)
    t = t.replace("⭐", "").replace("🔥", "").replace("📅", "").replace("🆔", "")
    t = re.sub(r"[₀₁₂₃₄₅₆₇₈₉]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def get_casual_briefing() -> str:
    now = datetime.datetime.now()
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
            sections = re.split(r"^##\s+(\d{4}-\d{2}-\d{2})", content, flags=re.MULTILINE)
            if len(sections) >= 3:
                body = sections[2]
                for line in body.splitlines():
                    line = line.strip()
                    if line.startswith("- [ ]"):
                        clean_t = clean_task_text(line)
                        if clean_t and len(clean_t) > 3:
                            tasks.append(clean_t)
        except Exception:
            pass

    # 2. Try reading from Todos.md if needed
    if not tasks and TODOS_FILE.exists():
        try:
            t_content = TODOS_FILE.read_text(encoding="utf-8")
            for m in re.finditer(r"-\s*\[\s*\]\s*(.*?)(?:📅|\s*🆔|$)", t_content):
                t_str = clean_task_text(m.group(1))
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
            speech = f"{greeting} Hier ist dein kurzer Check für heute: Erstens: {top_tasks[0]}. Zweitens: {top_tasks[1]}."
            if len(top_tasks) > 2:
                speech += f" Und außerdem: {top_tasks[2]}."

    return speech

def speak_briefing():
    text = get_casual_briefing()
    # Try Anna voice directly, fallback to default system voice
    cmd = ["say", "-v", "Anna", text]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=20)
        if res.returncode != 0:
            # Fallback without -v Anna
            subprocess.run(["say", text], capture_output=True, timeout=20)
    except Exception:
        try:
            subprocess.run(["say", text], capture_output=True, timeout=20)
        except Exception:
            pass

if __name__ == "__main__":
    print("Briefing Text:", get_casual_briefing())
    speak_briefing()
