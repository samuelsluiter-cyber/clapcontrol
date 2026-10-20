"""Clap pattern recognition (Double-Clap, Triple-Clap) with timing windows."""
import time
import threading
from typing import Callable, Optional

class PatternRecognizer:
    def __init__(
        self,
        on_double_clap: Optional[Callable[[], None]] = None,
        on_triple_clap: Optional[Callable[[], None]] = None,
        min_interval: float = 0.15,
        max_interval: float = 0.85,
        pattern_timeout: float = 0.40,
        cooldown: float = 1.0
    ):
        self.on_double_clap = on_double_clap
        self.on_triple_clap = on_triple_clap
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.pattern_timeout = pattern_timeout
        self.cooldown = cooldown

        self.timestamps: list[float] = []
        self.last_action_time = 0.0
        self.timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()

    def record_clap(self):
        """Called whenever a single valid clap impulse is detected."""
        now = time.time()
        with self.lock:
            # Check cooldown after a completed action
            if (now - self.last_action_time) < self.cooldown:
                return

            # Cancel pending double-clap timer if running
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None

            # Remove timestamps older than max_interval * 2
            self.timestamps = [t for t in self.timestamps if (now - t) < (self.max_interval * 2)]
            self.timestamps.append(now)

            n = len(self.timestamps)
            if n == 2:
                interval = self.timestamps[1] - self.timestamps[0]
                if self.min_interval <= interval <= self.max_interval:
                    # Could be double clap or beginning of triple clap!
                    # Start a short timer to wait if a 3rd clap arrives
                    self.timer = threading.Timer(self.pattern_timeout, self._trigger_double_clap)
                    self.timer.start()
                else:
                    # Interval too short or too long -> reset to just latest clap
                    self.timestamps = [now]

            elif n >= 3:
                # Check intervals between 0->1 and 1->2
                i1 = self.timestamps[-2] - self.timestamps[-3]
                i2 = self.timestamps[-1] - self.timestamps[-2]
                if (self.min_interval <= i1 <= self.max_interval) and (self.min_interval <= i2 <= self.max_interval):
                    self._trigger_triple_clap()
                else:
                    self.timestamps = [now]

    def _trigger_double_clap(self):
        with self.lock:
            self.last_action_time = time.time()
            self.timestamps.clear()
            self.timer = None
        if self.on_double_clap:
            self.on_double_clap()

    def _trigger_triple_clap(self):
        self.last_action_time = time.time()
        self.timestamps.clear()
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        if self.on_triple_clap:
            self.on_triple_clap()
