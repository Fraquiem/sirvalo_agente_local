# Backend - Agente de Cócteles

API construida con FastAPI, LangChain y LangGraph.

## Requisitos

- Python 3.10+
- Ollama corriendo localmente

## Instalación

1. Crear entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Con Docker en Linux, el `docker-compose.yml` usa la red del host para que el backend pueda acceder al Ollama del equipo en `http://localhost:11434`. Si cambias la topología de red, ajusta `OLLAMA_BASE_URL` a la dirección alcanzable desde el contenedor.

## Estructura

- `app/main.py`: Punto de entrada de la aplicación.
- `app/agents/`: Lógica del agente RAG con LangGraph.
- `app/controllers/`: Endpoints de la API (Auth, Chat, Documentos).
- `app/services/`: Lógica de negocio (Ingesta, Búsqueda Vectorial).
- `app/config.py`: Gestión de configuración y variables de entorno.

## Recuperación híbrida de cócteles

Las preguntas que nombran un cóctel (por ejemplo, «¿Cómo preparo un Daiquiri?»)
primero consultan el índice pgvector. Si el contexto local es insuficiente, se
realiza una búsqueda acotada en TheCocktailDB (`search.php?s=...`) y luego una
consulta de detalle. El resultado se normaliza, se guarda como documento global
`cocktaildb` y se re-embebe de forma idempotente por `external_id`; por ello,
un cóctel nuevo queda disponible desde la primera pregunta y las repeticiones no
crean filas duplicadas. El contexto obtenido dinámicamente se considera fuente
autorizada y sus referencias se devuelven en `sources`.

Las consultas de descubrimiento de ingredientes («¿qué puedo hacer con ron?»)
consultan primero TheCocktailDB mediante `filter.php?i=...` y recuperan detalles
acotados (`lookup.php?i=...`). Los resultados se normalizan y persisten de forma
idempotente antes de usarse como único contexto y fuente, evitando que un
fragmento vectorial irrelevante (por ejemplo, Mojito) determine la imagen o la
receta. Se admiten alias frecuentes (`lima`/`lime`, `ron`/`rum`,
`hierbabuena`/`mint`, `jugo de tomate`/`tomato juice`) y como máximo tres
resultados por pregunta. Si el proveedor no devuelve resultados, se conserva el
fallback vectorial y su rechazo seguro. El nombre mostrado depende del catálogo:
para jugo de tomate puede aparecer Bloody Maria o Bloody Mary.

## Seguimientos en una conversación

Cuando el chat envía un `conversation_id`, el backend carga como máximo 8 mensajes recientes usando el JWT del usuario y las políticas RLS. Referencias explícitas («esta receta») y seguimientos elípticos («¿Debería agitarla?») reusan los chunks citados por la última respuesta fundamentada y pueden añadir un documento de conocimiento relevante. Filtra otros cócteles globales para evitar que una pregunta sobre Piña Colada reciba una fuente o imagen de Margarita. El texto previo del modelo sirve sólo para identificar la referencia; las afirmaciones se fundamentan en chunks recuperados de Supabase.
