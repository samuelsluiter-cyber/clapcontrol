"""ClapControl configuration management."""
from pathlib import Path
import yaml

DEFAULT_CONFIG = {
    "audio": {
        "device_index": None,       # None = default input device
        "sample_rate": 44100,
        "chunk_size": 1024,
        "sensitivity": 70,          # 1 to 100
        "smart_sleep_wake": True,   # 2x Klatschen = Schlaf, 1x Klatschen wenn dunkel = Aufwachen + Butler!
        "noise_floor_decay": 0.95,
        "min_clap_interval": 0.15,  # seconds between claps
        "max_clap_interval": 0.75,  # max seconds to wait for next clap
        "pattern_timeout": 0.40,    # wait after 2nd clap to see if 3rd arrives
        "cooldown": 1.5             # cooldown after action execution
    },
    "actions": {
        "double_clap": "display_sleep",               # 2x Klatschen: Display Ruhemodus
        "single_clap_when_sleeping": "wake_and_butler", # 1x Klatschen im Ruhezustand: Aufwachen + Butler Briefing!
        "triple_clap": "butler_briefing",             # 3x Klatschen: Butler Briefing jederzeit
        "custom_double_command": "",
        "custom_triple_command": ""
    },
    "feedback": {
        "audio_feedback": True,     # play a gentle click/tick when recognized
        "feedback_sound": "/System/Library/Sounds/Tink.aiff"
    }
}

CONFIG_DIR = Path.home() / ".config" / "clapcontrol"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
            cfg = DEFAULT_CONFIG.copy()
            for k, v in user_cfg.items():
                if isinstance(v, dict) and k in cfg:
                    cfg[k].update(v)
                else:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
