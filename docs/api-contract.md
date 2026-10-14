# Contrato inicial de la API

Estado: propuesta implementable para la Fase 1. Los endpoints protegidos requieren `Authorization: Bearer <supabase_access_token>`.

## Convenciones

- Base local: `http://localhost:8000`.
- JSON UTF-8 salvo carga de archivos.
- IDs: UUID.
- Fechas: ISO 8601 UTC.
- Error estándar FastAPI:

```json
{
  "detail": "mensaje para el cliente"
}
```

- La API no devuelve tokens de servicio ni secretos.
- `401` indica token ausente, inválido o expirado.
- `403` indica usuario autenticado sin autorización sobre el recurso.
- `422` indica entrada inválida.
- Preguntas: entre 1 y 2000 caracteres, después de eliminar espacios extremos.
- Cargas: PDF, TXT, Markdown o CSV; máximo 10 MiB por archivo.
- Recuperación: 5 fragmentos por defecto, máximo 20.
- `503` indica dependencia externa no disponible o no preparada.

## Endpoint público de salud

### `GET /health`

No requiere autenticación.

Respuesta `200`:

```json
{
  "status": "ok"
}
```

No debe comprobar ni revelar credenciales. Las dependencias externas se verificarán mediante un endpoint administrativo o una comprobación interna no pública.

## Autenticación

La sesión se gestiona con Supabase Auth. Estos endpoints son una fachada opcional del backend; el frontend también puede usar directamente el SDK público de Supabase Auth.

### `POST /auth/register`

No requiere sesión.

Request:

```json
{
  "email": "usuario@example.com",
  "password": "una-clave-segura"
}
```

Respuesta `201`:

```json
{
  "user": {
    "id": "uuid",
    "email": "usuario@example.com"
  },
  "session": null,
  "email_confirmation_required": true
}
```

No se garantiza una sesión inmediata si Supabase exige confirmación de correo.

Errores: `400` credenciales rechazadas, `409` usuario existente, `422` request inválido.

### `POST /auth/login`

No requiere sesión.

Request:

```json
{
  "email": "usuario@example.com",
  "password": "una-clave-segura"
}
```

Respuesta `200`:

```json
{
  "access_token": "jwt-de-supabase",
  "refresh_token": "refresh-token-de-supabase",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "usuario@example.com"
  }
}
```

El frontend debe guardar la sesión mediante el SDK de Supabase; no debe persistir claves privilegiadas.

### `POST /auth/logout`

Requiere sesión. Invalida la sesión del cliente mediante Supabase Auth.

Respuesta `204` sin cuerpo.

## Chat

### `POST /chat/query`

Requiere sesión.

Request:

```json
{
  "question": "¿Qué ingredientes tiene un mojito?",
  "conversation_id": "uuid-opcional"
}
```

Cuando se envía `conversation_id`, el backend carga un tramo reciente y acotado del historial autorizado para resolver referencias explícitas («esta receta») y seguimientos elípticos con un objeto implícito («¿Debería agitarla?»). Relee los chunks citados por la última respuesta del asistente con el JWT actual y RLS. El texto previo del modelo sólo ayuda a resolver la referencia; no se acepta como evidencia. Si no hay fuente recuperable del turno anterior, el agente no inventa contexto. Sin `conversation_id`, cada pregunta se procesa sin contexto conversacional anterior.

Respuesta `200`:

```json
{
  "conversation_id": "uuid",
  "answer": "...",
  "context_sufficient": true,
  "sources": [
    {
      "document_id": "uuid",
      "chunk_id": "uuid",
      "title": "Mojito",
      "source_type": "cocktaildb",
      "source_uri": "https://www.thecocktaildb.com/...",
      "image_url": "https://www.thecocktaildb.com/images/media/drink/...",
      "similarity": 0.87
  ]
}
```
`image_url` es opcional y puede ser `null` (por ejemplo, en fuentes de archivos cargados). Cuando existe, contiene una URL HTTPS externa de la miniatura del cóctel; la API no almacena ni devuelve bytes de imagen. El mismo campo se conserva en `sources` de los mensajes del historial.

Cuando el contexto sea insuficiente, la API responde `200` porque la solicitud fue procesada, pero debe devolver:

```json
{
  "conversation_id": "uuid",
  "answer": "No tengo suficiente información en mi base de conocimiento para responder esa pregunta.",
  "context_sufficient": false,
  "sources": []
}
```

En este caso no se llama al modelo generativo.

Errores: `401`, `422`, `503` si Ollama o Supabase no están disponibles.

## Conversaciones e historial

### `GET /conversations`

Requiere sesión. Devuelve sólo conversaciones del usuario autenticado.

Respuesta `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Consulta sobre mojitos",
      "created_at": "2026-10-08T12:00:00Z",
      "updated_at": "2026-10-08T12:01:00Z"
    }
  ]
}
```

### `GET /conversations/{conversation_id}/messages`

Requiere sesión y autorización sobre la conversación.

Respuesta `200`:

```json
{
  "conversation_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "role": "user",
      "content": "¿Qué ingredientes tiene un mojito?",
      "sources": [],
      "created_at": "2026-10-08T12:00:00Z"
    }
  ]
}
```

Un ID perteneciente a otro usuario debe responder `404` o `403` de forma consistente, sin revelar la existencia del recurso.

## Documentos

### `POST /documents`

Requiere sesión. Recibe `multipart/form-data` con el campo `file`.

Formatos iniciales permitidos: PDF, TXT, Markdown y CSV.

Respuesta `202`:

La implementación actual procesa la carga de forma síncrona para no ocultar errores parciales, pero conserva `202` por compatibilidad contractual. El campo `document.status` refleja el estado real al devolver la respuesta: normalmente `ready` o `error`, no necesariamente `processing`.

```json
{
  "document": {
    "id": "uuid",
    "filename": "receta.md",
    "status": "ready",
    "source_type": "upload"
  }
}
```

El backend debe validar extensión, MIME, tamaño y nombre. Un archivo inválido responde `415` o `422` sin crear un documento listo.

### `GET /documents`

Requiere sesión. Devuelve documentos globales visibles y documentos privados propios, según la política definida en Supabase.

Respuesta `200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Recetas de cócteles",
      "source_type": "upload",
      "status": "ready",
      "created_at": "2026-10-08T12:00:00Z",
      "processed_at": "2026-10-08T12:00:03Z"
    }
  ]
}
```

### `GET /documents/{document_id}`

Requiere sesión y autorización sobre el documento. Devuelve metadatos y estado, no necesariamente el contenido completo.

### `DELETE /documents/{document_id}`

Requiere sesión y autorización sobre un documento privado propio. Elimina sus fragmentos asociados mediante cascada.

Respuesta `204` sin cuerpo.

### `POST /admin/ingest/cocktails`

Requiere una autorización administrativa de backend; no debe estar disponible para cualquier usuario autenticado desde el frontend.

Request:

```json
{
  "letters": ["a", "b"],
  "limit": 20
}
```

Respuesta `202`:

```json
{
  "status": "accepted",
  "requested": 20,
  "ingested": 20
}
```

La ingesta debe ser idempotente, conservar `source_uri`/`external_id` y respetar los límites de TheCocktailDB.

## Reglas de seguridad

1. Todos los endpoints salvo `GET /health`, registro y login requieren JWT válido.
2. El `user_id` se obtiene del JWT; nunca se acepta como autoridad desde el body.
3. La `service_role` key sólo se usa en backend y nunca se envía al frontend.
4. Las respuestas no incluyen tokens, credenciales ni contenido de otros usuarios.
5. Las consultas vectoriales deben aplicar autorización antes de devolver fragmentos.
6. La migración SQL y las políticas RLS deben probarse con dos usuarios y una sesión anónima.

## Criterios de aceptación del contrato

- [ ] FastAPI publica estos paths y métodos.
- [ ] OpenAPI refleja request, response y errores principales.
- [ ] Cada ruta protegida rechaza ausencia o invalidez del JWT.
- [ ] El chat devuelve fuentes y `context_sufficient`.
- [ ] El rechazo por contexto insuficiente no llama al LLM.
- [ ] Un usuario no puede leer, modificar o eliminar recursos privados de otro.
