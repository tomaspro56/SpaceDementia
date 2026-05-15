"""
asset_loader.py — Carga centralizada de sprites del pack SpaceRage.

Uso:
    import asset_loader
    asset_loader.inicializar()   # UNA VEZ, después de pygame.display.set_mode()

    sprite = asset_loader.get_player_frame(tilt)
    sprite = asset_loader.get_enemy_frame("1", "r", direction_y=-1)
    ...

Todos los assets se cargan, escalan y rotan aquí.
Ninguna otra clase hace pygame.image.load() ni transform.scale().
"""

import os

import pygame
import config

# ── Ruta a la carpeta assets/ (un nivel arriba de src/) ───────────────────────
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

# ── Tamaños finales (en píxeles) ──────────────────────────────────────────────
_TAM_JUGADOR       = 90     # jugador y enemigos: cuadrado final
_TAM_ENEMIGO       = 64
_TAM_MINE          = 64
_TAM_EXP_GRANDE    = 192    # explosion_1 (boss)
_TAM_EXP_MEDIANA   = 128    # explosion_2 (enemigos normales)
_TAM_EXP_PEQUEÑA   = 80     # explosion_3 (impactos de bala)
_ESCALA_PLASMA     = 4      # plasma original 6×21 → 24×84, tras rotar: 84×24
_ESCALA_VULCAN     = 4      # vulcan  original 6×22 → 24×88, tras rotar: 88×24
_ESCALA_PROTON     = 4      # proton  original 13×13 → 52×52
_TAM_EXHAUST       = 50     # propulsor de la nave
_TAM_BOSS          = 192    # boss: enemy_2 escalado 3×

# Planetas disponibles en assets/Planets/
_PLANETAS = [
    "Crystal", "Earth", "Hot", "Icy", "Jupiter", "Mars",
    "Mercury", "Moon", "Neptune", "Radiated", "Saturn",
    "Sun", "Terrestrial", "Uranus", "Venus",
]

# Color de enemigo por mundo (se usa en get_enemy_frame via game.py)
COLOR_ENEMIGO_POR_MUNDO = {1: "r", 2: "r", 3: "g", 4: "b", 5: "b"}

# ── Diccionario interno de sprites ────────────────────────────────────────────
_sprites: dict[str, pygame.Surface] = {}
_inicializado = False


# ════════════════════════════════════════════════════════════════════════════════
# Carga pública
# ════════════════════════════════════════════════════════════════════════════════

def inicializar() -> None:
    """Carga todos los assets. Llamar UNA VEZ tras pygame.display.set_mode()."""
    global _inicializado
    if _inicializado:
        return
    _cargar_jugador()
    _cargar_enemigos()
    _cargar_boss()
    _cargar_minas()
    _cargar_explosiones()
    _cargar_fx()
    _cargar_fondo()
    _cargar_planetas()
    _cargar_asteroides()
    _inicializado = True
    print(f"[asset_loader] {len(_sprites)} sprites cargados.")


# ════════════════════════════════════════════════════════════════════════════════
# Helpers de acceso (usados por player.py, enemy.py, bullet.py, etc.)
# ════════════════════════════════════════════════════════════════════════════════

def get_player_frame(tilt: float, mega_activo: bool = False, jugador_id: int = 1) -> pygame.Surface:
    """
    Retorna el sprite del jugador según su inclinación vertical.

    tilt ∈ [-1, 1]:
        ≤ -0.6  → l2 (inclinado fuerte arriba)
        ≤ -0.2  → l1 (leve arriba)
        [-0.2, 0.2] → m  (neutro)
        ≥  0.2  → r1 (leve abajo)
        ≥  0.6  → r2 (fuerte abajo)

    jugador_id: 1 = nave azul, 2 = nave roja
    """
    if jugador_id == 2:
        variante = "r"
    else:
        variante = "r" if mega_activo else "b"
    if tilt <= -0.6:
        frame = "l2"
    elif tilt <= -0.2:
        frame = "l1"
    elif tilt >= 0.6:
        frame = "r2"
    elif tilt >= 0.2:
        frame = "r1"
    else:
        frame = "m"
    return _get(f"player_{variante}_{frame}")


def get_enemy_frame(tipo: str, color: str, direction_y: int) -> pygame.Surface:
    """
    Retorna el sprite del enemigo según tipo, color y dirección vertical.

    tipo       : "1" (drone/ráfaga) | "2" (caza/apuntador)
    color      : "r" | "g" | "b"
    direction_y: -1 (subiendo) | 0 (neutro) | 1 (bajando)
    """
    if direction_y < 0:
        frame = "l1"
    elif direction_y > 0:
        frame = "r1"
    else:
        frame = "m"
    return _get(f"enemy_{tipo}_{color}_{frame}")


def get_explosion_frame(tamaño: str, frame_idx: int) -> pygame.Surface | None:
    """
    Retorna el frame de la explosión o None si la animación terminó.

    tamaño: "grande" (11 frames) | "mediana" (9) | "pequeña" (9)
    """
    if tamaño == "grande":
        total, prefijo = 11, "explosion_1"
    elif tamaño == "mediana":
        total, prefijo = 9, "explosion_2"
    else:
        total, prefijo = 9, "explosion_3"

    if frame_idx >= total:
        return None
    return _get(f"{prefijo}_{frame_idx + 1:02d}")


def get_plasma_frame(frame_global: int) -> pygame.Surface:
    """Alterna plasma_1 / plasma_2 cada 4 frames."""
    n = (frame_global // 4 % 2) + 1
    return _get(f"plasma_{n}")


def get_plasma_frame_p2(frame_global: int) -> pygame.Surface:
    """Plasma con tinte naranja/rojo para el jugador 2."""
    n = (frame_global // 4 % 2) + 1
    return _get(f"plasma_p2_{n}")


def get_vulcan_frame(frame_global: int) -> pygame.Surface:
    """Cicla vulcan_1 → 3 cada 3 frames."""
    n = (frame_global // 3 % 3) + 1
    return _get(f"vulcan_{n}")


def get_proton_frame(frame_global: int) -> pygame.Surface:
    """Cicla proton_01 → 03 cada 3 frames."""
    n = (frame_global // 3 % 3) + 1
    return _get(f"proton_{n:02d}")


def get_exhaust_frame(frame_global: int) -> pygame.Surface:
    """Cicla los 5 frames del propulsor cada 3 frames."""
    n = (frame_global // 3 % 5) + 1
    return _get(f"exhaust_{n:02d}")


def get_bg() -> pygame.Surface:
    """Retorna el fondo espacial escalado a la resolución del monitor."""
    return _get("BG")


def get_planet_sprite(nombre: str) -> pygame.Surface:
    """Retorna el sprite estático del planeta (último frame, el más iluminado)."""
    return _get(f"planet_{nombre}")


def get_boss_sprite() -> pygame.Surface:
    """Retorna el sprite del boss (enemy_2 rojo, 192×192, apunta izquierda)."""
    return _get("boss_sprite")


# Cantidad de variantes de asteroide cargadas (se establece en _cargar_asteroides)
_NUM_ASTEROIDES = 0


def get_asteroid_sprite(indice: int) -> pygame.Surface:
    """Retorna uno de los sprites de asteroide large según el índice."""
    n = max(1, _NUM_ASTEROIDES)
    return _get(f"asteroid_{indice % n}")


# ════════════════════════════════════════════════════════════════════════════════
# Funciones internas de carga
# ════════════════════════════════════════════════════════════════════════════════

def _get(nombre: str) -> pygame.Surface:
    """Obtiene un sprite del diccionario; retorna placeholder magenta si falta."""
    sprite = _sprites.get(nombre)
    if sprite is None:
        print(f"[asset_loader] AVISO: sprite '{nombre}' no encontrado.")
        ph = pygame.Surface((64, 64), pygame.SRCALPHA)
        ph.fill((255, 0, 255))
        return ph
    return sprite


def _cargar(ruta_rel: str) -> pygame.Surface:
    """Carga una imagen con convert_alpha(). Retorna placeholder si falla."""
    ruta = os.path.join(_ASSETS_DIR, ruta_rel)
    try:
        return pygame.image.load(ruta).convert_alpha()
    except (pygame.error, FileNotFoundError) as e:
        print(f"[asset_loader] ERROR cargando '{ruta_rel}': {e}")
        ph = pygame.Surface((64, 64), pygame.SRCALPHA)
        ph.fill((255, 0, 255))
        return ph


def _escalar(surf: pygame.Surface, ancho: int, alto: int | None = None) -> pygame.Surface:
    if alto is None:
        alto = ancho
    return pygame.transform.scale(surf, (ancho, alto))


def _escalar_x(surf: pygame.Surface, factor: int) -> pygame.Surface:
    w, h = surf.get_size()
    return pygame.transform.scale(surf, (w * factor, h * factor))


def _aplicar_alpha(surface: pygame.Surface, alpha_ratio: float) -> pygame.Surface:
    """Horneado del alpha por píxel: multiplica canal A por alpha_ratio (0.0-1.0)."""
    copia = surface.copy()
    overlay = pygame.Surface(copia.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, int(255 * alpha_ratio)))
    copia.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return copia


def _rotar(surf: pygame.Surface, angulo: int) -> pygame.Surface:
    """angulo > 0 = CCW, angulo < 0 = CW (convención pygame)."""
    return pygame.transform.rotate(surf, angulo)


# ── Jugador ───────────────────────────────────────────────────────────────────

def _cargar_jugador() -> None:
    """
    Carga los 10 frames del jugador (5 inclinaciones × 2 variantes azul/roja).
    Los sprites originales miran hacia ARRIBA; se rotan 90° CW (-90°) para mirar derecha.
    """
    for variante in ("b", "r"):
        for frame in ("l2", "l1", "m", "r1", "r2"):
            nombre = f"player_{variante}_{frame}"
            img = _cargar(f"Player/{nombre}.png")
            img = _escalar(img, _TAM_JUGADOR)
            img = _rotar(img, -90)  # 90° CW → la punta apunta a la derecha
            _sprites[nombre] = img


# ── Enemigos ──────────────────────────────────────────────────────────────────

def _cargar_enemigos() -> None:
    """
    Carga los 30 frames de enemigos (2 tipos × 3 colores × 5 inclinaciones).
    Los sprites originales miran hacia ARRIBA; se rotan 90° CCW para mirar izquierda.
    """
    for tipo in ("1", "2"):
        for color in ("r", "g", "b"):
            for frame in ("l2", "l1", "m", "r1", "r2"):
                nombre = f"enemy_{tipo}_{color}_{frame}"
                img = _cargar(f"Enemies/{nombre}.png")
                img = _escalar(img, _TAM_ENEMIGO)
                img = _rotar(img, 90)   # 90° CCW → la punta apunta a la izquierda
                _sprites[nombre] = img


def _cargar_boss() -> None:
    """
    Boss: enemy_2_r_m escalado a 192×192 y rotado para mirar a la izquierda.
    Se usa el mismo sprite que el enemigo tipo 2 rojo, pero 3× más grande.
    """
    img = _cargar("Enemies/enemy_2_r_m.png")
    img = _escalar(img, _TAM_BOSS)
    img = _rotar(img, 90)   # 90° CCW → la punta apunta a la izquierda
    _sprites["boss_sprite"] = img


# ── Minas (asteroides) ────────────────────────────────────────────────────────

def _cargar_minas() -> None:
    """Carga los 9 frames de mine_1 para reemplazar el polígono del asteroide."""
    for i in range(1, 10):
        nombre = f"mine_1_{i:02d}"
        img = _cargar(f"Enemies/mine_1_{i:02d}.png")
        img = _escalar(img, _TAM_MINE)
        _sprites[nombre] = img


# ── Explosiones ───────────────────────────────────────────────────────────────

def _cargar_explosiones() -> None:
    """
    Carga los 3 conjuntos de explosión:
      explosion_1: 11 frames → boss (grande, 192px)
      explosion_2:  9 frames → enemigos (mediana, 128px)
      explosion_3:  9 frames → impactos de bala (pequeña, 80px)
    """
    for i in range(1, 12):
        nombre = f"explosion_1_{i:02d}"
        img = _cargar(f"Explosions/explosion_1_{i:02d}.png")
        _sprites[nombre] = _escalar(img, _TAM_EXP_GRANDE)

    for i in range(1, 10):
        nombre = f"explosion_2_{i:02d}"
        img = _cargar(f"Explosions/explosion_2_{i:02d}.png")
        _sprites[nombre] = _escalar(img, _TAM_EXP_MEDIANA)

    for i in range(1, 10):
        nombre = f"explosion_3_{i:02d}"
        img = _cargar(f"Explosions/explosion_3_{i:02d}.png")
        _sprites[nombre] = _escalar(img, _TAM_EXP_PEQUEÑA)


# ── FX: balas y propulsor ─────────────────────────────────────────────────────

def _cargar_fx() -> None:
    """
    Plasma  (jugador, apunta derecha): escala ×4, rotar 90° CCW.
    Vulcan  (enemigo, apunta izquierda): escala ×4, rotar 90° CW.
    Proton  (boss, ángulo dinámico): escala ×4, sin rotar aquí.
    Exhaust (propulsor, sale a la izquierda): escala a 50px, rotar 90° CCW.
    """
    # Plasma: 6×21 → ×4 → 24×84 → rotar CCW → 84×24 (ancho × alto)
    for i in (1, 2):
        nombre = f"plasma_{i}"
        img = _cargar(f"FX/plasma_{i}.png")
        img = _escalar_x(img, _ESCALA_PLASMA)
        img = _rotar(img, 90)
        _sprites[nombre] = img

    # Plasma tintado para jugador 2 (tinte rojo-naranja via BLEND_RGB_ADD)
    for i in (1, 2):
        base   = _sprites[f"plasma_{i}"]
        tinted = base.copy()
        ovl    = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        ovl.fill((200, 0, 0, 0))
        tinted.blit(ovl, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        _sprites[f"plasma_p2_{i}"] = tinted

    # Vulcan: 6×22 → ×4 → 24×88 → rotar CW → 88×24
    for i in (1, 2, 3):
        nombre = f"vulcan_{i}"
        img = _cargar(f"FX/vulcan_{i}.png")
        img = _escalar_x(img, _ESCALA_VULCAN)
        img = _rotar(img, -90)
        _sprites[nombre] = img

    # Proton: 13×13 → ×4 → 52×52 (sin rotar; game.py aplica ángulo dinámico)
    for i in range(1, 4):
        nombre = f"proton_{i:02d}"
        img = _cargar(f"FX/proton_{i:02d}.png")
        img = _escalar_x(img, _ESCALA_PROTON)
        _sprites[nombre] = img

    # Exhaust: 64×64 → 50×50 → rotar 90° CCW (llama sale hacia la izquierda)
    for i in range(1, 6):
        nombre = f"exhaust_{i:02d}"
        img = _cargar(f"FX/exhaust_{i:02d}.png")
        img = _escalar(img, _TAM_EXHAUST)
        img = _rotar(img, 90)
        _sprites[nombre] = img


# ── Fondo tileable ────────────────────────────────────────────────────────────

def _cargar_fondo() -> None:
    """BG.png escalado 4px extra para cubrir gaps de redondeo en el tiling."""
    img = _cargar("BG.png")
    _sprites["BG"] = _escalar(img, config.WIDTH + 4, config.HEIGHT + 4).convert()


# ── Asteroides large ─────────────────────────────────────────────────────────

def _cargar_asteroides() -> None:
    """
    Carga una selección de sprites de asteroides grandes (series *3* y *4*).
    Un frame estático por variante, escalado a 80px para uso en Asteroide.draw().
    """
    global _NUM_ASTEROIDES
    # Variantes: primer frame (0000) de cada serie large disponible
    variantes = [
        "Asteroids/a30000.png",
        "Asteroids/b30000.png",
        "Asteroids/c30000.png",
        "Asteroids/c40000.png",
    ]
    cargadas = 0
    for ruta in variantes:
        img = _cargar(ruta)
        if img.get_width() > 64:   # Placeholder magenta tiene 64px → no contar
            img = _escalar(img, 80)
            _sprites[f"asteroid_{cargadas}"] = img
            cargadas += 1
    _NUM_ASTEROIDES = max(1, cargadas)


# ── Planetas de fondo ─────────────────────────────────────────────────────────

def _cargar_planetas() -> None:
    """
    Carga los 15 spritesheets de planetas.
    Cada spritesheet es 768×128 (6 frames de 128×128).
    Usa SOLO el último frame (el más iluminado/visible) — sin animación.
    """
    for nombre in _PLANETAS:
        sheet = _cargar(f"Planets/{nombre}-128x128.png")
        w, h = sheet.get_size()
        if w > h:
            # Spritesheet: tomar el último frame (más iluminado)
            num_frames = w // h
            frame_size = h
            ultimo = sheet.subsurface(
                pygame.Rect((num_frames - 1) * frame_size, 0, frame_size, frame_size)
            ).copy()
            _sprites[f"planet_{nombre}"] = _aplicar_alpha(ultimo, 0.3)
        else:
            # Sprite estático: usarlo directo
            _sprites[f"planet_{nombre}"] = _aplicar_alpha(sheet, 0.3)
