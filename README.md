# Agente RAG de Cócteles

Aplicación web RAG (Retrieval-Augmented Generation) para consultas y recomendaciones sobre cócteles utilizando datos de TheCocktailDB y documentos del usuario.

## Arquitectura y Tecnologías

- **Backend:** Python + FastAPI
- **Orquestación RAG:** LangChain + LangGraph
- **LLM Local:** Ollama (`qwen3:4b`)
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
3. **Ollama** instalado localmente con el modelo descargado:
   ```bash
   ollama pull qwen3:4b
   ollama pull nomic-embed-text
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

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Base de Datos (Supabase)

Aplica la migración SQL ubicada en `supabase/migrations/20261008000000_initial_schema.sql` en el SQL Editor de tu proyecto de Supabase.
