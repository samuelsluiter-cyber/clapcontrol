"""Action execution engine for macOS and system commands."""
import subprocess
import threading
import shutil

def play_feedback_sound(sound_path: str = "/System/Library/Sounds/Tink.aiff"):
    """Plays an unobtrusive system sound asynchronously."""
    if shutil.which("afplay") and sound_path:
        threading.Thread(target=lambda: subprocess.run(["afplay", sound_path], capture_output=True), daemon=True).start()

def toggle_media():
    """Toggles play/pause for Spotify or Apple Music."""
    script = '''
    if application "Spotify" is running then
        tell application "Spotify" to playpause
    else if application "Music" is running then
        tell application "Music" to playpause
    else
        tell application "System Events" to key code 100
    end if
    '''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=2)
    except Exception:
        pass

def toggle_mute():
    """Toggles master volume mute on macOS."""
    script = 'set volume output muted not (output muted of (get volume settings))'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=2)
    except Exception:
        pass

def sleep_display():
    """Instantly puts displays to sleep (keeps background audio listening alive)."""
    try:
        subprocess.run(["pmset", "displaysleepnow"], capture_output=True, timeout=2)
    except Exception:
        pass

def wake_display():
    """Wakes displays from sleep via user-activity assertion."""
    try:
        subprocess.run(["caffeinate", "-u", "-t", "2"], capture_output=True, timeout=2)
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 58'], capture_output=True, timeout=2)
    except Exception:
        pass

def trigger_butler(wait: bool = False):
    """Speaks the casual daily briefing (synchronously if testing, async otherwise)."""
    from .butler import speak_briefing
    if wait:
        speak_briefing()
    else:
        threading.Thread(target=speak_briefing, daemon=True).start()

def execute_action(action_name: str, custom_cmd: str = "", feedback: bool = True, sound_path: str = "", wait: bool = False):
    """Executes the specified action."""
    if feedback and sound_path and action_name != "butler_briefing":
        play_feedback_sound(sound_path)

    if action_name == "media_toggle":
        toggle_media()
    elif action_name == "volume_mute":
        toggle_mute()
    elif action_name == "display_sleep":
        sleep_display()
    elif action_name == "display_wake":
        wake_display()
    elif action_name == "butler_briefing":
        trigger_butler(wait=wait)
    elif action_name == "wake_and_butler":
        wake_display()
        trigger_butler(wait=wait)
    elif action_name == "custom" and custom_cmd:
        try:
            subprocess.Popen(custom_cmd, shell=True)
        except Exception:
            pass
