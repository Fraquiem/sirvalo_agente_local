# Agente RAG de Cócteles

Aplicación web RAG (Retrieval-Augmented Generation) para consultas y recomendaciones sobre cócteles utilizando datos de TheCocktailDB y documentos del usuario.

## Arquitectura y Tecnologías

- **Backend:** Python + FastAPI
- **Orquestación RAG:** LangChain + LangGraph
- **LLM Local:** Ollama (`qwen3.5:9b`, selección provisional)
- **Autenticación y Persistencia:** Supabase Auth + PostgreSQL (`pgvector`)
- **Frontend:** React + Vite

## Estructura del Proyecto

```text
.
├── backend/            # API REST con FastAPI, LangChain y LangGraph
├── frontend/           # Interfaz de usuario en React + Vite
├── supabase/           # Migraciones SQL y esquemas de base de datos
├── docs/               # Documentación del proyecto y plan de desarrollo
├── docker-compose.yml  # Configuración opcional de servicios locales
├── .env.example        # Variables de entorno de referencia
└── README.md
```

## Requisitos Previos

1. **Python 3.10+**
2. **Node.js 18+** y npm
3. **Ollama** instalado localmente con los modelos descargados:
   ```bash
   ollama pull qwen3.5:9b
   ollama pull bge-m3
   ```
4. Proyecto en **Supabase** habilitado con `pgvector`.

## Configuración e Instalación

### 1. Variables de entorno

Copia `.env.example` a `.env` y completa las credenciales de Supabase:

```bash
cp .env.example .env
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Si el backend corre dentro de Docker y Ollama escucha en el `localhost` del host, usa la red del host en Linux:

```bash
docker run --rm --network host --env-file .env \
  -e OLLAMA_BASE_URL=http://localhost:11434 \
  trabajoagentes-backend \
  uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Base de Datos (Supabase)

Aplica, en este orden, las migraciones SQL:

```text
supabase/migrations/20261008000000_initial_schema.sql
supabase/migrations/20261008010000_phase3_documents.sql
```

La segunda migración añade los índices de idempotencia de uploads y TheCocktailDB. No expongas `SUPABASE_SERVICE_ROLE_KEY` al frontend.
