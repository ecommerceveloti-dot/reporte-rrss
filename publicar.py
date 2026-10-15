"""Regenera data.json desde el Excel y, si hay cambios, los sube a GitHub (GitHub Pages se actualiza solo).

Uso: python publicar.py   (o doble clic en publicar.bat)
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
sys.path.insert(0, str(CARPETA))
import actualizar_datos  # noqa: E402

ARCHIVOS = ["index.html", "data.json"]


def git(*args, check=True):
    # sin ventana ni prompts: si la sesión de GitHub expira, falla y queda en el log en vez de colgarse
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    r = subprocess.run(["git", *args], cwd=CARPETA, capture_output=True, text=True, encoding="utf-8", env=env,
                       stdin=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} falló:\n{r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}]", end=" ")
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
