# 👏 ClapControl

> **Control your Mac & PC with hand claps.**  
> Ultra-lightweight background daemon with transient acoustic filtering and zero cloud footprint.

[![macOS](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-blue?style=flat-square&logo=apple)](https://github.com/samuelsluiter-cyber/clapcontrol)
[![Python](https://img.shields.io/badge/Python-3.11+-brightgreen?style=flat-square&logo=python)](https://github.com/samuelsluiter-cyber/clapcontrol)
[![Zero Cloud](https://img.shields.io/badge/Privacy-100%25%20Local-success?style=flat-square)](https://github.com/samuelsluiter-cyber/clapcontrol)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)

---

## ⚡ What is ClapControl?

Have you ever been cooking, lying in bed, or sitting on the couch while music is playing, and your hands were full?

**ClapControl** listens in the background using minimal CPU (`<0.2%` on Apple Silicon) and triggers system actions when you clap your hands:

* 👏 **2× Claps** ➔ **Toggle Media** (Spotify, Apple Music, YouTube Play/Pause)
* 👏👏 **3× Claps** ➔ **Display Sleep** or System Mute
* 🏠 **Custom Shell / Webhook** ➔ Toggle Home Assistant, Philips Hue, or smart plugs!

Unlike naive volume-threshold triggers, ClapControl uses a **transient acoustic detector** that analyzes amplitude rise time, crest factor, and frequency bandpass (~2.2–2.8 kHz). **It will not false-trigger when you speak, sing, or listen to music.**

---

## 🚀 Quickstart

### Prerequisites
Make sure you have [uv](https://github.com/astral-sh/uv) or Python 3.11+ installed.

### Installation & Run

```bash
# Clone the repository
git clone https://github.com/samuelsluiter-cyber/clapcontrol.git
cd clapcontrol

# 1. Run live acoustic calibration (tune to your room & mic)
uv run clapcontrol calibrate

# 2. Start the daemon (with optional Web Dashboard)
uv run clapcontrol start --web
```

Open your browser at `http://localhost:49152` to access the companion Web UI!

---

## 🎛️ Architecture

```
[ Microphone Stream (sounddevice) ]
                 │
                 ▼
[ Highpass Transient Filter (NumPy) ]  ─── Ignores speech & vocal bass
                 │
                 ▼
[ Crest & Rise-Time Detector ]         ─── Validates sharp handclap impulse (<3ms)
                 │
                 ▼
[ Pattern Recognizer & Debounce ]      ─── Matches timing window (0.15s - 0.75s)
                 │
                 ├── 2 Claps ──► osascript / Media Key (Spotify, Music, Web)
                 └── 3 Claps ──► pmset displaysleepnow / System Mute
```

---

## ⚙️ Configuration

Configuration is automatically stored in `~/.config/clapcontrol/config.yaml`:

```yaml
audio:
  sensitivity: 70            # 1 to 100 (adjust via 'clapcontrol calibrate')
  min_clap_interval: 0.15    # minimum seconds between claps (echo rejection)
  max_clap_interval: 0.75    # maximum seconds between claps

actions:
  double_clap: media_toggle  # media_toggle | volume_mute | display_sleep | custom
  triple_clap: display_sleep
  custom_double_command: "curl -X POST http://homeassistant.local/api/webhook/toggle-lights"

feedback:
  audio_feedback: true       # subtle tick sound when action triggers
```

---

## 🧪 Commands

| Command | Description |
| :--- | :--- |
| `clapcontrol start` | Starts background acoustic listener |
| `clapcontrol start --web` | Starts daemon + browser control interface |
| `clapcontrol calibrate` | Real-time interactive ASCII sound meter |
| `clapcontrol devices` | List available audio input microphones |
| `clapcontrol test double` | Trigger 2-clap action immediately (for testing) |

---

## 📄 License
MIT © Samuel Sluiter
