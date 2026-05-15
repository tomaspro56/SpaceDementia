"""
tienda.py — Tienda entre niveles del SpaceDementia.

Aparece tras completar niveles 1-3 de cada mundo (antes del boss).
En modo 2 jugadores, se abre primero para J1 y luego para J2.
Navegación: flechas ↑↓ · ENTER comprar · ESC continuar
"""

import pygame

import config


class Tienda:
    """
    Overlay de tienda que se dibuja sobre el juego pausado.
    game.py la crea, llama a handle_key() con eventos KEYDOWN
    y consulta self.activa para saber cuándo cerrarla.
    """

    ITEMS_BASE = [
        {
            "id":     "escudo",
            "nombre": "Escudo Protector",
            "desc":   "Absorbe 1 golpe sin perder vida.",
            "precio": 150,
        },
        {
            "id":     "doble",
            "nombre": "Disparo Doble",
            "desc":   "2 balas paralelas  (permanente).",
            "precio": 300,
        },
        {
            "id":     "plasma",
            "nombre": "Disparo Plasma",
            "desc":   "Balas de 2 dano, tipo proton  (permanente).",
            "precio": 500,
        },
        {
            "id":     "vida",
            "nombre": "Vida Extra",
            "desc":   "+1 vida  (maximo 5).",
            "precio": 200,
        },
        {
            "id":     "bomba",
            "nombre": "Mega Bomba",
            "desc":   "Tecla B/G: destruye todo en pantalla  (max 3).",
            "precio": 250,
        },
    ]

    ITEM_REVIVIR = {
        "id":     "revivir",
        "nombre": "Revivir Companero",
        "desc":   "Revive al otro jugador con 1 vida.",
        "precio": 300,
    }

    # ── Colores ────────────────────────────────────────────────────────────────
    _C_TITULO   = (255, 220, 80)
    _C_MONEDA   = (255, 210, 0)
    _C_PRECIO   = (255, 200, 60)
    _C_NORMAL   = (200, 210, 230)
    _C_SEL      = (255, 255, 255)
    _C_GRIS     = (90, 90, 105)
    _C_ACTIVO   = (80, 220, 110)
    _C_NO_ALCA  = (200, 80, 80)
    _C_AYUDA    = (110, 130, 155)

    def __init__(self, game, jugador_num=1):
        self.game       = game
        self.jugador_num = jugador_num
        # Seleccionar jugador activo para esta sesión de tienda
        if jugador_num == 2 and game.modo_2j and game.player2 is not None:
            self.player = game.player2
        else:
            self.player = game.player1
        self._items    = self._calcular_items()
        self.seleccion = 0
        self.activa    = True

    # ----------------------------------------------------------------- items

    def _calcular_items(self):
        """Construye la lista de items disponibles (incluye Revivir si aplica)."""
        items = list(self.ITEMS_BASE)
        if self.game.modo_2j:
            otro = (self.game.player2 if self.jugador_num == 1
                    else self.game.player1)
            if otro is not None and otro.life <= 0:
                items.append(self.ITEM_REVIVIR)
        return items

    # ----------------------------------------------------------------- lógica

    def handle_key(self, key):
        """Procesa una tecla. Cierra la tienda si corresponde."""
        if key == pygame.K_UP:
            self.seleccion = (self.seleccion - 1) % len(self._items)
            self.game.sound.play("menu_click")
        elif key == pygame.K_DOWN:
            self.seleccion = (self.seleccion + 1) % len(self._items)
            self.game.sound.play("menu_click")
        elif key == pygame.K_RETURN:
            self._intentar_compra()
        elif key == pygame.K_ESCAPE:
            self.activa = False

    def _intentar_compra(self):
        item   = self._items[self.seleccion]
        estado = self._estado_item(item["id"])

        if estado in ("[ACTIVO]", "[MAXIMO]"):
            return
        if self.player.monedas < item["precio"]:
            self.game.sound.play("sin_fondos")
            return

        self.player.monedas -= item["precio"]
        self.game.sound.play("compra")
        iid = item["id"]

        if iid == "escudo":
            self.player.powerups["ESCUDO"] = 1

        elif iid == "doble":
            self.player.disparo_doble = True
            self.player._max_balas    = 8

        elif iid == "plasma":
            self.player.disparo_plasma = True

        elif iid == "vida":
            self.player.life = min(5, self.player.life + 1)

        elif iid == "bomba":
            self.player.mega_bombas = min(3, self.player.mega_bombas + 1)

        elif iid == "revivir":
            otro = (self.game.player2 if self.jugador_num == 1
                    else self.game.player1)
            if otro is not None:
                otro.life = 1
                otro.x, otro.y = otro._pos_inicial
                otro.powerups.clear()
                otro.powerups_temporales.clear()

    def _estado_item(self, item_id):
        """Retorna badge de estado o None si está disponible."""
        if item_id == "escudo":
            return "[ACTIVO]" if self.player.tiene_escudo() else None
        if item_id == "doble":
            return "[ACTIVO]" if self.player.disparo_doble else None
        if item_id == "plasma":
            return "[ACTIVO]" if self.player.disparo_plasma else None
        if item_id == "vida":
            return "[MAXIMO]" if self.player.life >= 5 else None
        if item_id == "bomba":
            return "[MAXIMO]" if self.player.mega_bombas >= 3 else None
        if item_id == "revivir":
            return None
        return None

    # ------------------------------------------------------------------- draw

    def draw(self, screen):
        """Dibuja el overlay completo de la tienda."""
        self._draw_fondo(screen)
        self._draw_titulo(screen)
        self._draw_monedas(screen)
        self._draw_items(screen)
        self._draw_ayuda(screen)

    def _draw_fondo(self, screen):
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 15, 215))
        screen.blit(overlay, (0, 0))

    def _draw_titulo(self, screen):
        if self.game.modo_2j:
            color_j = (80, 160, 255) if self.jugador_num == 1 else (255, 80, 80)
            titulo_texto = f"TIENDA  —  JUGADOR {self.jugador_num}"
        else:
            color_j = self._C_TITULO
            titulo_texto = "TIENDA"

        font = pygame.font.SysFont("monospace", 68, bold=True)
        surf = font.render(titulo_texto, True, color_j)
        x = config.WIDTH // 2 - surf.get_width() // 2
        screen.blit(surf, (x, 30))
        pygame.draw.line(screen, color_j,
                         (x, 30 + surf.get_height() + 4),
                         (x + surf.get_width(), 30 + surf.get_height() + 4), 2)

    def _draw_monedas(self, screen):
        font = pygame.font.SysFont("monospace", 30, bold=True)
        texto = f"Monedas: {self.player.monedas}"
        surf = font.render(texto, True, self._C_MONEDA)
        x = config.WIDTH - surf.get_width() - 50
        bg = pygame.Surface((surf.get_width() + 22, surf.get_height() + 10), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        screen.blit(bg, (x - 11, 42))
        screen.blit(surf, (x, 47))

    def _draw_items(self, screen):
        font_n = pygame.font.SysFont("monospace", 32, bold=True)
        font_d = pygame.font.SysFont("monospace", 21)
        font_p = pygame.font.SysFont("monospace", 26, bold=True)
        font_e = pygame.font.SysFont("monospace", 23, bold=True)

        ancho    = 960
        x_base   = config.WIDTH // 2 - ancho // 2
        y_inicio = 155
        alto     = 98

        for i, item in enumerate(self._items):
            y      = y_inicio + i * alto
            estado = self._estado_item(item["id"])
            puede  = (estado is None and self.player.monedas >= item["precio"])
            sel    = (i == self.seleccion)

            # ── Fondo del item ────────────────────────────────────────────────
            if sel:
                bg_color = (25, 55, 120, 190)
            elif estado in ("[ACTIVO]", "[MAXIMO]"):
                bg_color = (10, 35, 20, 120)
            else:
                bg_color = (8, 8, 28, 120)
            bg = pygame.Surface((ancho, alto - 4), pygame.SRCALPHA)
            bg.fill(bg_color)
            screen.blit(bg, (x_base, y))
            if sel:
                pygame.draw.rect(screen, self._C_SEL,
                                 (x_base, y, ancho, alto - 4), 2)

            if estado in ("[ACTIVO]", "[MAXIMO]"):
                c_n = self._C_ACTIVO
            elif not puede and estado is None:
                c_n = self._C_GRIS
            elif sel:
                c_n = self._C_SEL
            else:
                c_n = self._C_NORMAL

            s_n = font_n.render(item["nombre"], True, c_n)
            screen.blit(s_n, (x_base + 18, y + 10))

            c_d = self._C_GRIS if (not puede and estado is None) else (155, 168, 195)
            s_d = font_d.render(item["desc"], True, c_d)
            screen.blit(s_d, (x_base + 18, y + 52))

            s_p = font_p.render(f"$ {item['precio']}", True, self._C_PRECIO)
            screen.blit(s_p, (x_base + ancho - s_p.get_width() - 18, y + 12))

            if estado:
                s_e = font_e.render(estado, True, self._C_ACTIVO)
                screen.blit(s_e, (x_base + ancho - s_e.get_width() - 18, y + 52))
            elif not puede:
                s_na = font_e.render("No alcanza", True, self._C_NO_ALCA)
                screen.blit(s_na, (x_base + ancho - s_na.get_width() - 18, y + 52))

    def _draw_ayuda(self, screen):
        font = pygame.font.SysFont("monospace", 22)
        surf = font.render(
            "flechas: navegar    ENTER: comprar    ESC: continuar",
            True, self._C_AYUDA
        )
        screen.blit(surf, (config.WIDTH // 2 - surf.get_width() // 2, config.HEIGHT - 48))
