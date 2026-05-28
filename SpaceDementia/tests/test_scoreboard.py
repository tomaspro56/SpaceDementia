import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scoreboard import Scoreboard


def _sb_temporal():
    """Crea un Scoreboard con archivo temporal (no toca el real)."""
    fd, ruta = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    return Scoreboard(archivo=ruta), ruta


def test_agregar_y_top():
    sb, ruta = _sb_temporal()
    try:
        sb.agregar("1j", "Tomas", 100)
        sb.agregar("1j", "Juan", 200)
        top = sb.top("1j")
        assert top[0] == ("Juan", 200)   # mayor primero
        assert top[1] == ("Tomas", 100)
    finally:
        os.remove(ruta)


def test_case_insensitive():
    """'Tomas' y 'TOMas' son la misma persona."""
    sb, ruta = _sb_temporal()
    try:
        sb.agregar("1j", "Tomas", 100)
        sb.agregar("1j", "TOMas", 300)   # mismo jugador, mejor puntaje
        top = sb.top("1j")
        assert len(top) == 1             # no se duplica
        assert top[0][1] == 300          # guarda el mejor puntaje
    finally:
        os.remove(ruta)


def test_solo_guarda_el_mejor():
    """Un puntaje menor no reemplaza al mayor existente."""
    sb, ruta = _sb_temporal()
    try:
        sb.agregar("1j", "Ana", 500)
        sb.agregar("1j", "Ana", 200)     # menor, no debe reemplazar
        assert sb.top("1j")[0][1] == 500
    finally:
        os.remove(ruta)


def test_top_limita_a_10():
    sb, ruta = _sb_temporal()
    try:
        for i in range(15):
            sb.agregar("1j", f"Jug{i}", i * 10)
        assert len(sb.top("1j")) <= 10
    finally:
        os.remove(ruta)


def test_clave_combinada_ordena():
    """La clave combinada es independiente del orden de los nombres."""
    c1 = Scoreboard.clave_combinada("Ana", "Beto")
    c2 = Scoreboard.clave_combinada("Beto", "Ana")
    assert c1 == c2                       # mismo resultado sin importar orden


def test_modos_separados():
    """Las tablas 1j y 2j son independientes."""
    sb, ruta = _sb_temporal()
    try:
        sb.agregar("1j", "Solo", 100)
        sb.agregar("2j", "Duo", 200)
        assert len(sb.top("1j")) == 1
        assert len(sb.top("2j")) == 1
    finally:
        os.remove(ruta)
