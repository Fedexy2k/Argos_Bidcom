�---
name: error-handling-patterns
description: Domina los patrones de manejo de errores en varios lenguajes, incluyendo excepciones, tipos Result, propagación de errores y degradación elegante. Úsala al implementar manejo de errores, diseñar APIs o mejorar la confiabilidad de la aplicación.
---

# Patrones de Manejo de Errores

Construye aplicaciones resilientes con estrategias robustas de manejo de errores que gestionen fallos con elegancia y proporcionen excelentes experiencias de depuración.

## Cuándo usar esta habilidad
- Implementar manejo de errores en nuevas funcionalidades.
- Diseñar APIs resilientes a errores.
- Depurar problemas en producción.
- Mejorar la confiabilidad de la aplicación.
- Crear mejores mensajes de error para usuarios y desarrolladores.
- Implementar patrones de reintento (retry) y cortacircuitos (circuit breaker).
- Manejar errores asíncronos/concurrentes.
- Construir sistemas distribuidos tolerantes a fallos.

## Instrucciones

### 0. Idioma
- **Español de Latinoamérica**: Todas las explicaciones, comentarios sugeridos y documentación generada deben estar en Español de Latinoamérica. El código se mantiene en su lenguaje original (Python, JS, etc.).

### 1. Conceptos Principales

#### Filosofías de Manejo de Errores
- **Excepciones vs Tipos Result**:
    - *Excepciones*: Try-catch tradicional, interrumpe el flujo de control (Python, Java/JS).
    - *Tipos Result*: Éxito/Fallo explícito, enfoque funcional (Rust, Elm).
    - *Códigos de Error*: Estilo C, requiere disciplina.
    - *Tipos Option/Maybe*: Para valores nulos.
- **Cuándo usar cada uno**:
    - *Excepciones*: Errores inesperados, condiciones excepcionales.
    - *Tipos Result*: Errores esperados, fallos de validación.
    - *Panics/Crashes*: Errores irrecuperables, bugs de programación.

#### Categorías de Errores
- **Recuperables**: Timeouts de red, archivos faltantes, input inválido, límites de API.
- **Irrecuperables**: Out of memory, Stack overflow, bugs de programación.

### 2. Patrones Específicos por Lenguaje

#### Python
- **Jerarquía de Excepciones Personalizada**: Heredar de `Exception` base de la app.
- **Context Managers**: Para limpieza (`try...finally`).
- **Decoradores de Reintento**: Con backoff exponencial.

#### TypeScript/JavaScript
- **Clases de Error Personalizadas**: Extender `Error`.
- **Patrón Result Type**: Objetos `{ ok: true, value: T } | { ok: false, error: E }`.
- **Async Error Handling**: `try...catch` en `async/await`, `.catch()` en Promesas.

#### Rust
- **Tipos Result y Option**: Uso de `?` para propagación.
- **Enums de Error Personalizados**: Para agrupar tipos de error.
- **Combinators**: `map_err`, `ok_or_else`.

#### Go
- **Retorno Explícito de Errores**: `val, err := func()`.
- **Errores Centinela**: `var ErrNotFound = errors.New(...)`.
- **Wrapping**: `fmt.Errorf("...: %w", err)` y `errors.Is/As`.

### 3. Patrones Universales

#### Circuit Breaker (Cortacircuito)
Previene fallos en cascada en sistemas distribuidos. Estados: Cerrado (Normal), Abierto (Fallando), Semi-Abierto (Probando).

#### Agregación de Errores
Recolectar múltiples errores (ej. validación de formulario) en lugar de fallar en el primero.

#### Degradación Elegante
Proveer funcionalidad de respaldo (fallback) cuando ocurren errores (ej. caché si la BD falla).

### 4. Mejores Prácticas
- **Fail Fast**: Valida entradas temprano.
- **Preservar Contexto**: Stack traces, metadatos, timestamps.
- **Mensajes Significativos**: Explica qué pasó y cómo arreglarlo.
- **Loguear Apropiadamente**: Error = log, fallo esperado = no spammear.
- **Limpiar Recursos**: `finally`, `defer`, `with`.
- **No Tragar Errores**: Loguear o relanzar, nunca ignorar silenciosamente.

## Recursos
- `scripts/error-analyzer.py`: Analizar patrones de error en logs.
- `assets/error-handling-checklist.md`: Checklist de revisión.
�*cascade082bfile:///C:/Users/FDean/Antigravity/Generador_Skills/.agent/skills/error-handling-patterns/SKILL.md