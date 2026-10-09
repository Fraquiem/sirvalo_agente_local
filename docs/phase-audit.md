# Auditoría de fases

Fecha de actualización: 2026-10-09.

Auditoría estática del repositorio más evidencia registrada de recorridos runtime realizados el 2026-10-09. Las evidencias runtime se distinguen de las implementaciones sólo leídas; esta auditoría no repite todos los recorridos remotos.

| Fase | Estado | Evidencia | Bloqueo principal |
|---|---|---|---|
| 0. Alineación y entorno | Parcial | Alcance, stack, ramas previstas, `.env.example`, modelos Ollama y Supabase documentados. | Falta inventario exacto de versiones, responsables, protección remota de `main` y decisión sobre despliegue cloud. |
| 1. Contrato API | Parcial | `docs/api-contract.md` define operaciones, límites numéricos, JWT, respuestas RAG, fuentes y rechazo; FastAPI ya publica health, auth y chat en OpenAPI. | Falta validar intención, comprobar respuestas contra Supabase y completar documentos/RAG. |
| 2. Supabase/Auth/pgvector | Parcial | Cuatro tablas y `match_documents` responden por PostgREST autenticado; `bge-m3` produce 1024 dimensiones; FastAPI ya tiene dependencia JWT contra `/auth/v1/user`. | Email Auth, pruebas con dos usuarios, RLS detallado, índice HNSW y extensión no están verificados end-to-end; falta probar el runtime del backend. |
| 3. Ingesta | Implementado verificado | Ingesta real de Markdown y de `Melya` desde TheCocktailDB con Ollama `bge-m3`, documentos `ready`, embeddings 1024 y persistencia en Supabase; consulta RPC recuperó ambos tipos de fuente. | Falta comprobar aislamiento con dos usuarios. |
| 4. Agente RAG | Implementado verificado con calibración inicial | La pregunta española sobre `Melya` pasó con threshold `0.60` y devolvió fuente `cocktaildb`; pregunta fuera de corpus fue rechazada; historial real persistió ambos roles. | Vigilar falsos positivos y subir el threshold si aparecen; falta medir latencia formal. |
| 5. API FastAPI | Parcial implementado | `main.py` registra auth/chat/documents, `/health` es público y la API expone carga, listado, detalle, borrado, chat e historial. | Falta prueba con dos usuarios y frontend. |
| 6. Frontend | Parcial scaffold | React/Vite y variables públicas previstas. | UI estática; sin Auth, chat, documentos, fuentes ni errores.
| 7. Integración | Implementado parcialmente verificado | Se ejecutó autenticación → ingesta TheCocktailDB/archivo → embedding → recuperación → generación/rechazo → historial; los usuarios temporales se eliminaron. | Falta recorrido con frontend, dos usuarios y evidencias formales de latencia.
| 8. Entrega | Parcial documental | README, plan, contrato, migración y validación de modelos. | Faltan documento técnico, diagramas, diapositivas, despliegue/evidencias finales. |

## Trabajo realizado en esta iteración

- Se implementó el adaptador de TheCocktailDB con enumeración por letra, `lookup.php`, normalización de los 15 slots de ingredientes, URL de origen y límite máximo de 100 elementos.
- Se implementó validación y extracción de PDF, TXT, Markdown y CSV, con límite de 10 MiB, nombres seguros, MIME permitido, rechazo de archivos vacíos/ilegibles y dependencia `pypdf`.
- Se implementó normalización, chunking determinista de 1200 caracteres con solapamiento de 200 y embeddings mediante Ollama `/api/embed`.
- Se implementó persistencia REST de Supabase con escritura `service_role` sólo en backend, lectura/borrado con el JWT del usuario y reemplazo de chunks.
- Se añadieron índices únicos para idempotencia por `external_id` global de TheCocktailDB y por `(owner_id, checksum)` en uploads.
- Se publicaron `POST/GET/DELETE /documents`, detalle por ID y `POST /admin/ingest/cocktails` protegido por `X-Admin-Ingest-Key`.
- Se documentaron configuración, atribución y límites en `docs/phase3-ingestion.md` y `.env.example`.
- Verificaciones reproducibles:
  - `docker compose build backend` pasó.
  - Ollama respondió: `bge-m3` produjo un vector de 1024 dimensiones y `qwen3.5:9b` generó una respuesta con `think=false`.
  - Se creó un usuario temporal confirmado mediante Admin Auth, se inició sesión y se obtuvo JWT sin imprimirlo.
  - Se cargó `/tmp/rag-smoke.md`; el documento quedó `ready` con persistencia real en Supabase.
  - La RPC `match_documents` recuperó el fragmento privado usando el JWT.
  - La pregunta respaldada sobre `Melya` devolvió `context_sufficient=true` y fuente `source_type=cocktaildb`.
  - La pregunta española general sobre `Melya` pasó con threshold `0.60`, similarity `0.618609`, respuesta y fuente `source_type=cocktaildb`.
  - `/conversations` y `/conversations/{id}/messages` devolvieron el historial con roles `user` y `assistant`.
  - El usuario temporal y sus datos asociados se eliminaron después del recorrido.
- El primer intento dentro de Docker con `localhost` no pudo alcanzar Ollama; se repitió con `--network host`, que es la configuración necesaria cuando Ollama escucha en el host local.

## Decisión de continuación

La siguiente prioridad es calibrar el umbral de recuperación con preguntas naturales en español y probar aislamiento RLS con dos usuarios. Después corresponde integrar el frontend.

1. Cerrar Fase 0: versiones, responsables, protección remota de `main` y decisión sobre despliegue.
2. Cerrar Fase 1: validación de intención, autorización administrativa y OpenAPI observado.
3. Completar Fase 2: prueba HTTP de JWT y aislamiento RLS con dos usuarios.
4. Calibrar Fase 4: recall frente a falsos positivos y latencia de `qwen3.5:9b`.
5. Implementar Fase 6: frontend de autenticación, documentos, chat, fuentes e historial.

## Decisión de modelo

Modelo generativo provisional: `qwen3.5:9b` con razonamiento desactivado y salida limitada. Embeddings: `bge-m3`, dimensión 1024.

## Evidencia remota registrada

- Auth Supabase: HTTP 200.
- `documents`, `document_chunks`, `conversations`, `messages`: HTTP 200 con consultas `limit=0` autenticadas.
- `match_documents`: HTTP 200 con vector de prueba de 1024 dimensiones.
- Las sondas no modificaron datos.
