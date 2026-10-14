# Fase 4: agente RAG

`POST /chat/query` valida el JWT y, si se proporciona, comprueba la conversación mediante RLS. El grafo LangGraph ejecuta `retrieve -> validate -> (generate | reject) -> save`. Recuperación crea un embedding con el modelo configurado y llama al RPC autorizado `match_documents`; si una pregunta de receta nombra un cóctel que aún no está en el índice, ejecuta una búsqueda acotada en TheCocktailDB, persiste el resultado de forma idempotente y lo usa como contexto autorizado. La extracción cubre variantes como `hacer`, `hace`, `preparar`, `preparo`, `prepara`, `elaborar`, artículos `un/una/el/la`, `ingredientes de` y `qué es`. El guardado usa el JWT del usuario para insertar ambos mensajes.

## Contexto conversacional acotado

Si el usuario pasa `conversation_id`, el backend carga como máximo los últimos 8 mensajes mediante el JWT y RLS. La continuidad se activa con referencias explícitas («esta receta», «el cóctel anterior») y seguimientos elípticos de técnica/servicio («¿Debería agitarla?», «¿La agito?», «¿Y cómo se sirve?», «¿Cuánto hielo le pongo?»), siempre que haya una respuesta previa con fuentes y la pregunta no nombre un cóctel distinto. El agente vuelve a leer los chunks citados por la respuesta previa y los usa como evidencia; no trata el texto previo del modelo como fuente factual. También puede añadir fragmentos de documentos propios relevantes, pero filtra otros cócteles globales para que Piña Colada no use una receta de Margarita. Sin una fuente previa recuperable, el seguimiento se rechaza de forma segura.

## Suficiencia y generación

La recuperación usa 5 fragmentos por defecto (máximo 20) y threshold general `0.55`. Las preguntas de descubrimiento por ingredientes usan `INGREDIENT_RETRIEVAL_THRESHOLD=0.40`; los seguimientos explícitos usan `RETRIEVAL_FOLLOWUP_THRESHOLD=0.35` para localizar guía complementaria. Los seguimientos reusan directamente los chunks citados por el turno anterior; la suficiencia se basa en esa evidencia autenticada, no en que el texto del asistente anterior pareciera convincente. Los resultados complementarios se filtran para conservar sólo la receta activa y documentos propios relevantes. Los thresholds deben elevarse si aparecen falsos positivos.

Ollama usa `qwen3.5:9b`, `think: false`, temperatura `0.1` y `num_predict=512`. El prompt incluye únicamente los fragmentos recuperados, exige responder sólo con el contexto, no emite marcadores `[Fuente N]` porque la interfaz renderiza las fuentes por separado, declara incertidumbre y no revela secretos.

## Fuentes y autorización

Las fuentes exponen `document_id`, `chunk_id`, `title`, `source_type`, `source_uri`, `image_url` opcional y `similarity`. En fuentes de TheCocktailDB, `image_url` es una URL HTTPS externa y no se almacenan binarios; en uploads permanece nulo. El RPC aplica RLS para permitir sólo documentos globales o propios. Conversaciones y mensajes se consultan y escriben con el JWT del usuario; una conversación ajena se presenta como `404` sin revelar existencia.

## Limitaciones

La calidad depende de Ollama, embeddings, TheCocktailDB y de la cobertura de documentos indexados. Las preguntas que nombran un cóctel pueden activar una consulta dinámica acotada al proveedor y dejarlo persistido para futuras preguntas; esto no sustituye un corpus documental para técnicas generales. El corpus global de pruebas contiene `Melya`, `Negroni`, `Mojito`, `Margarita` y, tras la verificación dinámica, `Daiquiri`. No hay fallback de proveedor alternativo.

## Ejecución con Docker

Ollama debe estar activo en el host:

```bash
ollama serve
ollama list
```

Si FastAPI corre en Docker y Ollama escucha sólo en `localhost`, iniciar el contenedor con red del host o configurar Ollama para escuchar en una interfaz accesible. En Linux, el recorrido verificado usa:

```bash
docker run --rm --network host --env-file .env \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  trabajoagentes-backend \
  uvicorn app.main:app --host 127.0.0.1 --port 8000
```

La configuración usa `bge-m3` para embeddings y `qwen3.5:9b` para generación. El primer uso puede tardar mientras Ollama carga el modelo; el timeout operativo se puede ampliar con `OLLAMA_TIMEOUT_SECONDS`.

## Smoke procedure

Con Supabase y Ollama configurados, iniciar FastAPI, solicitar `/chat/query` sin `Authorization` (debe devolver `401`), subir/indexar un documento, preguntar algo cubierto (respuesta `200`, `context_sufficient=true` y fuentes), y preguntar algo no cubierto (respuesta `200` con el rechazo exacto y sin llamada `/api/generate`). Consultar `/conversations` y `/conversations/{id}/messages` con el mismo JWT y verificar que devuelven ambos mensajes.
