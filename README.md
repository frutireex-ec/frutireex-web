# Fruti Reex · página web

Página de la marca Fruti Reex (Guayllabamba, Quito), publicada en **https://www.frutireex.com** con GitHub Pages.

Es una página estática (HTML, CSS, JavaScript y la carpeta `assets` con fotos, videos y stickers). No usa base de datos ni guarda datos de nadie.

- `frutireex.com` y `www.frutireex.com` → esta página.
- `app.frutireex.com` → la app de la tarjeta de fidelidad (proyecto aparte). El botón **"Ingresar a la app"** lleva ahí.
- Atajos: `/app`, `/ingresar`, `/registro`, `/login` y `/tarjeta` llevan a https://app.frutireex.com.

## Archivos
| Archivo | Para qué |
|---|---|
| `index.html` | La página completa |
| `assets/` | Fotos (`assets/f`), reels (`assets/r`), videos, stickers y letras |
| `404.html` | Página de "no encontrada" |
| `CNAME` | Dominio de GitHub Pages (www.frutireex.com) |
| `.nojekyll` | Publicar los archivos tal cual |
| `robots.txt`, `sitemap.xml` | Para Google |
| `data/` | Reseñas de Google, videos de YouTube y fotos de Instagram (los actualiza la tarea diaria) |
| `scripts/actualizar.py`, `.github/workflows/actualizar.yml` | La tarea diaria |

Cada cambio que se sube a la rama `main` se publica solo en 1–2 minutos.

## Actualización diaria automática
Cada madrugada (05:17, hora de Ecuador) GitHub corre la tarea **"Actualización diaria de la página"**. No hace falta tener ninguna computadora encendida.

| Qué se actualiza | Qué necesita |
|---|---|
| Videos nuevos de YouTube (@Fruti_reex) | Nada: ya funciona |
| TikTok y Facebook en «Lo último en nuestras redes» | Nada: se cargan solos desde las cuentas oficiales |
| Nota y número de opiniones de Google, y las reseñas recientes | El secreto `GOOGLE_PLACES_KEY` |
| Fotos de Instagram en cuadrícula | El secreto `BEHOLD_FEED` (si no está, se muestra la cuenta de Instagram) |
| Contador de visitas | Poner el código de GoatCounter en `data/sitio.json` → `contador.goatcounter` (y `"mostrar": true` para que se vea en el pie de página) |

**Cómo se pone un secreto:** en GitHub, este repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Nombre: el de la tabla. Valor: la clave.

**Clave de Google (`GOOGLE_PLACES_KEY`):** en https://console.cloud.google.com crea un proyecto, activa **Places API (New)**, y en **Credenciales** crea una **clave de API**. Restríngela a "Places API (New)". Con una consulta al día queda dentro del uso gratuito de Google.

**Instagram (`BEHOLD_FEED`):** crea una cuenta gratis en https://behold.so, conecta el Instagram @frutireex, crea un feed "JSON" y copia su enlace (https://feeds.behold.so/...).

Para probar la tarea sin esperar a la madrugada: pestaña **Actions** → "Actualización diaria de la página" → **Run workflow**.
