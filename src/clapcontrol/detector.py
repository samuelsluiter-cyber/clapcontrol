"""High-performance acoustic clap detector with transient & frequency analysis."""
import time
import numpy as np

class ClapDetector:
    def __init__(self, sample_rate: int = 44100, sensitivity: int = 70):
        self.sample_rate = sample_rate
        self.update_sensitivity(sensitivity)
        
        # State tracking
        self.noise_floor = 0.005
        self.last_clap_time = 0.0
        self.min_clap_spacing = 0.12  # Minimum 120ms between distinct claps (ignores echo)
        self.prev_sample = 0.0

    def update_sensitivity(self, sensitivity: int):
        """Sensitivity from 1 (hard to trigger) to 100 (very sensitive)."""
        self.sensitivity = max(1, min(100, sensitivity))
        # Map 1-100 to an amplitude threshold
        # High sensitivity (100) -> lower threshold (0.05)
        # Low sensitivity (1) -> higher threshold (0.50)
        norm = (100 - self.sensitivity) / 99.0
        self.peak_threshold = 0.04 + norm * 0.40
        self.crest_threshold = 3.5 + (1.0 - norm) * 1.5

    def process_chunk(self, audio_data: np.ndarray) -> tuple[bool, float, float]:
        """
        Processes a block of audio samples.
        Returns: (is_clap, peak_value, crest_factor)
        """
        now = time.time()
        
        # Ensure mono float32
        if audio_data.ndim > 1:
            samples = audio_data.mean(axis=1)
        else:
            samples = audio_data
            
        peak = float(np.max(np.abs(samples)))
        rms = float(np.sqrt(np.mean(samples ** 2))) + 1e-6
        crest_factor = peak / rms

        # Fast 1st-order highpass filter to isolate sharp transients (handclaps) from vocal bass
        # y[n] = x[n] - 0.92 * x[n-1]
        hp_samples = samples[1:] - 0.92 * samples[:-1]
        hp_peak = float(np.max(np.abs(hp_samples))) if len(hp_samples) > 0 else peak

        # Update rolling background noise floor slowly
        self.noise_floor = 0.96 * self.noise_floor + 0.04 * rms

        # Detection criteria:
        # 1. Absolute peak exceeds threshold
        # 2. Significant transient jump over background noise floor (at least 3.5x noise)
        # 3. High crest factor (peaky impulse vs sustained tone)
        # 4. High-pass transient matches (ensures it's not a low desk bump or deep voice)
        # 5. Debounce window to avoid echo of the same clap
        is_clap = False
        if (now - self.last_clap_time) > self.min_clap_spacing:
            if (peak > self.peak_threshold and
                peak > (self.noise_floor * 3.5) and
                crest_factor > self.crest_threshold and
                hp_peak > (self.peak_threshold * 0.65)):
                
                is_clap = True
                self.last_clap_time = now

        return is_clap, peak, crest_factor
