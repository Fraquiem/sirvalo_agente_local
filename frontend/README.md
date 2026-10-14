# Frontend — Pourover

Interfaz React + Vite para el agente RAG de cócteles. La dirección visual es un **laboratorio de coctelería nocturno**: superficies glassmorphism, verde lima como acento y tipografía editorial para diferenciar conversación, fuentes y corpus privado.

## Requisitos

- Node.js 18+
- Backend FastAPI en `http://localhost:8000`
- Proyecto Supabase configurado en el backend

## Configuración

Crea `frontend/.env.local` (no subas secretos) con:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

La aplicación usa los endpoints autenticados del backend (`/auth`, `/chat/query`, `/conversations` y `/documents`). El navegador sólo conserva el access token de la sesión; nunca recibe la `service_role` key.

## Ejecución

```bash
npm install
npm run dev
```

Abre `http://localhost:5173`.

Para validar la compilación de producción:

```bash
npm run build
npm run preview
```

## Flujos disponibles

- Registro e inicio de sesión, con manejo de confirmación de correo.
- Preguntas fundamentadas y rechazo cuando falta contexto; las fuentes se muestran debajo de cada respuesta, sin marcadores incrustados en el texto generado.
- Fuentes consultadas con enlace, relevancia y miniatura externa de TheCocktailDB cuando la API proporciona `image_url`; si la imagen no carga, se muestra un fallback y el enlace de origen se conserva.
- Historial de conversaciones y carga/eliminación de documentos propios.
- Las preguntas predeterminadas cubren recetas y descubrimiento por ingredientes; las preguntas generales de técnica requieren que esa explicación exista en el corpus.
- Estado de sesión, proveedor, procesamiento y errores accionables.
