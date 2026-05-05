import pygame

if not pygame.get_init():
    pygame.init()
_info   = pygame.display.Info()
WIDTH   = _info.current_w
HEIGHT  = _info.current_h

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
