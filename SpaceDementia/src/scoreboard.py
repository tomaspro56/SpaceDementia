"""
scoreboard.py — Tablas de puntajes arcade (top 10) con persistencia JSON.

Mantiene DOS tablas separadas: modo "1j" y modo "2j".
Las claves son case-insensitive: "Tomas" y "tomas" son la misma entrada.
Se conserva el nombre tal como se escribió en el mejor puntaje.

Formato interno de cada tabla:
    { clave_minuscula: [nombre_display, puntaje] }
"""

import json
import os

from rutas import ruta_datos

_ARCHIVO = ruta_datos("scores.json")
_MAX_ENTRADAS = 10
_MODOS = ("1j", "2j")


class Scoreboard:
    """Gestiona dos tablas de puntajes (1j / 2j), case-insensitive."""

    def __init__(self, archivo=_ARCHIVO):
        self._archivo = archivo
        self._tablas = {"1j": {}, "2j": {}}
        self.cargar()

    # ---------------------------------------------------------- persistencia

    def cargar(self):
        """Lee el JSON. Formato {modo: {clave: [display, puntaje]}}."""
        try:
            with open(self._archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for modo in _MODOS:
                    tabla = data.get(modo, {})
                    if isinstance(tabla, dict):
                        limpia = {}
                        for clave, valor in tabla.items():
                            # Soporta [display, puntaje] o puntaje suelto
                            if isinstance(valor, list) and len(valor) == 2:
                                limpia[str(clave).lower()] = [str(valor[0]), int(valor[1])]
                            else:
                                limpia[str(clave).lower()] = [str(clave), int(valor)]
                        self._tablas[modo] = limpia
        except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
            self._tablas = {"1j": {}, "2j": {}}

    def guardar(self):
        """Escribe ambas tablas al disco en JSON."""
        try:
            with open(self._archivo, "w", encoding="utf-8") as f:
                json.dump(self._tablas, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ----------------------------------------------------------------- lógica

    def agregar(self, modo, nombre, puntaje):
        """Agrega/actualiza un puntaje (case-insensitive) en la tabla del modo.

        Si la clave (nombre en minúsculas) ya existe, solo actualiza si el
        nuevo puntaje es mayor, y en ese caso guarda el nombre tal como se
        escribió ahora. Retorna True si la tabla cambió.
        """
        if modo not in _MODOS:
            modo = "1j"
        tabla = self._tablas[modo]
        nombre = (nombre or "ANON").strip()[:12] or "ANON"
        clave = nombre.lower()
        puntaje = int(puntaje)
        actual = tabla.get(clave)
        if actual is None or puntaje > actual[1]:
            tabla[clave] = [nombre, puntaje]
            self._recortar(modo)
            self.guardar()
            return True
        return False

    def _recortar(self, modo):
        """Deja solo las top _MAX_ENTRADAS de la tabla del modo."""
        ordenados = sorted(self._tablas[modo].items(),
                           key=lambda kv: kv[1][1], reverse=True)
        self._tablas[modo] = dict(ordenados[:_MAX_ENTRADAS])

    def top(self, modo, n=_MAX_ENTRADAS):
        """Retorna [(nombre_display, puntaje)] del modo, mayor a menor."""
        if modo not in _MODOS:
            modo = "1j"
        ordenados = sorted(self._tablas[modo].values(),
                           key=lambda v: v[1], reverse=True)
        return [(disp, pts) for disp, pts in ordenados[:n]]

    @staticmethod
    def clave_combinada(nombre1, nombre2):
        """Combina dos nombres en clave única independiente del orden."""
        limpios = sorted([
            (nombre1 or "P1").strip()[:12] or "P1",
            (nombre2 or "P2").strip()[:12] or "P2",
        ], key=lambda s: s.lower())
        return "+".join(limpios)
