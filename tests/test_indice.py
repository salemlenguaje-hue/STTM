import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import indice  # noqa: E402


def _linea(n, ts, titulo, detalle="detalle"):
    return json.dumps({"n": n, "ts": ts, "titulo": titulo, "detalle": detalle,
                        "firma_tipo": "hash", "hash": f"h{n}"}, ensure_ascii=False)


class TestIndice(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.bitacora = self.carpeta / "BITACORA.jsonl"
        self.db = self.carpeta / "indice.db"

    def tearDown(self):
        self._tmp.cleanup()

    def _escribir_bitacora(self, lineas):
        self.bitacora.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    def test_reconstruir_cuenta_entradas(self):
        self._escribir_bitacora([
            _linea(1, "2026-09-01T00:00:00Z", "Primera entrada"),
            _linea(2, "2026-09-02T00:00:00Z", "Segunda entrada"),
        ])
        res = indice.reconstruir(self.bitacora, self.db)
        self.assertEqual(res["entradas_indexadas"], 2)
        self.assertEqual(indice.contar(self.db), 2)

    def test_reconstruir_es_idempotente(self):
        self._escribir_bitacora([_linea(1, "2026-09-01T00:00:00Z", "Única")])
        indice.reconstruir(self.bitacora, self.db)
        indice.reconstruir(self.bitacora, self.db)
        indice.reconstruir(self.bitacora, self.db)
        self.assertEqual(indice.contar(self.db), 1)

    def test_bitacora_inexistente_da_indice_vacio(self):
        res = indice.reconstruir(self.bitacora, self.db)
        self.assertEqual(res["entradas_indexadas"], 0)
        self.assertEqual(indice.contar(self.db), 0)

    def test_linea_corrupta_no_rompe_reconstruccion(self):
        self._escribir_bitacora([
            _linea(1, "2026-09-01T00:00:00Z", "Buena"),
            "esto no es json valido {{{",
            _linea(2, "2026-09-02T00:00:00Z", "También buena"),
        ])
        res = indice.reconstruir(self.bitacora, self.db)
        self.assertEqual(res["entradas_indexadas"], 2)

    def test_busqueda_texto_encuentra_por_palabra(self):
        self._escribir_bitacora([
            _linea(1, "2026-09-01T00:00:00Z", "Incidente de seguridad en el servidor"),
            _linea(2, "2026-09-02T00:00:00Z", "Actualización de documentación"),
        ])
        indice.reconstruir(self.bitacora, self.db)
        resultados = indice.buscar_texto(self.db, "seguridad")
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["n"], 1)

    def test_busqueda_sin_resultados(self):
        self._escribir_bitacora([_linea(1, "2026-09-01T00:00:00Z", "Algo")])
        indice.reconstruir(self.bitacora, self.db)
        self.assertEqual(indice.buscar_texto(self.db, "inexistente"), [])

    def test_busqueda_con_sintaxis_invalida_no_rompe(self):
        self._escribir_bitacora([_linea(1, "2026-09-01T00:00:00Z", "Algo")])
        indice.reconstruir(self.bitacora, self.db)
        # Comillas sin cerrar: sintaxis FTS5 inválida.
        self.assertEqual(indice.buscar_texto(self.db, '"sin cerrar'), [])

    def test_busqueda_con_guiones_encuentra_la_entrada(self):
        # Bug real encontrado en integración: FTS5 trata '-' como NOT,
        # así que un identificador como "Ref-STTM-004" rompía la búsqueda
        # o no encontraba nada, sin avisar por qué.
        self._escribir_bitacora([
            _linea(1, "2026-09-01T00:00:00Z", "Cambio en Ref-STTM-004"),
        ])
        indice.reconstruir(self.bitacora, self.db)
        resultados = indice.buscar_texto(self.db, "Ref-STTM-004")
        self.assertEqual(len(resultados), 1)

    def test_busqueda_con_solo_puntuacion_no_rompe(self):
        self._escribir_bitacora([_linea(1, "2026-09-01T00:00:00Z", "Algo")])
        indice.reconstruir(self.bitacora, self.db)
        self.assertEqual(indice.buscar_texto(self.db, "---:::"), [])

    def test_rango_de_fechas(self):
        self._escribir_bitacora([
            _linea(1, "2026-09-01T00:00:00Z", "Uno"),
            _linea(2, "2026-09-10T00:00:00Z", "Dos"),
            _linea(3, "2026-09-20T00:00:00Z", "Tres"),
        ])
        indice.reconstruir(self.bitacora, self.db)
        resultados = indice.por_rango_fecha(
            self.db, "2026-09-05T00:00:00Z", "2026-09-15T00:00:00Z")
        self.assertEqual([r["n"] for r in resultados], [2])

    def test_indice_sin_construir_busqueda_devuelve_vacio(self):
        self.assertEqual(indice.buscar_texto(self.db, "lo que sea"), [])
        self.assertEqual(indice.contar(self.db), 0)


if __name__ == "__main__":
    unittest.main()
