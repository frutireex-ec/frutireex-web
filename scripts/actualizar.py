#!/usr/bin/env python3
"""Actualización diaria de www.frutireex.com. La corre GitHub Actions cada madrugada (.github/workflows/actualizar.yml).

- Reseñas de Google (nota, número de opiniones y las opiniones recientes): necesita el secreto GOOGLE_PLACES_KEY.
- Videos nuevos del canal de YouTube: no necesita claves (lista pública del canal).
- Fotos de Instagram: necesita el secreto BEHOLD_FEED (enlace o código del feed de behold.so).

Si un paso falla o no tiene su clave, se deja lo que había: la página nunca se queda vacía.
Solo usa la biblioteca estándar de Python.
"""
import datetime, json, os, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RAIZ, "data")
HOY = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)).date().isoformat()  # fecha de Ecuador


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
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def google(sitio):
    clave = os.environ.get("GOOGLE_PLACES_KEY", "").strip()
    if not clave:
        print("Google: falta el secreto GOOGLE_PLACES_KEY; se mantiene el número que hay.")
        return
    g = sitio.setdefault("google", {})
    lugar = (os.environ.get("GOOGLE_PLACE_ID") or g.get("place_id") or "").strip()
    if not lugar:  # la primera vez se busca el local por nombre y se guarda su identificador
        cuerpo = json.dumps({"textQuery": "Fruti Reex fresas con chocolate Guayllabamba", "languageCode": "es"}).encode()
        r = json.loads(pedir("https://places.googleapis.com/v1/places:searchText",
                             {"Content-Type": "application/json", "X-Goog-Api-Key": clave,
                              "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress"}, cuerpo, "POST"))
        candidatos = [p for p in r.get("places", []) if re.search(r"re+x", p.get("displayName", {}).get("text", ""), re.I)]
        if not candidatos:
            print("Google: no se encontró el local en la búsqueda.")
            return
        lugar = candidatos[0]["id"]
        g["place_id"] = lugar
        print("Google: local encontrado:", candidatos[0].get("displayName", {}).get("text"), "·", candidatos[0].get("formattedAddress"))
    r = json.loads(pedir("https://places.googleapis.com/v1/places/" + urllib.parse.quote(lugar) + "?languageCode=es",
                         {"X-Goog-Api-Key": clave, "X-Goog-FieldMask": "rating,userRatingCount,reviews"}))
    if r.get("userRatingCount"):
        g["opiniones"] = int(r["userRatingCount"])
    if r.get("rating"):
        g["nota"] = round(float(r["rating"]), 1)
    resenas = []
    for x in r.get("reviews", [])[:5]:
        texto = (x.get("text") or x.get("originalText") or {}).get("text", "").strip()
        if not texto:
            continue
        resenas.append({"autor": x.get("authorAttribution", {}).get("displayName", "Cliente"), "nota": x.get("rating", 5),
                        "texto": texto[:600], "cuando": x.get("relativePublishTimeDescription", ""), "fecha": (x.get("publishTime") or "")[:10]})
    resenas.sort(key=lambda z: z.get("fecha", ""), reverse=True)
    if resenas:
        g["resenas"] = resenas
    g["fuente"] = "Google"
    g["fecha"] = HOY
    print("Google:", g.get("nota"), "estrellas,", g.get("opiniones"), "opiniones,", len(resenas), "reseñas recientes.")


def youtube(sitio):
    canal = (sitio.get("youtube") or {}).get("canal")
    if not canal:
        return
    xml = pedir("https://www.youtube.com/feeds/videos.xml?channel_id=" + urllib.parse.quote(canal))
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    videos = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        vid = e.findtext("yt:videoId", namespaces=ns)
        if vid:
            videos.append({"id": vid, "titulo": e.findtext("a:title", default="", namespaces=ns),
                           "fecha": (e.findtext("a:published", default="", namespaces=ns) or "")[:10]})
    if videos:
        guardar("youtube.json", {"videos": videos[:8], "fecha": HOY})
    print("YouTube:", len(videos), "videos.")


def instagram():
    feed = os.environ.get("BEHOLD_FEED", "").strip()
    if not feed:
        print("Instagram: falta el secreto BEHOLD_FEED; se muestra la cuenta directamente.")
        return
    if not feed.startswith("https://"):
        feed = "https://feeds.behold.so/" + feed
    d = json.loads(pedir(feed))
    posts = d.get("posts", []) if isinstance(d, dict) else d
    salida = []
    for p in posts[:9]:
        tam = (p.get("sizes") or {}).get("medium") or {}
        img = tam.get("mediaUrl") or p.get("thumbnailUrl") or p.get("mediaUrl")
        if p.get("mediaType") == "VIDEO" and not tam.get("mediaUrl"):
            img = p.get("thumbnailUrl") or img
        if img and p.get("permalink"):
            salida.append({"url": p["permalink"], "img": img, "texto": (p.get("prunedCaption") or p.get("caption") or "")[:200],
                           "fecha": (p.get("timestamp") or "")[:10]})
    if salida:
        guardar("instagram.json", {"posts": salida, "fecha": HOY})
    print("Instagram:", len(salida), "fotos.")


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
    for nombre, paso in (("Google", lambda: google(sitio)), ("YouTube", lambda: youtube(sitio)), ("Instagram", instagram)):
        try:
            paso()
        except Exception as e:  # un paso que falla no detiene a los demás
            print(nombre + ": no se pudo actualizar (" + type(e).__name__ + ": " + str(e)[:200] + "). Se deja lo anterior.")
    sitio["revisado"] = HOY
    guardar("sitio.json", sitio)
    cifras_en_pagina(sitio)


if __name__ == "__main__":
    sys.exit(main())
