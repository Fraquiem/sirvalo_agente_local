# Plan coordinable del proyecto: agente RAG de cócteles

> **Estado:** plan de trabajo vivo. Cada fase se cierra únicamente cuando se cumplen sus criterios de aceptación.
>
> **Alcance:** aplicación web local para usuarios autenticados que consulta información de cócteles mediante un agente RAG. La base de conocimiento combina datos de **TheCocktailDB** y archivos cargados por el usuario. El backend será **FastAPI/Python**; el frontend, **React + Vite**; la orquestación, **LangChain + LangGraph**; el modelo generativo local, **Ollama**; y la persistencia, **Supabase Auth + PostgreSQL/pgvector**.

## 1. Decisiones y límites acordados

- **Ramas Git:** sólo `main` y `develop`. El trabajo cotidiano se integra en `develop`; `main` contiene entregas estables. No se crean ramas `feature/*` ni equivalentes.
- **Ejecución:** local, sin depender de servidores pagos ni de un proveedor de inferencia comercial. Ollama corre en el equipo de desarrollo.
- **Servicios externos:** se requiere un proyecto Supabase (plan gratuito mientras sea suficiente) para Auth y PostgreSQL/pgvector. Esto no convierte la aplicación en un despliegue pago: la API y el frontend se ejecutan localmente.
- **Backend:** Python con FastAPI. La API valida la sesión de Supabase antes de permitir operaciones protegidas.
- **Frontend:** React con Vite. La interfaz debe poder iniciarse localmente y consumir la URL local del backend.
- **Agente:** el flujo principal se programa con LangChain y LangGraph; no se usan constructores visuales.
- **Conocimiento:** TheCocktailDB aporta datos de cócteles; los archivos aportan conocimiento adicional. Las respuestas deben distinguir o citar sus fuentes cuando sea posible.
- **Modelo local:** Ollama. La selección provisional es `qwen3.5:9b`, porque la validación documentada mostró respuestas contextualizadas en 17.13 s y rechazo fuera de contexto en 12.96 s; `qwen3:4b` tardó 246.10 s con razonamiento visible. La configuración final debe desactivar razonamiento y limitar la salida.

**Inventario local observado (8 de octubre de 2026):** Ollama tiene `qwen3.5:9b` (9.7B, cuantización Q4_K_M, Apache 2.0), `qwen3.5-opencode:latest`, `qwen3:4b` y `bge-m3`. `bge-m3` produce embeddings de 1024 dimensiones.
- **Datos:** modelo mínimo, con una tabla de documentos, una tabla de fragmentos vectorizados y una tabla de conversaciones/mensajes sólo si el historial forma parte de la entrega. No se crea una jerarquía de tablas por ingrediente, utensilio o categoría sin una necesidad funcional comprobada.
- **Seguridad:** las credenciales y secretos viven en variables de entorno. La clave pública de Supabase puede llegar al frontend; nunca se expone una `service_role` key ni otro secreto privilegiado.
**Compatibilidad con la consigna:** `trabajo_agente.md` enumera despliegue en la nube como requisito académico, mientras este plan fija ejecución local sin servidores pagos. El alcance implementable actual es local; antes de la entrega, el equipo debe confirmar si la evaluación exige una URL pública y, sólo si se exige, acordar una excepción explícita sin cambiar silenciosamente la arquitectura.

## 2. Criterio transversal de coordinación

Cada tarea se marca `[x]` sólo cuando existe una evidencia revisable: commit en `develop`, captura/log reproducible, endpoint comprobado, consulta verificable o documento actualizado. En cada integración:

- [ ] indicar responsable y fecha en el tablero o issue correspondiente;
- [ ] actualizar la documentación afectada;
- [ ] conservar sólo cambios compatibles con `main`/`develop`;
- [ ] registrar bloqueos (credenciales, límites de API, hardware o decisiones pendientes) antes de cerrar la fase.

## 3. Fases 0–8

### Fase 0 — Alineación, alcance y entorno

**Objetivo:** dejar el alcance y las condiciones de ejecución inequívocos antes de implementar.

**Tareas verificables**

- [x] Confirmar que el caso de uso es preguntas y recomendaciones fundamentadas sobre cócteles.
- [ ] Confirmar responsables, disponibilidad y criterio de terminado de cada fase.
- [ ] Crear/usar únicamente `main` y `develop`; proteger `main` de cambios no revisados.
- [ ] Inventariar versiones de Python, Node.js, Ollama y Docker (si se usa sólo como ayuda local).
- [x] Instalar y comprobar Ollama; descargar los modelos disponibles y validar `qwen3.5:9b`, `qwen3:4b` y `bge-m3`.
- [x] Crear un proyecto Supabase de desarrollo y configurar su URL y clave pública en variables locales.
- [x] Acordar formatos iniciales de archivo: PDF, TXT, Markdown y CSV; documentar explícitamente cualquier formato no soportado.

**Evidencia:** `docs/model-validation.md`, `.env.example`, `docs/plan-proyecto.md` y la verificación HTTP autenticada de Supabase.

**Pendiente de Fase 0:** responsables, inventario exacto de versiones, protección remota de `main` y decisión sobre el requisito académico de despliegue cloud.

**Aceptación**

- [x] Una persona nueva puede leer este plan y reproducir las decisiones sin elegir otra arquitectura.
- [x] `ollama list` muestra los modelos disponibles y la aplicación puede apuntar a una URL local de Ollama.
- [x] Existe un `.env.example` sin secretos y una lista de variables requerida.

### Fase 1 — Diseño funcional y contrato de la API

**Objetivo:** convertir los requisitos en flujos y contratos comprobables.

**Tareas verificables**

- [x] Definir flujos: registro/inicio de sesión, cierre de sesión, pregunta, carga de archivo, listado/eliminación de documentos y consulta de historial.
- [x] Definir estados de UI: cargando, respuesta fundamentada, contexto insuficiente, error de validación, error de proveedor y sesión expirada.
- [x] Especificar endpoints protegidos, método, entrada, salida, códigos HTTP y requisito de usuario autenticado.
- [x] Especificar el formato de una respuesta RAG: respuesta, fuentes/fragmentos usados y señal de suficiencia del contexto.
- [x] Definir límites numéricos: preguntas de 1–2000 caracteres, archivos PDF/TXT/Markdown/CSV de máximo 10 MiB y recuperación de 5 fragmentos por defecto (máximo 20); documentar mensajes de error seguros.
- [x] Dibujar el flujo LangGraph: recibir → recuperar → evaluar suficiencia → responder o rechazar → guardar historial.

**Evidencia:** [`api-contract.md`](api-contract.md).

**Aceptación**

- [x] El contrato permite implementar frontend y backend sin inventar nombres ni formas de respuesta.
- [x] Cada operación protegida tiene una regla de autorización y un caso de rechazo no autenticado.
- [x] Existe un caso explícito para responder “No tengo suficiente información...” sin llamar al modelo generativo.

### Fase 2 — Supabase Auth y PostgreSQL/pgvector

**Objetivo:** disponer de identidad y persistencia mínima para desarrollo local.

**Configuración externa paso a paso**

1. [x] Crear una cuenta y un proyecto en [Supabase Dashboard](https://supabase.com/dashboard).
2. [x] En **Project Settings → API**, copiar la **Project URL** y la clave pública (`anon`/publishable, según la interfaz). Guardarlas únicamente en variables de entorno locales.
3. [ ] En **Authentication → Providers**, habilitar Email. Mantener la confirmación de correo según la política del proyecto; para una demo local, documentar si se desactiva y por qué.
4. [ ] En **Authentication → URL Configuration**, añadir sólo las URLs locales usadas por el frontend (por ejemplo, `http://localhost:5173`) y su callback si la integración lo requiere.
5. [ ] Abrir **SQL Editor** y habilitar `vector` con la sentencia recomendada por la documentación de [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector). Verificar que la extensión queda instalada.
6. [x] Ejecutar las migraciones `supabase/migrations/20261008000000_initial_schema.sql` y `supabase/migrations/20261008010000_phase3_documents.sql`; las tablas, índices de idempotencia y la RPC responden por PostgREST.
7. [x] Crear índices sólo después de conocer la dimensión del embedding; `bge-m3` produce 1024 dimensiones y la migración usa `vector(1024)`.
8. [ ] Probar registro, inicio y cierre de sesión desde el cliente local. Verificar que un usuario no puede leer ni borrar documentos de otro usuario.
9. [x] No copiar la `service_role` key al frontend, al repositorio ni a tickets. La conexión local fue probada sin imprimir sus valores.

**Estado de verificación actual:** Auth, las cuatro tablas, la RPC `match_documents` y la ingesta real de un upload y de `Melya` respondieron correctamente en el recorrido del 9 de octubre de 2026. El backend valida JWT mediante `current_user`; la escritura de ingesta usa `service_role` sólo en backend y las lecturas de usuario usan su JWT. El backend expone `POST /auth/refresh` y el frontend persiste/renueva el `refresh_token` con una sola renovación concurrente; los errores transitorios no eliminan la sesión local.

**No confirmado todavía:** Email/callback del proyecto, comportamiento A/B/anon para todas las tablas, extensión/índice mediante consulta de catálogo, logout desde frontend y cascadas observadas después de borrar un usuario.

**Tareas verificables**

- [x] Implementar validación del JWT de Supabase en FastAPI.
- [x] Asociar cada documento, fragmento y conversación a `user_id` cuando el dato sea privado; los chunks se asocian mediante `document_id`.
- [x] Definir que los datos de TheCocktailDB sean globales de sólo lectura y los archivos privados por usuario; la migración aplica acceso global sólo a `authenticated`.
- [ ] Verificar RLS con dos usuarios de prueba y una sesión sin autenticar.

**Aceptación**
- [ ] Un JWT inválido o ausente produce un rechazo consistente en todos los endpoints protegidos.
- [ ] La búsqueda vectorial devuelve una fila de prueba con su fragmento y metadatos de origen.

### Fase 3 — Ingesta de TheCocktailDB y archivos

**Objetivo:** construir un corpus reproducible y trazable.

**Tareas verificables**

- [x] Consultar la [documentación oficial de TheCocktailDB](https://www.thecocktaildb.com/api.php) y registrar límites, endpoint(s) y atribución exigida por el plan utilizado.
- [x] Definir un adaptador que normalice nombre, categoría, tipo de vaso, ingredientes, preparación, identificador remoto y URL de origen.
- [x] Definir carga de archivos con validación de extensión/MIME/tamaño y nombre seguro.
- [x] Extraer texto, normalizar espacios, conservar metadatos de archivo y dividir en fragmentos con solapamiento documentado.
- [x] Generar embeddings localmente y persistir texto, embedding, `source_type`, `source_uri`, `document_id` y posición del fragmento.
- [x] Hacer la ingesta idempotente: repetir la misma fuente no crea duplicados silenciosos.
- [x] Registrar errores por archivo o fuente sin marcar como exitoso un documento parcialmente procesado.

**Estado de implementación (10 de octubre de 2026):** la ingesta end-to-end de un Markdown y de los cócteles globales `Melya`, `Negroni`, `Mojito` y `Margarita` se ejecutó con Ollama `bge-m3` y Supabase. Además, las preguntas sobre `Daiquiri` y `Whiskey Sour` activaron la recuperación híbrida, persistieron ambos cócteles idempotentemente como `cocktaildb` y dejaron sus fuentes trazables. Las preguntas de descubrimiento de ingredientes consultan primero `filter.php?i=...` y `lookup.php?i=...` en TheCocktailDB, persisten hasta tres recetas y usan únicamente esos documentos como contexto cuando existen; el fallback vectorial se mantiene cuando no hay resultados. Se normalizan alias frecuentes como `jugo de tomate` → `tomato juice`. El catálogo puede nombrar ese resultado como Bloody Maria o Bloody Mary.

**Aceptación**

- [x] Se puede reconstruir el origen de cada fragmento hasta TheCocktailDB o hasta un archivo cargado.
- [x] Una búsqueda de prueba recupera al menos un cóctel conocido y un fragmento de archivo relevante.
- [x] Un archivo vacío, ilegible o no permitido recibe un error comprensible y no contamina la base vectorial.

### Fase 4 — Agente RAG con LangChain y LangGraph

**Objetivo:** responder sólo con contexto recuperado y rechazar preguntas fuera de la base.

**Tareas verificables**

- [x] Implementar el estado del grafo con pregunta, usuario, documentos recuperados, suficiencia, respuesta, fuentes y error.
- [x] Implementar recuperación con filtros de autorización y metadatos de fuente.
- [x] Implementar umbral o regla de suficiencia revisable; no asumir que cualquier resultado es evidencia suficiente.
- [x] Añadir nodo de validación de contexto y una rama explícita de rechazo/solicitud de aclaración.
- [x] Configurar Ollama como modelo generativo local; documentar modelo, temperatura/configuración y limitaciones observadas.
- [x] Crear prompt que obligue a usar sólo el contexto recuperado, declare incertidumbre y no revele secretos.
- [x] Guardar la interacción después de producir una respuesta válida o un rechazo, sin guardar tokens sensibles.

**Estado de implementación (12 de octubre de 2026):** el recorrido real se ejecutó con Piña Colada global y `docs/knowledge/guia-cocteleria.md` cargada en la biblioteca del usuario. Tras «¿Cómo hacer una Piña Colada?», los seguimientos «Debo agitar algo en esta receta?» y «¿Debería agitarla?» devolvieron que la receta indica licuar, no agitar, con fuente Piña Colada y sin mezclar Margarita. La causa era que `conversation_id` sólo se usaba para persistir historial y el grafo no recibía los mensajes ni sus fuentes. Ahora el backend carga hasta 8 mensajes autorizados por RLS; referencias explícitas y elípticas reusan los chunks citados por la última respuesta fundamentada y pueden añadir documentos propios relevantes. El texto previo del modelo sólo ayuda a resolver referencias; no se toma como evidencia. Una pregunta fuera de tema en la misma conversación siguió rechazada. Thresholds: general `0.55`, ingredientes `0.40`, contexto suplementario de seguimiento `0.35`.

**Aceptación**

- [x] Una pregunta respaldada devuelve respuesta y fuentes pertinentes.
- [x] Una pregunta fuera del corpus produce rechazo explícito, sin una afirmación inventada.
- [x] El grafo se puede inspeccionar en código y contiene las ramas de suficiencia y rechazo solicitadas.
- [x] Se evidencian al menos dos controles contra alucinaciones: umbral/validación de contexto y prompt restrictivo, además de fuentes cuando aplique.

### Fase 5 — API FastAPI protegida

**Objetivo:** exponer el flujo de forma segura y usable por el frontend.

**Tareas verificables**

- [x] Organizar routers, dependencias de autenticación, servicios de ingesta, recuperación, agente y persistencia sin duplicar lógica.
- [x] Publicar documentación OpenAPI de los endpoints no secretos; consultar [FastAPI](https://fastapi.tiangolo.com/).
- [x] Implementar pregunta, carga/procesamiento, listado y eliminación autorizada de documentos, y consulta de historial.
- [x] Validar entradas, límites, tipos de archivo y errores de proveedores con respuestas HTTP consistentes.
- [x] Configurar CORS sólo para los orígenes locales necesarios.
- [ ] Evitar registrar JWT, claves, contenido sensible o archivos completos en logs.

**Estado:** las tareas de implementación de esta fase están presentes en el backend y fueron ejercitadas parcialmente con Docker; falta observar la matriz completa de errores/OpenAPI y comprobar consumo desde frontend. La prevención de secretos en logs permanece pendiente de una revisión específica.

- [ ] La API inicia localmente y el frontend puede llamar un endpoint autenticado.
- [ ] La especificación OpenAPI coincide con las respuestas observadas, incluyendo errores.
- [ ] Todas las rutas de datos rechazan solicitudes no autenticadas y respetan el `user_id` del token.

### Fase 6 — Frontend React + Vite

**Objetivo:** ofrecer una interfaz clara para autenticación, conversación y corpus.

**Tareas verificables**

- [ ] Configurar cliente Supabase con la clave pública y URL mediante variables de entorno del frontend.
- [ ] Implementar registro, inicio, persistencia/renovación de sesión y cierre de sesión.
- [ ] Implementar pantalla de chat con pregunta, respuesta, fuentes, estado de carga y rechazo por contexto insuficiente.
- [ ] Implementar carga, progreso/resultado, listado y eliminación de documentos propios.
- [ ] Mostrar errores accionables sin filtrar detalles internos.
- [ ] Consumir únicamente contratos de la Fase 1 y enviar el JWT en las peticiones protegidas.
- [ ] Documentar comandos locales conforme a los scripts reales de Vite; referencia: [Vite](https://vite.dev/guide/) y [React](https://react.dev/learn).

**Aceptación**

- [ ] Un usuario puede registrarse, autenticarse, preguntar y cerrar sesión sin editar código.
- [ ] La interfaz distingue respuesta fundamentada, ausencia de contexto y error de red.
- [ ] Un usuario no ve ni puede borrar documentos de otro usuario desde la interfaz.

### Fase 7 — Integración, evidencia y endurecimiento

**Objetivo:** demostrar el recorrido completo y corregir fallos de integración.

**Tareas verificables**

- [ ] Ejecutar el recorrido: crear usuario → cargar archivo → procesar → preguntar → ver fuentes → consultar historial → cerrar sesión.
- [ ] Ejecutar recorrido con datos de TheCocktailDB y comprobar atribución/origen en la respuesta o vista de fuentes.
- [ ] Probar preguntas conocidas, ambiguas, fuera de dominio, contexto insuficiente, archivo inválido y sesión expirada.
- [ ] Medir latencia aproximada de embeddings, recuperación y generación con `qwen3.5:9b`; registrar hardware y fecha. `qwen3:4b` queda como comparación opcional.
- [ ] Revisar RLS, CORS, variables de entorno, límites de archivo y ausencia de secretos en Git.
- [ ] Capturar evidencias reproducibles: pantallas, respuestas HTTP, logs sanitizados y diagrama del flujo.

**Aceptación**

- [ ] Los escenarios críticos pasan con una base limpia y se conservan sus resultados.
- [ ] Los fallos conocidos tienen mensaje y comportamiento definidos, no sólo una excepción genérica.
- [ ] La documentación técnica puede enlazar cada requisito evaluable a una evidencia.

### Fase 8 — Entrega y mantenimiento

**Objetivo:** dejar una entrega reproducible y trazable en las ramas acordadas.

**Tareas verificables**

- [ ] Actualizar README, `.env.example`, instrucciones de Supabase/Ollama y este plan con el estado real.
- [ ] Revisar que no existan secretos, credenciales, archivos de usuarios ni dumps de base en el repositorio.
- [ ] Integrar cambios revisados en `develop` y promover a `main` sólo el estado estable; no crear ramas adicionales.
- [ ] Preparar documento técnico, arquitectura, limitaciones, evidencias y decisiones descartadas.
- [ ] Preparar demostración de 7–10 minutos: autenticación, carga, pregunta fundamentada, rechazo y trazabilidad.
- [ ] Registrar pasos para borrar/recrear el proyecto Supabase de desarrollo y revocar credenciales.

**Aceptación**

- [ ] Una persona con Ollama y un proyecto Supabase puede iniciar la aplicación local siguiendo la documentación.
- [ ] Los cuatro entregables académicos (repositorio, documento técnico, sustentación y diapositivas) tienen enlaces o archivos finales.
- [ ] `main` contiene únicamente una versión revisada y ejecutable del alcance acordado.

## 4. Modelo de datos mínimo

> Los nombres son una propuesta de contrato de datos; deben mantenerse estables una vez que existan consumidores. Añadir una tabla requiere justificar una necesidad funcional o de seguridad.

### `documents`

- `id` UUID, clave primaria.
- `owner_id` UUID nullable si el documento es global; referencia al usuario de Supabase cuando sea privado.
- `source_type` (`cocktaildb` | `upload`).
- `source_uri`/`external_id` para trazabilidad e idempotencia.
- `filename` nullable para archivos; `mime_type`, `size_bytes` y `status` (`pending`, `processing`, `ready`, `error`).
- `title`, `checksum`, `error_message` nullable.
- `created_at`, `updated_at`.

### `document_chunks`

- `id` UUID, clave primaria; `document_id` obligatorio.
- `chunk_index` entero y `content` texto.
- `embedding` vector con dimensión igual al modelo de embeddings escogido.
- `metadata` JSONB para página, identificador de cóctel, ingrediente u otros metadatos realmente usados en filtros.
- `created_at`.

Restricción recomendada: unicidad por `(document_id, chunk_index)` y/o checksum de contenido para evitar duplicados. El índice vectorial se elige según la dimensión y el volumen; no se fija antes de medir.

### `conversations` y `messages` (sólo si se entrega historial)

- `conversations`: `id`, `user_id`, `title` opcional, `created_at`, `updated_at`.
- `messages`: `id`, `conversation_id`, `role` (`user` | `assistant`), `content`, `sources` JSONB opcional, `created_at`.

RLS debe garantizar que un usuario sólo lea/modifique sus propias conversaciones y documentos privados. Los datos globales de TheCocktailDB pueden ser de sólo lectura para usuarios autenticados.

En el modelo actual, los documentos de TheCocktailDB usan `owner_id = NULL`, se escriben únicamente desde el backend con `service_role` y se leen como globales sólo por usuarios autenticados mediante RLS. Los uploads usan `owner_id` del JWT; `document_chunks` se vincula mediante `document_id`. Las claves foráneas aplican cascada desde documentos a chunks y desde conversaciones a mensajes; la cascada desde el usuario de Auth y el aislamiento entre dos usuarios aún requieren prueba runtime conservada.

## 5. Riesgos, señales y mitigaciones

| Riesgo | Señal temprana | Mitigación / decisión de escalamiento |
|---|---|---|
| Ollama lento o sin memoria | latencia alta, modelo no carga | Medir el recorrido con `qwen3.5:9b`, timeout configurado de 300 s, reducir contexto/fragmentos y documentar hardware; no sustituir por API comercial sin decisión explícita |
| Alucinaciones | respuesta sin fuente o no respaldada | umbral, nodo de suficiencia, prompt restrictivo, rechazo y pruebas fuera de corpus |
| Dimensión de embeddings incompatible | error al insertar/buscar vectores | fijar modelo antes de migrar, comprobar dimensión automáticamente y recrear índice sólo con migración controlada |
| Límites o cambios de TheCocktailDB | respuestas 429, campos ausentes | respetar documentación, cachear/ingestar con trazabilidad, manejar reintentos acotados y atribución |
| Archivos maliciosos o excesivos | consumo de CPU/disco, parser falla | allowlist de tipos, límite de tamaño, nombre seguro, aislamiento y estado `error` |
| Fuga de secretos | clave en Git/logs/frontend | `.env`, revisión previa, RLS, nunca `service_role` en cliente, rotación inmediata |
| RLS incorrecto | usuario ve datos de otro usuario | pruebas con dos cuentas, políticas explícitas y revisión antes de integrar |
| Contrato frontend/backend divergente | errores 4xx inesperados | OpenAPI como referencia, ejemplos de respuestas y recorrido completo de Fase 7 |
| Supabase no disponible | Auth o consultas fallan | documentar dependencia externa y mensajes de error; no inventar un backend alterno no acordado |
| Alcance crece | nuevas tablas/proveedores sin criterio | mantener modelo mínimo y exigir justificación funcional para cada cambio |

## 6. Referencias oficiales

- [Trabajo académico y requisitos del proyecto](../trabajo_agente.md)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/learn)
- [Vite](https://vite.dev/guide/)
- [LangChain](https://python.langchain.com/docs/introduction/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Ollama](https://ollama.com/) y [API local de Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Supabase Auth](https://supabase.com/docs/guides/auth)
- [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [TheCocktailDB API](https://www.thecocktaildb.com/api.php)
- [PostgreSQL](https://www.postgresql.org/docs/current/)
