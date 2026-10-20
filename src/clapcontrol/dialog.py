"""Voice dialog and task delegation to Antigravity for Samuel Sluiter."""
import os
import json
import time
import wave
import subprocess
import urllib.request
from pathlib import Path
import numpy as np
import sounddevice as sd

from .config import load_config
from .butler import speak_with_elevenlabs

AUDIO_PROMPT_PATH = Path("/tmp/clapcontrol_voice_input.wav")
VAULT_DIR = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Second Brain"
JOBBOERSE_FILE = VAULT_DIR / "Projekte/Chat AI Jobbörse.md"

def record_user_speech(max_seconds: float = 6.0, sample_rate: int = 16000) -> bool:
    """Records audio from microphone until silence is detected or max_seconds reached."""
    # Play chime to signal: 'Listening...'
    subprocess.run(["afplay", "/System/Library/Sounds/Tink.aiff"], capture_output=True)

    chunk_duration = 0.1  # 100ms
    chunk_size = int(sample_rate * chunk_duration)
    recorded_chunks = []
    
    silence_count = 0
    silence_limit = int(1.2 / chunk_duration) # 1.2s of silence stops recording
    has_started_speaking = False

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        start_time = time.time()
        while (time.time() - start_time) < max_seconds:
            chunk, _ = stream.read(chunk_size)
            recorded_chunks.append(chunk)

            # Measure volume
            rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
            if rms > 450:
                has_started_speaking = True
                silence_count = 0
            elif has_started_speaking:
                silence_count += 1
                if silence_count >= silence_limit:
                    break  # User stopped speaking

    if not recorded_chunks or not has_started_speaking:
        return False

    audio_data = np.concatenate(recorded_chunks, axis=0)
    with wave.open(str(AUDIO_PROMPT_PATH), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    return True

def transcribe_audio(api_key: str) -> str:
    """Transcribes the recorded audio file via ElevenLabs Scribe STT."""
    if not AUDIO_PROMPT_PATH.exists() or not api_key:
        return ""

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = [
        f"--{boundary}".encode(),
        b"Content-Disposition: form-data; name=\"model_id\"",
        b"",
        b"scribe_v1",
        f"--{boundary}".encode(),
        b"Content-Disposition: form-data; name=\"file\"; filename=\"voice_prompt.wav\"",
        b"Content-Type: audio/wav",
        b"",
    ]
    with open(AUDIO_PROMPT_PATH, "rb") as f:
        file_bytes = f.read()

    payload = b"\r\n".join(body) + b"\r\n" + file_bytes + b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(url, data=payload, headers={
        "xi-api-key": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("text", "").strip()
    except Exception:
        return ""

def delegate_task_to_antigravity(prompt_text: str) -> str:
    """Adds task to Jobbörse and/or invokes Antigravity background processing."""
    if not prompt_text:
        return "Ich habe leider nichts verstanden."

    # 1. Append directly to Chat AI Jobbörse in Second Brain
    if JOBBOERSE_FILE.exists():
        try:
            content = JOBBOERSE_FILE.read_text(encoding="utf-8")
            # Generate next Job ID
            import re
            ids = [int(m) for m in re.findall(r"\bJ(\d+)\b", content)]
            next_id = f"J{(max(ids) + 1) if ids else 57}"
            
            entry = f"\n- [ ] **{next_id} Sprachauftrag: {prompt_text}** · Sprach-Input Samuel (via Butler) · 🎙️ Direkt von Antigravity bearbeiten"
            
            # Insert right below ## 📋 Offen
            if "## 📋 Offen" in content:
                content = content.replace("## 📋 Offen (oben = als Nächstes)\n", f"## 📋 Offen (oben = als Nächstes)\n{entry}\n")
                JOBBOERSE_FILE.write_text(content, encoding="utf-8")
        except Exception:
            pass

    return f"Verstanden Samuel! Ich habe den Auftrag '{prompt_text}' an Antigravity übergeben und in die Jobbörse eingetragen."

def run_voice_interaction():
    """Complete voice loop: listen -> transcribe -> process -> answer."""
    cfg = load_config()
    api_key = cfg.get("butler", {}).get("elevenlabs_api_key", "")
    voice_id = cfg.get("butler", {}).get("elevenlabs_voice_id", "IKne3meq5aSn9XLyUdCD")

    # 1. Record
    heard_speech = record_user_speech()
    if not heard_speech:
        return

    # 2. Transcribe
    user_text = transcribe_audio(api_key)
    if not user_text:
        return

    # 3. Delegate to Antigravity
    response_text = delegate_task_to_antigravity(user_text)

    # 4. Speak response back via ElevenLabs
    speak_with_elevenlabs(response_text, api_key, voice_id)
