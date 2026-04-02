import pygame
import math
import array


class SoundManager:
    """Procedurally generated sound effects and 8-bit music."""

    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self._generate_all()
        self._music_playing = False
        self._combat_intensity = 0.0
        self._generate_music()

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------

    def play(self, name: str):
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    def start_music(self):
        if not self._music_playing and self._bgm_base:
            self._base_channel = pygame.mixer.Channel(1)
            self._combat_channel = pygame.mixer.Channel(2)
            self._base_channel.play(self._bgm_base, loops=-1)
            self._base_channel.set_volume(0.20)
            self._combat_channel.play(self._bgm_combat, loops=-1)
            self._combat_channel.set_volume(0.0)
            self._music_playing = True

    def stop_music(self):
        if hasattr(self, '_base_channel'):
            self._base_channel.stop()
            self._combat_channel.stop()
        self._music_playing = False

    def set_music_intensity(self, level: float):
        """Crossfade between calm and combat music layers. 0.0=calm, 1.0=intense."""
        target = max(0.0, min(1.0, level))
        self._combat_intensity += (target - self._combat_intensity) * 0.05
        if self._music_playing and hasattr(self, '_base_channel'):
            self._combat_channel.set_volume(self._combat_intensity * 0.22)
            self._base_channel.set_volume(0.20 - self._combat_intensity * 0.06)

    def play_radar_beep(self, dist_ratio: float):
        """Play radar beep — higher pitch for closer enemies."""
        if dist_ratio < 0.33:
            self.sounds["radar_beep_close"].play()
        elif dist_ratio < 0.66:
            self.sounds["radar_beep_mid"].play()
        else:
            self.sounds["radar_beep_far"].play()

    # ------------------------------------------------------------------
    # generation
    # ------------------------------------------------------------------

    def _generate_all(self):
        self.sounds["swing"] = self._make_swing()
        self.sounds["enemy_shoot"] = self._make_shoot()
        self.sounds["hit"] = self._make_hit()
        self.sounds["step"] = self._make_step()
        self.sounds["pickup"] = self._make_pickup()
        self.sounds["levelup"] = self._make_levelup()
        self.sounds["dash"] = self._make_dash()
        self.sounds["boss_roar"] = self._make_boss_roar()
        self.sounds["throw"] = self._make_throw()
        self.sounds["radar_beep_far"] = self._make_radar_beep(800, 0.06)
        self.sounds["radar_beep_mid"] = self._make_radar_beep(1200, 0.09)
        self.sounds["radar_beep_close"] = self._make_radar_beep(1800, 0.13)

    # ---- individual sound generators ----

    @staticmethod
    def _tone(freq: float, duration_ms: int, volume: float = 0.3,
              decay: bool = True, wave: str = "saw") -> pygame.mixer.Sound:
        """Generate a simple waveform tone."""
        rate = 22050
        n_samples = int(rate * duration_ms / 1000)
        buf = array.array("h")  # signed short
        for i in range(n_samples):
            t = i / rate
            env = 1.0 - (i / n_samples) if decay else 1.0
            if wave == "sin":
                val = math.sin(2 * math.pi * freq * t)
            elif wave == "saw":
                val = 2.0 * (t * freq % 1.0) - 1.0
            elif wave == "square":
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            else:  # noise
                val = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            sample = int(val * volume * env * 32767)
            sample = max(-32768, min(32767, sample))
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf)

    def _make_swing(self) -> pygame.mixer.Sound:
        """Quick swoosh — descending noise burst."""
        rate = 22050
        n = int(rate * 0.12)
        buf = array.array("h")
        for i in range(n):
            env = 1.0 - i / n
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            freq = 800 - 600 * (i / n)
            tone = math.sin(2 * math.pi * freq * i / rate)
            sample = int((noise * 0.3 + tone * 0.15) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_shoot(self) -> pygame.mixer.Sound:
        """Dalek zap — short descending square."""
        rate = 22050
        n = int(rate * 0.15)
        buf = array.array("h")
        for i in range(n):
            env = 1.0 - i / n
            freq = 600 - 400 * (i / n)
            val = 1.0 if math.sin(2 * math.pi * freq * i / rate) >= 0 else -1.0
            buf.append(max(-32768, min(32767, int(val * 0.2 * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_hit(self) -> pygame.mixer.Sound:
        """Impact thud."""
        rate = 22050
        n = int(rate * 0.08)
        buf = array.array("h")
        for i in range(n):
            env = 1.0 - i / n
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            val = noise / 16384.0 - 1.0
            tone = math.sin(2 * math.pi * 120 * i / rate)
            buf.append(max(-32768, min(32767, int((val * 0.25 + tone * 0.3) * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_step(self) -> pygame.mixer.Sound:
        """Soft footstep tick."""
        rate = 22050
        n = int(rate * 0.04)
        buf = array.array("h")
        for i in range(n):
            env = 1.0 - i / n
            noise = (((i * 13 + 7) * 1103515245 + 12345) >> 16) & 0x7FFF
            val = noise / 16384.0 - 1.0
            buf.append(max(-32768, min(32767, int(val * 0.10 * env * 32767))))
        snd = pygame.mixer.Sound(buffer=buf)
        snd.set_volume(0.3)
        return snd

    def _make_pickup(self) -> pygame.mixer.Sound:
        """Ascending chime."""
        rate = 22050
        n = int(rate * 0.2)
        buf = array.array("h")
        for i in range(n):
            env = 1.0 - (i / n) ** 2
            freq = 500 + 800 * (i / n)
            val = math.sin(2 * math.pi * freq * i / rate)
            buf.append(max(-32768, min(32767, int(val * 0.25 * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_levelup(self) -> pygame.mixer.Sound:
        """Triumphant double chime."""
        rate = 22050
        n = int(rate * 0.4)
        buf = array.array("h")
        for i in range(n):
            t = i / n
            env = 1.0 - t
            if t < 0.5:
                freq = 660
            else:
                freq = 880
            val = math.sin(2 * math.pi * freq * i / rate)
            buf.append(max(-32768, min(32767, int(val * 0.25 * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_dash(self) -> pygame.mixer.Sound:
        """Quick whoosh."""
        rate = 22050
        n = int(rate * 0.1)
        buf = array.array("h")
        for i in range(n):
            env = (1.0 - i / n) ** 2
            noise = (((i * 31 + 17) * 1103515245 + 12345) >> 16) & 0x7FFF
            val = noise / 16384.0 - 1.0
            buf.append(max(-32768, min(32767, int(val * 0.2 * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_boss_roar(self) -> pygame.mixer.Sound:
        """Deep menacing boss entrance rumble."""
        rate = 22050
        n = int(rate * 0.6)
        buf = array.array("h")
        for i in range(n):
            t = i / n
            env = (1.0 - t) * min(1.0, t * 8)  # quick attack, slow decay
            # Low growl: layered detuned saws
            freq1 = 55 + 20 * math.sin(t * 6)
            freq2 = 62 + 15 * math.sin(t * 8)
            saw1 = 2.0 * ((i / rate * freq1) % 1.0) - 1.0
            saw2 = 2.0 * ((i / rate * freq2) % 1.0) - 1.0
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = noise / 16384.0 - 1.0
            val = (saw1 * 0.25 + saw2 * 0.2 + n_val * 0.15) * env
            buf.append(max(-32768, min(32767, int(val * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_throw(self) -> pygame.mixer.Sound:
        """Quick sharp throw sound."""
        rate = 22050
        n = int(rate * 0.08)
        buf = array.array("h")
        for i in range(n):
            env = (1.0 - i / n) ** 1.5
            freq = 1200 - 800 * (i / n)
            val = math.sin(2 * math.pi * freq * i / rate)
            noise = (((i * 31 + 7) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = noise / 16384.0 - 1.0
            buf.append(max(-32768, min(32767, int((val * 0.15 + n_val * 0.1) * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_radar_beep(self, freq: int, volume: float) -> pygame.mixer.Sound:
        """Short radar ping at given frequency and volume."""
        rate = 22050
        n = int(rate * 0.04)
        buf = array.array("h")
        for i in range(n):
            env = 1.0 - (i / n) ** 2
            val = math.sin(2 * math.pi * freq * i / rate)
            buf.append(max(-32768, min(32767, int(val * volume * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    # ------------------------------------------------------------------
    # 8-bit background music
    # ------------------------------------------------------------------

    def _generate_music(self):
        """Generate two-layer 8-bit chiptune: base (calm) + combat (intense)."""
        rate = 22050
        bpm = 140
        beat = 60.0 / bpm
        bars = 8
        beats_per_bar = 4
        total_beats = bars * beats_per_bar
        samples_per_beat = int(rate * beat)

        melody_notes = [
            330, 330, 392, 392, 440, 440, 523, 523,
            587, 587, 523, 523, 440, 392, 330, 330,
            392, 440, 523, 523, 587, 659, 587, 523,
            440, 440, 392, 330, 392, 440, 392, 330,
        ]
        bass_notes = [
            165, 165, 165, 165, 196, 196, 196, 196,
            220, 220, 220, 220, 196, 196, 165, 165,
            196, 196, 196, 196, 220, 220, 220, 220,
            262, 262, 220, 220, 196, 196, 165, 165,
        ]
        drum_pattern = [1, 3, 2, 3] * 8
        arp_notes = [523, 659, 784, 659]

        # --- Base layer: soft melody + light bass + hihats only ---
        buf_base = array.array("h")
        for beat_idx in range(total_beats):
            nidx = beat_idx % len(melody_notes)
            mel_freq = melody_notes[nidx]
            bas_freq = bass_notes[nidx % len(bass_notes)]
            drum = drum_pattern[beat_idx % len(drum_pattern)]
            for i in range(samples_per_beat):
                t = i / rate
                pos = i / samples_per_beat
                mel = 1.0 if math.sin(2 * math.pi * mel_freq * t) >= 0 else -1.0
                mel_val = mel * 0.08 * (1.0 - pos * 0.3)
                bas = 1.0 if math.sin(2 * math.pi * bas_freq * t) >= 0 else -1.0
                bas_val = bas * 0.06 * (1.0 - pos * 0.2)
                drm = 0.0
                if drum == 3 and pos < 0.05:
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.02 * (1.0 - pos / 0.05)
                sample = int((mel_val + bas_val + drm) * 32767)
                buf_base.append(max(-32768, min(32767, sample)))
        self._bgm_base = pygame.mixer.Sound(buffer=buf_base)

        # --- Combat layer: heavy drums + arp + saw bass ---
        buf_combat = array.array("h")
        for beat_idx in range(total_beats):
            nidx = beat_idx % len(melody_notes)
            bas_freq = bass_notes[nidx % len(bass_notes)]
            drum = drum_pattern[beat_idx % len(drum_pattern)]
            for i in range(samples_per_beat):
                t = i / rate
                pos = i / samples_per_beat
                arp_idx = int(pos * 4) % len(arp_notes)
                arp_freq = arp_notes[arp_idx]
                arp = 1.0 if math.sin(2 * math.pi * arp_freq * t) >= 0 else -1.0
                arp_val = arp * 0.06 * (1.0 - (pos * 4 % 1.0) * 0.5)
                bas = 2.0 * ((t * bas_freq) % 1.0) - 1.0
                bas_val = bas * 0.08 * (1.0 - pos * 0.1)
                drm = 0.0
                if drum == 1 and pos < 0.15:
                    kf = 80 * (1.0 - pos / 0.15)
                    drm = math.sin(2 * math.pi * kf * t) * 0.18 * (1.0 - pos / 0.15)
                elif drum == 2 and pos < 0.12:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.14 * (1.0 - pos / 0.12)
                elif drum == 3 and pos < 0.06:
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.06 * (1.0 - pos / 0.06)
                sample = int((arp_val + bas_val + drm) * 32767)
                buf_combat.append(max(-32768, min(32767, sample)))
        self._bgm_combat = pygame.mixer.Sound(buffer=buf_combat)
