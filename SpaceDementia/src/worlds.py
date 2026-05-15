"""
Configuración de los 5 mundos espaciales de SpaceDementia.
Cada mundo tiene 5 niveles + 1 boss final.
Las claves de color son compatibles con Player, Enemy, Bullet, etc.
"""

MUNDOS = [
    # ── MUNDO 1: Sector Nebulosa ──────────────────────────────────────────
    {
        "id": 1,
        # Identificador visual (siempre "cosmic" por ahora; Fase 2 agrega sprites únicos)
        "sprite_id": "cosmic",
        "nombre": "Sector Nebulosa",
        # Paleta visual
        "color_fondo":             (10, 14, 28),
        "color_jugador":           (80, 160, 255),
        "color_jugador_detalle":   (0, 240, 255),
        "color_propulsor":         (255, 120, 0),
        "color_enemigo_normal":    (90, 80, 230),
        "color_enemigo_agil":      (0, 180, 255),
        "color_bala_jugador":      (0, 255, 200),
        "color_bala_enemigo":      (130, 90, 255),
        "colores_explosion":       [(0, 180, 255), (80, 0, 200), (0, 255, 255),
                                    (255, 255, 255), (100, 80, 255)],
        "color_hud":               (180, 210, 255),
        # Compatibilidad con Background (fondo espacial en todos los mundos por ahora)
        "fondo_tipo":              "espacio",
        # Boss (Fase 4)
        "nombre_boss":             "Drone Madre",
        "boss_vida":               200,
        # Oleadas por nivel [n1, n2, n3, n4, n5] — completa todas las oleadas para avanzar
        "oleadas_por_nivel":       [4, 4, 4, 4, 4],
        # Config de enemigos
        "vel_enemigo_base":        3.0,
        "vel_bala_enemigo":        10,
        "disparo_chance":          8,     # % por frame
        "tipos_oleada":            ["normal", "kamikaze"],
        "enemies_per_wave":        5,
    },

    # ── MUNDO 2: Cinturón de Asteroides ───────────────────────────────────
    {
        "id": 2,
        "sprite_id": "cosmic",
        "nombre": "Cinturón de Asteroides",
        "color_fondo":             (16, 10, 6),
        "color_jugador":           (80, 160, 255),
        "color_jugador_detalle":   (0, 240, 255),
        "color_propulsor":         (255, 140, 20),
        "color_enemigo_normal":    (190, 80, 30),
        "color_enemigo_agil":      (220, 130, 40),
        "color_bala_jugador":      (0, 255, 200),
        "color_bala_enemigo":      (240, 100, 20),
        "colores_explosion":       [(240, 100, 0), (200, 60, 0), (255, 200, 80),
                                    (255, 255, 200), (150, 50, 0)],
        "color_hud":               (220, 180, 130),
        "fondo_tipo":              "espacio",
        "nombre_boss":             "Asteroide Viviente",
        "boss_vida":               300,
        "oleadas_por_nivel":       [5, 5, 5, 5, 5],
        "vel_enemigo_base":        4.0,
        "vel_bala_enemigo":        12,
        "disparo_chance":          10,
        "tipos_oleada":            ["normal", "agil", "kamikaze"],
        "enemies_per_wave":        6,
    },

    # ── MUNDO 3: Zona Tóxica ──────────────────────────────────────────────
    {
        "id": 3,
        "sprite_id": "cosmic",
        "nombre": "Zona Tóxica",
        "color_fondo":             (6, 14, 6),
        "color_jugador":           (80, 160, 255),
        "color_jugador_detalle":   (0, 240, 255),
        "color_propulsor":         (255, 120, 0),
        "color_enemigo_normal":    (60, 190, 40),
        "color_enemigo_agil":      (150, 230, 0),
        "color_bala_jugador":      (0, 255, 200),
        "color_bala_enemigo":      (100, 255, 50),
        "colores_explosion":       [(50, 230, 30), (100, 255, 0), (200, 255, 100),
                                    (255, 255, 150), (30, 150, 0)],
        "color_hud":               (150, 255, 120),
        "fondo_tipo":              "espacio",
        "nombre_boss":             "Estación Contaminante",
        "boss_vida":               400,
        "oleadas_por_nivel":       [6, 6, 6, 6, 6],
        "vel_enemigo_base":        4.5,
        "vel_bala_enemigo":        13,
        "disparo_chance":          12,
        "tipos_oleada":            ["normal", "agil", "rafaga", "kamikaze"],
        "enemies_per_wave":        7,
    },

    # ── MUNDO 4: Campo de Guerra ──────────────────────────────────────────
    {
        "id": 4,
        "sprite_id": "cosmic",
        "nombre": "Campo de Guerra",
        "color_fondo":             (16, 6, 6),
        "color_jugador":           (80, 160, 255),
        "color_jugador_detalle":   (0, 240, 255),
        "color_propulsor":         (255, 120, 0),
        "color_enemigo_normal":    (210, 40, 40),
        "color_enemigo_agil":      (255, 90, 30),
        "color_bala_jugador":      (0, 255, 200),
        "color_bala_enemigo":      (255, 60, 60),
        "colores_explosion":       [(255, 60, 0), (200, 20, 0), (255, 160, 0),
                                    (255, 255, 100), (180, 0, 0)],
        "color_hud":               (255, 160, 130),
        "fondo_tipo":              "espacio",
        "nombre_boss":             "Crucero de Guerra",
        "boss_vida":               500,
        "oleadas_por_nivel":       [7, 7, 7, 7, 7],
        "vel_enemigo_base":        5.0,
        "vel_bala_enemigo":        14,
        "disparo_chance":          15,
        "tipos_oleada":            ["normal", "agil", "rafaga", "apuntador", "kamikaze"],
        "enemies_per_wave":        7,
    },

    # ── MUNDO 5: El Vacío Final ───────────────────────────────────────────
    {
        "id": 5,
        "sprite_id": "cosmic",
        "nombre": "El Vacío Final",
        "color_fondo":             (4, 4, 10),
        "color_jugador":           (80, 160, 255),
        "color_jugador_detalle":   (0, 240, 255),
        "color_propulsor":         (255, 120, 0),
        "color_enemigo_normal":    (200, 200, 210),
        "color_enemigo_agil":      (255, 255, 255),
        "color_bala_jugador":      (0, 255, 200),
        "color_bala_enemigo":      (200, 0, 0),
        "colores_explosion":       [(200, 0, 0), (255, 50, 50), (255, 255, 255),
                                    (150, 0, 0), (100, 0, 0)],
        "color_hud":               (220, 220, 230),
        "fondo_tipo":              "espacio",
        "nombre_boss":             "Entidad del Vacío",
        "boss_vida":               700,
        "oleadas_por_nivel":       [8, 8, 8, 8, 8],
        "vel_enemigo_base":        5.5,
        "vel_bala_enemigo":        15,
        "disparo_chance":          18,
        "tipos_oleada":            ["normal", "agil", "rafaga", "apuntador", "kamikaze"],
        "enemies_per_wave":        8,
    },
]


def obtener_mundo(mundo_id):
    """Retorna la config del mundo 1-5. Si no existe, retorna el mundo 1."""
    for m in MUNDOS:
        if m["id"] == mundo_id:
            return m
    return MUNDOS[0]
