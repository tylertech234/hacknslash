import pygame
import math
import array


class SoundManager:
    """Procedurally generated sound effects and 8-bit music."""

    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(8)
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
        # Fast ramp up, moderate decay back to calm
        if target > self._combat_intensity:
            self._combat_intensity += (target - self._combat_intensity) * 0.08
        else:
            self._combat_intensity += (target - self._combat_intensity) * 0.02
        # Snap to zero when close enough to avoid permanent low hum
        if self._combat_intensity < 0.01:
            self._combat_intensity = 0.0
        if self._music_playing and hasattr(self, '_base_channel'):
            ci = self._combat_intensity
            self._combat_channel.set_volume(ci * 0.30)
            self._base_channel.set_volume(0.18 * (1.0 - ci * 0.6))

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
        self.sounds["chicken"] = self._make_chicken()
        self.sounds["confetti_boom"] = self._make_confetti_boom()
        self.sounds["parry"] = self._make_parry()
        self.sounds["wheel_tick"] = self._make_wheel_tick()
        self.sounds["wheel_stop"] = self._make_wheel_stop()
        self.sounds["chest_open"] = self._make_chest_open()
        self.sounds["shield_block"] = self._make_shield_block()
        self.sounds["enemy_death"] = self._make_enemy_death()
        self.sounds["charge_whoosh"] = self._make_charge_whoosh()
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
        """Triumphant ascending arpeggio with shimmer."""
        rate = 22050
        n = int(rate * 0.6)
        buf = array.array("h")
        # C5 → E5 → G5 → C6  (arpeggio chord)
        notes = [523, 659, 784, 1047]
        note_len = n // len(notes)
        for i in range(n):
            t = i / n
            note_idx = min(i // note_len, len(notes) - 1)
            freq = notes[note_idx]
            env = (1.0 - t) * 0.9 + 0.1
            # Main tone + octave shimmer
            val = math.sin(2 * math.pi * freq * i / rate) * 0.6
            val += math.sin(2 * math.pi * freq * 2 * i / rate) * 0.2
            # Bright shimmer overtone
            val += math.sin(2 * math.pi * freq * 3 * i / rate) * 0.1
            buf.append(max(-32768, min(32767, int(val * 0.3 * env * 32767))))
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

    def _make_chicken(self) -> pygame.mixer.Sound:
        """Rubber chicken squawk — rising then falling pitch wobble."""
        rate = 22050
        n = int(rate * 0.25)
        buf = array.array("h")
        for i in range(n):
            t = i / n
            # Envelope: quick attack, sustain, decay
            if t < 0.05:
                env = t / 0.05
            elif t < 0.6:
                env = 1.0
            else:
                env = (1.0 - (t - 0.6) / 0.4) ** 2
            # Pitch: rises then wobbles then falls — like a chicken squawk
            base_freq = 400 + 600 * math.sin(t * math.pi * 0.8)
            wobble = math.sin(t * 60) * 80  # fast vibrato
            freq = base_freq + wobble
            val = math.sin(2 * math.pi * freq * i / rate)
            # Add nasal overtone
            val2 = math.sin(2 * math.pi * freq * 2.5 * i / rate) * 0.3
            # Slight noise for texture
            noise = (((i * 13 + 5) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.08
            sample = int((val * 0.25 + val2 * 0.1 + n_val) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_confetti_boom(self) -> pygame.mixer.Sound:
        """Comical pop-explosion with party horn overtone."""
        rate = 22050
        n = int(rate * 0.2)
        buf = array.array("h")
        for i in range(n):
            t = i / n
            env = (1.0 - t) ** 1.5
            # Low thump
            thump = math.sin(2 * math.pi * (120 - 80 * t) * i / rate) * 0.3
            # Party horn: rising sine
            horn = math.sin(2 * math.pi * (300 + 400 * t) * i / rate) * 0.15 * min(1, t * 5)
            # Noise burst
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.2 * max(0, 1 - t * 3)
            sample = int((thump + horn + n_val) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_parry(self) -> pygame.mixer.Sound:
        """Metallic clang/ring for a successful parry."""
        rate = 22050
        n = int(rate * 0.18)
        buf = array.array("h")
        for i in range(n):
            t = i / n
            env = (1.0 - t) ** 2
            # High metallic ring
            ring = math.sin(2 * math.pi * 1200 * i / rate) * 0.25
            ring2 = math.sin(2 * math.pi * 1800 * i / rate) * 0.15
            # Impact
            impact = math.sin(2 * math.pi * 300 * i / rate) * 0.2 * max(0, 1 - t * 6)
            sample = int((ring + ring2 + impact) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_wheel_tick(self) -> pygame.mixer.Sound:
        """Short click for wheel segment passing pointer."""
        return self._tone(2400, 20, volume=0.12, wave="square")

    def _make_wheel_stop(self) -> pygame.mixer.Sound:
        """Triumphant ding when wheel stops."""
        rate = 22050
        n = int(rate * 0.4)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            env = 1.0 - (i / n) ** 0.5
            val = (math.sin(2 * math.pi * 880 * t) * 0.4 +
                   math.sin(2 * math.pi * 1320 * t) * 0.3 +
                   math.sin(2 * math.pi * 1760 * t) * 0.2)
            sample = int(val * env * 0.25 * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_chest_open(self) -> pygame.mixer.Sound:
        """Creaky chest opening sound — rising noise + chime."""
        rate = 22050
        n = int(rate * 0.5)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            env = 1.0 - (i / n)
            # Rising creak
            freq = 200 + 600 * (i / n)
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            creak = math.sin(2 * math.pi * freq * t) * 0.3 + noise * 0.15
            # Chime at end
            chime = 0
            if i > n * 0.6:
                chime_env = 1.0 - (i - n * 0.6) / (n * 0.4)
                chime = math.sin(2 * math.pi * 1047 * t) * 0.4 * chime_env
            sample = int((creak + chime) * env * 0.2 * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_shield_block(self) -> pygame.mixer.Sound:
        """Metallic clang for shielder block."""
        rate = 22050
        n = int(rate * 0.15)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            env = 1.0 - (i / n) ** 0.3
            val = (math.sin(2 * math.pi * 600 * t) * 0.3 +
                   math.sin(2 * math.pi * 1500 * t) * 0.2 +
                   math.sin(2 * math.pi * 3000 * t) * 0.15)
            sample = int(val * env * 0.2 * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_enemy_death(self) -> pygame.mixer.Sound:
        """Brief electronic death burst."""
        rate = 22050
        n = int(rate * 0.2)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            env = 1.0 - (i / n)
            freq = 400 - 300 * (i / n)
            val = (2.0 * (t * freq % 1.0) - 1.0) * 0.3
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            val += noise * 0.2 * env
            sample = int(val * env * 0.15 * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_charge_whoosh(self) -> pygame.mixer.Sound:
        """Rising whoosh for charger enemy dashing."""
        rate = 22050
        n = int(rate * 0.3)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            env = math.sin(math.pi * i / n)
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            freq = 300 + 800 * (i / n)
            val = noise * 0.4 + math.sin(2 * math.pi * freq * t) * 0.2
            sample = int(val * env * 0.12 * 32767)
            buf.append(max(-32768, min(32767, sample)))
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
        """Generate two-layer 8-bit chiptune: atmospheric base + battle combat."""
        rate = 22050
        bpm_base = 90   # slow atmospheric
        bpm_combat = 160  # fast battle
        bars = 8
        beats_per_bar = 4
        total_beats = bars * beats_per_bar

        # We make both loops the same sample length so they stay in sync.
        # Use base BPM for the shared length.
        beat_base = 60.0 / bpm_base
        samples_per_beat_base = int(rate * beat_base)
        total_samples = samples_per_beat_base * total_beats

        # --- ATMOSPHERIC BASE LAYER ---
        # Slow, sparse, eerie ambient — sine pads + gentle low hum + sparse pings
        ambient_notes = [
            110, 110, 0, 131, 0, 0, 110, 0,
            147, 0, 131, 0, 110, 0, 0, 98,
            110, 0, 0, 131, 147, 0, 131, 0,
            110, 0, 98, 0, 0, 110, 0, 0,
        ]  # 0 = silence
        pad_notes = [55, 55, 55, 55, 65, 65, 65, 65,
                     73, 73, 73, 73, 65, 65, 55, 55,
                     55, 55, 55, 55, 65, 65, 65, 65,
                     73, 73, 73, 73, 65, 65, 55, 55]

        buf_base = array.array("h")
        for beat_idx in range(total_beats):
            nidx = beat_idx % len(ambient_notes)
            mel_freq = ambient_notes[nidx]
            pad_freq = pad_notes[nidx % len(pad_notes)]
            for i in range(samples_per_beat_base):
                t = i / rate
                pos = i / samples_per_beat_base

                # Warm sine pad — slow attack/release, very low
                pad_env = math.sin(pos * math.pi)  # swell shape
                pad_val = math.sin(2 * math.pi * pad_freq * t) * 0.04 * pad_env
                # Detuned layer for width
                pad_val += math.sin(2 * math.pi * (pad_freq * 1.005) * t) * 0.03 * pad_env

                # Sparse melody pings — triangle-ish wave, gentle
                mel_val = 0.0
                if mel_freq > 0 and pos < 0.4:
                    mel_env = (1.0 - pos / 0.4) ** 2
                    # Triangle wave
                    phase = (t * mel_freq) % 1.0
                    tri = 4.0 * abs(phase - 0.5) - 1.0
                    mel_val = tri * 0.05 * mel_env

                sample = int((pad_val + mel_val) * 32767)
                buf_base.append(max(-32768, min(32767, sample)))
        self._bgm_base = pygame.mixer.Sound(buffer=buf_base)

        # --- BATTLE COMBAT LAYER ---
        # Fast, aggressive — driving drums, saw bass, staccato square arps
        beat_combat = 60.0 / bpm_combat
        # Total combat beats to fill same duration
        combat_total_beats = int(total_samples / (rate * beat_combat))
        samples_per_beat_combat = int(rate * beat_combat)
        # We might have a few samples difference; pad at end
        combat_bass = [110, 110, 131, 131, 147, 147, 131, 131,
                       110, 110, 98, 98, 131, 131, 147, 147]
        combat_arp = [440, 523, 659, 523, 440, 587, 659, 784,
                      523, 659, 784, 659, 523, 440, 587, 523]
        drum_pattern = [1, 3, 2, 3] * 16  # kick, hat, snare, hat

        buf_combat = array.array("h")
        for beat_idx in range(combat_total_beats):
            bidx = beat_idx % len(combat_bass)
            bas_freq = combat_bass[bidx]
            arp_freq = combat_arp[beat_idx % len(combat_arp)]
            drum = drum_pattern[beat_idx % len(drum_pattern)]

            for i in range(samples_per_beat_combat):
                t = i / rate
                pos = i / samples_per_beat_combat

                # Aggressive saw bass
                bas = 2.0 * ((t * bas_freq) % 1.0) - 1.0
                bas_val = bas * 0.09 * (1.0 - pos * 0.15)

                # Staccato square arp — short notes
                arp_val = 0.0
                if pos < 0.35:
                    arp_env = 1.0 - pos / 0.35
                    arp = 1.0 if math.sin(2 * math.pi * arp_freq * t) >= 0 else -1.0
                    arp_val = arp * 0.06 * arp_env

                # Heavy drums
                drm = 0.0
                if drum == 1 and pos < 0.15:  # kick
                    kf = 100 * (1.0 - pos / 0.15)
                    drm = math.sin(2 * math.pi * kf * t) * 0.20 * (1.0 - pos / 0.15)
                elif drum == 2 and pos < 0.10:  # snare
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.16 * (1.0 - pos / 0.10)
                elif drum == 3 and pos < 0.05:  # hihat
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.06 * (1.0 - pos / 0.05)

                sample = int((bas_val + arp_val + drm) * 32767)
                buf_combat.append(max(-32768, min(32767, sample)))

        # Pad to match base layer length
        while len(buf_combat) < len(buf_base):
            buf_combat.append(0)
        # Trim if slightly over
        while len(buf_combat) > len(buf_base):
            buf_combat.pop()

        self._bgm_combat = pygame.mixer.Sound(buffer=buf_combat)
