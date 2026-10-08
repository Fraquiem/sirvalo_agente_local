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

## Estructura

- `app/main.py`: Punto de entrada de la aplicación.
- `app/agents/`: Lógica del agente RAG con LangGraph.
- `app/controllers/`: Endpoints de la API (Auth, Chat, Documentos).
- `app/services/`: Lógica de negocio (Ingesta, Búsqueda Vectorial).
- `app/config.py`: Gestión de configuración y variables de entorno.
