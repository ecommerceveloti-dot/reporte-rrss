"""Lee Base_Datos_KPIs_Redes_Sociales.xlsx (hoja Registro_Diario) y genera data.json para el dashboard.

Las columnas se ubican por NOMBRE (no por letra) y la fila de encabezado se detecta sola,
así que agregar/mover columnas o filas de título no rompe la lectura. Las interacciones y
el ER se recalculan aquí, sin depender de las fórmulas del Excel.
"""
import json
import unicodedata
from datetime import datetime, date
from pathlib import Path

import openpyxl

CARPETA = Path(__file__).resolve().parent
EXCEL = CARPETA / "Base_Datos_KPIs_Redes_Sociales.xlsx"
SALIDA = CARPETA / "data.json"
HOJA = "Registro_Diario"

# campo -> nombres aceptados (normalizados: minúsculas, sin tildes) en Excel o API
COLUMNAS = {
    "date": ["fecha", "date"],
    "platform": ["plataforma", "platform"],
    "content_type": ["formato / tipo", "formato", "tipo", "content_type"],
    "followers": ["seguidores totales", "followers"],
    "new_followers": ["nuevos seguidores", "new_followers"],
    "impressions": ["impresiones / views", "impresiones", "views", "impressions"],
    "reach": ["alcance unico", "alcance", "reach"],
    "likes": ["me gusta (likes)", "me gusta", "likes"],
    "comments": ["comentarios", "comments"],
    "shares": ["compartidos", "shares"],
    "saves": ["guardados", "saves"],
    "watch_time_seconds": ["tiempo visto (seg)", "tiempo visto", "watch_time_seconds"],
}
NUMERICOS = [k for k in COLUMNAS if k not in ("date", "platform", "content_type")]
PLATAFORMAS = {"instagram": "Instagram", "tiktok": "TikTok", "youtube": "YouTube"}


def norm(texto):
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


def a_numero(valor):
    if valor is None or valor == "":
        return 0
    if isinstance(valor, (int, float)):
        return int(round(valor))
    texto = str(valor).strip().replace(".", "").replace(",", ".")  # formato es-CL: 12.500
    try:
        return int(round(float(texto)))
    except ValueError:
        return 0


def a_fecha(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(valor.strip(), fmt).date()
            except ValueError:
                pass
    return None


def ubicar_encabezado(ws):
    for fila in ws.iter_rows(min_row=1, max_row=30):
        nombres = {norm(c.value): c.column - 1 for c in fila if c.value is not None}
        if "fecha" in nombres and "plataforma" in nombres:
            indices = {}
            for campo, alias in COLUMNAS.items():
                for a in alias:
                    if a in nombres:
                        indices[campo] = nombres[a]
                        break
            return fila[0].row, indices
    raise SystemExit(f"No encontré la fila de encabezado (Fecha / Plataforma) en la hoja {HOJA}")


def leer():
    wb = openpyxl.load_workbook(EXCEL, data_only=True, read_only=True)
    ws = wb[HOJA]
    fila_enc, idx = ubicar_encabezado(ws)
    faltantes = [c for c in ("date", "platform", "impressions") if c not in idx]
    if faltantes:
        raise SystemExit(f"Faltan columnas obligatorias: {faltantes}")

    registros, omitidas = [], 0
    for fila in ws.iter_rows(min_row=fila_enc + 1, values_only=True):
        celda = lambda campo: fila[idx[campo]] if campo in idx and idx[campo] < len(fila) else None
        fecha = a_fecha(celda("date"))
        plataforma = PLATAFORMAS.get(norm(celda("platform")))
        if not fecha or not plataforma:  # filas vacías, totales o plataformas desconocidas
            if any(v not in (None, "") for v in fila):
                omitidas += 1
            continue
        r = {"date": fecha.isoformat(), "platform": plataforma,
             "content_type": str(celda("content_type") or "Sin formato").strip()}
        for campo in NUMERICOS:
            r[campo] = a_numero(celda(campo))
        r["interactions"] = r["likes"] + r["comments"] + r["shares"] + r["saves"]
        registros.append(r)
    wb.close()
    registros.sort(key=lambda r: (r["date"], r["platform"]))
    return registros, omitidas


def main():
    if not EXCEL.exists():
        raise SystemExit(f"No existe {EXCEL}")
    registros, omitidas = leer()
    datos = {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fuente": EXCEL.name,
        "registros": registros,
    }
    nuevo = json.dumps(datos, ensure_ascii=False, indent=1)
    anterior = SALIDA.read_text(encoding="utf-8") if SALIDA.exists() else ""
    cambio = json.loads(anterior)["registros"] != registros if anterior else True
    if cambio:
        SALIDA.write_text(nuevo, encoding="utf-8")
    print(f"{len(registros)} registros leídos, {omitidas} filas omitidas (totales/vacías). "
          f"{'data.json actualizado' if cambio else 'Sin cambios en los datos'}.")
    return cambio


if __name__ == "__main__":
    main()
