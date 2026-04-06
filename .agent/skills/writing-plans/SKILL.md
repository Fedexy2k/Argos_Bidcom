---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code. Writes comprehensive implementation plans.
---

# Writing Plans & TDD Strategy

## When to use this skill
- You have a spec or requirement for a multi-step task.
- You are about to start implementation but haven't touched code yet.
- You need to break down a complex feature into bite-sized, testable actions.

## Workflow
1.  **Announce**: "Estoy usando la habilidad `writing-plans` para crear el plan de implementación."
2.  **Context**: Ensure you are in a dedicated worktree (if applicable).
3.  **Draft**: Write the plan to `docs/plans/YYYY-MM-DD-<feature-name>.md`.
4.  **Handoff**: Offer execution options (Subagent-Driven vs. Parallel Session) in Spanish.

## Instructions

### 0. Reference Language
- **Latin American Spanish**: The plan content (descriptions, steps, trade-offs) and your interaction with the user MUST be in Latin American Spanish. Code and filenames remain in English/Python/etc.

### 1. Granularity & Principles
- **Bite-Sized**: Each step is one action (2-5 mins).
- **TDD**: "Write failing test" -> "Verify fail" -> "Minimal code" -> "Verify pass" -> "Commit".
- **Audience**: skilled developer with zero context of this codebase.
- **DRY / YAGNI**: Remove unnecessary steps or complexity.

### 2. Plan Document Header
Every plan MUST start with:
```markdown
# Plan de Implementación: [Feature Name]

> **Para Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Objetivo:** [Una frase describiendo qué se construye]
**Arquitectura:** [2-3 frases sobre el enfoque]
**Tech Stack:** [Tecnologías clave/librerías]
```

### 3. Task Structure Template
Each task in the plan must follow this format (Tasks and steps in Spanish, code in English):

```markdown
### Tarea N: [Component Name]

**Archivos:**
- Crear: `exact/path/to/file.py`
- Modificar: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Paso 1: Escribir el test que falla**
[Provide exact python code for the test]

**Paso 2: Ejecutar test para verificar que falla**
Ejecutar: `pytest tests/path/test.py::test_name -v`
Esperado: FALLO con "function not defined" o similar.

**Paso 3: Escribir implementación mínima**
[Provide exact python code to satisfy the test]

**Paso 4: Ejecutar test para verificar que pasa**
Ejecutar: `pytest tests/path/test.py::test_name -v`
Esperado: ÉXITO (PASS)

**Paso 5: Commit**
`git add tests/path/test.py src/path/file.py`
`git commit -m "feat: add specific feature"`
```

### 4. Execution Handoff
After saving the plan, output this EXACT text:

> **Plan completo y guardado en `docs/plans/<filename>.md`. Dos opciones de ejecución:**
>
> **1. Subagent-Driven (esta sesión)** - Despacho un subagente por tarea, revisión entre tareas, iteración rápida.
>
> **2. Parallel Session (separada)** - Abre nueva sesión con executing-plans, ejecución por lotes con checkpoints.
>
> **¿Qué enfoque prefieres?**
