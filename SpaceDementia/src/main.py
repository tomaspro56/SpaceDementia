import pygame

pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.init()

from config import HEIGHT, WIDTH
from game import Game
from menu import Menu
import asset_loader

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
asset_loader.inicializar()   # Carga todos los sprites UNA SOLA VEZ
pygame.display.set_caption("SpaceDementia")

ejecutando = True
while ejecutando:
    menu = Menu(screen)
    resultado_menu = menu.run()

    if not resultado_menu:
        break

    modo_2j   = (resultado_menu == "2j")
    resultado = "reintentar"
    while resultado == "reintentar":
        game      = Game(screen, modo_2j=modo_2j)
        resultado = game.run()

    if resultado == "quit":
        ejecutando = False

pygame.quit()
