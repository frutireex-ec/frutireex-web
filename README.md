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
| `data/sitio.json` | Nota, número y reseñas recientes de Google (los actualiza la tarea diaria) |
| `scripts/actualizar.py`, `.github/workflows/actualizar.yml` | La tarea diaria |

Cada cambio que se sube a la rama `main` se publica solo en 1–2 minutos.

## Actualización diaria automática
Cada madrugada (05:17, hora de Ecuador) GitHub corre la tarea **"Actualización diaria de la página"**. No hace falta tener ninguna computadora encendida. Trae de Google la nota, el número de opiniones y las **reseñas más recientes**, y las pone en «Nuestros clientes».

Necesita **uno** de estos secretos:

| Secreto | Qué da | Cómo se consigue |
|---|---|---|
| `SERPAPI_KEY` (recomendado) | Nota, número de opiniones y las reseñas **más nuevas** primero | Cuenta gratis en https://serpapi.com (100 consultas al mes; la tarea usa unas 30). En **Dashboard** → **Your Private API Key** |
| `GOOGLE_PLACES_KEY` | Nota y número exactos; las reseñas que da Google son las "más relevantes", no siempre las más nuevas | https://console.cloud.google.com → proyecto → activar **Places API (New)** → **Credenciales** → clave de API |

**Cómo se pone un secreto:** en GitHub, este repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Nombre: el de la tabla. Valor: la clave.

Para no mostrar la reseña de alguien (por ejemplo, del equipo), agrega su nombre en `data/sitio.json` → `google.excluir`.

Para probar la tarea sin esperar a la madrugada: pestaña **Actions** → "Actualización diaria de la página" → **Run workflow**.

## Contador de visitas
El pie de página muestra cuántas veces se ha abierto la página (una por persona cada vez que entra; recargar no suma). Usa el contador público y gratuito https://abacus.jasoncameron.dev (clave `frutireex-com/visitas`). Para ver el número en cualquier momento: https://abacus.jasoncameron.dev/get/frutireex-com/visitas
