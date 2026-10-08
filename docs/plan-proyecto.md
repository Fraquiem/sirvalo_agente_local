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
- **Modelo local:** Ollama. La primera opción registrada es `qwen3:4b` (véase `toma_de_notas.md`); su latencia y calidad se medirán con el proyecto real.
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

- [ ] Confirmar que el caso de uso es preguntas y recomendaciones fundamentadas sobre cócteles.
- [ ] Confirmar responsables, disponibilidad y criterio de terminado de cada fase.
- [ ] Crear/usar únicamente `main` y `develop`; proteger `main` de cambios no revisados.
- [ ] Inventariar versiones de Python, Node.js, Ollama y Docker (si se usa sólo como ayuda local).
- [ ] Instalar y comprobar Ollama; descargar el modelo acordado: `ollama pull qwen3:4b`.
- [ ] Crear un proyecto Supabase de desarrollo y anotar su URL y clave pública fuera del repositorio.
- [ ] Acordar formatos iniciales de archivo: PDF, TXT, Markdown y CSV; documentar explícitamente cualquier formato no soportado.

**Aceptación**

- [ ] Una persona nueva puede leer este plan y reproducir las decisiones sin elegir otra arquitectura.
- [ ] `ollama list` muestra el modelo elegido y la aplicación puede apuntar a una URL local de Ollama.
- [ ] Existe un `.env.example` sin secretos y una lista de variables requerida (sin modificar código de aplicación en esta fase).

### Fase 1 — Diseño funcional y contrato de la API

**Objetivo:** convertir los requisitos en flujos y contratos comprobables.

**Tareas verificables**

- [ ] Definir flujos: registro/inicio de sesión, cierre de sesión, pregunta, carga de archivo, listado/eliminación de documentos y consulta de historial.
- [ ] Definir estados de UI: cargando, respuesta fundamentada, contexto insuficiente, error de validación, error de proveedor y sesión expirada.
- [ ] Especificar endpoints protegidos, método, entrada, salida, códigos HTTP y requisito de usuario autenticado.
- [ ] Especificar el formato de una respuesta RAG: respuesta, fuentes/fragmentos usados y señal de suficiencia del contexto.
- [ ] Definir límites: tamaño/tipo de archivo, longitud de pregunta, número de resultados recuperados y mensajes de error seguros.
- [ ] Dibujar el flujo LangGraph: recibir → recuperar → evaluar suficiencia → responder o rechazar → guardar historial.

**Aceptación**

- [ ] El contrato permite implementar frontend y backend sin inventar nombres ni formas de respuesta.
- [ ] Cada operación protegida tiene una regla de autorización y un caso de rechazo no autenticado.
- [ ] Existe un caso explícito para responder “No tengo suficiente información...” sin llamar al modelo generativo.

### Fase 2 — Supabase Auth y PostgreSQL/pgvector

**Objetivo:** disponer de identidad y persistencia mínima para desarrollo local.

**Configuración externa paso a paso**

1. [ ] Crear una cuenta y un proyecto en [Supabase Dashboard](https://supabase.com/dashboard).
2. [ ] En **Project Settings → API**, copiar la **Project URL** y la clave pública (`anon`/publishable, según la interfaz). Guardarlas únicamente en variables de entorno locales.
3. [ ] En **Authentication → Providers**, habilitar Email. Mantener la confirmación de correo según la política del proyecto; para una demo local, documentar si se desactiva y por qué.
4. [ ] En **Authentication → URL Configuration**, añadir sólo las URLs locales usadas por el frontend (por ejemplo, `http://localhost:5173`) y su callback si la integración lo requiere.
5. [ ] Abrir **SQL Editor** y habilitar `vector` con la sentencia recomendada por la documentación de [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector). Verificar que la extensión queda instalada.
6. [ ] Crear las tablas mínimas descritas en este documento, con `id`, claves foráneas, `created_at` y políticas RLS coherentes con el usuario autenticado. La migración debe ser repetible y quedar versionada como artefacto de infraestructura/documentación, no como secreto.
7. [ ] Crear índices sólo después de conocer la dimensión del embedding; la dimensión de la columna y la del modelo deben coincidir.
8. [ ] Probar registro, inicio y cierre de sesión desde el cliente local. Verificar que un usuario no puede leer ni borrar documentos de otro usuario.
9. [ ] No copiar la `service_role` key al frontend, al repositorio ni a tickets. Rotarla si se expone accidentalmente.

**Tareas verificables**

- [ ] Implementar validación del JWT de Supabase en FastAPI.
- [ ] Asociar cada documento, fragmento y conversación a `user_id` cuando el dato sea privado.
- [ ] Definir si los datos de TheCocktailDB son globales o se replican por usuario; preferencia: corpus global de sólo lectura y archivos privados por usuario.
- [ ] Verificar RLS con dos usuarios de prueba y una sesión sin autenticar.

**Aceptación**

- [ ] Usuario A no puede consultar documentos privados de usuario B aunque conozca sus identificadores.
- [ ] Un JWT inválido o ausente produce un rechazo consistente en todos los endpoints protegidos.
- [ ] La búsqueda vectorial devuelve una fila de prueba con su fragmento y metadatos de origen.

### Fase 3 — Ingesta de TheCocktailDB y archivos

**Objetivo:** construir un corpus reproducible y trazable.

**Tareas verificables**

- [ ] Consultar la [documentación oficial de TheCocktailDB](https://www.thecocktaildb.com/api.php) y registrar límites, endpoint(s) y atribución exigida por el plan utilizado.
- [ ] Definir un adaptador que normalice nombre, categoría, tipo de vaso, ingredientes, preparación, identificador remoto y URL de origen.
- [ ] Definir carga de archivos con validación de extensión/MIME/tamaño y nombre seguro.
- [ ] Extraer texto, normalizar espacios, conservar metadatos de archivo y dividir en fragmentos con solapamiento documentado.
- [ ] Generar embeddings localmente y persistir texto, embedding, `source_type`, `source_uri`, `document_id` y posición del fragmento.
- [ ] Hacer la ingesta idempotente: repetir la misma fuente no crea duplicados silenciosos.
- [ ] Registrar errores por archivo o fuente sin marcar como exitoso un documento parcialmente procesado.

**Aceptación**

- [ ] Se puede reconstruir el origen de cada fragmento hasta TheCocktailDB o hasta un archivo cargado.
- [ ] Una búsqueda de prueba recupera al menos un cóctel conocido y un fragmento de archivo relevante.
- [ ] Un archivo vacío, ilegible o no permitido recibe un error comprensible y no contamina la base vectorial.

### Fase 4 — Agente RAG con LangChain y LangGraph

**Objetivo:** responder sólo con contexto recuperado y rechazar preguntas fuera de la base.

**Tareas verificables**

- [ ] Implementar el estado del grafo con pregunta, usuario, documentos recuperados, suficiencia, respuesta, fuentes y error.
- [ ] Implementar recuperación con filtros de autorización y metadatos de fuente.
- [ ] Implementar umbral o regla de suficiencia revisable; no asumir que cualquier resultado es evidencia suficiente.
- [ ] Añadir nodo de validación de contexto y una rama explícita de rechazo/solicitud de aclaración.
- [ ] Configurar Ollama como modelo generativo local; documentar modelo, temperatura/configuración y limitaciones observadas.
- [ ] Crear prompt que obligue a usar sólo el contexto recuperado, declare incertidumbre y no revele secretos.
- [ ] Guardar la interacción después de producir una respuesta válida o un rechazo, sin guardar tokens sensibles.

**Aceptación**

- [ ] Una pregunta respaldada devuelve respuesta y fuentes pertinentes.
- [ ] Una pregunta fuera del corpus produce rechazo explícito, sin una afirmación inventada.
- [ ] El grafo se puede inspeccionar en código y contiene las ramas de suficiencia y rechazo solicitadas.
- [ ] Se evidencian al menos dos controles contra alucinaciones: umbral/validación de contexto y prompt restrictivo, además de fuentes cuando aplique.

### Fase 5 — API FastAPI protegida

**Objetivo:** exponer el flujo de forma segura y usable por el frontend.

**Tareas verificables**

- [ ] Organizar routers, dependencias de autenticación, servicios de ingesta, recuperación, agente y persistencia sin duplicar lógica.
- [ ] Publicar documentación OpenAPI de los endpoints no secretos; consultar [FastAPI](https://fastapi.tiangolo.com/).
- [ ] Implementar pregunta, carga/procesamiento, listado y eliminación autorizada de documentos, y consulta de historial.
- [ ] Validar entradas, límites, tipos de archivo y errores de proveedores con respuestas HTTP consistentes.
- [ ] Configurar CORS sólo para los orígenes locales necesarios.
- [ ] Evitar registrar JWT, claves, contenido sensible o archivos completos en logs.

**Aceptación**

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
- [ ] Medir latencia aproximada de embeddings, recuperación y generación con `qwen3:4b`; registrar hardware y fecha.
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

## 5. Riesgos, señales y mitigaciones

| Riesgo | Señal temprana | Mitigación / decisión de escalamiento |
|---|---|---|
| Ollama lento o sin memoria | latencia alta, modelo no carga | medir con `qwen3:4b`, reducir contexto/fragmentos, documentar hardware; no sustituir por API comercial sin decisión explícita |
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
