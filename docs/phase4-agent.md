# Fase 4: agente RAG

## Topología

`POST /chat/query` valida el JWT y, si se proporciona, comprueba la conversación mediante RLS. El grafo LangGraph ejecuta `retrieve -> validate -> (generate | reject) -> save`. Recuperación crea un embedding con el modelo configurado y llama al RPC autorizado `match_documents`; el guardado usa el JWT del usuario para insertar ambos mensajes.

## Suficiencia y generación

La recuperación usa 5 fragmentos por defecto (máximo 20) y umbral inicial de similitud coseno `0.60`. Es suficiente únicamente si existe al menos un resultado con similitud igual o mayor al umbral. El rechazo exacto es: `No tengo suficiente información en mi base de conocimiento para responder esa pregunta.` En esa rama no se llama a generación. El valor se calibró con una pregunta española sobre `Melya` (`similarity=0.618609`) y debe subir si aparecen falsos positivos.

Ollama usa `qwen3.5:9b`, `think: false`, temperatura `0.1` y `num_predict=512`. El prompt incluye únicamente los fragmentos recuperados, exige responder sólo con el contexto, citar `[Fuente N]`, declarar incertidumbre y no revelar secretos.

## Fuentes y autorización

Las fuentes exponen `document_id`, `chunk_id`, `title`, `source_type`, `source_uri` y `similarity`. El RPC aplica RLS para permitir sólo documentos globales o propios. Conversaciones y mensajes se consultan y escriben con el JWT del usuario; una conversación ajena se presenta como `404` sin revelar existencia.

## Limitaciones

La calidad depende de Ollama, embeddings y de la cobertura de documentos indexados. El RPC actualmente devuelve metadata del chunk, por lo que `title`/`source_uri` pueden ser nulos cuando no están presentes en esa metadata. No hay fallback de proveedor.

## Ejecución con Docker

Ollama debe estar activo en el host:

```bash
ollama serve
ollama list
```

Si FastAPI corre en Docker y Ollama escucha sólo en `localhost`, iniciar el contenedor con red del host o configurar Ollama para escuchar en una interfaz accesible. En Linux, el recorrido verificado usa:

```bash
docker run --rm --network host --env-file .env \
  -e OLLAMA_BASE_URL=http://localhost:11434 \
  trabajoagentes-backend \
  uvicorn app.main:app --host 127.0.0.1 --port 8000
```

La configuración usa `bge-m3` para embeddings y `qwen3.5:9b` para generación. El primer uso puede tardar mientras Ollama carga el modelo; el timeout operativo se puede ampliar con `OLLAMA_TIMEOUT_SECONDS`.

## Smoke procedure

Con Supabase y Ollama configurados, iniciar FastAPI, solicitar `/chat/query` sin `Authorization` (debe devolver `401`), subir/indexar un documento, preguntar algo cubierto (respuesta `200`, `context_sufficient=true` y fuentes), y preguntar algo no cubierto (respuesta `200` con el rechazo exacto y sin llamada `/api/generate`). Consultar `/conversations` y `/conversations/{id}/messages` con el mismo JWT y verificar que devuelven ambos mensajes.
