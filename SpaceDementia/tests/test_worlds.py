import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from worlds import obtener_mundo, MUNDOS


def test_hay_cinco_mundos():
    assert len(MUNDOS) == 5


def test_obtener_mundo_valido():
    m = obtener_mundo(3)
    assert m["id"] == 3


def test_obtener_mundo_invalido_devuelve_primero():
    """Un id fuera de rango devuelve el mundo 1 (fallback seguro)."""
    m = obtener_mundo(99)
    assert m["id"] == 1


def test_cada_mundo_tiene_campos_clave():
    """Todos los mundos tienen los campos que el juego espera."""
    campos = ["id", "nombre", "boss_estilo", "boss_vida", "oleadas_por_nivel"]
    for m in MUNDOS:
        for campo in campos:
            assert campo in m, f"Mundo {m.get('id')} sin campo {campo}"


def test_estilos_de_boss_unicos():
    """Cada mundo tiene un estilo de boss (pueden repetirse, pero existen)."""
    for m in MUNDOS:
        assert m["boss_estilo"] in (
            "tirador", "embestidor", "rociador", "artillero", "caotico"
        )
