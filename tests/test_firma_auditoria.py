# Creado por Martín José Dalberto, Argentina, 2026.
# SPDX-License-Identifier: MIT
"""
tests/test_firma_auditoria.py — Firma del meta.json de auditoría (ejecutor).

Cubre: auditoría firmada con la clave del usuario que la ejecuta, verificación
de la firma y del manifiesto, detección de alteraciones, auditoría sin firma
cuando no hay usuario, rol por defecto de menor privilegio y ausencia de
nombres del autor como valores por defecto en la CLI.

Cada test trabaja en un sandbox propio (STTM_ROOT temporal). La verificación
corre en un proceso aparte para no mezclar raíces entre tests.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
PASS_ADMIN = "clave-admin-123456"


class TestFirmaAuditoria(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sttm_firma_aud_"))
        shutil.copytree(SCRIPTS_DIR, self.tmp / "scripts")
        (self.tmp / "auditorias").mkdir()
        (self.tmp / "docs").mkdir()
        (self.tmp / "web").mkdir()
        (self.tmp / "data" / "proyectos" / "1-STTM").mkdir(parents=True)
        (self.tmp / "data" / "proyectos" / "1-STTM" / "BITACORA.jsonl").write_text(
            "", encoding="utf-8")
        (self.tmp / "data" / "proyectos.jsonl").write_text(
            json.dumps({"n": 1, "ref_interna": "STTM", "titulo": "T", "descripcion": "d",
                        "creado_utc": "2026-01-01T00:00:00Z", "nivel_inicial": "simple",
                        "nivel_actual": "simple", "primera_auditoria_utc": None,
                        "ultima_auditoria_utc": None, "activo": True}) + "\n",
            encoding="utf-8")
        self.env = os.environ.copy()
        self.env["STTM_ROOT"] = str(self.tmp)
        # Usuario admin con clave propia, creado con el módulo del sandbox.
        self._python(
            "import identidad; identidad.crear_usuario('admin1', "
            f"'{PASS_ADMIN}', 'admin')")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _python(self, codigo):
        r = subprocess.run([sys.executable, "-c",
                            f"import sys; sys.path.insert(0, r'{self.tmp / 'scripts'}'); {codigo}"],
                           env=self.env, capture_output=True, text=True, timeout=60)
        return r

    def _auditar(self, *extra):
        r = subprocess.run(
            [sys.executable, str(self.tmp / "scripts" / "auditar.py"),
             "--proyecto", "1", "--motivo", "prueba de firma", "--tipo", "rapida", *extra],
            env=self.env, capture_output=True, text=True, timeout=120)
        carpetas = [d for d in (self.tmp / "auditorias").iterdir() if d.is_dir()]
        self.assertTrue(carpetas, r.stdout + r.stderr)
        return max(carpetas, key=lambda d: d.name)

    def _verificar(self, carpeta):
        r = self._python(
            "import json, auditoria_meta; "
            f"print(json.dumps(auditoria_meta.verificar_firma_meta(r'{carpeta}')))")
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_auditoria_firmada_se_verifica(self):
        carpeta = self._auditar("--actor", "admin1", "--rol-actor", "admin")
        meta = json.loads((carpeta / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["firma"]["firmado_por"], "admin1")
        self.assertEqual(meta["firma"]["rol"], "admin")
        self.assertIn("manifiesto_sha256", meta)
        v = self._verificar(carpeta)
        self.assertEqual(v["estado"], "firmada_valida", v)
        self.assertEqual(v["manifiesto"], "ok", v)

    def test_meta_alterado_invalida_la_firma(self):
        carpeta = self._auditar("--actor", "admin1", "--rol-actor", "admin")
        ruta = carpeta / "meta.json"
        meta = json.loads(ruta.read_text(encoding="utf-8"))
        meta["motivo"] = "motivo cambiado a mano"
        ruta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        self.assertEqual(self._verificar(carpeta)["estado"], "firma_invalida")

    def test_manifiesto_alterado_se_detecta(self):
        carpeta = self._auditar("--actor", "admin1", "--rol-actor", "admin")
        man = carpeta / "manifiesto.json"
        man.write_text(man.read_text(encoding="utf-8") + "\n ", encoding="utf-8")
        self.assertEqual(self._verificar(carpeta)["manifiesto"], "alterado")

    def test_sin_actor_queda_sin_firma(self):
        carpeta = self._auditar()
        meta = json.loads((carpeta / "meta.json").read_text(encoding="utf-8"))
        self.assertIsNone(meta["firma"])
        self.assertEqual(self._verificar(carpeta)["estado"], "sin_firma")

    def test_rol_por_defecto_es_lector(self):
        carpeta = self._auditar("--actor", "admin1")
        meta = json.loads((carpeta / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["firma"]["rol"], "lector")

    def test_cli_no_tiene_nombres_del_autor_por_defecto(self):
        # La cabecera de autoría sí lleva el nombre (convención); los
        # valores por defecto no pueden tenerlo.
        codigo = (SCRIPTS_DIR / "auditoria_meta.py").read_text(encoding="utf-8")
        self.assertNotIn('default="Martín', codigo)
        self.assertNotIn("default='Martín", codigo)
        r = subprocess.run([sys.executable, str(SCRIPTS_DIR / "auditoria_meta.py"), "generar",
                            "--proyecto", "1"], env=self.env, capture_output=True,
                           text=True, timeout=30)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
