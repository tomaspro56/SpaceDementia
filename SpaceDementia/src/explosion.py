import asset_loader


class Explosion:
    """
    Explosión animada con sprites del pack SpaceRage.
    Reemplaza el sistema de partículas por frames de spritesheet.

    tamaño:
        "grande"  → explosion_1 (11 frames, 192px) — para boss
        "mediana" → explosion_2 ( 9 frames, 128px) — para enemigos normales
        "pequeña" → explosion_3 ( 9 frames,  80px) — para impactos de bala
    """

    _FRAMES_POR_SPRITE = 3           # Cada frame del sprite dura 3 ticks de juego
    _MAX_FRAMES = {"grande": 11, "mediana": 9, "pequeña": 9}

    def __init__(self, x, y, tamaño="mediana", tema=None):
        self.x = x
        self.y = y
        # Tolerancia: si llega un tamaño desconocido, usar mediana
        self.tamaño = tamaño if tamaño in self._MAX_FRAMES else "mediana"
        self._tick = 0
        self._frame_sprite = 0

    # ------------------------------------------------------------------ update

    def update(self):
        self._tick += 1
        self._frame_sprite = self._tick // self._FRAMES_POR_SPRITE

    # -------------------------------------------------------------------- draw

    def draw(self, screen):
        sprite = asset_loader.get_explosion_frame(self.tamaño, self._frame_sprite)
        if sprite is None:
            return
        w, h = sprite.get_size()
        screen.blit(sprite, (int(self.x) - w // 2, int(self.y) - h // 2))

    # ----------------------------------------------------------------- is_dead

    def is_dead(self):
        return self._frame_sprite >= self._MAX_FRAMES[self.tamaño]
