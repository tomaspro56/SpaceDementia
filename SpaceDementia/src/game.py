import math
import random

import pygame

import asset_loader
from background import Background
from boss import Boss
from bullet import Bullet
import config
from config import WHITE
from enemy import (EnemigoNormal, EnemigoAgil,
                   EnemigoRafaga, EnemigoApuntador, EnemigoKamikaze)
from explosion import Explosion
from tienda import Tienda
from obstaculo import (AgujeronNegro, ZonaInterferencia,
                       LluviaMeteoros, PulsoEMP,
                       generar_campo_asteroides)
from player import Player
from sound import SoundManager
from worlds import obtener_mundo

# ── Constantes de disparo del jugador ────────────────────────────────────────
_MAX_BALAS      = 5
_SHOOT_COOLDOWN = 8

# ── Formaciones disponibles ───────────────────────────────────────────────────
_FORMACIONES = ["aleatoria", "linea", "v_invertida", "pinza"]

# ── Textos de aviso de eventos ────────────────────────────────────────────────
_AVISOS = {
    "asteroides":    "LLUVIA DE ASTEROIDES",
    "agujero":       "ANOMALIA GRAVITATORIA",
    "interferencia": "INTERFERENCIA DETECTADA",
    "gravedad":      "INVERSION GRAVITACIONAL",
    "meteoros":      "LLUVIA DE METEOROS",
    "emp":           "PULSO EMP",
}


class Game:
    """
    Controlador principal del juego.

    Estados (self.estado):
        "transicion"  — pantalla MUNDO X · NIVEL Y por 60 frames
        "jugando"     — gameplay activo
        "completado"  — nivel completado, 90 frames antes de avanzar
        "game_over"   — sin vidas, espera input
        "victoria"    — todos los mundos terminados

    Retorna "menu" o "quit" desde run().
    """

    def __init__(self, screen, modo_2j: bool = False):
        self.screen  = screen
        self.modo_2j = modo_2j

        # ── Progresión ───────────────────────────────────────────────────────
        self.mundo_id = 1
        self.nivel    = 1
        self.config   = obtener_mundo(1)

        # ── Estado ───────────────────────────────────────────────────────────
        self.estado       = "transicion"
        self.estado_timer = 60

        # ── Jugadores ────────────────────────────────────────────────────────
        self.player1 = Player(150, config.HEIGHT // 3,     20, 10, 3, tema=self.config, jugador_id=1)
        self.player2 = (
            Player(150, config.HEIGHT * 2 // 3, 20, 10, 3, tema=self.config, jugador_id=2)
            if modo_2j else None
        )
        # Alias de compatibilidad: self.player apunta a player1
        self.player = self.player1

        # ── Listas de entidades ──────────────────────────────────────────────
        self.bullets          = []
        self.enemy_bullets    = []
        self.enemies          = []
        self.explosions       = []
        self.textos_flotantes  = []
        self.calaveras_flotantes = []  # {x, y, frame, max_frames}

        # ── Mejoras de tienda ─────────────────────────────────────────────────
        self._tienda      = None    # Instancia activa de Tienda
        self._tienda_turno = 1      # Qué jugador está comprando (1 o 2)
        self._bomba_flash  = 0      # Frames de flash blanco al usar mega bomba

        # ── Inversión gravitacional ────────────────────────────────────────────
        self.gravedad_invertida = False
        self.gravedad_timer     = 0

        # ── Boss ──────────────────────────────────────────────────────────────
        self.boss           = None
        self._alerta_timer  = 0

        # ── Contadores de kills ───────────────────────────────────────────────
        self.kills_actuales     = 0   # Reset por nivel (control de oleadas)
        self.enemigos_eliminados = 0  # Acumulado total para pantalla de Game Over

        # ── Tiempo de partida ─────────────────────────────────────────────────
        self._frames_jugados = 0

        # ── Selección en pantalla Game Over ──────────────────────────────────
        self._gameover_sel = 0  # 0 = REINTENTAR, 1 = MENU

        # ── Transición de nivel completado ────────────────────────────────────
        self._bonus_nivel     = 0   # Monedas extra mostradas en la transición
        self._completado_fade = 0   # Contador de fade-in (0→30 frames)

        # ── Sistema de oleadas ────────────────────────────────────────────────
        self.oleadas_objetivo    = self.config["oleadas_por_nivel"][0]
        self.oleada_num          = 0
        self._cola_oleada        = []
        self._spawn_timer        = 0
        self._en_descanso        = False
        self._descanso_timer     = 0
        self._texto_oleada_timer = 0

        # ── Obstáculos espaciales ────────────────────────────────────────────
        self.obstaculos       = []
        self._aviso_timer     = 0
        self._aviso_texto     = ""
        self._evento_pendiente = None

        # ── Pausa ─────────────────────────────────────────────────────────────
        self.paused             = False
        self._pausa_sel         = 0
        self._pausa_controles   = False
        self._mute_aviso_timer  = 0
        self._mute_aviso_texto  = ""

        # ── Audio ─────────────────────────────────────────────────────────────
        self.sound               = SoundManager()
        self._gameover_sonido_ok = True
        self.sound.iniciar_musica("juego")

        # ── Fondo ─────────────────────────────────────────────────────────────
        self.background = Background(1, tema=self.config)

        # ── Screen shake ──────────────────────────────────────────────────────
        self._surface            = pygame.Surface((config.WIDTH, config.HEIGHT))
        self._shake_timer        = 0
        self._shake_intensidad   = 0
        self._shake_frames_total = 1

        # ── Partículas visuales ───────────────────────────────────────────────
        self._propulsor        = []
        self._impact_particles = []

        # ── Flash rojo al recibir daño ────────────────────────────────────────
        self._damage_flash = 0

        # ── Trails de jugadores ───────────────────────────────────────────────
        self._player1_trail  = []
        self._player2_trail  = []
        self._jugador1_movio = False
        self._jugador2_movio = False

        # ── Combo ─────────────────────────────────────────────────────────────
        self._combo       = 0   # Kills consecutivos sin recibir daño
        self._combo_timer = 0   # Frames hasta decaimiento (90 = 3s, luego 45 = 1.5s)

    # ================================================================ helpers

    def _lista_jugadores(self) -> list:
        """Todos los jugadores del juego (vivos o muertos)."""
        if self.modo_2j and self.player2 is not None:
            return [self.player1, self.player2]
        return [self.player1]

    def _jugadores_vivos(self) -> list:
        return [p for p in self._lista_jugadores() if p.life > 0]

    def _todos_muertos(self) -> bool:
        return all(p.life <= 0 for p in self._lista_jugadores())

    def _get_player(self, jugador_id: int) -> Player:
        if jugador_id == 2 and self.player2 is not None:
            return self.player2
        return self.player1

    # ================================================================== loop

    def run(self):
        """Loop principal. Retorna "menu" o "quit"."""
        resultado = "menu"
        clock     = pygame.time.Clock()
        running   = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    resultado = "quit"
                    running   = False
                    break
                if event.type == pygame.KEYDOWN:
                    r = self._manejar_tecla(event.key)
                    if r:
                        resultado = r
                        running   = False
                        break

            if running:
                # ── Input continuo ───────────────────────────────────────────
                if not self.paused and self.estado in ("jugando", "boss"):
                    keys = pygame.key.get_pressed()

                    # Jugador 1: flechas + espacio + B
                    if self.player1.life > 0:
                        mover1 = False
                        if keys[pygame.K_LEFT] and self.player1.x - self.player1.speed > self.player1.size:
                            self.player1.move("LEFT"); mover1 = True
                        elif keys[pygame.K_RIGHT] and self.player1.x + self.player1.speed < config.WIDTH * 0.55:
                            self.player1.move("RIGHT"); mover1 = True
                        k_arr = pygame.K_DOWN if self.gravedad_invertida else pygame.K_UP
                        k_aba = pygame.K_UP   if self.gravedad_invertida else pygame.K_DOWN
                        if keys[k_arr] and self.player1.y - self.player1.speed > self.player1.size:
                            self.player1.move("UP"); mover1 = True
                        elif keys[k_aba] and self.player1.y + self.player1.speed < config.HEIGHT - self.player1.size:
                            self.player1.move("DOWN"); mover1 = True

                        if keys[k_arr]:
                            self.player1.tilt = max(-1.0, self.player1.tilt - 0.15)
                        elif keys[k_aba]:
                            self.player1.tilt = min(1.0, self.player1.tilt + 0.15)
                        else:
                            self.player1.tilt *= 0.85

                        # Limitar posición dentro de pantalla
                        self.player1.x = max(50.0, min(float(config.WIDTH - 50), self.player1.x))
                        self.player1.y = max(50.0, min(float(config.HEIGHT - 50), self.player1.y))

                        if mover1:
                            self._player1_trail.append((int(self.player1.x), int(self.player1.y)))
                            if len(self._player1_trail) > 4:
                                self._player1_trail.pop(0)
                        self._jugador1_movio = mover1

                        if keys[pygame.K_SPACE]:
                            self.disparar_jugador(self.player1)

                    # Jugador 2: WASD + F + G
                    if self.modo_2j and self.player2 and self.player2.life > 0:
                        mover2 = False
                        if keys[pygame.K_a] and self.player2.x - self.player2.speed > self.player2.size:
                            self.player2.move("LEFT"); mover2 = True
                        elif keys[pygame.K_d] and self.player2.x + self.player2.speed < config.WIDTH * 0.55:
                            self.player2.move("RIGHT"); mover2 = True
                        k_w = pygame.K_s if self.gravedad_invertida else pygame.K_w
                        k_s = pygame.K_w if self.gravedad_invertida else pygame.K_s
                        if keys[k_w] and self.player2.y - self.player2.speed > self.player2.size:
                            self.player2.move("UP"); mover2 = True
                        elif keys[k_s] and self.player2.y + self.player2.speed < config.HEIGHT - self.player2.size:
                            self.player2.move("DOWN"); mover2 = True

                        if keys[k_w]:
                            self.player2.tilt = max(-1.0, self.player2.tilt - 0.15)
                        elif keys[k_s]:
                            self.player2.tilt = min(1.0, self.player2.tilt + 0.15)
                        else:
                            self.player2.tilt *= 0.85

                        # Limitar posición dentro de pantalla
                        self.player2.x = max(50.0, min(float(config.WIDTH - 50), self.player2.x))
                        self.player2.y = max(50.0, min(float(config.HEIGHT - 50), self.player2.y))

                        if mover2:
                            self._player2_trail.append((int(self.player2.x), int(self.player2.y)))
                            if len(self._player2_trail) > 4:
                                self._player2_trail.pop(0)
                        self._jugador2_movio = mover2

                        if keys[pygame.K_f]:
                            self.disparar_jugador(self.player2)

                if not self.paused:
                    self._update()
                self._draw()
                pygame.display.flip()
                clock.tick(30)

        return resultado

    # ----------------------------------------------------------------- teclas

    def _manejar_tecla(self, key):
        if self.estado == "game_over":
            if key in (pygame.K_UP, pygame.K_DOWN):
                self._gameover_sel = 1 - self._gameover_sel
            elif key == pygame.K_RETURN:
                return "reintentar" if self._gameover_sel == 0 else "menu"
            elif key in (pygame.K_ESCAPE, pygame.K_q):
                return "quit"
        elif self.estado == "victoria":
            if key == pygame.K_RETURN:
                return "menu"
            if key in (pygame.K_ESCAPE, pygame.K_q):
                return "quit"
        elif self.estado in ("jugando", "boss"):
            if self.paused:
                r = self._manejar_tecla_pausa(key)
                if r:
                    return r
            else:
                if key in (pygame.K_ESCAPE, pygame.K_q):
                    return "quit"
                if key == pygame.K_p:
                    self.paused    = True
                    self._pausa_sel = 0
                    self.sound.pausar_musica()
                if key == pygame.K_m:
                    muteado = self.sound.toggle_mute()
                    self._mute_aviso_texto = "AUDIO OFF" if muteado else "AUDIO ON"
                    self._mute_aviso_timer = 60
                if key == pygame.K_b:
                    self._usar_mega_bomba(self.player1)
                if key == pygame.K_g and self.modo_2j and self.player2:
                    self._usar_mega_bomba(self.player2)
        elif self.estado == "tienda":
            if self._tienda:
                self._tienda.handle_key(key)
        return None

    # ---------------------------------------------------- pausa helpers

    _PAUSA_OPCIONES = ["REANUDAR", "CONTROLES", "MUTEAR", "MENU PRINCIPAL", "SALIR"]

    def _manejar_tecla_pausa(self, key):
        """Maneja input mientras el menú de pausa está activo. Retorna resultado o None."""
        if self._pausa_controles:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._pausa_controles = False
            return None

        n = len(self._PAUSA_OPCIONES)
        if key == pygame.K_UP:
            self._pausa_sel = (self._pausa_sel - 1) % n
        elif key == pygame.K_DOWN:
            self._pausa_sel = (self._pausa_sel + 1) % n
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self._ejecutar_pausa_opcion()
        elif key in (pygame.K_p, pygame.K_ESCAPE):
            self.paused = False
            self.sound.reanudar_musica()
        return None

    def _ejecutar_pausa_opcion(self):
        opcion = self._PAUSA_OPCIONES[self._pausa_sel]
        if opcion == "REANUDAR":
            self.paused = False
            self.sound.reanudar_musica()
        elif opcion == "CONTROLES":
            self._pausa_controles = True
        elif opcion == "MUTEAR":
            self.sound.toggle_mute()
        elif opcion == "MENU PRINCIPAL":
            self.paused = False
            return "menu"
        elif opcion == "SALIR":
            return "quit"
        return None

    # ================================================================ update

    def _update(self):
        self.sound.update()

        if self.estado in ("jugando", "boss") and not self.paused:
            self._frames_jugados += 1

        if self.estado == "transicion":
            self.estado_timer -= 1
            self.background.update()
            if self.estado_timer <= 0:
                self.estado = "jugando"
                self._iniciar_oleada()

        elif self.estado == "jugando":
            self._update_jugando()

        elif self.estado == "completado":
            self.estado_timer -= 1
            if self._completado_fade < 30:
                self._completado_fade += 1
            self._update_explosiones()
            self._update_textos()
            self.background.update()
            if self.estado_timer <= 0:
                if self.nivel < 4:
                    self._tienda_turno = 1
                    self._tienda = Tienda(self, jugador_num=1)
                    self.estado  = "tienda"
                    self.sound.pausar_musica()
                else:
                    self._avanzar()

        elif self.estado == "tienda":
            self.background.update()
            if self._tienda and not self._tienda.activa:
                self._tienda = None
                # En 2j: después del turno 1, abrir tienda del jugador 2
                if self.modo_2j and self._tienda_turno == 1:
                    self._tienda_turno = 2
                    self._tienda = Tienda(self, jugador_num=2)
                else:
                    self._tienda_turno = 1
                    self.sound.reanudar_musica()
                    self._avanzar()

        elif self.estado == "alerta":
            self._alerta_timer -= 1
            self.background.update()
            self._update_explosiones()
            self._update_textos()
            if self._alerta_timer <= 0:
                self.sound.detener_musica()
                self.sound.iniciar_musica("boss")
                self.boss   = Boss(float(config.WIDTH + 100), float(config.HEIGHT // 2), tema=self.config)
                self.estado = "boss"

        elif self.estado == "boss":
            if not self.paused:
                self._update_boss()

        else:
            self.background.update()

    def _update_jugando(self):
        for p in self._lista_jugadores():
            p.update()

        # Propulsor continuo para jugadores vivos
        if self.player1.life > 0:
            self._emitir_propulsor(self.player1, 3 if self._jugador1_movio else 1)
        if self.modo_2j and self.player2 and self.player2.life > 0:
            self._emitir_propulsor(self.player2, 3 if self._jugador2_movio else 1)
        self._jugador1_movio = False
        self._jugador2_movio = False

        # Balas del jugador
        for b in self.bullets[:]:
            b.move()
            if b.x > config.WIDTH or b.x < 0 or b.y < 0 or b.y > config.HEIGHT:
                self.bullets.remove(b)

        # Oleadas
        self._update_oleadas()

        # Enemigos
        self._update_enemies()
        self._disparar_enemies()

        # Balas enemigas → jugadores
        for b in self.enemy_bullets[:]:
            b.move()
            if b.x < 0 or b.x > config.WIDTH or b.y < 0 or b.y > config.HEIGHT:
                self.enemy_bullets.remove(b)
                continue
            for p in self._jugadores_vivos():
                if self.check_collision(b, p):
                    if b in self.enemy_bullets:
                        self.enemy_bullets.remove(b)
                    self._daño_jugador(p)
                    break

        # Obstáculos
        self._update_obstaculos()

        # Efectos visuales
        self._update_explosiones()
        self._update_textos()
        self._update_impact_particles()
        self._update_propulsor()
        if self._damage_flash > 0:
            self._damage_flash -= 1
        if self.gravedad_timer > 0:
            self.gravedad_timer -= 1
            if self.gravedad_timer <= 0:
                self.gravedad_invertida = False
        if self._aviso_timer > 0:
            self._aviso_timer -= 1
            if self._aviso_timer == 0 and self._evento_pendiente:
                self._spawn_evento(self._evento_pendiente)
                self._evento_pendiente = None

        if self._combo > 0 and self._combo_timer > 0:
            self._combo_timer -= 1
            if self._combo_timer <= 0:
                self._combo -= 1
                self._combo_timer = 45 if self._combo > 0 else 0

        self.background.update()

        # Fin de nivel: todas las oleadas completadas
        if self.oleada_num >= self.oleadas_objetivo and not self._cola_oleada and not self.enemies:
            if self.nivel == 5:
                self.enemies.clear()
                self.enemy_bullets.clear()
                self._alerta_timer = 60
                self.estado        = "alerta"
                self.sound.play("boss_alerta")
            else:
                self._bonus_nivel     = 10
                self._completado_fade = 0
                for p in self._jugadores_vivos():
                    p.monedas += self._bonus_nivel
                self.estado       = "completado"
                self.estado_timer = 60
            self.sound.play("nivel_up")
            return

        if self._todos_muertos() and self._gameover_sonido_ok:
            self.sound.detener_musica()
            self._gameover_sonido_ok = False
            self.estado        = "game_over"
            self._gameover_sel = 0

    # ========================================================== obstáculos

    def _update_obstaculos(self):
        """Actualiza todos los obstáculos y evalúa colisiones con jugadores."""
        # Restaurar velocidades antes de que ZonaInterferencia pueda reducirlas
        for p in self._jugadores_vivos():
            tiene_vel = "VELOCIDAD" in p.powerups_temporales
            p.speed = p.velocidad_base * 2 if tiene_vel else p.velocidad_base

        for obs in self.obstaculos[:]:
            obs.update()
            if obs.is_dead():
                self.obstaculos.remove(obs)
                continue
            dañados = obs.afectar_jugadores(self._jugadores_vivos())
            for p in dañados:
                self._daño_jugador(p)
                if obs.causa_impacto_fisico:
                    self._iniciar_shake(4, 8)

    def _sortear_evento(self):
        """Retorna tipo de evento o None. Probabilidades por mundo/nivel."""
        r = random.random()

        if self.mundo_id == 1:
            if self.nivel < 2:
                return None
            if r < 0.25:
                return "asteroides"
            elif r < 0.40:
                return "meteoros"
            elif r < 0.60:
                return "gravedad"
            return None

        elif self.mundo_id == 2:
            if r < 0.25:
                return "asteroides"
            elif r < 0.40:
                return "meteoros"
            elif r < 0.55:
                return "agujero"
            elif r < 0.65:
                return "emp"
            elif r < 0.70:
                return "gravedad"
            return None

        else:   # Mundo 3+
            if r < 0.20:
                return "asteroides"
            elif r < 0.35:
                return "meteoros"
            elif r < 0.50:
                return "agujero"
            elif r < 0.60:
                return "emp"
            elif r < 0.70:
                return "interferencia"
            elif r < 0.80:
                return "gravedad"
            return None

    def _spawn_evento(self, tipo):
        if tipo == "asteroides":
            self.obstaculos.extend(generar_campo_asteroides())
        elif tipo == "agujero":
            self.obstaculos.append(AgujeronNegro())
        elif tipo == "interferencia":
            self.obstaculos.append(ZonaInterferencia())
        elif tipo == "gravedad":
            self.gravedad_invertida = True
            self.gravedad_timer     = 240
        elif tipo == "meteoros":
            self.obstaculos.append(LluviaMeteoros())
        elif tipo == "emp":
            self.obstaculos.append(PulsoEMP())

    # ====================================================== oleadas

    def _iniciar_oleada(self):
        """Genera la siguiente oleada con una formación aleatoria."""
        self.oleada_num          += 1
        self._texto_oleada_timer  = 50

        cfg   = self.config
        vel   = cfg["vel_enemigo_base"]
        tipos = list(cfg["tipos_oleada"])
        # En el nivel 1 del mundo 1, omitir kamikaze para no romper el "tutorial"
        if self.mundo_id == 1 and self.nivel == 1 and "kamikaze" in tipos:
            tipos.remove("kamikaze")
        n     = cfg["enemies_per_wave"]
        forma = random.choice(_FORMACIONES)

        self._cola_oleada = self._generar_formacion(forma, n, tipos, vel)
        self._spawn_timer = 12

    def _generar_formacion(self, forma, n, tipos, vel):
        """Devuelve lista [(y, tipo, speed)] según la formación elegida."""
        cola = []

        if forma == "linea":
            centro_y = random.randint(240, config.HEIGHT - 240)
            ys = [centro_y + (i - n // 2) * 70 for i in range(n)]

        elif forma == "v_invertida":
            cx = config.HEIGHT // 2
            offsets = [0, -90, 90, -180, 180, -270, 270][:n]
            ys = [cx + o for o in offsets]

        elif forma == "pinza":
            mitad  = n // 2
            ys_top = [random.randint(80, config.HEIGHT // 2 - 60) for _ in range(mitad)]
            ys_bot = [random.randint(config.HEIGHT // 2 + 60, config.HEIGHT - 80) for _ in range(n - mitad)]
            ys = []
            for i in range(max(len(ys_top), len(ys_bot))):
                if i < len(ys_top):
                    ys.append(ys_top[i])
                if i < len(ys_bot):
                    ys.append(ys_bot[i])
            ys = ys[:n]

        else:
            usados = []
            ys     = []
            for _ in range(n):
                y = self._elegir_y_separado(usados)
                ys.append(y)
                usados.append(y)

        for i, y in enumerate(ys):
            # DEBUG TEMPORAL: forzar 50% kamikaze si está en tipos
            if "kamikaze" in tipos and i % 2 == 0:
                tipo = "kamikaze"
            else:
                tipo = random.choice(tipos)
            speed = vel + (1.5 if tipo == "agil" else
                           0.8 if tipo == "rafaga" else
                           1.2 if tipo == "apuntador" else
                           0.5 if tipo == "kamikaze" else 0)
            cola.append((max(80, min(config.HEIGHT - 80, int(y))), tipo, speed))

        return cola

    def _elegir_y_separado(self, usados, min_sep=80):
        for _ in range(25):
            y = random.randint(80, config.HEIGHT - 80)
            if all(abs(y - u) >= min_sep for u in usados):
                return y
        return random.randint(80, config.HEIGHT - 80)

    def _update_oleadas(self):
        """Ciclo: spawn → esperar → descanso → posible evento → spawn."""
        if self._texto_oleada_timer > 0:
            self._texto_oleada_timer -= 1

        if self._en_descanso:
            self._descanso_timer -= 1
            if self._descanso_timer <= 0:
                self._en_descanso = False
                self._iniciar_oleada()
            return

        if self._cola_oleada:
            self._spawn_timer -= 1
            if self._spawn_timer <= 0:
                self._spawn_timer = 12
                y, tipo, speed = self._cola_oleada.pop(0)
                _CLASE_POR_TIPO = {
                    "normal":    EnemigoNormal,
                    "agil":      EnemigoAgil,
                    "rafaga":    EnemigoRafaga,
                    "apuntador": EnemigoApuntador,
                    "kamikaze":  EnemigoKamikaze,
                }
                _COLOR_POR_TIPO = {"normal": "r", "agil": "b", "rafaga": "g",
                                   "apuntador": "b", "kamikaze": "g"}
                ClaseEnemigo   = _CLASE_POR_TIPO.get(tipo, EnemigoNormal)
                e              = ClaseEnemigo(config.WIDTH + 30, y, 30, speed, tema=self.config)
                print(f"[SPAWN] mundo={self.mundo_id} nivel={self.nivel} tipo={tipo} clase={ClaseEnemigo.__name__}", flush=True)
                e.color_sprite = _COLOR_POR_TIPO.get(tipo, "r")

                if self.mundo_id >= 4 and isinstance(e, (EnemigoNormal, EnemigoRafaga)) and random.random() < 0.3:
                    e.vida = 2
                elif self.mundo_id == 3 and isinstance(e, EnemigoNormal) and random.random() < 0.15:
                    e.vida = 2

                self.enemies.append(e)
            return

        if self.enemies:
            return

        if self.oleada_num < self.oleadas_objetivo:
            self._en_descanso    = True
            self._descanso_timer = 75
            self.sound.play("oleada_completa")

            puede_evento = self.mundo_id >= 2 or (self.mundo_id == 1 and self.nivel >= 2)
            if puede_evento and not self._aviso_timer:
                evento = self._sortear_evento()
                if evento:
                    self._evento_pendiente = evento
                    self._aviso_timer      = 45
                    self._aviso_texto      = _AVISOS.get(evento, "")
                    self.sound.play("boss_alerta")

    # ====================================================== progresión

    def _iniciar_nivel(self):
        """Resetea estado del nivel sin tocar score/monedas/upgrades de tienda."""
        cfg = self.config
        self.kills_actuales  = 0
        self.oleadas_objetivo = cfg["oleadas_por_nivel"][self.nivel - 1]
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.explosions.clear()
        self.textos_flotantes.clear()
        self.calaveras_flotantes.clear()
        self._impact_particles.clear()
        self._propulsor.clear()
        self._player1_trail.clear()
        self._player2_trail.clear()
        self.obstaculos.clear()
        self._damage_flash      = 0
        self._jugador1_movio    = False
        self._jugador2_movio    = False
        self._aviso_timer       = 0
        self._aviso_texto       = ""
        self._evento_pendiente  = None
        self.oleada_num         = 0
        self._cola_oleada       = []
        self._spawn_timer       = 0
        self._en_descanso       = False
        self._descanso_timer    = 0
        self._texto_oleada_timer = 0
        self._gameover_sonido_ok = True
        self.boss               = None
        self._alerta_timer      = 0
        self.gravedad_invertida = False
        self.gravedad_timer     = 0
        # Limpiar EMP entre niveles
        for p in self._lista_jugadores():
            p.emp_activo = False
            p.emp_timer  = 0
        self.estado       = "transicion"
        self.estado_timer = 60

    def _avanzar(self):
        """Avanza al siguiente nivel o mundo."""
        if self.nivel < 5:
            self.nivel += 1
            self._iniciar_nivel()
        else:
            if self.mundo_id < 5:
                self.mundo_id += 1
                self.nivel     = 1
                self.config    = obtener_mundo(self.mundo_id)
                for p in self._lista_jugadores():
                    p.tema = self.config
                self.background = Background(1, tema=self.config)
                self._iniciar_nivel()
            else:
                self.estado = "victoria"

    def _daño_jugador(self, player: Player):
        """Aplica daño al jugador; consume escudo si existe."""
        if player.consumir_escudo():
            self._texto_flotante("ESCUDO!", int(player.x),
                                  int(player.y) - 35, (80, 200, 255))
            return
        self._combo       = 0
        self._combo_timer = 0
        player.life -= 1
        self.sound.play("daño")
        self._iniciar_shake(8, 15)
        self._damage_flash = 5
        if player.life <= 0:
            self.calaveras_flotantes.append({"x": int(player.x), "y": float(player.y), "frame": 0, "max_frames": 60})
            player.powerups.clear()
            player.powerups_temporales.clear()
            player.disparo_doble  = False
            player.disparo_plasma = False
            player._max_balas     = _MAX_BALAS

    # ====================================================== enemigos

    def _update_enemies(self):
        for enemy in self.enemies[:]:
            if enemy not in self.enemies:
                continue
            enemy.move()

            if enemy.x < -enemy.size:
                self.enemies.remove(enemy)
                continue

            # Bala jugador → enemigo
            golpeado = False
            for bullet in self.bullets[:]:
                if self.check_collision(bullet, enemy):
                    golpeado = True
                    self._crear_impacto(bullet.x, bullet.y)
                    shooter = self._get_player(bullet.jugador_id)
                    if not bullet.es_mega and bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if enemy.recibir_daño(bullet.daño):
                        shooter.score            += enemy.PUNTOS
                        self.kills_actuales      += 1
                        self.enemigos_eliminados += 1
                        self._combo              += 1
                        self._combo_timer         = 90
                        ganadas = enemy.MONEDAS + max(0, self._combo - 1)
                        shooter.monedas          += ganadas
                        self._texto_flotante(
                            f"+{ganadas}", int(enemy.x), int(enemy.y) - 20,
                            (255, 220, 0)
                        )
                        self.explosions.append(Explosion(enemy.x, enemy.y, "mediana"))
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        self.sound.play("enemigo_muerto")
                    break

            # Colisión directa enemigo → jugadores
            if not golpeado and enemy in self.enemies:
                for p in self._jugadores_vivos():
                    if self.check_attack(enemy, p):
                        self.enemies.remove(enemy)
                        self._daño_jugador(p)
                        break

    def _disparar_enemies(self):
        """Delega el disparo a cada enemigo mediante polimorfismo."""
        vivos = self._jugadores_vivos()
        if not vivos:
            return
        for enemy in self.enemies:
            if enemy.x > config.WIDTH - 100 or enemy._frame < 30:
                continue
            self.enemy_bullets.extend(enemy.shoot_frame(vivos))

    # ====================================================== boss

    def _update_boss(self):
        """Loop completo de la pelea de boss."""
        for p in self._lista_jugadores():
            p.update()

        if self.player1.life > 0:
            self._emitir_propulsor(self.player1, 3 if self._jugador1_movio else 1)
        if self.modo_2j and self.player2 and self.player2.life > 0:
            self._emitir_propulsor(self.player2, 3 if self._jugador2_movio else 1)
        self._jugador1_movio = False
        self._jugador2_movio = False

        # Balas del jugador
        for b in self.bullets[:]:
            b.move()
            if b.x > config.WIDTH or b.x < 0 or b.y < 0 or b.y > config.HEIGHT:
                self.bullets.remove(b)

        if self.boss:
            self.boss.update()

            for bala in self.boss.disparos_pendientes:
                self.enemy_bullets.append(bala)
            self.boss.disparos_pendientes.clear()

            while self.boss.refuerzos_pendientes > 0:
                self.boss.refuerzos_pendientes -= 1
                y = random.randint(100, config.HEIGHT - 100)
                e = EnemigoNormal(config.WIDTH + 30, y, 30, 4, tema=self.config)
                e.color_sprite = asset_loader.COLOR_ENEMIGO_POR_MUNDO.get(self.mundo_id, "r")
                self.enemies.append(e)

            for bullet in self.bullets[:]:
                if self.check_collision(bullet, self.boss):
                    self._crear_impacto(bullet.x, bullet.y)
                    shooter = self._get_player(bullet.jugador_id)
                    if not bullet.es_mega and bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if self.boss.recibir_daño(bullet.daño):
                        self._boss_muerto(shooter)
                        return
                    break

            for p in self._jugadores_vivos():
                if self.check_attack(self.boss, p):
                    self._daño_jugador(p)

        # Balas enemigas → jugadores
        for b in self.enemy_bullets[:]:
            b.move()
            if b.x < 0 or b.x > config.WIDTH or b.y < 0 or b.y > config.HEIGHT:
                self.enemy_bullets.remove(b)
                continue
            for p in self._jugadores_vivos():
                if self.check_collision(b, p):
                    if b in self.enemy_bullets:
                        self.enemy_bullets.remove(b)
                    self._daño_jugador(p)
                    break

        self._update_enemies()
        self._disparar_enemies()
        self._update_explosiones()
        self._update_textos()
        self._update_impact_particles()
        self._update_propulsor()
        if self._damage_flash > 0:
            self._damage_flash -= 1
        if self.gravedad_timer > 0:
            self.gravedad_timer -= 1
            if self.gravedad_timer <= 0:
                self.gravedad_invertida = False

        if self._combo > 0 and self._combo_timer > 0:
            self._combo_timer -= 1
            if self._combo_timer <= 0:
                self._combo -= 1
                self._combo_timer = 45 if self._combo > 0 else 0

        self.background.update()

        if self._todos_muertos() and self._gameover_sonido_ok:
            self.sound.detener_musica()
            self._gameover_sonido_ok = False
            self.estado        = "game_over"
            self._gameover_sel = 0

    def _boss_muerto(self, shooter: Player):
        """Maneja la muerte del boss: explosiones, recompensa y transición."""
        for _ in range(6):
            ox = random.randint(-self.boss.size // 2, self.boss.size // 2)
            oy = random.randint(-self.boss.size // 2, self.boss.size // 2)
            self.explosions.append(
                Explosion(self.boss.x + ox, self.boss.y + oy, "grande")
            )
        self.enemigos_eliminados += 1
        shooter.score   += 500
        shooter.monedas += 100
        self._texto_flotante("+100", int(self.boss.x), int(self.boss.y) - 50,
                             (255, 220, 0))
        self._texto_flotante("BOSS ELIMINADO", int(self.boss.x),
                             int(self.boss.y) - 90, (255, 100, 50))
        self._iniciar_shake(14, 30)
        self._bomba_flash     = 6
        self.boss             = None
        self.sound.play("explosion_grande")
        self.sound.detener_musica()
        self.sound.iniciar_musica("juego")
        self._bonus_nivel     = 0
        self._completado_fade = 0
        self.estado           = "completado"
        self.estado_timer     = 150

    # ====================================================== disparo jugador

    def disparar_jugador(self, player: Player):
        """Respeta cooldown, límite de balas y bloqueo por EMP."""
        if player._shoot_cooldown > 0:
            return
        if player.emp_activo:
            return
        player_bullets = sum(
            1 for b in self.bullets
            if b.jugador_id == player.jugador_id and not b.es_mega
        )
        if player_bullets >= player._max_balas:
            return
        daño_bala = 2 if player.disparo_plasma else 1
        ox = player.x + player.size
        oy = player.y - 12 if player.disparo_doble else player.y
        self.bullets.append(
            Bullet(ox, oy, 20, "RIGHT", tema=self.config,
                   es_proton=player.disparo_plasma, daño=daño_bala,
                   jugador_id=player.jugador_id)
        )
        if player.disparo_doble:
            pb2 = sum(
                1 for b in self.bullets
                if b.jugador_id == player.jugador_id and not b.es_mega
            )
            if pb2 < player._max_balas:
                self.bullets.append(
                    Bullet(ox, player.y + 12, 20, "RIGHT", tema=self.config,
                           es_proton=player.disparo_plasma, daño=daño_bala,
                           jugador_id=player.jugador_id)
                )
        player._shoot_cooldown = _SHOOT_COOLDOWN
        self.sound.play("disparo" if player.jugador_id == 1 else "disparo_p2")

    # ====================================================== colisiones

    def check_collision(self, obj1, obj2):
        def bounds(o):
            if hasattr(o, "size"):
                s = o.size
                return o.x - s // 2, o.x + s // 2, o.y - s // 2, o.y + s // 2
            return o.x, o.x + o.width, o.y - o.height // 2, o.y + o.height // 2
        x1l, x1r, y1t, y1b = bounds(obj1)
        x2l, x2r, y2t, y2b = bounds(obj2)
        return x1l < x2r and x1r > x2l and y1t < y2b and y1b > y2t

    def check_attack(self, enemy, player):
        el = enemy.x - enemy.size // 2 - player.size
        er = enemy.x + enemy.size // 2 + player.size
        et = enemy.y - enemy.size // 2 - player.size
        eb = enemy.y + enemy.size // 2 + player.size
        return el < player.x < er and et < player.y < eb

    # ====================================================== efectos visuales

    def _iniciar_shake(self, intensidad, frames):
        if intensidad >= self._shake_intensidad:
            self._shake_intensidad   = intensidad
            self._shake_frames_total = max(1, frames)
            self._shake_timer        = frames

    def _emitir_propulsor(self, player: Player, cantidad=1):
        tiene_vel  = "VELOCIDAD" in player.powerups_temporales
        color_base = (80, 180, 255) if tiene_vel else self.config.get("color_propulsor", (255, 120, 0))
        max_vida   = 16 if tiene_vel else 12

        px, py = int(player.x), int(player.y)
        s      = player.size
        for _ in range(cantidad):
            vel = random.uniform(1.5, 3.5) * (1.5 if tiene_vel else 1.0)
            self._propulsor.append([
                float(px - s + random.randint(-4, 4)),
                float(py + random.randint(-s // 3, s // 3)),
                -vel,
                random.uniform(-1.0, 1.0),
                max_vida, max_vida, color_base,
            ])

    def _update_propulsor(self):
        for p in self._propulsor[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self._propulsor.remove(p)

    def _crear_impacto(self, x, y):
        """4 partículas blancas en el punto de impacto bala→enemigo."""
        for _ in range(4):
            ang = random.uniform(0, 2 * math.pi)
            vel = random.uniform(1.5, 4.0)
            self._impact_particles.append([
                float(x), float(y),
                math.cos(ang) * vel,
                math.sin(ang) * vel,
                8, 8,
            ])

    def _update_impact_particles(self):
        for p in self._impact_particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self._impact_particles.remove(p)

    def _usar_mega_bomba(self, player: Player):
        """Destruye todos los enemigos en pantalla y lanza explosiones grandes."""
        if player.mega_bombas <= 0 or player.life <= 0:
            return
        player.mega_bombas -= 1
        for e in self.enemies[:]:
            player.score             += e.PUNTOS
            self.kills_actuales      += 1
            self.enemigos_eliminados += 1
            ganadas = e.MONEDAS
            player.monedas      += ganadas
            self.explosions.append(Explosion(e.x, e.y, "grande"))
        self.enemies.clear()
        self.enemy_bullets.clear()
        self._bomba_flash = 10
        self.sound.play("explosion")

    def _update_explosiones(self):
        for exp in self.explosions[:]:
            exp.update()
            if exp.is_dead():
                self.explosions.remove(exp)

    def _texto_flotante(self, texto, x, y, color):
        self.textos_flotantes.append({
            "texto": texto, "x": x, "y": float(y),
            "color": color, "frame": 0, "max_frames": 55,
        })

    def _update_textos(self):
        for tf in self.textos_flotantes[:]:
            tf["frame"] += 1
            if tf["frame"] >= tf["max_frames"]:
                self.textos_flotantes.remove(tf)
        for cf in self.calaveras_flotantes[:]:
            cf["frame"] += 1
            if cf["frame"] >= cf["max_frames"]:
                self.calaveras_flotantes.remove(cf)

    # ====================================================== dibujo

    def _draw(self):
        surf          = self._surface
        pantalla_real = self.screen
        self.screen   = surf

        self.background.draw(surf)

        if self.estado in ("jugando", "completado", "tienda", "alerta", "boss"):
            for obs in self.obstaculos:
                obs.draw(surf)
            # Trails y propulsores
            self._draw_trail(surf)
            self._draw_propulsor(surf)
            # Jugadores vivos
            if self.player1.life > 0:
                self.player1.draw(surf)
            if self.modo_2j and self.player2 and self.player2.life > 0:
                self.player2.draw(surf)
            for b in self.bullets:
                b.draw(surf)
            for e in self.enemies:
                e.draw(surf)
            for b in self.enemy_bullets:
                b.draw(surf)
            for exp in self.explosions:
                exp.draw(surf)
            if self.estado == "boss" and self.boss:
                self.boss.draw(surf)
            self._draw_impact_particles(surf)
            self._draw_damage_flash(surf)
            self._draw_bomba_flash(surf)
            self._draw_gravedad(surf)

        self._draw_hud()
        if self.estado == "boss" and self.boss:
            self.boss._dibujar_barra_vida(self.screen)
        self._draw_textos_flotantes()
        self._draw_overlay()
        self._draw_vignette(surf)

        self.screen = pantalla_real
        if self._shake_timer > 0:
            ratio             = self._shake_timer / self._shake_frames_total
            intensidad_actual = max(1, int(self._shake_intensidad * ratio))
            sx = random.randint(-intensidad_actual, intensidad_actual)
            sy = random.randint(-intensidad_actual, intensidad_actual)
            self._shake_timer -= 1
            pantalla_real.fill((0, 0, 0))
        else:
            sx = sy = 0
        pantalla_real.blit(surf, (sx, sy))
        if self.estado == "tienda" and self._tienda:
            self._tienda.draw(pantalla_real)

    # ---------------------------------------------------------------- efectos

    def _draw_propulsor(self, surf):
        for p in self._propulsor:
            ratio = p[4] / max(1, p[5])
            r     = max(1, int(4 * ratio))
            c     = p[6]
            color = (max(0, int(c[0] * ratio)),
                     max(0, int(c[1] * ratio)),
                     max(0, int(c[2] * ratio)))
            pygame.draw.circle(surf, color, (int(p[0]), int(p[1])), r)

    def _draw_impact_particles(self, surf):
        for p in self._impact_particles:
            ratio = p[4] / max(1, p[5])
            r     = max(1, int(3 * ratio))
            s     = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, int(ratio * 255)),
                               (r + 1, r + 1), r)
            surf.blit(s, (int(p[0]) - r - 1, int(p[1]) - r - 1))

    def _draw_trail(self, surf):
        cb1 = self.config.get("color_jugador", (80, 160, 255))
        self._draw_player_trail(surf, self._player1_trail, cb1, self.player1.size)
        if self.modo_2j and self.player2 and self.player2.life > 0:
            self._draw_player_trail(surf, self._player2_trail, (255, 80, 80), self.player2.size)

    def _draw_player_trail(self, surf, trail, color_base, size):
        n = len(trail)
        if n == 0:
            return
        for i, (tx, ty) in enumerate(trail):
            ratio = (i + 1) / (n + 1)
            r     = max(1, int(size * 0.4 * ratio))
            alpha = int(ratio * 55)
            srf   = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            c     = tuple(int(ch * ratio) for ch in color_base)
            pygame.draw.circle(srf, (*c, alpha), (r + 1, r + 1), r)
            surf.blit(srf, (tx - r - 1, ty - r - 1))

    def _draw_damage_flash(self, surf):
        if self._damage_flash <= 0:
            return
        alpha   = int((self._damage_flash / 5) * 80)
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((220, 20, 20, alpha))
        surf.blit(overlay, (0, 0))

    def _draw_bomba_flash(self, surf):
        if self._bomba_flash <= 0:
            return
        self._bomba_flash -= 1
        alpha   = int((self._bomba_flash / 10) * 220)
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, alpha))
        surf.blit(overlay, (0, 0))

    def _draw_gravedad(self, surf):
        if not self.gravedad_invertida:
            return
        pulso = abs(math.sin(self.gravedad_timer * 0.08))
        alpha = int(55 + pulso * 110)
        borde = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(borde, (160, 0, 220, alpha), (0, 0, config.WIDTH, config.HEIGHT), 20)
        surf.blit(borde, (0, 0))
        if self.gravedad_timer > 180:
            self._draw_overlay_centrado("! GRAVEDAD INVERTIDA !",
                                        config.HEIGHT // 2 + 80, 34, (200, 80, 255))

    def _draw_vignette(self, surf):
        g   = 110
        s_h = pygame.Surface((config.WIDTH, g), pygame.SRCALPHA)
        s_h.fill((0, 0, 0, 85))
        s_v = pygame.Surface((g, config.HEIGHT), pygame.SRCALPHA)
        s_v.fill((0, 0, 0, 85))
        surf.blit(s_h, (0, 0))
        surf.blit(s_h, (0, config.HEIGHT - g))
        surf.blit(s_v, (0, 0))
        surf.blit(s_v, (config.WIDTH - g, 0))

    # ------------------------------------------------------------------ HUD

    def _draw_hud(self):
        color = self.config.get("color_hud", WHITE)
        if self.modo_2j:
            self._draw_hud_2j(color)
        else:
            self._draw_hud_1j(color)

    def _draw_hud_1j(self, color):
        """HUD original: score izquierda, vidas derecha, centro mundo/nivel."""
        self._draw_text(f"Puntos: {self.player1.score}", (12, 12), 28, color)
        self._draw_powerups_player(self.player1, color, y_inicio=52, lado="izq")

        self._draw_centro_hud(color)

        # Corazones dibujados con primitivas, alineados a la derecha
        xv = config.WIDTH - 12
        for _ in range(max(0, self.player1.life)):
            self._dibujar_corazon(self.screen, xv - 16, 20, tam=20, color=(220, 60, 80))
            xv -= 34

        self._draw_monedas_player(self.player1, xr=True, y_base=48)
        self._draw_mega_bombas_player(self.player1, xr=True, y_base=90, tecla="B")

        if self._texto_oleada_timer > 0 and self.estado == "jugando":
            alpha = min(255, self._texto_oleada_timer * 7)
            self._draw_overlay_centrado(f"OLEADA  {self.oleada_num}",
                                        config.HEIGHT // 2 - 35, 38,
                                        (255, 220, 80), alpha)

        self._draw_aviso()
        self._draw_combo()
        self._draw_mute_aviso()

        if self.paused:
            self._draw_pausa_menu()

    def _draw_hud_2j(self, color):
        """HUD para 2 jugadores: J1 izquierda, J2 derecha, centro común."""
        c_j1 = (80, 160, 255)
        c_j2 = (255, 80, 80)

        # ── Jugador 1 (izquierda) ─────────────────────────────────────────
        if self.player1.life > 0:
            self._draw_text(f"P1   Pts: {self.player1.score}", (12, 12), 26, c_j1)
            xh1 = 12
            for _ in range(self.player1.life):
                self._dibujar_corazon(self.screen, xh1 + 10, 48, tam=18, color=(220, 60, 80))
                xh1 += 28
            self._draw_monedas_player(self.player1, xr=False, y_base=72)
            self._draw_mega_bombas_player(self.player1, xr=False, y_base=102, tecla="B")
            self._draw_powerups_player(self.player1, c_j1, y_inicio=132, lado="izq")
        else:
            self._draw_caido(lado="izq")

        # ── Jugador 2 (derecha) ───────────────────────────────────────────
        if self.player2.life > 0:
            self._draw_text_derecha(f"Pts: {self.player2.score}   P2", y=12, size=26,
                                    color=c_j2)
            xh2 = config.WIDTH - 12
            for _ in range(self.player2.life):
                self._dibujar_corazon(self.screen, xh2 - 10, 48, tam=18, color=(220, 60, 80))
                xh2 -= 28
            self._draw_monedas_player(self.player2, xr=True, y_base=72)
            self._draw_mega_bombas_player(self.player2, xr=True, y_base=102, tecla="G")
            self._draw_powerups_player(self.player2, c_j2, y_inicio=132, lado="der")
        else:
            self._draw_caido(lado="der")

        # ── Centro ────────────────────────────────────────────────────────
        self._draw_centro_hud(color)

        # EMP activo: avisar al jugador afectado
        for p in self._lista_jugadores():
            if p.emp_activo:
                label = f"J{p.jugador_id} EMP ({p.emp_timer // 30 + 1}s)"
                self._draw_overlay_centrado(label, config.HEIGHT // 2 + 80, 28, (50, 150, 255))

        if self._texto_oleada_timer > 0 and self.estado == "jugando":
            alpha = min(255, self._texto_oleada_timer * 7)
            self._draw_overlay_centrado(f"OLEADA  {self.oleada_num}",
                                        config.HEIGHT // 2 - 35, 38,
                                        (255, 220, 80), alpha)

        self._draw_aviso()
        self._draw_combo()
        self._draw_mute_aviso()

        if self.paused:
            self._draw_pausa_menu()

    def _draw_aviso(self):
        """Warning parpadeante en amarillo antes de cada anomalía."""
        if self._aviso_timer <= 0 or not self._aviso_texto:
            return
        # Parpadeo: 5 frames visible, 3 frames oscuro
        alpha = 255 if self._aviso_timer % 8 < 5 else 70

        font  = pygame.font.SysFont("monospace", 38, bold=True)
        texto = f"!! {self._aviso_texto} !!"
        surf  = font.render(texto, True, (255, 220, 0))
        surf.set_alpha(alpha)

        x  = config.WIDTH  // 2 - surf.get_width()  // 2
        y  = config.HEIGHT // 2 - surf.get_height() // 2 + 30
        bg = pygame.Surface((surf.get_width() + 24, surf.get_height() + 12), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 145))
        bg.set_alpha(alpha)
        self.screen.blit(bg, (x - 12, y - 6))
        self.screen.blit(surf, (x, y))

    def _draw_combo(self):
        """Contador de combo en la parte inferior central del HUD."""
        if self._combo < 2:
            return
        if self._combo <= 3:
            color = (200, 220, 255)
        elif self._combo <= 7:
            color = (255, 220, 0)
        else:
            color = (255, 80, 50)

        font  = pygame.font.SysFont("monospace", 32, bold=True)
        surf  = font.render(f"COMBO  x{self._combo}", True, color)
        x     = config.WIDTH  // 2 - surf.get_width() // 2
        y     = config.HEIGHT - 90
        self.screen.blit(surf, (x, y))

        bar_max_w = 80
        bar_w = int(bar_max_w * min(1.0, self._combo_timer / 90))
        ratio = self._combo_timer / 90 if self._combo_timer > 0 else 0.0
        if ratio > 0.6:
            bar_color = (50, 220, 80)
        elif ratio > 0.3:
            bar_color = (255, 200, 0)
        else:
            bar_color = (255, 60, 50)
        bx = config.WIDTH // 2 - bar_max_w // 2
        by = y + surf.get_height() + 4
        pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, bar_max_w, 5))
        if bar_w > 0:
            pygame.draw.rect(self.screen, bar_color, (bx, by, bar_w, 5))

    def _draw_mute_aviso(self):
        """Muestra brevemente 'AUDIO ON' o 'AUDIO OFF' al presionar M."""
        if self._mute_aviso_timer <= 0:
            return
        self._mute_aviso_timer -= 1
        alpha = min(255, self._mute_aviso_timer * 5)
        self._draw_overlay_centrado(self._mute_aviso_texto,
                                    config.HEIGHT // 2 - 30, 44, (255, 220, 80), alpha)

    def _draw_pausa_menu(self):
        """Dibuja el menú de pausa navigable o la pantalla de controles."""
        if self._pausa_controles:
            self._draw_controles_overlay()
            return

        # Fondo semitransparente
        velo = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        velo.fill((0, 0, 10, 160))
        self.screen.blit(velo, (0, 0))

        panel_w, panel_h = 750, 420
        px = config.WIDTH  // 2 - panel_w // 2
        py = config.HEIGHT // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((8, 12, 35, 230))
        pygame.draw.rect(panel, (80, 160, 255), (0, 0, panel_w, panel_h), 2)
        self.screen.blit(panel, (px, py))

        font_t = pygame.font.SysFont("monospace", 34, bold=True)
        font_o = pygame.font.SysFont("monospace", 28, bold=True)
        c_titulo = (80, 160, 255)
        c_sel    = (0, 255, 200)
        c_norm   = (160, 200, 255)

        st = font_t.render("PAUSA", True, c_titulo)
        self.screen.blit(st, (px + (panel_w - st.get_width()) // 2, py + 20))
        pygame.draw.line(self.screen, c_titulo,
                         (px + 30, py + 66), (px + panel_w - 30, py + 66), 1)

        # Etiqueta dinámica para mute
        muteado = self.sound.is_muted()
        etiquetas = list(self._PAUSA_OPCIONES)
        etiquetas[2] = "DESMUTEAR" if muteado else "MUTEAR"

        for i, opcion in enumerate(etiquetas):
            selec = (i == self._pausa_sel)
            color = c_sel if selec else c_norm
            surf  = font_o.render(opcion, True, color)
            y_op  = py + 90 + i * 55
            x_op  = px + (panel_w - surf.get_width()) // 2
            self.screen.blit(surf, (x_op, y_op))
            if selec:
                fl = font_o.render(">", True, c_sel)
                self.screen.blit(fl, (x_op - fl.get_width() - 14, y_op))

        font_h = pygame.font.SysFont("monospace", 16)
        lineas_hint = [
            "Flechas arriba/abajo:  Navegar",
            "ENTER:  Confirmar          ESC / P:  Reanudar",
        ]
        y_hint = py + panel_h - 52
        for linea in lineas_hint:
            s = font_h.render(linea, True, (80, 90, 110))
            self.screen.blit(s, (px + (panel_w - s.get_width()) // 2, y_hint))
            y_hint += 22

    def _draw_controles_overlay(self):
        """Panel con la tabla de controles (también accesible desde pausa)."""
        velo = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        velo.fill((0, 0, 10, 170))
        self.screen.blit(velo, (0, 0))

        panel_w, panel_h = 680, 480
        px = config.WIDTH  // 2 - panel_w // 2
        py = config.HEIGHT // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((8, 12, 35, 230))
        pygame.draw.rect(panel, (80, 160, 255), (0, 0, panel_w, panel_h), 2)
        self.screen.blit(panel, (px, py))

        font_t = pygame.font.SysFont("monospace", 30, bold=True)
        font_s = pygame.font.SysFont("monospace", 24, bold=True)
        font_n = pygame.font.SysFont("monospace", 22)
        c_titulo = (80, 160, 255)
        c_sec    = (0, 220, 180)
        c_normal = (180, 210, 255)
        c_esc    = (120, 120, 140)

        def _ln(texto, y_rel, fnt, color, centrar=False):
            s = fnt.render(texto, True, color)
            x = px + (panel_w - s.get_width()) // 2 if centrar else px + 40
            self.screen.blit(s, (x, py + y_rel))

        _ln("CONTROLES", 22, font_t, c_titulo, centrar=True)
        pygame.draw.line(self.screen, c_titulo,
                         (px + 30, py + 62), (px + panel_w - 30, py + 62), 1)

        secciones = [
            (75,  c_sec,    "JUGADOR 1  (Nave Azul)",      font_s),
            (108, c_normal, "Mover ........... Flechas",    font_n),
            (132, c_normal, "Disparar ........ Espacio",    font_n),
            (156, c_normal, "Mega Bomba ...... B",           font_n),
            (195, c_sec,    "JUGADOR 2  (Nave Roja)",       font_s),
            (228, c_normal, "Mover ........... WASD",        font_n),
            (252, c_normal, "Disparar ........ F",           font_n),
            (276, c_normal, "Mega Bomba ...... G",           font_n),
            (315, c_sec,    "GENERAL",                       font_s),
            (348, c_normal, "Pausa ........... P",           font_n),
            (372, c_normal, "Mutear .......... M  (en juego)", font_n),
        ]
        for y_rel, color, texto, fnt in secciones:
            _ln(texto, y_rel, fnt, color)

        pygame.draw.line(self.screen, (60, 60, 80),
                         (px + 30, py + 418), (px + panel_w - 30, py + 418), 1)
        _ln("ESC  para volver", 428, font_n, c_esc, centrar=True)

    def _draw_centro_hud(self, color):
        """Bloque central: Mundo/Nivel + barra de oleadas."""
        texto_mn = f"MUNDO {self.mundo_id}  ·  NIVEL {self.nivel}"
        font_mn  = pygame.font.SysFont("monospace", 26, bold=True)
        surf_mn  = font_mn.render(texto_mn, True, color)
        cx_mn    = config.WIDTH // 2 - surf_mn.get_width() // 2
        r_bg     = surf_mn.get_rect(topleft=(cx_mn, 12))
        r_bg.inflate_ip(12, 6)
        s_bg     = pygame.Surface(r_bg.size, pygame.SRCALPHA)
        s_bg.fill((0, 0, 0, 110))
        self.screen.blit(s_bg, r_bg.topleft)
        self.screen.blit(surf_mn, (cx_mn, 12))

        if self.estado in ("jugando", "completado"):
            self._draw_oleada_bar_centrada(color, y=46)

    def _dibujar_corazon(self, screen, cx, cy, tam=10, color=(255, 60, 80)):
        """Corazón dibujado con primitivas."""
        r = tam // 3
        pygame.draw.circle(screen, color, (cx - r, cy - r // 2), r)
        pygame.draw.circle(screen, color, (cx + r, cy - r // 2), r)
        pygame.draw.polygon(screen, color, [
            (cx - tam // 2 - 2, cy - 2),
            (cx + tam // 2 + 2, cy - 2),
            (cx, cy + tam // 2 + 2),
        ])

    def _dibujar_calavera(self, screen, cx, cy, tam=16):
        """Calavera simple dibujada con primitivas."""
        color = (200, 50, 50)
        pygame.draw.circle(screen, color, (cx, cy - 2), tam // 2)
        ojo_r = max(2, tam // 8)
        pygame.draw.circle(screen, (0, 0, 0), (cx - tam // 5, cy - 4), ojo_r)
        pygame.draw.circle(screen, (0, 0, 0), (cx + tam // 5, cy - 4), ojo_r)
        jaw_w = tam // 2
        pygame.draw.rect(screen, color, (cx - jaw_w // 2, cy + 2, jaw_w, tam // 4))
        for dx in range(-jaw_w // 4, jaw_w // 4 + 1, max(1, jaw_w // 4)):
            pygame.draw.line(screen, (0, 0, 0),
                             (cx + dx, cy + 2), (cx + dx, cy + 2 + tam // 4), 1)

    def _draw_caido(self, lado: str):
        """Muestra calavera + 'CAIDO' en el lado del jugador muerto."""
        font  = pygame.font.SysFont("monospace", 28, bold=True)
        surf  = font.render("CAIDO", True, (200, 50, 50))
        surf.set_alpha(200)
        tam   = 22
        gap   = 8
        total = tam + gap + surf.get_width()
        x = 12 if lado == "izq" else config.WIDTH - total - 12
        self._dibujar_calavera(self.screen, x + tam // 2, 42 + tam // 2, tam=tam)
        self.screen.blit(surf, (x + tam + gap, 42))

    def _draw_powerups_player(self, player: Player, color, y_inicio, lado: str):
        """Muestra power-ups activos del jugador dado."""
        activos = {**player.powerups, **player.powerups_temporales}
        if not activos:
            return
        font = pygame.font.SysFont("monospace", 18, bold=True)
        y    = y_inicio
        for nombre, val in activos.items():
            es_temporal = nombre in player.powerups_temporales
            c = (80, 200, 255) if es_temporal else color
            s = font.render(f" {nombre} ", True, c)
            if lado == "izq":
                x = 12
            else:
                x = config.WIDTH - s.get_width() - 12
            r = s.get_rect(topleft=(x, y))
            r.inflate_ip(4, 2)
            bg = pygame.Surface(r.size, pygame.SRCALPHA)
            bg.fill((0, 0, 0, 100))
            self.screen.blit(bg, r.topleft)
            self.screen.blit(s, (x, y))
            if es_temporal and isinstance(val, int):
                barra_w = 80
                bx = x
                by = y + 22
                pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, barra_w, 5))
                relleno = max(0, int(barra_w * min(1.0, val / 180)))
                if relleno:
                    pygame.draw.rect(self.screen, (80, 200, 255), (bx, by, relleno, 5))
                y += 34
            else:
                y += 26

    def _draw_monedas_player(self, player: Player, xr: bool, y_base: int):
        """Monedas del jugador. xr=True → alineado a la derecha."""
        MONEDA_COLOR = (255, 210, 0)
        MONEDA_RADIO = 10
        ancho_total  = MONEDA_RADIO * 2 + 8 + 80
        bg = pygame.Surface((ancho_total + 16, MONEDA_RADIO * 2 + 10), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 110))
        if xr:
            bx = config.WIDTH - ancho_total - 18
        else:
            bx = 12
        self.screen.blit(bg, (bx - 2, y_base - 2))
        cx = bx + MONEDA_RADIO
        cy = y_base + MONEDA_RADIO + 2
        pygame.draw.circle(self.screen, MONEDA_COLOR, (cx, cy), MONEDA_RADIO)
        pygame.draw.circle(self.screen, (200, 160, 0), (cx, cy), MONEDA_RADIO, 2)
        font_sym = pygame.font.SysFont("monospace", 12, bold=True)
        sym = font_sym.render("$", True, (80, 50, 0))
        self.screen.blit(sym, (cx - sym.get_width() // 2, cy - sym.get_height() // 2))
        font_n = pygame.font.SysFont("monospace", 22, bold=True)
        texto  = font_n.render(str(player.monedas), True, MONEDA_COLOR)
        self.screen.blit(texto, (cx + MONEDA_RADIO + 6, cy - texto.get_height() // 2))

    def _draw_mega_bombas_player(self, player: Player, xr: bool, y_base: int, tecla: str):
        if player.mega_bombas <= 0:
            return
        font  = pygame.font.SysFont("monospace", 22, bold=True)
        texto = f"BOMBA x{player.mega_bombas}  [{tecla}]"
        surf  = font.render(texto, True, (255, 110, 50))
        if xr:
            x = config.WIDTH - surf.get_width() - 12
        else:
            x = 12
        bg = pygame.Surface((surf.get_width() + 16, surf.get_height() + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 110))
        self.screen.blit(bg, (x - 8, y_base - 2))
        self.screen.blit(surf, (x, y_base))

    def _draw_oleada_bar_centrada(self, color, y):
        barra_w = 360
        barra_h = 16
        bx      = config.WIDTH // 2 - barra_w // 2
        oleadas_hechas = min(self.oleada_num, self.oleadas_objetivo)
        ratio   = min(1.0, oleadas_hechas / max(1, self.oleadas_objetivo))
        texto   = f"OLEADA  {oleadas_hechas} / {self.oleadas_objetivo}"

        font = pygame.font.SysFont("monospace", 18)
        s    = font.render(texto, True, color)
        total_h = 14 + barra_h
        bg_surf = pygame.Surface((barra_w + 10, total_h + 4), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 100))
        self.screen.blit(bg_surf, (bx - 5, y - 2))
        self.screen.blit(s, (config.WIDTH // 2 - s.get_width() // 2, y))
        by2 = y + 20
        pygame.draw.rect(self.screen, (30, 30, 30), (bx, by2, barra_w, barra_h))
        fill_w = max(0, int(barra_w * ratio))
        if fill_w:
            c_barra = (80, 255, 120) if ratio >= 1.0 else (60, 200, 80)
            pygame.draw.rect(self.screen, c_barra, (bx, by2, fill_w, barra_h))
        pygame.draw.rect(self.screen, color, (bx, by2, barra_w, barra_h), 2)

    # ── Aviso de EMP en modo 1j (en _draw_hud_1j no hay loop de jugadores) ───

    # ---------------------------------------------------------------- overlays

    def _draw_overlay(self):
        color = self.config.get("color_hud", WHITE)

        if self.estado == "transicion":
            nombre = self.config.get("nombre", "")
            self._draw_overlay_centrado(
                f"MUNDO {self.mundo_id}  —  NIVEL {self.nivel}",
                config.HEIGHT // 2 - 60, 52, color)
            self._draw_overlay_centrado(nombre, config.HEIGHT // 2 + 15, 30, color)
            obj = self.config["oleadas_por_nivel"][self.nivel - 1]
            self._draw_overlay_centrado(f"Objetivo: {obj} oleadas",
                                        config.HEIGHT // 2 + 60, 22, color)

        elif self.estado == "alerta":
            if (self._alerta_timer // 6) % 2 == 0:
                self._draw_overlay_centrado("!  ALERTA  !",
                                            config.HEIGHT // 2 - 55, 80, (255, 40, 40))
            nombre_boss = self.config.get("nombre_boss", "BOSS")
            self._draw_overlay_centrado(nombre_boss,
                                        config.HEIGHT // 2 + 40, 36, (220, 110, 110))
            self._draw_overlay_centrado("SE APROXIMA",
                                        config.HEIGHT // 2 + 90, 28, (180, 80, 80))

        elif self.estado == "completado":
            self._draw_completado_panel()

        elif self.estado == "game_over":
            self._draw_gameover_panel()

        elif self.estado == "victoria":
            self._draw_overlay_centrado("VICTORIA",
                                        config.HEIGHT // 2 - 100, 88, (255, 220, 0))
            self._draw_overlay_centrado("Los 5 mundos han sido conquistados",
                                        config.HEIGHT // 2 + 10, 32, (80, 255, 120))
            if self.modo_2j and self.player2:
                self._draw_overlay_centrado(
                    f"J1: {self.player1.score}    J2: {self.player2.score}",
                    config.HEIGHT // 2 + 65, 36, color)
            else:
                self._draw_overlay_centrado(f"Puntuacion final: {self.player1.score}",
                                            config.HEIGHT // 2 + 65, 36, color)
            self._draw_overlay_centrado("ENTER: Menu",
                                        config.HEIGHT // 2 + 120, 26, color)

        # Aviso EMP en modo 1j
        if not self.modo_2j and self.player1.emp_activo:
            seg = self.player1.emp_timer // 30 + 1
            self._draw_overlay_centrado(f"EMP — disparo bloqueado ({seg}s)",
                                        config.HEIGHT // 2 + 80, 28, (50, 150, 255))

    def _draw_textos_flotantes(self):
        font = pygame.font.SysFont("monospace", 20, bold=True)
        for tf in self.textos_flotantes:
            prog  = tf["frame"] / tf["max_frames"]
            alpha = int((1 - prog) * 255)
            y_act = int(tf["y"] - tf["frame"] * 1.8)
            surf  = font.render(tf["texto"], True, tf["color"])
            surf.set_alpha(alpha)
            self.screen.blit(surf, (tf["x"] - surf.get_width() // 2, y_act))

        for cf in self.calaveras_flotantes:
            prog  = cf["frame"] / cf["max_frames"]
            alpha = int((1 - prog) * 255)
            y_act = int(cf["y"] - cf["frame"] * 1.8)
            tam   = int(28 * (1 - prog * 0.4))
            tmp   = pygame.Surface((tam * 2, tam * 2), pygame.SRCALPHA)
            self._dibujar_calavera(tmp, tam, tam, tam=tam)
            tmp.set_alpha(alpha)
            self.screen.blit(tmp, (cf["x"] - tam, y_act - tam))

    # ----------------------------------------------------------------- utils

    def _draw_completado_panel(self):
        """Texto de nivel completado con efecto de brillo y fade-in."""
        alpha = min(255, self._completado_fade * 9)

        font_t = pygame.font.SysFont("monospace", 72, bold=True)
        font_b = pygame.font.SysFont("monospace", 38, bold=True)

        texto  = "NIVEL COMPLETADO"
        surf_t = font_t.render(texto, True, (80, 255, 120))
        surf_t.set_alpha(alpha)

        # Glow: misma cadena en color claro, alpha bajo, ligeramente desplazado
        surf_g = font_t.render(texto, True, (180, 255, 210))
        surf_g.set_alpha(min(alpha // 3, 55))

        cx = config.WIDTH  // 2 - surf_t.get_width()  // 2
        cy = config.HEIGHT // 2 - surf_t.get_height() // 2 - 30

        for ox, oy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
            self.screen.blit(surf_g, (cx + ox, cy + oy))
        self.screen.blit(surf_t, (cx, cy))

        if self._bonus_nivel > 0:
            texto_b = f"+{self._bonus_nivel} MONEDAS BONUS"
            surf_b  = font_b.render(texto_b, True, (255, 210, 0))
            surf_b.set_alpha(alpha)
            bx = config.WIDTH // 2 - surf_b.get_width() // 2
            self.screen.blit(surf_b, (bx, cy + surf_t.get_height() + 18))

    def _draw_gameover_panel(self):
        """Panel de Game Over con estadísticas y opciones REINTENTAR / MENU."""
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 700, 510
        px = config.WIDTH  // 2 - panel_w // 2
        py = config.HEIGHT // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 5, 5, 235))
        pygame.draw.rect(panel, (200, 40, 40), (0, 0, panel_w, panel_h), 2)
        self.screen.blit(panel, (px, py))

        # Título
        font_t = pygame.font.SysFont("monospace", 58, bold=True)
        st = font_t.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(st, (px + (panel_w - st.get_width()) // 2, py + 18))
        pygame.draw.line(self.screen, (160, 30, 30),
                         (px + 30, py + 90), (px + panel_w - 30, py + 90), 1)

        # Estadísticas
        font_s  = pygame.font.SysFont("monospace", 24)
        c_label = (140, 155, 175)
        c_valor = (220, 235, 255)

        score_total   = self.player1.score
        monedas_total = self.player1.monedas
        if self.modo_2j and self.player2:
            score_total   += self.player2.score
            monedas_total += self.player2.monedas

        segundos   = self._frames_jugados // 30
        tiempo_str = f"{segundos // 60:02d}:{segundos % 60:02d}"

        stats = [
            ("Puntuacion",       str(score_total)),
            ("Mundo / Nivel",    f"{self.mundo_id}  /  {self.nivel}"),
            ("Enemigos caidos",  str(self.enemigos_eliminados)),
            ("Monedas",          str(monedas_total)),
            ("Tiempo",           tiempo_str),
        ]

        y_s = py + 108
        for label, valor in stats:
            s_l = font_s.render(label, True, c_label)
            s_v = font_s.render(valor, True, c_valor)
            self.screen.blit(s_l, (px + 55, y_s))
            self.screen.blit(s_v, (px + panel_w - 55 - s_v.get_width(), y_s))
            # Puntos suspensivos entre label y valor
            x_ini = px + 55 + s_l.get_width() + 6
            x_fin = px + panel_w - 55 - s_v.get_width() - 6
            mid_y = y_s + s_l.get_height() // 2 + 1
            for xd in range(x_ini, x_fin, 7):
                pygame.draw.circle(self.screen, (55, 65, 85), (xd, mid_y), 1)
            y_s += 44

        pygame.draw.line(self.screen, (70, 30, 30),
                         (px + 30, y_s + 6), (px + panel_w - 30, y_s + 6), 1)

        # Opciones
        font_o  = pygame.font.SysFont("monospace", 28, bold=True)
        opciones = ["REINTENTAR", "MENU PRINCIPAL"]
        c_sel   = (0, 255, 200)
        c_norm  = (160, 200, 255)
        y_op    = y_s + 26
        for i, opcion in enumerate(opciones):
            selec = (i == self._gameover_sel)
            color = c_sel if selec else c_norm
            s     = font_o.render(opcion, True, color)
            x_op  = px + (panel_w - s.get_width()) // 2
            self.screen.blit(s, (x_op, y_op))
            if selec:
                fl = font_o.render(">", True, c_sel)
                self.screen.blit(fl, (x_op - fl.get_width() - 14, y_op))
            y_op += 50

        # Hint
        font_h = pygame.font.SysFont("monospace", 16)
        hint   = font_h.render(
            "Flechas:  Navegar     ENTER:  Confirmar     ESC:  Salir",
            True, (75, 85, 105))
        self.screen.blit(hint, (px + (panel_w - hint.get_width()) // 2,
                                 py + panel_h - 26))

    def _draw_overlay_centrado(self, texto, y, size, color, alpha=255):
        font = pygame.font.SysFont("monospace", size, bold=True)
        surf = font.render(texto, True, color)
        surf.set_alpha(alpha)
        self.screen.blit(surf, (config.WIDTH // 2 - surf.get_width() // 2, y))

    def _draw_text(self, text, pos, size, color=WHITE, bg=False):
        font  = pygame.font.SysFont("monospace", size)
        label = font.render(text, True, color)
        if bg:
            r = label.get_rect(topleft=pos)
            r.inflate_ip(8, 4)
            s = pygame.Surface(r.size, pygame.SRCALPHA)
            s.fill((0, 0, 0, 110))
            self.screen.blit(s, r.topleft)
        self.screen.blit(label, pos)

    def _draw_text_derecha(self, text, y, size, color=WHITE):
        """Renderiza texto alineado a la derecha con fondo semitransparente."""
        font  = pygame.font.SysFont("monospace", size)
        label = font.render(text, True, color)
        x     = config.WIDTH - label.get_width() - 12
        r     = label.get_rect(topleft=(x, y))
        r.inflate_ip(8, 4)
        s     = pygame.Surface(r.size, pygame.SRCALPHA)
        s.fill((0, 0, 0, 110))
        self.screen.blit(s, r.topleft)
        self.screen.blit(label, (x, y))
