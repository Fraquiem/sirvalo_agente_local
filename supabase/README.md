# Configuración de Supabase

Este directorio contiene la configuración y migraciones para el proyecto de base de datos en Supabase.

## Instrucciones

1. Crea o selecciona un proyecto en [Supabase Dashboard](https://supabase.com/dashboard).
2. En **Authentication → Providers**, habilita Email y configura la confirmación de correo según la demo.
3. En **Project Settings → API**, copia la Project URL y la clave pública a `.env`. La `service_role` key sólo debe existir en el backend.
4. En **SQL Editor**, ejecuta `migrations/20261008000000_initial_schema.sql`.
5. Comprueba que la consulta siguiente devuelve las cuatro tablas:

   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
     AND table_name IN ('documents', 'document_chunks', 'conversations', 'messages')
   ORDER BY table_name;
   ```

6. Comprueba que la función de recuperación existe:

   ```sql
   SELECT routine_schema, routine_name
   FROM information_schema.routines
   WHERE routine_schema = 'public'
     AND routine_name = 'match_documents';
   ```

7. Ejecuta la migración una segunda vez sólo como prueba de repetibilidad. No debe fallar por políticas existentes.

La migración crea RLS para que los documentos globales sean visibles únicamente a usuarios autenticados. La ingesta de fragmentos vectoriales se realizará desde el backend con `service_role`; esa clave nunca se copia al frontend.

## Estructura de Tablas

- `documents`: Metadatos de archivos cargados y fuentes externas (TheCocktailDB).
- `document_chunks`: Fragmentos de texto con sus embeddings `vector(1024)`.
- `conversations`: Sesiones de chat por usuario.
- `messages`: Historial de mensajes dentro de una conversación.
