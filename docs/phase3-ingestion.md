# Fase 3: ingesta y documentos

La ingesta síncrona acepta PDF, TXT, Markdown y CSV de hasta 10 MiB. Se valida nombre sin rutas, extensión y MIME antes de crear la fila. PDF usa `pypdf`; los otros formatos usan la biblioteca estándar. El texto se normaliza y se divide en bloques de 1200 caracteres con solapamiento de 200. Cada bloque conserva `document_id`, índice y metadatos de origen.

Los embeddings se generan con Ollama `POST /api/embed`, modelo `bge-m3`, dimensión 1024. Una falla marca el documento como `error`; no se anuncia como `ready`. Al repetir un archivo del mismo usuario (checksum SHA-256), o un cóctel remoto (external_id), se reutiliza la fila y se reemplazan sus chunks.

En los cócteles de TheCocktailDB se normaliza `strDrinkThumb` como `image_url` sólo si es una URL HTTPS. Ese valor se conserva en los metadatos del documento y del fragmento para que la API lo entregue como referencia externa; no se descargan ni almacenan bytes de imagen. Los uploads no tienen imagen y exponen `image_url: null`.

## Configuración

Además de las variables de Supabase y Ollama existentes:

- `THECOCKTAILDB_BASE_URL` (por defecto API global oficial v1/1)
- `THECOCKTAILDB_MAX_ITEMS` (100 por defecto; respeta el límite de listados gratuitos)
- `THECOCKTAILDB_TIMEOUT_SECONDS`
- `ADMIN_INGEST_KEY` (secreto backend para `X-Admin-Ingest-Key`)
- `MAX_UPLOAD_BYTES`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `EMBEDDING_DIMENSIONS`

`POST /documents` es autenticado y síncrono aunque conserva HTTP 202; su respuesta contiene el estado real. `GET /documents`, `GET /documents/{id}` y `DELETE /documents/{id}` usan el JWT del usuario y RLS. Los documentos globales de TheCocktailDB no se pueden borrar por usuarios. `POST /admin/ingest/cocktails` exige exclusivamente la cabecera administrativa y limita `limit` a 100.

TheCocktailDB es la fuente global y debe atribuirse al proveedor: https://www.thecocktaildb.com/. Sus datos pueden cambiar y la API gratuita tiene límites de listado; la ingesta acotada es intencional.
