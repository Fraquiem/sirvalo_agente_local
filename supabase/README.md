# Configuración de Supabase

Este directorio contiene la configuración y migraciones para el proyecto de base de datos en Supabase.

## Instrucciones

1. Crea un proyecto en [Supabase Dashboard](https://supabase.com/dashboard).
2. Ve al **SQL Editor**.
3. Copia y pega el contenido del archivo `migrations/20261008000000_initial_schema.sql`.
4. Ejecuta el script para crear las tablas, extensiones y políticas de seguridad (RLS).
5. Obtén tu `Project URL` y `anon public` key desde **Project Settings > API** y añádelas a tu archivo `.env` en la raíz del proyecto.

## Estructura de Tablas

- `documents`: Metadatos de archivos cargados y fuentes externas (TheCocktailDB).
- `document_chunks`: Fragmentos de texto con sus respectivos embeddings vectoriales.
- `conversations`: Sesiones de chat por usuario.
- `messages`: Historial de mensajes dentro de una conversación.
