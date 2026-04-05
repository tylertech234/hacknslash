import pygame
import math
import array


class SoundManager:
    """Procedurally generated sound effects and zone-specific music."""

    def __init__(self):
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self._music_playing = False
        self._combat_intensity = 0.0
        self._zone_music: dict[str, tuple] = {}
        self._bgm_base = None
        self._bgm_combat = None
        self._current_music_zone = None
        self._boss_music: dict[str, pygame.mixer.Sound] = {}
        self.boss_music_playing = False

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(8)
        self._generate_all()
        self._generate_zone_music()
        self._generate_boss_music()

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------

    def play(self, name: str):
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    def set_zone_music(self, zone_name: str):
        """Switch to the music pair for the given zone."""
        if zone_name == self._current_music_zone:
            return
        was_playing = self._music_playing
        if was_playing:
            self.stop_music()
        pair = self._zone_music.get(zone_name)
        if pair:
            self._bgm_base, self._bgm_combat = pair
            self._current_music_zone = zone_name
        if was_playing:
            self.start_music()

    def start_music(self):
        if not self._music_playing and self._bgm_base:
            self._base_channel = pygame.mixer.Channel(1)
            self._combat_channel = pygame.mixer.Channel(2)
            self._base_channel.play(self._bgm_base, loops=-1)
            self._base_channel.set_volume(0.15)
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
        # Fast ramp up, slow decay back to calm
        if target > self._combat_intensity:
            self._combat_intensity += (target - self._combat_intensity) * 0.08
        else:
            self._combat_intensity += (target - self._combat_intensity) * 0.008
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
            snd = self.sounds.get("radar_beep_close")
        elif dist_ratio < 0.66:
            snd = self.sounds.get("radar_beep_mid")
        else:
            snd = self.sounds.get("radar_beep_far")
        if snd:
            snd.play()

    def start_boss_music(self, zone: str):
        """Play intense boss music; mute regular BGM to background level."""
        track = self._boss_music.get(zone)
        if not track:
            return
        if self._music_playing and hasattr(self, '_base_channel'):
            self._base_channel.set_volume(0.04)
            self._combat_channel.set_volume(0.0)
        self._boss_channel = pygame.mixer.Channel(5)
        self._boss_channel.play(track, loops=-1)
        self._boss_channel.set_volume(0.32)
        self.boss_music_playing = True

    def stop_boss_music(self):
        """Stop boss music and restore zone music."""
        if not hasattr(self, '_boss_channel'):
            return
        self._boss_channel.stop()
        self.boss_music_playing = False
        # Restore zone BGM
        if self._music_playing and hasattr(self, '_base_channel'):
            self._base_channel.set_volume(0.15)

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
        self.sounds["chest_fanfare"] = self._make_chest_fanfare()
        self.sounds["shield_block"] = self._make_shield_block()
        self.sounds["enemy_death"] = self._make_enemy_death()
        self.sounds["charge_whoosh"] = self._make_charge_whoosh()
        self.sounds["dog_bark"] = self._make_dog_bark()
        self.sounds["dog_growl"] = self._make_dog_growl()
        self.sounds["radar_beep_far"] = self._make_radar_beep(800, 0.06)
        self.sounds["radar_beep_mid"] = self._make_radar_beep(1200, 0.09)
        self.sounds["radar_beep_close"] = self._make_radar_beep(1800, 0.13)
        self.sounds["pause"] = self._tone(600, 80, volume=0.15, wave="sin")
        self.sounds["unpause"] = self._tone(800, 80, volume=0.15, wave="sin")
        self.sounds["boss_death"] = self._make_boss_death()
        self.sounds["big_boss_death"] = self._make_big_boss_death()
        self.sounds["player_death"] = self._make_player_death()
        self.sounds["player_hit"] = self._make_player_hit()

        # Explicit headphone-friendly volumes — clearly lower than raw generator output
        _vol = {
            "swing":         0.40,
            "enemy_shoot":   0.35,
            "hit":           0.38,
            "step":          0.18,
            "pickup":        0.30,
            "levelup":       0.58,
            "dash":          0.32,
            "boss_roar":     0.42,
            "throw":         0.30,
            "chicken":       0.62,
            "confetti_boom": 0.35,
            "parry":         0.40,
            "wheel_tick":    0.18,
            "wheel_stop":    0.40,
            "chest_open":    0.35,
            "chest_fanfare": 0.55,
            "shield_block":  0.38,
            "enemy_death":   0.32,
            "charge_whoosh": 0.35,
            "dog_bark":      0.35,
            "dog_growl":     0.28,
            "radar_beep_far":   0.12,
            "radar_beep_mid":   0.16,
            "radar_beep_close": 0.22,
            "pause":         0.20,
            "unpause":       0.20,
            "boss_death":    0.45,
            "big_boss_death": 0.50,
            "player_death":  0.45,
            "player_hit":    0.48,
        }
        for _name, _v in _vol.items():
            if _name in self.sounds:
                self.sounds[_name].set_volume(_v)

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
        """Rich swoosh — layered noise with tonal sweep and tail."""
        rate = 22050
        n = int(rate * 0.15)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.5 * min(1.0, pos * 15)
            freq = 900 - 700 * pos
            tone = math.sin(2 * math.pi * freq * t) * 0.12
            tone2 = math.sin(2 * math.pi * freq * 1.5 * t) * 0.06
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            # Filtered noise — emphasize mid frequencies
            sample = int((noise * 0.25 + tone + tone2) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_shoot(self) -> pygame.mixer.Sound:
        """Dalek zap — layered descending pulse with resonance."""
        rate = 22050
        n = int(rate * 0.18)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.3 * min(1.0, pos * 20)
            freq = 700 - 500 * pos
            # Square pulse
            pulse = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            # Resonant sine body
            body = math.sin(2 * math.pi * freq * t) * 0.4
            # High harmonic sizzle
            sizzle = math.sin(2 * math.pi * freq * 3 * t) * 0.1 * max(0, 1 - pos * 3)
            sample = int((pulse * 0.15 + body + sizzle) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_hit(self) -> pygame.mixer.Sound:
        """Meaty impact — layered thump with crunch."""
        rate = 22050
        n = int(rate * 0.12)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.2 * min(1.0, pos * 20)
            # Deep thump
            thump = math.sin(2 * math.pi * 90 * t) * 0.35
            thump2 = math.sin(2 * math.pi * 55 * t) * 0.2
            # Crunch noise
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.2 * max(0, 1 - pos * 3)
            # Mid punch
            punch = math.sin(2 * math.pi * 200 * t) * 0.15 * max(0, 1 - pos * 5)
            sample = int((thump + thump2 + n_val + punch) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_player_hit(self) -> pygame.mixer.Sound:
        """Sharp body-hit — high crack + low thump, distinct from melee hit."""
        rate = 22050
        n = int(rate * 0.20)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 0.9 * min(1.0, pos * 50)
            # Sharp crack transient (brief high-freq noise burst)
            crack_env = max(0.0, 1.0 - pos * 12)
            crack_noise = (((i * 31337 + 9) * 1103515245 + 12345) >> 16) & 0x7FFF
            crack = (crack_noise / 16384.0 - 1.0) * 0.5 * crack_env
            # Low body thump
            thump = math.sin(2 * math.pi * 65 * t) * 0.35
            # Descending pain whine
            whine_env = max(0.0, 1.0 - pos * 6)
            whine = math.sin(2 * math.pi * (900 - 600 * pos) * t) * 0.18 * whine_env
            sample = int((crack + thump + whine) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        snd = pygame.mixer.Sound(buffer=buf)
        snd.set_volume(0.75)
        return snd

    def _make_step(self) -> pygame.mixer.Sound:
        """Soft footstep with subtle thud and scuff."""
        rate = 22050
        n = int(rate * 0.06)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.5 * min(1.0, pos * 30)
            # Low thud
            thud = math.sin(2 * math.pi * 80 * t) * 0.15 * max(0, 1 - pos * 5)
            # Scuff noise
            noise = (((i * 13 + 7) * 1103515245 + 12345) >> 16) & 0x7FFF
            scuff = (noise / 16384.0 - 1.0) * 0.12
            sample = int((thud + scuff) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        snd = pygame.mixer.Sound(buffer=buf)
        snd.set_volume(0.3)
        return snd

    def _make_pickup(self) -> pygame.mixer.Sound:
        """Sparkling ascending chime with harmonics."""
        rate = 22050
        n = int(rate * 0.25)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos ** 2) * min(1.0, pos * 10)
            freq = 600 + 1000 * pos
            val = math.sin(2 * math.pi * freq * t) * 0.2
            val += math.sin(2 * math.pi * freq * 2 * t) * 0.1
            val += math.sin(2 * math.pi * freq * 3 * t) * 0.05
            # Sparkle: noise bursts
            if (i % 400) < 50:
                noise = (((i * 31 + 17) * 1103515245 + 12345) >> 16) & 0x7FFF
                val += (noise / 16384.0 - 1.0) * 0.06
            buf.append(max(-32768, min(32767, int(val * env * 32767))))
        return pygame.mixer.Sound(buffer=buf)

    def _make_levelup(self) -> pygame.mixer.Sound:
        """Deep gong strike + low brass swell — WoW-style level-up DING.
        Phase 1 (0–0.15s): deep resonant GONG hit (inharmonic bell partials)
        Phase 2 (0.05–2.2s): low brass chord swells up and fades (F2 major triad)
        Total: ~2.5s"""
        rate = 22050
        total = int(rate * 2.5)
        buf = array.array("h")

        # Gong partials — inharmonic ratios typical of a bronze bell/gong
        # Root F2 = 87 Hz
        root = 87.0
        gong_partials = [
            (root,        0.55),   # fundamental
            (root * 1.50, 0.30),   # quint
            (root * 2.00, 0.18),   # octave
            (root * 2.76, 0.22),   # characteristic inharmonic bell partial
            (root * 3.00, 0.10),
            (root * 3.50, 0.08),
            (root * 4.07, 0.06),   # another inharmonic partial
        ]
        gong_decay = 4.5   # slow resonant decay

        # Brass chord: F2 major triad voiced low
        # F2=87, A2=110, C3=131, (F3=175 for brightness)
        brass_notes = [
            (87,  0.35),
            (110, 0.28),
            (131, 0.22),
            (175, 0.15),
        ]
        brass_start = int(rate * 0.05)   # brass enters just after gong
        brass_attack_dur = int(rate * 0.25)
        brass_decay_start = int(rate * 1.4)
        brass_end = total

        for i in range(total):
            t = i / rate
            val = 0.0

            # ── Gong ──────────────────────────────────────────
            gong_env = math.exp(-t * gong_decay)
            for freq, amp in gong_partials:
                val += math.sin(2 * math.pi * freq * t) * amp * gong_env

            # ── Brass swell ───────────────────────────────────
            if i >= brass_start:
                bi = i - brass_start
                # Attack swell
                b_attack = min(1.0, bi / brass_attack_dur)
                # Sustain + decay
                if i < brass_decay_start:
                    b_env = b_attack
                else:
                    b_env = b_attack * max(0.0, 1.0 - (i - brass_decay_start) /
                                           (brass_end - brass_decay_start))
                # Brass timbre: saw wave (buzz) + strong harmonics
                for freq, amp in brass_notes:
                    bphase = (t * freq) % 1.0
                    bsaw = 2.0 * bphase - 1.0   # raw saw
                    # Soft clip for warm brass (not harsh)
                    bsaw = math.tanh(bsaw * 1.6) * 0.75
                    val += bsaw * amp * b_env
                    # Add 2nd harmonic for richness
                    val += math.sin(2 * math.pi * freq * 2 * t) * amp * 0.25 * b_env
                    # Slight vibrato on sustain
                    if i > brass_attack_dur + brass_start:
                        vib = 1.0 + 0.006 * math.sin(2 * math.pi * 5.5 * t)
                        val += math.sin(2 * math.pi * freq * vib * t) * amp * 0.10 * b_env

            # Normalise — gong + brass stack can exceed 1.0
            sample = int(val * 0.38 * 32767)
            buf.append(max(-32768, min(32767, sample)))

        return pygame.mixer.Sound(buffer=buf)

    def _make_dash(self) -> pygame.mixer.Sound:
        """Punchy whoosh with tonal sweep."""
        rate = 22050
        n = int(rate * 0.14)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = math.sin(math.pi * pos) * (1.0 - pos * 0.3)
            # Wind noise
            noise = (((i * 31 + 17) * 1103515245 + 12345) >> 16) & 0x7FFF
            wind = (noise / 16384.0 - 1.0) * 0.2
            # Rising tone sweep
            freq = 200 + 600 * pos
            tone = math.sin(2 * math.pi * freq * t) * 0.12
            sample = int((wind + tone) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_boss_roar(self) -> pygame.mixer.Sound:
        """Deep menacing boss entrance — layered growl with sub-bass."""
        rate = 22050
        n = int(rate * 0.8)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 0.7 * min(1.0, pos * 6)
            # Sub bass rumble
            sub = math.sin(2 * math.pi * 35 * t) * 0.2
            # Detuned growl saws
            freq1 = 55 + 25 * math.sin(pos * 8)
            freq2 = 62 + 18 * math.sin(pos * 10)
            saw1 = 2.0 * ((t * freq1) % 1.0) - 1.0
            saw2 = 2.0 * ((t * freq2) % 1.0) - 1.0
            # Gritty distortion
            growl = max(-0.7, min(0.7, (saw1 * 0.3 + saw2 * 0.25) * 1.4))
            # Heavy noise
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.18
            sample = int((sub + growl + n_val) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_throw(self) -> pygame.mixer.Sound:
        """Sharp knife throw with metallic ring."""
        rate = 22050
        n = int(rate * 0.12)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.8 * min(1.0, pos * 25)
            freq = 1400 - 900 * pos
            # Sharp blade tone
            blade = math.sin(2 * math.pi * freq * t) * 0.2
            # Metallic ring overtone
            ring = math.sin(2 * math.pi * 2200 * t) * 0.08 * (1.0 - pos)
            # Air whoosh
            noise = (((i * 31 + 7) * 1103515245 + 12345) >> 16) & 0x7FFF
            whoosh = (noise / 16384.0 - 1.0) * 0.12 * env
            sample = int((blade + ring + whoosh) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_chicken(self) -> pygame.mixer.Sound:
        """Rubber chicken — air-through-rubber-hole physics.
        Sharp high gasp → brief squealing peak → long breathy dying yell.
        3.0s.  Mostly flowing air noise; resonant pitch is secondary."""
        rate = 22050
        n    = int(rate * 3.0)
        buf  = array.array("h")
        ph   = 0.0
        lp1  = 0.0   # 1st-order noise lowpass (bright hiss layer)
        lp2  = 0.0   # 2nd-order noise lowpass (dull body-air layer)

        for i in range(n):
            pos = i / n

            # ── Pitch envelope ──────────────────────────────────────────────
            # 0–7%:   fast squeeze rise    180 → 720 Hz  (the gasp)
            # 7–16%:  held peak            ~720 Hz
            # 16–22%: pause / inflection   720 → 640 Hz  (slight dip)
            # 22–100% long dying fall      640 → 50 Hz   (the yell)
            if pos < 0.07:
                freq = 180.0 + 540.0 * (pos / 0.07) ** 0.75   # fast concave rise
            elif pos < 0.16:
                freq = 720.0
            elif pos < 0.22:
                freq = 720.0 - 80.0 * ((pos - 0.16) / 0.06)
            else:
                r    = (pos - 0.22) / 0.78
                freq = 640.0 * (1.0 - r * 0.922) ** 1.6       # 640 → 50 Hz
            freq = max(48.0, freq)

            # ── Amplitude envelope ──────────────────────────────────────────
            # Snap attack → full peak → pause dip → very slow dying fade
            if pos < 0.06:
                amp = (pos / 0.06) ** 0.45      # sqrt-ish = snappy onset
            elif pos < 0.16:
                amp = 1.0
            elif pos < 0.22:
                amp = 1.0 - 0.42 * ((pos - 0.16) / 0.06)      # 1.0→0.58
            else:
                r   = (pos - 0.22) / 0.78
                amp = 0.58 * (1.0 - r) ** 0.65  # still ~0.2 at 80% — slow bleed

            # ── Tonal reed component (minority) ────────────────────────────
            ph   = (ph + freq / rate) % 1.0
            tone  = math.sin(2 * math.pi * ph) * 0.55
            tone += math.sin(2 * math.pi * ph * 2.0) * 0.32   # honky 2nd harmonic
            tone += math.sin(2 * math.pi * ph * 3.0) * 0.13

            # ── Colored air noise (dominant component) ─────────────────────
            # Two-pole lowpass on white noise → sounds like rushing air/breath
            raw  = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            lp1  = lp1 * 0.62 + raw * 0.38    # ~3 kHz: bright hiss
            lp2  = lp2 * 0.87 + lp1 * 0.13   # ~400 Hz: dull body air
            air  = lp1 * 0.35 + lp2 * 0.65   # blend: mostly body air

            # Noise dominates at onset + tail (airy gasp/yell), less at peak
            if pos < 0.16:
                noise_w = 0.68
            elif pos < 0.22:
                noise_w = 0.60
            else:
                # Become almost pure breath by the very end
                noise_w = min(0.95, 0.62 + 0.33 * (pos - 0.22) / 0.78)
            tone_w = 1.0 - noise_w

            val    = tone * tone_w + air * noise_w
            val   *= amp
            # Soft rubber-fuzz saturation
            val    = math.tanh(val * 1.35) / 1.35
            sample = int(val * 0.50 * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_confetti_boom(self) -> pygame.mixer.Sound:
        """Comical pop-explosion with party horn and sparkle."""
        rate = 22050
        n = int(rate * 0.3)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.2 * min(1.0, pos * 15)
            # Deep boom
            boom = math.sin(2 * math.pi * (100 - 60 * pos) * t) * 0.3
            boom2 = math.sin(2 * math.pi * 60 * t) * 0.15 * max(0, 1 - pos * 4)
            # Party horn: rising nasal tone
            horn = math.sin(2 * math.pi * (300 + 500 * pos) * t) * 0.12
            horn += math.sin(2 * math.pi * (300 + 500 * pos) * 3 * t) * 0.05  # nasal overtone
            # Crackle noise burst
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            crackle = (noise / 16384.0 - 1.0) * 0.2 * max(0, 1 - pos * 2.5)
            # Sparkle tail
            sparkle = 0.0
            if pos > 0.4:
                sp_env = (1.0 - (pos - 0.4) / 0.6)
                sparkle = math.sin(2 * math.pi * 2000 * t) * 0.04 * sp_env
            sample = int((boom + boom2 + horn + crackle + sparkle) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_parry(self) -> pygame.mixer.Sound:
        """Satisfying metallic clang with bright ring-out."""
        rate = 22050
        n = int(rate * 0.25)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.5 * min(1.0, pos * 30)
            # Metal impact cluster
            impact = math.sin(2 * math.pi * 300 * t) * 0.2 * max(0, 1 - pos * 8)
            # Bright metallic ring harmonics
            ring1 = math.sin(2 * math.pi * 1200 * t) * 0.2
            ring2 = math.sin(2 * math.pi * 1800 * t) * 0.12
            ring3 = math.sin(2 * math.pi * 2400 * t) * 0.06
            # Noise transient
            noise = (((i * 17 + 5) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.1 * max(0, 1 - pos * 6)
            sample = int((impact + ring1 + ring2 + ring3 + n_val) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_wheel_tick(self) -> pygame.mixer.Sound:
        """Short click for wheel segment passing pointer."""
        return self._tone(2400, 20, volume=0.12, wave="square")

    def _make_wheel_stop(self) -> pygame.mixer.Sound:
        """Triumphant bell ding with rich harmonics."""
        rate = 22050
        n = int(rate * 0.5)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos ** 0.6) * min(1.0, pos * 20)
            # Rich bell chord: A5, E6, A6
            val = math.sin(2 * math.pi * 880 * t) * 0.3
            val += math.sin(2 * math.pi * 1320 * t) * 0.2
            val += math.sin(2 * math.pi * 1760 * t) * 0.12
            val += math.sin(2 * math.pi * 2640 * t) * 0.06
            # Sparkle tail
            if pos > 0.3:
                sp = math.sin(2 * math.pi * 3520 * t) * 0.03 * (1 - pos)
                val += sp
            sample = int(val * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_chest_open(self) -> pygame.mixer.Sound:
        """Creaky chest with wooden groan and magical chime."""
        rate = 22050
        n = int(rate * 0.6)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = min(1.0, pos * 4) * (1.0 - max(0, pos - 0.8) / 0.2)
            # Wooden creak — FM synthesis
            creak_freq = 200 + 500 * pos + 80 * math.sin(pos * 15)
            creak = math.sin(2 * math.pi * creak_freq * t + math.sin(t * 400) * 2) * 0.2
            # Low groan
            groan = math.sin(2 * math.pi * 80 * t) * 0.1 * max(0, 1 - pos * 3)
            # Noise texture
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            n_val = noise * 0.1 * env
            # Magical chime bloom
            chime = 0.0
            if pos > 0.5:
                c_env = min(1.0, (pos - 0.5) / 0.15) * max(0, 1 - (pos - 0.65) / 0.35)
                chime = (math.sin(2 * math.pi * 1047 * t) * 0.25 +
                         math.sin(2 * math.pi * 1568 * t) * 0.12 +
                         math.sin(2 * math.pi * 2093 * t) * 0.06) * c_env
            sample = int((creak + groan + n_val + chime) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_chest_fanfare(self) -> pygame.mixer.Sound:
        """Brass DU-DU-DUHHHHNN boss-chest jackpot fanfare — three punchy hits then a held swell."""
        rate = 22050
        buf = array.array("h")

        def brass_hit(freq: float, dur_s: float, amp: float = 0.7) -> list:
            """Single brass stab at freq for dur_s seconds."""
            n = int(rate * dur_s)
            out = []
            for i in range(n):
                t = i / rate
                pos = i / n
                # Fast attack, quick decay
                env = min(1.0, pos * 30) * math.exp(-pos * 5)
                # Saw + harmonics = brass timbre
                val = (2.0 * (t * freq % 1.0) - 1.0) * 0.35
                val += math.sin(2 * math.pi * freq * t) * 0.30
                val += math.sin(2 * math.pi * freq * 2 * t) * 0.18
                val += math.sin(2 * math.pi * freq * 3 * t) * 0.10
                val += math.sin(2 * math.pi * freq * 4 * t) * 0.05
                out.append(int(val * amp * env * 32767))
            return out

        def brass_swell(freq: float, dur_s: float) -> list:
            """Sustained brass swell with slight vibrato and reverb tail."""
            n = int(rate * dur_s)
            out = []
            for i in range(n):
                t = i / rate
                pos = i / n
                attack = min(1.0, pos * 10)
                release = max(0.0, 1.0 - max(0.0, pos - 0.6) / 0.4)
                env = attack * release
                vibrato = 1.0 + 0.008 * math.sin(2 * math.pi * 5.5 * t)
                val = (2.0 * (t * freq * vibrato % 1.0) - 1.0) * 0.28
                val += math.sin(2 * math.pi * freq * vibrato * t) * 0.32
                val += math.sin(2 * math.pi * freq * 2 * vibrato * t) * 0.16
                val += math.sin(2 * math.pi * freq * 3 * vibrato * t) * 0.08
                # Low sub-bass thump under the swell
                val += math.sin(2 * math.pi * (freq / 2) * t) * 0.12 * max(0, 1 - pos * 3)
                out.append(int(val * env * 32767))
            return out

        # DU (220 Hz) — 0.13s, gap 0.04s
        # DU (277 Hz) — 0.13s, gap 0.04s
        # DUHHHHNN (330 Hz) — 0.80s sustained swell
        gap = [0] * int(rate * 0.04)
        segments = (brass_hit(220, 0.13) + gap +
                    brass_hit(277, 0.13) + gap +
                    brass_hit(330, 0.10) +
                    brass_swell(330, 0.80))
        for s in segments:
            buf.append(max(-32768, min(32767, s)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_shield_block(self) -> pygame.mixer.Sound:
        """Heavy shield impact with resonant ring."""
        rate = 22050
        n = int(rate * 0.2)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.2 * min(1.0, pos * 25)
            # Deep shield thud
            thud = math.sin(2 * math.pi * 150 * t) * 0.25 * max(0, 1 - pos * 5)
            # Metallic ring
            ring = math.sin(2 * math.pi * 600 * t) * 0.2
            ring += math.sin(2 * math.pi * 1500 * t) * 0.12
            ring += math.sin(2 * math.pi * 3000 * t) * 0.06
            # Impact noise
            noise = (((i * 19 + 11) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.1 * max(0, 1 - pos * 4)
            sample = int((thud + ring + n_val) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_enemy_death(self) -> pygame.mixer.Sound:
        """Satisfying electronic death — descending saw with crunch."""
        rate = 22050
        n = int(rate * 0.25)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.3 * min(1.0, pos * 15)
            freq = 500 - 380 * pos
            # Descending saw
            saw = (2.0 * (t * freq % 1.0) - 1.0) * 0.25
            # Sub thud
            thud = math.sin(2 * math.pi * 70 * t) * 0.15 * max(0, 1 - pos * 4)
            # Noise crunch
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            crunch = noise * 0.18 * max(0, 1 - pos * 2.5)
            sample = int((saw + thud + crunch) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_boss_death(self) -> pygame.mixer.Sound:
        """Heavy metallic explosion with deep reverb — boss defeated."""
        rate = 22050
        n = int(rate * 0.6)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 1.1 * min(1.0, pos * 10)
            # Deep sub boom
            sub = math.sin(2 * math.pi * 55 * t) * 0.35 * max(0, 1 - pos * 2.0)
            # Mid impact hit
            mid_env = max(0, 1 - pos * 3.5) ** 1.5
            mid = math.sin(2 * math.pi * 140 * t) * 0.25 * mid_env
            # Descending metallic sweep
            freq = 800 - 700 * min(1.0, pos * 3)
            sweep = (2.0 * (t * freq % 1.0) - 1.0) * 0.15 * max(0, 1 - pos * 2.2)
            # Noise explosion burst
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            burst = noise * 0.22 * max(0, 1 - pos * 1.8)
            sample = int((sub + mid + sweep + burst) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_big_boss_death(self) -> pygame.mixer.Sound:
        """Massive layered explosion — sub-bass shockwave for big boss defeat."""
        rate = 22050
        n = int(rate * 1.2)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 0.85 * min(1.0, pos * 8)
            # Sub-bass earthquake
            sub = math.sin(2 * math.pi * 38 * t) * 0.38 * max(0, 1 - pos * 1.3)
            # Second sub layer for depth
            sub2 = math.sin(2 * math.pi * 62 * t) * 0.28 * max(0, 1 - pos * 1.6)
            # Deep boom impact
            boom_env = max(0, 1 - pos * 2.5) ** 1.2
            boom = math.sin(2 * math.pi * 110 * t) * 0.25 * boom_env
            # Wide noise roar
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            noise2 = (((i * 22695477 + 1) >> 15) & 0x7FFF) / 16384.0 - 1.0
            roar = (noise * 0.15 + noise2 * 0.12) * max(0, 1 - pos * 0.9)
            # High harmonic ring — diminishing
            ring = math.sin(2 * math.pi * 320 * t) * 0.08 * max(0, 1 - pos * 2.0)
            sample = int((sub + sub2 + boom + roar + ring) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_player_death(self) -> pygame.mixer.Sound:
        """Dramatic descending wail + noise swell — player defeated."""
        rate = 22050
        n = int(rate * 1.5)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = (1.0 - pos) ** 0.9 * min(1.0, pos * 5)
            # Descending mournful tone
            freq = 440 * (1.0 - pos * 0.65)
            tone = math.sin(2 * math.pi * freq * t) * 0.3
            # Detuned lower harmonic
            freq2 = freq * 0.75
            tone2 = math.sin(2 * math.pi * freq2 * t) * 0.18
            # Noise swell rising then fading
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            swell_env = math.sin(math.pi * min(1.0, pos * 1.6)) * max(0, 1 - pos * 0.7)
            swell = noise * 0.14 * swell_env
            # Sub low rumble at start
            sub = math.sin(2 * math.pi * 48 * t) * 0.2 * max(0, 1 - pos * 3.5)
            sample = int((tone + tone2 + swell + sub) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_charge_whoosh(self) -> pygame.mixer.Sound:
        """Aggressive rising whoosh with rumble."""
        rate = 22050
        n = int(rate * 0.35)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = math.sin(math.pi * pos) * min(1.0, pos * 5)
            # Heavy wind noise
            noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
            wind = noise * 0.25
            # Rising tonal sweep
            freq = 250 + 900 * pos
            tone = math.sin(2 * math.pi * freq * t) * 0.15
            # Low rumble
            rumble = math.sin(2 * math.pi * 50 * t) * 0.1 * (1 - pos)
            sample = int((wind + tone + rumble) * env * 32767)
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

    def _make_dog_bark(self) -> pygame.mixer.Sound:
        """Robotic bark — sharp metallic yap with distortion."""
        rate = 22050
        n = int(rate * 0.15)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            if pos < 0.05:
                env = pos / 0.05
            elif pos < 0.3:
                env = 1.0
            else:
                env = max(0, (1.0 - (pos - 0.3) / 0.7) ** 2)
            freq = 350 + 200 * math.sin(pos * math.pi * 2)
            wave = math.sin(2 * math.pi * freq * t)
            # Clip for metallic distortion
            wave = max(-0.6, min(0.6, wave * 1.5))
            # Add buzz overtone
            buzz = math.sin(2 * math.pi * freq * 3 * t) * 0.15
            noise = (((i * 13 + 7) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.08
            sample = int((wave * 0.35 + buzz + n_val) * env * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    def _make_dog_growl(self) -> pygame.mixer.Sound:
        """Low mechanical growl — rumbling with servo whine."""
        rate = 22050
        n = int(rate * 0.4)
        buf = array.array("h")
        for i in range(n):
            t = i / rate
            pos = i / n
            env = min(1.0, pos * 5) * max(0, 1.0 - (pos - 0.6) / 0.4) if pos > 0.6 else min(1.0, pos * 5)
            # Low rumble
            rumble = math.sin(2 * math.pi * 65 * t) * 0.3
            rumble2 = math.sin(2 * math.pi * 72 * t) * 0.2
            # Servo whine
            whine = math.sin(2 * math.pi * (800 + 200 * math.sin(t * 10)) * t) * 0.06
            noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
            n_val = (noise / 16384.0 - 1.0) * 0.1
            sample = int((rumble + rumble2 + whine + n_val) * env * 0.5 * 32767)
            buf.append(max(-32768, min(32767, sample)))
        return pygame.mixer.Sound(buffer=buf)

    # ------------------------------------------------------------------
    # 8-bit background music
    # ------------------------------------------------------------------

    # 8-bit background music
    # ------------------------------------------------------------------

    def _generate_boss_music(self):
        """Generate intense boss combat tracks per zone — cached separately."""
        import os
        import pickle
        from src.settings import DATA_DIR
        _cache_dir = os.path.join(DATA_DIR, '.cache')
        _cache_file = os.path.join(_cache_dir, 'boss_music_v2.pkl')
        if os.path.exists(_cache_file):
            try:
                with open(_cache_file, 'rb') as _f:
                    _cached = pickle.load(_f)
                for _zone, _raw_bytes in _cached.items():
                    self._boss_music[_zone] = pygame.mixer.Sound(buffer=_raw_bytes)
                return
            except Exception:
                pass
        rate = 22050
        _raw: dict = {}

        # ================================================================
        # WASTELAND BOSS — Military march: heavy saw bass + war drums
        # D minor pentatonic, BPM 168, aggressive and relentless
        # ================================================================
        # Wasteland — tuned down a fifth, slower BPM, less distortion
        bpm_w = 148
        spb_w = int(rate * 60.0 / bpm_w)
        bars_w = 16
        beats_w = bars_w * 4
        # A minor riff (D minor transposed down a fifth): A1=55, E2=82, G2=98, A2=110, C3=131, E3=165
        bass_riff = [55, 55, 82, 55, 98, 55, 110, 82,
                     55, 82, 98, 110, 82, 55, 55, 82,
                     110, 110, 98, 82, 55, 55, 82, 98,
                     55, 110, 82, 55, 98, 110, 82, 55]
        # Lead arp down a fifth: A3=220, C4=262, E4=330, G4=392, A4=440
        lead_riff = [220, 262, 330, 262, 220, 0, 330, 392,
                     262, 330, 392, 330, 262, 220, 0, 220,
                     330, 392, 440, 392, 330, 0, 262, 330,
                     392, 330, 262, 220, 330, 440, 392, 330]
        # Drums: 1=kick, 2=snare, 3=hat, 4=open hat, 0=rest
        drum_w = [1, 3, 2, 3, 1, 3, 2, 4, 1, 3, 2, 3, 1, 2, 1, 2]
        buf_w = array.array("h")
        for bi in range(beats_w):
            bf = bass_riff[bi % len(bass_riff)]
            lf = lead_riff[bi % len(lead_riff)]
            dr = drum_w[bi % len(drum_w)]
            for i in range(spb_w):
                t = i / rate
                pos = i / spb_w
                # Warm saw bass — lighter distortion
                bphase = (t * bf) % 1.0
                bsaw = 2.0 * bphase - 1.0
                # Soft clip instead of hard (less harsh)
                bsaw = math.tanh(bsaw * 1.2) * 0.85
                bass_v = bsaw * 0.12 * (1.0 - pos * 0.1)
                # Sub octave
                sub = math.sin(2 * math.pi * bf * 0.5 * t) * 0.07
                # Lead: soft triangle arpeggio
                lead_v = 0.0
                if lf > 0 and pos < 0.5:
                    lenv = (1.0 - pos / 0.5) ** 1.2
                    ltri_p = (t * lf) % 1.0
                    ltri = 4.0 * abs(ltri_p - 0.5) - 1.0
                    lead_v = ltri * 0.05 * lenv
                # Hard drum hits
                drum_v = 0.0
                if dr == 1 and pos < 0.18:
                    kick_f = 80 * (1 - pos / 0.18)
                    drum_v = math.sin(2 * math.pi * kick_f * t) * 0.22 * (1 - pos / 0.18)
                elif dr == 2 and pos < 0.12:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drum_v = noise * 0.20 * (1 - pos / 0.12)
                elif dr == 3 and pos < 0.04:
                    noise = (((i * 6364136223 + 1) >> 15) & 0x7FFF) / 16384.0 - 1.0
                    drum_v = noise * 0.08 * (1 - pos / 0.04)
                elif dr == 4 and pos < 0.10:
                    noise = (((i * 1664525 + 1013904223) >> 14) & 0x7FFF) / 16384.0 - 1.0
                    drum_v = noise * 0.10 * (1 - pos / 0.10)
                sample = int((bass_v + sub + lead_v + drum_v) * 32767)
                buf_w.append(max(-32768, min(32767, sample)))
        wasteland_boss = pygame.mixer.Sound(buffer=buf_w)
        self._boss_music["wasteland"] = wasteland_boss
        _raw["wasteland"] = bytes(buf_w)

        # ================================================================
        # CITY BOSS — Cyborg terror: glitchy industrial crush
        # C# minor, BPM 180, electronic dystopia
        # ================================================================
        # City — transposed down a fourth, BPM 160, detuned but less shrill
        bpm_c = 160
        spb_c = int(rate * 60.0 / bpm_c)
        beats_c = 64
        # G# minor (C# minor down a fourth): G#1=52, D#2=78, F#2=92, G#2=104, B2=123, D#3=156
        cbass = [52, 52, 78, 52, 92, 104, 78, 52,
                 78, 104, 123, 104, 78, 52, 0, 52,
                 104, 123, 156, 123, 104, 78, 52, 78,
                 52, 92, 104, 78, 52, 104, 123, 104]
        # Glitch lead down a fourth: G#3=208, B3=247, D#4=311, F#4=370, G#4=415
        clead = [208, 0, 247, 311, 208, 0, 370, 311,
                 247, 311, 370, 415, 311, 247, 0, 208,
                 311, 370, 415, 0, 311, 247, 208, 0,
                 370, 311, 247, 208, 311, 415, 370, 311]
        drum_c = [1, 3, 2, 1, 1, 3, 2, 3, 1, 3, 2, 1, 1, 2, 1, 3]
        buf_c = array.array("h")
        for bi in range(beats_c):
            bf = cbass[bi % len(cbass)]
            lf = clead[bi % len(clead)]
            dr = drum_c[bi % len(drum_c)]
            for i in range(spb_c):
                t = i / rate
                pos = i / spb_c
                # Smooth industrial bass
                bass_v = 0.0
                if bf > 0:
                    fm_mod = 1.0 + 0.03 * math.sin(2 * math.pi * 3 * t)
                    bphase = (t * bf * fm_mod) % 1.0
                    bsaw = math.tanh((2.0 * bphase - 1.0) * 1.1) * 0.9
                    bass_v = bsaw * 0.11 * (0.85 + 0.15 * (1 - pos))
                    bass_v += math.sin(2 * math.pi * bf * 0.5 * t) * 0.07
                # Glitch lead: detuned triangle (softer than square)
                lead_v = 0.0
                if lf > 0 and pos < 0.45:
                    lenv = (1.0 - pos / 0.45) ** 0.8
                    lt1_p = (t * lf) % 1.0
                    lt2_p = (t * lf * 1.010) % 1.0
                    lt1 = 4.0 * abs(lt1_p - 0.5) - 1.0
                    lt2 = 4.0 * abs(lt2_p - 0.5) - 1.0
                    lead_v = (lt1 * 0.035 + lt2 * 0.025) * lenv
                # Industrial percussion — punchy kick + hard snare + noise clicks
                drum_v = 0.0
                if dr == 1 and pos < 0.20:
                    kick_f = 90 * (1 - pos / 0.20)
                    drum_v = (math.sin(2 * math.pi * kick_f * t) * 0.26
                              * (1 - pos / 0.20) ** 1.3)
                elif dr == 2 and pos < 0.13:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drum_v = noise * 0.22 * (1 - pos / 0.13)
                elif dr == 3 and pos < 0.05:
                    noise = (((i * 6364136223 + 1) >> 15) & 0x7FFF) / 16384.0 - 1.0
                    drum_v = noise * 0.07 * (1 - pos / 0.05)
                # Glitch stutter noise bursts on offbeats
                glitch_v = 0.0
                if bi % 7 == 3 and 0.48 < pos < 0.52:
                    gn = (((i * 22695477 + 1) >> 14) & 0x7FFF) / 16384.0 - 1.0
                    glitch_v = gn * 0.07
                sample = int((bass_v + lead_v + drum_v + glitch_v) * 32767)
                buf_c.append(max(-32768, min(32767, sample)))
        city_boss = pygame.mixer.Sound(buffer=buf_c)
        self._boss_music["city"] = city_boss
        _raw["city"] = bytes(buf_c)

        # ================================================================
        # ABYSS BOSS — Cosmic horror: slow massive bass drops + chaos
        # Tritone/dissonant intervals. BPM 85, ominous and overwhelming.
        # ================================================================
        # Abyss — slower (BPM 72), transposed down an octave for deep rumble
        bpm_a = 72
        spb_a = int(rate * 60.0 / bpm_a)
        beats_a = 64
        # Down an octave from original: E0/1=41→21, Bb1→29, E1→41, Bb1→58, F#1→46, B0→31
        abass = [21, 21, 29, 21, 41, 29, 21, 41,
                 29, 41, 46, 41, 29, 21, 21, 29,
                 41, 41, 58, 41, 46, 29, 21, 41,
                 21, 29, 41, 46, 41, 29, 21, 21]
        # Lead down an octave: E3=165, Bb3=233, F#3=185, B2=124, C3=131
        alead = [165, 0, 233, 0, 185, 0, 165, 0,
                 124, 0, 131, 233, 165, 0, 0, 0,
                 233, 0, 185, 0, 165, 124, 0, 233,
                 185, 0, 165, 0, 124, 233, 165, 0]
        drum_a = [1, 0, 0, 2, 0, 0, 1, 0, 2, 0, 1, 0, 0, 2, 0, 1]
        buf_a = array.array("h")
        for bi in range(beats_a):
            bf = abass[bi % len(abass)]
            lf = alead[bi % len(alead)]
            dr = drum_a[bi % len(drum_a)]
            for i in range(spb_a):
                t = i / rate
                pos = i / spb_a
                # Deep sub bass — sine with overtones creates cosmic rumble
                bass_v = 0.0
                if bf > 0:
                    bass_v = math.sin(2 * math.pi * bf * t) * 0.20
                    bass_v += math.sin(2 * math.pi * bf * 2.0 * t) * 0.06
                    bass_v += math.sin(2 * math.pi * bf * 3.0 * t) * 0.03
                    bass_env = 0.7 + 0.3 * math.exp(-pos * 1.5)
                    bass_v *= bass_env
                # Choir/whistle: sine with slow tremolo — cosmic wail
                lead_v = 0.0
                if lf > 0 and pos < 0.8:
                    lenv = min(1.0, pos / 0.15) * (0.8 + 0.2 * math.sin(2 * math.pi * 2.5 * t))
                    if pos > 0.65:
                        lenv *= (0.8 - pos) / 0.15
                    choir = math.sin(2 * math.pi * lf * t) * 0.06
                    # Slight vibrato
                    choir += math.sin(2 * math.pi * lf * t + math.sin(2*math.pi*4*t)*0.2) * 0.025
                    lead_v = choir * lenv
                # Sparse heavy drums — massive kick, rare snare
                drum_v = 0.0
                if dr == 1 and pos < 0.30:
                    # Earth-shaking kick
                    kick_f = 55 * (1 - pos / 0.30) ** 2
                    drum_v = math.sin(2 * math.pi * kick_f * t) * 0.28 * (1 - pos / 0.30)
                elif dr == 2 and pos < 0.20:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drum_v = noise * 0.18 * (1 - pos / 0.20)
                # Cosmic noise texture — distant void hiss
                void_noise = (((i * 1103515245 + 12345 + bi * 1337) >> 16) & 0x7FFF) / 16384.0 - 1.0
                void_swell = 0.2 + 0.8 * (0.5 + 0.5 * math.sin(bi * 0.3 + t * 0.5))
                void_v = void_noise * 0.012 * void_swell
                # Chaos stab: random dissonant hit every ~8 beats
                chaos_v = 0.0
                if bi % 8 == 5 and pos < 0.08:
                    dissonant_f = 466 * (1.0 + pos * 0.3)
                    chaos_v = math.sin(2 * math.pi * dissonant_f * t) * 0.05 * (1 - pos / 0.08)
                sample = int((bass_v + lead_v + drum_v + void_v + chaos_v) * 32767)
                buf_a.append(max(-32768, min(32767, sample)))
        abyss_boss = pygame.mixer.Sound(buffer=buf_a)
        self._boss_music["abyss"] = abyss_boss
        _raw["abyss"] = bytes(buf_a)

        # Save cache
        try:
            import os as _os
            _os.makedirs(_cache_dir, exist_ok=True)
            with open(_cache_file, 'wb') as _f:
                import pickle as _pk
                _pk.dump(_raw, _f)
        except Exception:
            pass
        # Clean up old cache version
        import os as _os2
        _old = os.path.join(_cache_dir, 'boss_music_v1.pkl')
        if _os2.path.exists(_old):
            try:
                _os2.remove(_old)
            except Exception:
                pass

    def _generate_zone_music(self):
        """Generate ambient base + combat layers for each zone."""
        import os
        import pickle
        from src.settings import DATA_DIR
        _cache_dir = os.path.join(DATA_DIR, '.cache')
        _cache_file = os.path.join(_cache_dir, 'zone_music_v1.pkl')
        if os.path.exists(_cache_file):
            try:
                with open(_cache_file, 'rb') as _f:
                    _cached = pickle.load(_f)
                for _zone, (_bb, _cb) in _cached.items():
                    self._zone_music[_zone] = (
                        pygame.mixer.Sound(buffer=_bb),
                        pygame.mixer.Sound(buffer=_cb),
                    )
                self._bgm_base, self._bgm_combat = self._zone_music["wasteland"]
                self._current_music_zone = "wasteland"
                return
            except Exception:
                pass  # Cache corrupt or version mismatch — regenerate
        _raw: dict = {}
        rate = 22050

        # ================================================================
        # FOREST (wasteland) — warm instrumental woodsy beat
        # ================================================================
        bpm = 82
        beat_dur = 60.0 / bpm
        spb = int(rate * beat_dur)           # samples per beat
        bars = 16
        beats_per_bar = 4
        total_beats = bars * beats_per_bar   # 64 beats

        # G major pentatonic: G3=196, A3=220, B3=247, D4=294, E4=330
        # 64-beat flute melody — phrases with breathing room
        flute_mel = [
            196, 0,   220, 0,   294, 294, 0,   0,     # bar 1-2: G A  D D
            330, 0,   294, 0,   247, 0,   220, 0,     # bar 3-4: E D  B A
            196, 0,   0,   0,   220, 0,   247, 0,     # bar 5-6: G    A B
            294, 0,   330, 330, 294, 0,   0,   0,     # bar 7-8: D EE D
            220, 0,   196, 0,   0,   0,   294, 0,     # bar 9-10: A G  D
            330, 0,   330, 294, 247, 0,   0,   0,     # bar 11-12: E ED B
            196, 0,   220, 294, 330, 0,   294, 0,     # bar 13-14: G AD E D
            247, 0,   220, 0,   196, 0,   0,   0,     # bar 15-16: B A G
        ]
        # Bass notes (root movement) — one per 2 beats
        bass_notes = [
            98, 98, 110, 110, 73, 73, 82, 82,         # G2 G2 A2 A2 D2 D2 E2 E2
            98, 98, 82, 82, 73, 73, 98, 98,           # G2 G2 E2 E2 D2 D2 G2 G2
            110, 110, 98, 98, 82, 82, 73, 73,         # A2 A2 G2 G2 E2 E2 D2 D2
            98, 98, 110, 110, 82, 82, 98, 98,         # G2 G2 A2 A2 E2 E2 G2 G2
            73, 73, 98, 98, 110, 110, 82, 82,         # D2 D2 G2 G2 A2 A2 E2 E2
            98, 98, 73, 73, 82, 82, 110, 110,         # G2 G2 D2 D2 E2 E2 A2 A2
            98, 98, 98, 98, 73, 73, 82, 82,           # G2 G2 G2 G2 D2 D2 E2 E2
            110, 110, 82, 82, 98, 98, 98, 98,         # A2 A2 E2 E2 G2 G2 G2 G2
        ]
        # Drum pattern: 0=rest, 1=kick, 2=snare brush, 3=hat
        #               8th-note subdivision: 2 sub-beats per beat
        drum_pat = [1,3, 0,3, 2,3, 0,3,               # bar pattern A
                    1,3, 0,3, 2,3, 1,3,               # bar pattern B
                    1,3, 0,3, 2,3, 0,0,               # bar pattern C (breathing)
                    1,3, 1,3, 2,3, 0,3]               # bar pattern D
        # Bird chirp timings (beat indices where a chirp happens)
        chirp_beats = {5, 19, 37, 51, 14, 42, 28, 60}

        buf_base = array.array("h")
        for bi in range(total_beats):
            fm = flute_mel[bi % len(flute_mel)]
            bn = bass_notes[bi % len(bass_notes)]
            for i in range(spb):
                t = i / rate
                pos = i / spb    # 0..1 within beat

                # ── Warm bass pad (filtered triangle) ──
                bass_phase = (t * bn) % 1.0
                bass_tri = 4.0 * abs(bass_phase - 0.5) - 1.0
                # Gentle volume swell per beat
                bass_env = 0.8 + 0.2 * (1.0 - pos)
                bass_val = bass_tri * 0.04 * bass_env
                # Add sub-octave warmth
                sub_phase = (t * bn * 0.5) % 1.0
                bass_val += math.sin(2 * math.pi * sub_phase) * 0.02

                # ── Flute melody (sine + soft 2nd harmonic) ──
                flute_val = 0.0
                if fm > 0:
                    # Slow attack, long sustain, gentle release
                    if pos < 0.08:
                        fl_env = pos / 0.08
                    elif pos < 0.7:
                        fl_env = 1.0
                    else:
                        fl_env = (1.0 - (pos - 0.7) / 0.3) ** 1.5
                    fl_env *= 0.06
                    flute_val = math.sin(2 * math.pi * fm * t) * fl_env
                    flute_val += math.sin(2 * math.pi * fm * 2 * t) * fl_env * 0.15
                    # Gentle vibrato
                    vib = math.sin(2 * math.pi * 5.0 * t) * 0.003
                    flute_val += math.sin(2 * math.pi * fm * t + vib * 10) * fl_env * 0.1

                # ── Soft drums (8th note grid) ──
                drum_val = 0.0
                # Two sub-beats per beat
                sub = 0 if pos < 0.5 else 1
                sub_pos = (pos - sub * 0.5) / 0.5   # 0..1 within sub-beat
                d_idx = (bi % 16) * 2 + sub
                dr = drum_pat[d_idx % len(drum_pat)]

                if dr == 1 and sub_pos < 0.15:
                    # Kick: soft thump
                    kick_f = 65 * (1.0 - sub_pos / 0.15)
                    drum_val = math.sin(2 * math.pi * kick_f * t) * 0.10 * (1.0 - sub_pos / 0.15)
                elif dr == 2 and sub_pos < 0.08:
                    # Brush snare: filtered noise
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drum_val = noise * 0.04 * (1.0 - sub_pos / 0.08)
                elif dr == 3 and sub_pos < 0.03:
                    # Closed hat: very short noise tick
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drum_val = (noise / 16384.0 - 1.0) * 0.025 * (1.0 - sub_pos / 0.03)

                # ── Nature texture: gentle wind + occasional bird chirp ──
                wind_noise = (((i * 1103515245 + 12345 + bi * 997) >> 16) & 0x7FFF) / 16384.0 - 1.0
                wind_swell = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(bi * 0.12 + t * 0.2))
                wind = wind_noise * 0.008 * wind_swell

                chirp = 0.0
                if bi in chirp_beats and pos > 0.3 and pos < 0.5:
                    chirp_pos = (pos - 0.3) / 0.2
                    chirp_f = 1200 - 400 * chirp_pos
                    chirp = math.sin(2 * math.pi * chirp_f * t) * 0.03 * (1.0 - chirp_pos)

                sample = int((bass_val + flute_val + drum_val + wind + chirp) * 32767)
                buf_base.append(max(-32768, min(32767, sample)))

        forest_base = pygame.mixer.Sound(buffer=buf_base)

        # Forest combat: driving beat, more aggressive, same key
        bpm_c = 140
        beat_c = 60.0 / bpm_c
        spb_c = int(rate * beat_c)
        total_s = spb * total_beats
        ct = total_s // spb_c
        c_bass = [98, 98, 110, 110, 82, 82, 73, 73,
                  98, 98, 73, 73, 110, 110, 82, 82]
        c_arp = [392, 440, 494, 440, 392, 330, 392, 440,
                 494, 588, 494, 440, 392, 330, 294, 330]
        c_drums = [1, 3, 2, 3, 1, 3, 2, 3, 1, 2, 1, 2, 3, 1, 2, 1]
        buf_c = array.array("h")
        for bi in range(ct):
            bf = c_bass[bi % len(c_bass)]
            af = c_arp[bi % len(c_arp)]
            dr = c_drums[bi % len(c_drums)]
            for i in range(spb_c):
                t = i / rate
                pos = i / spb_c
                bas = (2.0 * ((t * bf) % 1.0) - 1.0) * 0.08 * (1 - pos * 0.15)
                arp_val = 0.0
                if pos < 0.3:
                    arp_env = 1.0 - pos / 0.3
                    arp_val = math.sin(2 * math.pi * af * t) * 0.05 * arp_env
                drm = 0.0
                if dr == 1 and pos < 0.15:
                    drm = math.sin(2 * math.pi * (100 * (1 - pos / 0.15)) * t) * 0.18 * (1 - pos / 0.15)
                elif dr == 2 and pos < 0.1:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.14 * (1 - pos / 0.1)
                elif dr == 3 and pos < 0.05:
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.05 * (1 - pos / 0.05)
                sample = int((bas + arp_val + drm) * 32767)
                buf_c.append(max(-32768, min(32767, sample)))
        while len(buf_c) < len(buf_base):
            buf_c.append(0)
        while len(buf_c) > len(buf_base):
            buf_c.pop()
        forest_combat = pygame.mixer.Sound(buffer=buf_c)
        self._zone_music["wasteland"] = (forest_base, forest_combat)
        _raw["wasteland"] = (bytes(buf_base), bytes(buf_c))

        # ================================================================
        # CITY — dark industrial ambient
        # ================================================================
        bpm_city = 78
        beat_dur = 60.0 / bpm_city
        spb = int(rate * beat_dur)
        total_beats_city = 64

        c_mel = [0, 0, 131, 0, 0, 139, 0, 0, 147, 0, 0, 0, 131, 0, 0, 0,
                 156, 0, 0, 0, 0, 147, 0, 0, 131, 0, 0, 139, 0, 0, 0, 0,
                 0, 0, 0, 147, 0, 0, 156, 0, 0, 0, 0, 147, 0, 139, 0, 0,
                 131, 0, 0, 0, 0, 0, 0, 0, 0, 139, 0, 131, 0, 0, 0, 0]
        city_drums = [1, 0, 3, 0, 2, 0, 3, 0,
                      1, 0, 3, 1, 2, 0, 3, 0,
                      1, 3, 0, 3, 2, 0, 0, 3,
                      1, 0, 3, 0, 2, 3, 1, 0]
        city_bass = [65, 65, 65, 65, 62, 62, 62, 62,
                     58, 58, 58, 58, 65, 65, 65, 65,
                     69, 69, 69, 69, 65, 65, 65, 65,
                     62, 62, 58, 58, 65, 65, 65, 65]

        buf_base = array.array("h")
        for bi in range(total_beats_city):
            mel = c_mel[bi % len(c_mel)]
            bn = city_bass[bi % len(city_bass)]
            for i in range(spb):
                t = i / rate
                pos = i / spb
                # Industrial drone
                drone = math.sin(2 * math.pi * bn * t) * 0.025
                drone += math.sin(2 * math.pi * bn * 1.005 * t) * 0.02
                # Rhythmic pulse (8th notes)
                sub = 0 if pos < 0.5 else 1
                sub_pos = (pos - sub * 0.5) / 0.5
                d_idx = (bi % 8) * 4 + sub * 2 + (0 if sub_pos < 0.5 else 1)
                dr = city_drums[d_idx % len(city_drums)]
                drm = 0.0
                if dr == 1 and sub_pos < 0.12:
                    drm = math.sin(2 * math.pi * (90 * (1 - sub_pos / 0.12)) * t) * 0.08 * (1 - sub_pos / 0.12)
                elif dr == 2 and sub_pos < 0.06:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.04 * (1 - sub_pos / 0.06)
                elif dr == 3 and sub_pos < 0.03:
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.02 * (1 - sub_pos / 0.03)
                # Melody
                mel_val = 0.0
                if mel > 0 and pos < 0.3:
                    mel_env = (1.0 - pos / 0.3) ** 2
                    sq = 1.0 if math.sin(2 * math.pi * mel * t) >= 0 else -1.0
                    mel_val = sq * 0.03 * mel_env
                # Atmo hum
                hum = math.sin(2 * math.pi * 60 * t) * 0.005
                sample = int((drone + drm + mel_val + hum) * 32767)
                buf_base.append(max(-32768, min(32767, sample)))
        city_base = pygame.mixer.Sound(buffer=buf_base)

        # City combat
        bpm_c = 155
        beat_c = 60.0 / bpm_c
        spb_c = int(rate * beat_c)
        total_s_city = spb * total_beats_city
        ct = total_s_city // spb_c
        cb_bass = [131, 131, 139, 139, 147, 147, 156, 156,
                   147, 147, 139, 139, 131, 131, 123, 123]
        cb_arp = [523, 554, 587, 554, 523, 494, 523, 554,
                  587, 622, 659, 622, 587, 554, 523, 494]
        cb_drums = [1, 2, 1, 3, 1, 2, 1, 2, 1, 3, 2, 3, 1, 2, 3, 1]
        buf_c = array.array("h")
        for bi in range(ct):
            bf = cb_bass[bi % len(cb_bass)]
            af = cb_arp[bi % len(cb_arp)]
            dr = cb_drums[bi % len(cb_drums)]
            for i in range(spb_c):
                t = i / rate
                pos = i / spb_c
                raw = (2.0 * ((t * bf) % 1.0) - 1.0)
                bas = max(-0.7, min(0.7, raw * 1.3)) * 0.08 * (1 - pos * 0.1)
                arp_val = 0.0
                if pos < 0.25:
                    ae = 1.0 - pos / 0.25
                    arp_val = (1.0 if math.sin(2 * math.pi * af * t) >= 0 else -1.0) * 0.04 * ae
                drm = 0.0
                if dr == 1 and pos < 0.12:
                    drm = math.sin(2 * math.pi * (110 * (1 - pos / 0.12)) * t) * 0.2 * (1 - pos / 0.12)
                elif dr == 2 and pos < 0.08:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.15 * (1 - pos / 0.08)
                elif dr == 3 and pos < 0.05:
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.06 * (1 - pos / 0.05)
                sample = int((bas + arp_val + drm) * 32767)
                buf_c.append(max(-32768, min(32767, sample)))
        while len(buf_c) < len(buf_base):
            buf_c.append(0)
        while len(buf_c) > len(buf_base):
            buf_c.pop()
        city_combat = pygame.mixer.Sound(buffer=buf_c)
        self._zone_music["city"] = (city_base, city_combat)
        _raw["city"] = (bytes(buf_base), bytes(buf_c))

        # ================================================================
        # ABYSS — Lovecraftian dissonant ambient
        # ================================================================
        bpm_abyss = 60
        beat_dur = 60.0 / bpm_abyss
        spb = int(rate * beat_dur)
        total_beats_abyss = 64

        a_mel = [0, 0, 0, 0, 0, 0, 185, 0, 0, 0, 0, 0, 0, 0, 131, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, 175, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 139, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 185,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 131, 0, 0, 0, 0, 0]
        abyss_drums = [1, 0, 0, 0, 0, 0, 2, 0,
                       0, 0, 0, 0, 1, 0, 0, 0,
                       0, 0, 2, 0, 0, 0, 0, 0,
                       1, 0, 0, 0, 0, 2, 0, 0]

        buf_base = array.array("h")
        for bi in range(total_beats_abyss):
            mel = a_mel[bi % len(a_mel)]
            for i in range(spb):
                t = i / rate
                pos = i / spb
                phase_shift = math.sin(bi * 0.2 + t * 0.3) * 0.5
                drone = math.sin(2 * math.pi * 40 * t + phase_shift) * 0.03
                drone += math.sin(2 * math.pi * 40.7 * t) * 0.025
                drone += math.sin(2 * math.pi * 57 * t) * 0.015
                # Sparse percussion
                sub = 0 if pos < 0.5 else 1
                sub_pos = (pos - sub * 0.5) / 0.5
                d_idx = (bi % 8) * 4 + sub * 2 + (0 if sub_pos < 0.5 else 1)
                dr = abyss_drums[d_idx % len(abyss_drums)]
                drm = 0.0
                if dr == 1 and sub_pos < 0.2:
                    drm = math.sin(2 * math.pi * (55 * (1 - sub_pos / 0.2)) * t) * 0.12 * (1 - sub_pos / 0.2)
                elif dr == 2 and sub_pos < 0.1:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.05 * (1 - sub_pos / 0.1)
                # Eerie texture
                whistle_f = 800 + 200 * math.sin(t * 0.7 + bi * 0.5)
                whistle = math.sin(2 * math.pi * whistle_f * t) * 0.004
                breath_env = 0.5 + 0.5 * math.sin(bi * 0.15 + t * 0.3)
                noise = (((i * 1103515245 + 12345 + bi * 1013) >> 16) & 0x7FFF) / 16384.0 - 1.0
                breath = noise * 0.008 * breath_env
                mel_val = 0.0
                if mel > 0:
                    if pos < 0.5:
                        mel_env = pos / 0.5 * (1.0 - pos / 0.5) * 2.0
                    else:
                        mel_env = (1.0 - (pos - 0.5) / 0.5) ** 3
                    mel_val = math.sin(2 * math.pi * mel * t) * 0.03 * mel_env
                    mel_val += math.sin(2 * math.pi * mel * 1.5 * t) * 0.01 * mel_env
                sample = int((drone + drm + whistle + breath + mel_val) * 32767)
                buf_base.append(max(-32768, min(32767, sample)))
        abyss_base = pygame.mixer.Sound(buffer=buf_base)

        # Abyss combat
        bpm_c = 140
        beat_c = 60.0 / bpm_c
        spb_c = int(rate * beat_c)
        total_s_abyss = spb * total_beats_abyss
        ct = total_s_abyss // spb_c
        ab_bass = [82, 82, 78, 78, 82, 82, 87, 87,
                   78, 78, 82, 82, 73, 73, 78, 78]
        ab_arp = [330, 370, 392, 415, 330, 370, 440, 415,
                  392, 370, 330, 370, 415, 392, 370, 330]
        ab_drums = [1, 0, 2, 0, 1, 3, 0, 2, 1, 0, 3, 0, 1, 2, 3, 0]
        buf_c = array.array("h")
        for bi in range(ct):
            bf = ab_bass[bi % len(ab_bass)]
            af = ab_arp[bi % len(ab_arp)]
            dr = ab_drums[bi % len(ab_drums)]
            for i in range(spb_c):
                t = i / rate
                pos = i / spb_c
                s1 = (2.0 * ((t * bf) % 1.0) - 1.0)
                s2 = (2.0 * ((t * (bf * 1.02)) % 1.0) - 1.0)
                bas = (s1 * 0.06 + s2 * 0.04) * (1 - pos * 0.1)
                arp_val = 0.0
                if pos < 0.4:
                    ae = (1.0 - pos / 0.4) ** 1.5
                    arp_val = math.sin(2 * math.pi * af * t) * 0.04 * ae
                    arp_val += math.sin(2 * math.pi * af * 1.5 * t) * 0.015 * ae
                drm = 0.0
                if dr == 1 and pos < 0.2:
                    drm = math.sin(2 * math.pi * (70 * (1 - pos / 0.2)) * t) * 0.18 * (1 - pos / 0.2)
                elif dr == 2 and pos < 0.15:
                    noise = (((i * 1103515245 + 12345) >> 16) & 0x7FFF) / 16384.0 - 1.0
                    drm = noise * 0.10 * (1 - pos / 0.15)
                elif dr == 3 and pos < 0.08:
                    noise = (((i * 7 + 3) * 1103515245 + 12345) >> 16) & 0x7FFF
                    drm = (noise / 16384.0 - 1.0) * 0.06 * (1 - pos / 0.08)
                sample = int((bas + arp_val + drm) * 32767)
                buf_c.append(max(-32768, min(32767, sample)))
        while len(buf_c) < len(buf_base):
            buf_c.append(0)
        while len(buf_c) > len(buf_base):
            buf_c.pop()
        abyss_combat = pygame.mixer.Sound(buffer=buf_c)
        self._zone_music["abyss"] = (abyss_base, abyss_combat)
        _raw["abyss"] = (bytes(buf_base), bytes(buf_c))

        # Save cache for fast future loads
        try:
            import os
            os.makedirs(_cache_dir, exist_ok=True)
            with open(_cache_file, 'wb') as _f:
                import pickle
                pickle.dump(_raw, _f)
        except Exception:
            pass

        # Default to wasteland (forest)
        self._bgm_base, self._bgm_combat = self._zone_music["wasteland"]
        self._current_music_zone = "wasteland"
