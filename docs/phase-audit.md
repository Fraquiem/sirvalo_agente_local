# Auditoría de fases

Fecha de actualización: 2026-10-09.

Auditoría estática del repositorio más evidencia registrada de recorridos runtime realizados el 2026-10-09. Las evidencias runtime se distinguen de las implementaciones sólo leídas; esta auditoría no repite todos los recorridos remotos.

| Fase | Estado | Evidencia | Bloqueo principal |
|---|---|---|---|
| 0. Alineación y entorno | Parcial | Alcance, stack, ramas previstas, `.env.example`, modelos Ollama y Supabase documentados. | Falta inventario exacto de versiones, responsables, protección remota de `main` y decisión sobre despliegue cloud. |
| 1. Contrato API | Parcial | `docs/api-contract.md` define operaciones, límites numéricos, JWT, respuestas RAG, fuentes y rechazo; FastAPI ya publica health, auth y chat en OpenAPI. | Falta validar intención, comprobar respuestas contra Supabase y completar documentos/RAG. |
| 2. Supabase/Auth/pgvector | Parcial | Cuatro tablas y `match_documents` responden por PostgREST autenticado; `bge-m3` produce 1024 dimensiones; FastAPI valida tokens contra `/auth/v1/user` y ahora expone renovación de sesión. | Email Auth, pruebas con dos usuarios, RLS detallado, índice HNSW y extensión no están verificados end-to-end; el frontend debe probar restauración y expiración con una cuenta real. |
| 3. Ingesta | Implementado verificado | Ingesta real de Markdown y de `Melya`/`Negroni`/`Mojito`/`Margarita` desde TheCocktailDB con Ollama `bge-m3`, documentos `ready`, embeddings 1024, `image_url` HTTPS y persistencia en Supabase; la recuperación híbrida añadió `Daiquiri` y `Whiskey Sour` bajo demanda. | Falta comprobar aislamiento con dos usuarios. |
| 4. Agente RAG | Implementado verificado | Tras Piña Colada, «Debo agitar algo en esta receta?» y «¿Debería agitarla?» respondieron licuar/no agitar con fuente Piña Colada (y guía cuando fue cargada); no se usó Margarita. Una pregunta fuera de tema siguió rechazada. | Vigilar falsos positivos y calibrar thresholds; falta medir latencia formal. |
| 5. API FastAPI | Parcial implementado | `main.py` registra auth/chat/documents, `/health` es público y la API expone carga, listado, detalle, borrado, chat e historial; `POST /auth/refresh` renueva sesiones. | Falta prueba con dos usuarios, frontend y recorrido completo de expiración/renovación. |
| 6. Frontend | Parcial implementado | React/Vite tiene pantalla de login/registro, chat, biblioteca, fuentes, logout, persiste/renueva `refresh_token` y evita renovaciones concurrentes. | Falta verificar login real, expiración de token, restauración tras recarga y errores con una cuenta real. |
| 7. Integración | Implementado parcialmente verificado | Se ejecutó autenticación → ingesta TheCocktailDB/archivo → embedding → recuperación → generación/rechazo → historial; los usuarios temporales se eliminaron. | Falta recorrido con frontend, dos usuarios y evidencias formales de latencia. |
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
  - La pregunta `¿Cómo preparo un negroni equilibrado?` pasó con threshold `0.55`, similarity `0.578740`, respuesta fundamentada y fuente `Negroni`.
  - `/conversations` y `/conversations/{id}/messages` devolvieron el historial con roles `user` y `assistant`.
  - El usuario temporal y sus datos asociados se eliminaron después del recorrido.
- Se reprodujo el fallo conversacional: `conversation_id` se guardaba, pero no cargaba historial en el grafo; el vectorizador devolvía Margarita para la pregunta de seguimiento de Piña Colada.
- Se añadió carga de los últimos 8 mensajes autorizados por RLS. Referencias explícitas y elípticas de técnica/servicio reutilizan chunks citados en la última respuesta fundamentada; el prompt no considera la respuesta anterior como fuente factual.
- Recorrido real: Piña Colada → «Debo agitar algo en esta receta?» y «¿Debería agitarla?» → respuesta basada en la receta que indica licuar, con fuente Piña Colada; en la prueba con guía cargada también citó `guia-cocteleria.md`. No citó Margarita.
- Una pregunta sin relación («¿Cuál es la capital de Francia?») en la misma conversación mantuvo `context_sufficient=false` y `sources=[]`.
- Prueba aislada del filtro: si recuperación vectorial devuelve Piña Colada + guía + Margarita, conserva Piña Colada/guía y excluye Margarita.
- El primer intento dentro de Docker con `localhost` no pudo alcanzar Ollama; se repitió con `--network host`, que es la configuración necesaria cuando Ollama escucha en el host local.

## Decisión de continuación

La siguiente prioridad es probar más referencias elípticas y ejecutar la matriz de aislamiento RLS con dos usuarios. Si aparecen falsos positivos, subir progresivamente el threshold general `0.55`, el de ingredientes `0.40` o el de seguimientos `0.35`.

1. Cerrar Fase 0: versiones, responsables, protección remota de `main` y decisión sobre despliegue.
2. Cerrar Fase 1: validación de intención, autorización administrativa y OpenAPI observado.
3. Completar Fase 2: prueba HTTP de JWT y aislamiento RLS con dos usuarios.
4. Calibrar Fase 4: recall frente a falsos positivos y latencia de `qwen3.5:9b`.
5. Cerrar integración conversacional de Fase 7 y completar pruebas frontend.

## Decisión de modelo

Modelo generativo provisional: `qwen3.5:9b` con razonamiento desactivado y salida limitada. Embeddings: `bge-m3`, dimensión 1024.

## Evidencia remota registrada

- Auth Supabase: HTTP 200.
- `documents`, `document_chunks`, `conversations`, `messages`: HTTP 200 con consultas `limit=0` autenticadas.
- `match_documents`: HTTP 200 con vector de prueba de 1024 dimensiones.
- Las sondas no modificaron datos.
