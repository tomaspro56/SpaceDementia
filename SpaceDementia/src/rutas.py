"""
rutas.py — Resolución de rutas compatible con PyInstaller.

- ruta_recurso(): para archivos de SOLO LECTURA (assets). Dentro del .exe
  apuntan a la carpeta temporal sys._MEIPASS; en desarrollo, al proyecto.
- ruta_datos(): para archivos que se ESCRIBEN y deben PERSISTIR (scores.json).
  Siempre junto al ejecutable / proyecto, nunca en la carpeta temporal.
"""
import os
import sys


def _base_recursos():
    # PyInstaller descomprime los datos en _MEIPASS
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    # En desarrollo: la raíz del proyecto (un nivel arriba de src/)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def ruta_recurso(*partes):
    """Ruta a un recurso de solo lectura (assets empaquetados)."""
    return os.path.join(_base_recursos(), *partes)


def _base_datos():
    # Si está empaquetado, junto al .exe; si no, la raíz del proyecto
    if hasattr(sys, "_MEIPASS"):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def ruta_datos(*partes):
    """Ruta a un archivo que se escribe y debe persistir (scores.json)."""
    return os.path.join(_base_datos(), *partes)
