Modelo generativo principal: qwen3:4b

 Recomendación:

 ```bash
ollama pull qwen3:4b
 ```

 Razones:

 - 4 mil millones de parámetros.
 - Soporte multilingüe, incluido español.
 - Contexto nativo de hasta 32K tokens.
 - Licencia Apache 2.0.
 - Tamaño razonable para los aproximadamente 30 GB de RAM disponibles.
 - Compatible con ejecución local mediante Ollama.
 - Puede funcionar en modo de razonamiento o en modo normal.
 - Adecuado para responder con contexto recuperado desde pgvector.

 En este equipo debería ser viable, aunque la latencia debe medirse con el proyecto real. Para respuestas rápidas se puede configurar el modelo para no usar
 razonamiento extendido.


