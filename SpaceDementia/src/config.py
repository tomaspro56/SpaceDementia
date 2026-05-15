"""
Constantes globales. WIDTH y HEIGHT se inicializan desde main.py
DESPUÉS de crear la ventana, para que reporten el tamaño REAL del
surface y no del escritorio.
"""

# Dimensiones del display — main.py las setea con set_dimensions()
WIDTH  = 0
HEIGHT = 0

def set_dimensions(w: int, h: int) -> None:
    """Llamar UNA SOLA VEZ desde main.py tras pygame.display.set_mode()."""
    global WIDTH, HEIGHT
    WIDTH  = w
    HEIGHT = h

# Colores
WHITE   = (255, 255, 255)
RED     = (255, 0, 0)
GREEN   = (0, 255, 0)
BLUE    = (0, 0, 255)
BLACK   = (0, 0, 0)
YELLOW  = (255, 255, 0)
CYAN    = (0, 255, 255)
MAGENTA = (255, 0, 255)
