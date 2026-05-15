"""
sound.py — Reproduce efectos de sonido y música desde archivos de audio.
Archivos en assets/Audio/. Falla silenciosamente si no hay driver de audio.
"""

import math
import os
import struct

import pygame

_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "Audio")


class SoundManager:
    def __init__(self):
        self._sonidos: dict = {}
        self._activo = False
        self._muted  = False
        self._disparo_cooldown = 0

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._cargar_todos()
            self._activo = True
        except Exception:
            pass

    def toggle_mute(self) -> bool:
        """Alterna mute on/off. Retorna True si quedó muteado."""
        self._muted = not self._muted
        if self._activo:
            vol = 0.0 if self._muted else 0.35
            try:
                pygame.mixer.music.set_volume(vol)
            except Exception:
                pass
        return self._muted

    def is_muted(self) -> bool:
        return self._muted

    def _generar_pew(self, freq_inicio=800, freq_fin=200, duracion_ms=80):
        """Barrido descendente de frecuencia: sonido 'pew' arcade clásico."""
        sample_rate = 22050
        n_muestras  = int(sample_rate * duracion_ms / 1000)
        muestras    = []
        fase        = 0.0
        for i in range(n_muestras):
            progreso = i / max(1, n_muestras - 1)
            freq     = freq_inicio + (freq_fin - freq_inicio) * progreso
            amplitud = int(32767 * 0.55 * (1.0 - progreso * 0.7))
            muestra  = max(-32768, min(32767, int(amplitud * math.sin(fase))))
            muestras.append(struct.pack("<h", muestra))
            fase += 2.0 * math.pi * freq / sample_rate
        return pygame.mixer.Sound(buffer=b"".join(muestras))

    def _cargar(self, nombre_archivo):
        """Carga un archivo de sonido. Retorna None si falla."""
        ruta = os.path.join(_AUDIO_DIR, nombre_archivo)
        try:
            return pygame.mixer.Sound(ruta)
        except Exception:
            print(f"[sound] No se pudo cargar: {nombre_archivo}")
            return None

    def _cargar_todos(self):
        # Disparo: pew arcade generado programáticamente (800→200 Hz en 80 ms)
        self._sonidos["disparo"]    = self._generar_pew(800, 200, 80)
        self._sonidos["disparo_p2"] = self._generar_pew(900, 250, 70)

        self._sonidos["explosion"]        = self._cargar("explosion.mp3")
        self._sonidos["explosion_grande"] = self._cargar("explosion_grande.mp3")
        self._sonidos["powerup"]          = self._cargar("powerup.mp3")
        self._sonidos["enemigo_muerto"]   = self._cargar("enemigo_muerto.mp3")
        self._sonidos["boss_alerta"]      = self._cargar("boss_alerta.mp3")
        self._sonidos["nivel_up"]         = self._cargar("nivel_up.mp3")
        self._sonidos["compra"]           = self._cargar("compra.wav")
        self._sonidos["sin_fondos"]       = self._cargar("sin_fondos.wav")
        self._sonidos["menu_click"]       = self._cargar("menu_click.wav")
        self._sonidos["oleada_completa"]  = self._cargar("oleada_completa.wav")

        _VOLUMENES = {
            "disparo":          0.15,
            "disparo_p2":       0.15,
            "explosion":        0.25,
            "explosion_grande": 0.5,
            "enemigo_muerto":   0.2,
            "boss_alerta":      0.6,
        }
        for nombre, sonido in self._sonidos.items():
            if sonido is not None:
                sonido.set_volume(_VOLUMENES.get(nombre, 0.5))

    def play(self, nombre: str):
        """Reproduce un efecto de sonido por nombre."""
        if not self._activo or self._muted:
            return
        if nombre in ("disparo", "disparo_p2"):
            if self._disparo_cooldown > 0:
                return
            self._disparo_cooldown = 6
        sonido = self._sonidos.get(nombre)
        if sonido:
            sonido.play()

    def update(self):
        """Llamar cada frame para cooldowns."""
        if self._disparo_cooldown > 0:
            self._disparo_cooldown -= 1

    # ── Música de fondo ──────────────────────────────────────────────────────

    def iniciar_musica(self, tipo: str = "juego"):
        """Inicia música de fondo en loop. tipo: 'juego', 'boss', 'menu'."""
        if not self._activo:
            return
        archivos = {
            "juego": "musica_juego.mp3",
            "boss":  "musica_boss.mp3",
            "menu":  "musica_menu.mp3",
        }
        archivo = archivos.get(tipo)
        if not archivo:
            return
        ruta = os.path.join(_AUDIO_DIR, archivo)
        try:
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def detener_musica(self):
        if not self._activo:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def pausar_musica(self):
        if not self._activo:
            return
        try:
            pygame.mixer.music.pause()
        except Exception:
            pass

    def reanudar_musica(self):
        if not self._activo:
            return
        try:
            pygame.mixer.music.unpause()
        except Exception:
            pass
