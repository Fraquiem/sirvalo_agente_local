# Validación local de modelos

Fecha de ejecución: 2026-10-08.

## Entorno observado

- CPU: Intel Core i7-1265U, 12 hilos.
- RAM disponible del sistema: aproximadamente 30 GiB.
- GPU: Intel UHD integrada; las pruebas usaron CPU.
- Ollama local.

## Embeddings: `bge-m3`

Instalado correctamente:

```text
bge-m3:latest
Tamaño mostrado por Ollama: 1.2 GB
Arquitectura: bert
Parámetros: 566.70M
Contexto: 8192
Embedding length: 1024
Capacidad: embedding
Licencia: MIT
```

Una llamada real a `POST http://localhost:11434/api/embed` produjo un vector de **1024 dimensiones**, compatible con `VECTOR(1024)` de la migración inicial.

Tiempo observado de una llamada local de prueba: aproximadamente 3.84 s incluyendo el proceso HTTP y la lectura de la respuesta.

## `qwen3.5:9b`

Modelo previamente instalado:

```text
Parámetros: 9.7B
Cuantización: Q4_K_M
Contexto mostrado por Ollama: 262144
Licencia: Apache 2.0
Procesador utilizado: 100% CPU
Tamaño mostrado por Ollama: 6.6 GB
```

### Consulta general en español

Pregunta: ingredientes habituales de un mojito, sin contexto externo.

- Tiempo total: **1170.83 s** con configuración predeterminada.
- La respuesta fue en español y listó ingredientes razonables.
- El modelo reconoció que no se había proporcionado una fuente externa.
- La ejecución predeterminada expuso una cadena extensa de razonamiento; no debe utilizarse así para el endpoint normal.

### Consulta fundamentada con contexto

Se proporcionó exclusivamente un contexto con ingredientes y vaso del Mojito.

- Tiempo total: **17.13 s**.
- Prompt evaluation: 14.32 tokens/s.
- Generation: 3.90 tokens/s.
- Respuesta correcta, usando únicamente los datos proporcionados.

### Consulta fuera del contexto

Se preguntó por el campeón mundial de fútbol utilizando el mismo contexto limitado a Mojito.

- Tiempo total: **12.96 s**.
- Prompt evaluation: 11.10 tokens/s.
- Generation: 4.04 tokens/s.
- Respondió exactamente con el rechazo esperado:

```text
No tengo suficiente información en mi base de conocimiento para responder esa pregunta.
```

## `qwen3:4b`

Se descargó correctamente para comparación.

Consulta fundamentada con el mismo contexto:

- Tiempo total: **246.10 s**.
- Prompt evaluation: 21.53 tokens/s.
- Generation: 5.80 tokens/s.
- La respuesta final fue correcta, pero produjo aproximadamente 1372 tokens de razonamiento visible antes de responder.
- Se observó CPU al 100%.
- Tamaño mostrado por Ollama: 5.1 GB.

Este comportamiento lo hace poco conveniente para la demostración si no se consigue desactivar de forma fiable el razonamiento o limitar la salida.

## Decisión provisional

Usar **`qwen3.5:9b`** como modelo generativo inicial, configurando el endpoint para:

- desactivar el razonamiento cuando sea posible (`think=false`);
- limitar tokens de salida;
- enviar sólo los fragmentos recuperados;
- imponer el rechazo desde un nodo de LangGraph antes de invocar el modelo cuando el contexto sea insuficiente.

No se debe confiar únicamente en el prompt para rechazar preguntas externas.

`qwen3:4b` queda como alternativa si se resuelve su comportamiento de razonamiento o si futuras pruebas muestran una configuración más rápida.

## Limitaciones de esta validación

- No se midió una batería estadística de preguntas.
- No se midió consumo exacto de RAM del proceso; `ollama ps` mostró modelos cargados al 100% en CPU y tamaños de 6.6 GB (`qwen3.5:9b`) y 5.1 GB (`qwen3:4b`).
- No se validó todavía integración con LangChain, LangGraph ni Supabase.
- La calidad final debe volver a evaluarse con recetas realmente ingeridas desde TheCocktailDB.
