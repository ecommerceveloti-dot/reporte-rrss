"""
lanzador_oculto.py — Corre scripts de esta carpeta SIN abrir ninguna ventana de consola (para el Programador de tareas).

Se ejecuta con pythonw.exe (no abre consola) y lanza cada script con python.exe + CREATE_NO_WINDOW, dejando la salida en cache/<log>.

  pythonw.exe lanzador_oculto.py --log meli_api_ejecuciones.txt -- script1.py arg1 arg2 :: script2.py :: script3.py arg

Cada bloque separado por "::" es un comando; se ejecutan en orden y un fallo no detiene a los siguientes (igual que el .bat anterior).
"""
import os
import subprocess
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")


def _python_exe():
    exe = sys.executable
    if os.path.basename(exe).lower() == "pythonw.exe":
        cand = os.path.join(os.path.dirname(exe), "python.exe")
        if os.path.exists(cand):
            return cand
    return exe


def main(argv):
    if "--log" not in argv or "--" not in argv:
        return 2
    log = argv[argv.index("--log") + 1]
    bloques, actual = [], []
    for a in argv[argv.index("--") + 1:]:
        if a == "::":
            if actual:
                bloques.append(actual)
            actual = []
        else:
            actual.append(a)
    if actual:
        bloques.append(actual)
    os.makedirs(CACHE_DIR, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    py = _python_exe()
    codigo = 0
    with open(os.path.join(CACHE_DIR, log), "ab") as salida:
        for b in bloques:
            r = subprocess.run([py, os.path.join(BASE_DIR, b[0])] + b[1:], cwd=BASE_DIR, env=env, stdout=salida,
                               stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags)
            if r.returncode:
                codigo = r.returncode
                salida.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {b[0]} terminó con código {r.returncode}\n".encode("utf-8"))
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
