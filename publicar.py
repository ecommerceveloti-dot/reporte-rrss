"""Regenera data.json desde el Excel y, si hay cambios, los sube a GitHub (GitHub Pages se actualiza solo).

Uso: python publicar.py   (o doble clic en publicar.bat)
"""
import subprocess
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
sys.path.insert(0, str(CARPETA))
import actualizar_datos  # noqa: E402

ARCHIVOS = ["index.html", "data.json"]


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=CARPETA, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} falló:\n{r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def main():
    actualizar_datos.main()
    git("add", *ARCHIVOS)
    if not git("diff", "--cached", "--name-only"):
        print("Nada nuevo que publicar.")
        return
    git("commit", "-m", "Actualiza datos RRSS")
    git("push", "origin", "HEAD")
    print("Publicado. GitHub Pages refleja el cambio en 1-2 minutos.")


if __name__ == "__main__":
    main()
