#!/usr/bin/env python3
"""Actualización diaria de www.frutireex.com. La corre GitHub Actions cada madrugada (.github/workflows/actualizar.yml).

Trae de Google la nota, el número de opiniones y las reseñas MÁS RECIENTES del local, y las deja en
data/sitio.json (y las cifras también escritas en index.html).

Necesita UNO de estos secretos del repositorio:
- SERPAPI_KEY (recomendado): serpapi.com, plan gratis de 100 consultas al mes. Da las reseñas ordenadas
  de la más nueva a la más vieja.
- GOOGLE_PLACES_KEY: clave de Google Cloud (Places API New). Da la nota y el número exactos, pero las
  reseñas que entrega Google son las "más relevantes", no siempre las más nuevas.

Si no hay clave o algo falla, se deja lo que había: la página nunca se queda vacía.
Solo usa la biblioteca estándar de Python.
"""
import datetime, json, os, re, sys, urllib.parse, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RAIZ, "data")
AHORA = datetime.datetime.now(datetime.timezone.utc)
HOY = (AHORA - datetime.timedelta(hours=5)).date().isoformat()  # fecha de Ecuador
DATA_ID = "0x91d58b7485fdcf89:0x2e2cef1353b72836"               # Frutireex - Fresas con chocolate (Google Maps)


def leer(nombre, por_defecto):
    try:
        with open(os.path.join(DATA, nombre), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return por_defecto


def guardar(nombre, datos):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, nombre), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def pedir(url, cabeceras=None, cuerpo=None, metodo=None):
    req = urllib.request.Request(url, data=cuerpo, headers=dict(cabeceras or {}), method=metodo)
    req.add_header("User-Agent", "frutireex-actualizacion/1.0 (+https://www.frutireex.com)")
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def fecha_desde_texto(txt):
    """«hace 2 días», «hace una semana», «a week ago»… → fecha aproximada (AAAA-MM-DD)."""
    t = (txt or "").lower()
    n = re.search(r"(\d+)", t)
    k = int(n.group(1)) if n else 1
    dias = 0
    if re.search(r"hora|minuto|hour|minute", t):
        dias = 0
    elif re.search(r"día|dia|day", t):
        dias = k
    elif re.search(r"semana|week", t):
        dias = 7 * k
    elif re.search(r"mes|month", t):
        dias = 30 * k
    elif re.search(r"año|ano|year", t):
        dias = 365 * k
    return ((AHORA - datetime.timedelta(hours=5)) - datetime.timedelta(days=dias)).date().isoformat()


def limpiar(resenas, excluir):
    fuera = {x.strip().lower() for x in excluir or []}
    vistas, salida = set(), []
    for r in resenas:
        if not r.get("texto") or r.get("autor", "").strip().lower() in fuera:
            continue
        clave = (r.get("autor"), r.get("texto")[:40])
        if clave in vistas:
            continue
        vistas.add(clave)
        salida.append(r)
    salida.sort(key=lambda z: z.get("fecha", ""), reverse=True)
    return salida[:6]


def con_serpapi(g, clave):
    q = urllib.parse.urlencode({"engine": "google_maps_reviews", "data_id": g.get("data_id") or DATA_ID,
                                "sort_by": "newestFirst", "hl": "es", "api_key": clave})
    d = json.loads(pedir("https://serpapi.com/search.json?" + q))
    if d.get("error"):
        raise RuntimeError(d["error"])
    info = d.get("place_info") or {}
    if info.get("reviews"):
        g["opiniones"] = int(info["reviews"])
    if info.get("rating"):
        g["nota"] = round(float(info["rating"]), 1)
    resenas = []
    for x in d.get("reviews", [])[:20]:
        texto = (x.get("snippet") or (x.get("extracted_snippet") or {}).get("original") or "").strip()
        fecha = (x.get("iso_date") or "")[:10] or fecha_desde_texto(x.get("date"))
        resenas.append({"autor": (x.get("user") or {}).get("name", "Cliente"), "nota": x.get("rating", 5),
                        "texto": texto[:600], "fecha": fecha})
    return resenas


def con_places(g, clave):
    lugar = (os.environ.get("GOOGLE_PLACE_ID") or g.get("place_id") or "").strip()
    if not lugar:  # la primera vez se busca el local por nombre y se guarda su identificador
        cuerpo = json.dumps({"textQuery": "Frutireex Fresas con chocolate Guayllabamba", "languageCode": "es"}).encode()
        r = json.loads(pedir("https://places.googleapis.com/v1/places:searchText",
                             {"Content-Type": "application/json", "X-Goog-Api-Key": clave,
                              "X-Goog-FieldMask": "places.id,places.displayName"}, cuerpo, "POST"))
        candidatos = [p for p in r.get("places", []) if re.search(r"re+x", p.get("displayName", {}).get("text", ""), re.I)]
        if not candidatos:
            raise RuntimeError("no se encontró el local")
        lugar = g["place_id"] = candidatos[0]["id"]
    r = json.loads(pedir("https://places.googleapis.com/v1/places/" + urllib.parse.quote(lugar) + "?languageCode=es",
                         {"X-Goog-Api-Key": clave, "X-Goog-FieldMask": "rating,userRatingCount,reviews"}))
    if r.get("userRatingCount"):
        g["opiniones"] = int(r["userRatingCount"])
    if r.get("rating"):
        g["nota"] = round(float(r["rating"]), 1)
    resenas = []
    for x in r.get("reviews", []):
        texto = (x.get("text") or x.get("originalText") or {}).get("text", "").strip()
        resenas.append({"autor": x.get("authorAttribution", {}).get("displayName", "Cliente"), "nota": x.get("rating", 5),
                        "texto": texto[:600], "fecha": (x.get("publishTime") or "")[:10]})
    return resenas


def google(sitio):
    g = sitio.setdefault("google", {})
    serp, places = os.environ.get("SERPAPI_KEY", "").strip(), os.environ.get("GOOGLE_PLACES_KEY", "").strip()
    if not serp and not places:
        print("Google: falta el secreto SERPAPI_KEY (o GOOGLE_PLACES_KEY); se mantiene lo que hay.")
        return
    nuevas = con_serpapi(g, serp) if serp else con_places(g, places)
    # se juntan con las que ya había, para no perder las recientes si Google devuelve menos
    juntas = limpiar(nuevas + (g.get("resenas") or []), g.get("excluir"))
    if juntas:
        g["resenas"] = juntas
    g["fuente"] = "Google (SerpApi, más recientes)" if serp else "Google (Places)"
    g["fecha"] = HOY
    print("Google:", g.get("nota"), "estrellas,", g.get("opiniones"), "opiniones; reseñas más recientes:",
          ", ".join(r["autor"] + " (" + r.get("fecha", "") + ")" for r in juntas[:3]))


def cifras_en_pagina(sitio):
    """Deja las cifras también escritas en index.html (así se ven aunque el navegador no lea data/sitio.json)."""
    ruta = os.path.join(RAIZ, "index.html")
    if not os.path.exists(ruta):
        return
    g = sitio.get("google", {})
    html = original = open(ruta, encoding="utf-8").read()
    if g.get("opiniones"):
        n = "{:,}".format(int(g["opiniones"])).replace(",", ".")
        html = re.sub(r'(<span data-g="opiniones">)[\d.]+( opiniones en Google</span>)', r"\g<1>" + n + r"\g<2>", html)
    if g.get("nota"):
        nota = ("%.1f" % float(g["nota"])).replace(".", ",")
        html = re.sub(r'(<b data-g="nota">)[\d,]+( ★</b>)', r"\g<1>" + nota + r"\g<2>", html)
        html = re.sub(r'(<b class="disp" data-g="nota-sola">)[\d,]+(</b>)', r"\g<1>" + nota + r"\g<2>", html)
    if html != original:
        open(ruta, "w", encoding="utf-8").write(html)
        print("Página: cifras de Google actualizadas en index.html.")


def main():
    sitio = leer("sitio.json", {})
    try:
        google(sitio)
    except Exception as e:  # si falla, se queda lo anterior
        print("Google: no se pudo actualizar (" + type(e).__name__ + ": " + str(e)[:200] + "). Se deja lo anterior.")
    sitio["revisado"] = HOY
    guardar("sitio.json", sitio)
    cifras_en_pagina(sitio)


if __name__ == "__main__":
    sys.exit(main())
