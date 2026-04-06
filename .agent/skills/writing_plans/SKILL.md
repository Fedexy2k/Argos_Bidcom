°---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code. Writes comprehensive implementation plans.
---

# Writing Plans & TDD Strategy

## When to use this skill
- You have a spec or requirement for a multi-step task.
- You are about to start implementation but haven't touched code yet.
- You need to break down a complex feature into bite-sized, testable actions.

## Workflow
1.  **Announce**: "Estoy usando la habilidad `writing-plans` para crear el plan de implementaciÃ³n."
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
# Plan de ImplementaciÃ³n: [Feature Name]

> **Para Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Objetivo:** [Una frase describiendo quÃ© se construye]
**Arquitectura:** [2-3 frases sobre el enfoque]
**Tech Stack:** [TecnologÃ­as clave/librerÃ­as]
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

**Paso 3: Escribir implementaciÃ³n mÃ­nima**
[Provide exact python code to satisfy the test]

**Paso 4: Ejecutar test para verificar que pasa**
Ejecutar: `pytest tests/path/test.py::test_name -v`
Esperado: Ã‰XITO (PASS)

**Paso 5: Commit**
`git add tests/path/test.py src/path/file.py`
`git commit -m "feat: add specific feature"`
```

### 4. Execution Handoff
After saving the plan, output this EXACT text:

> **Plan completo y guardado en `docs/plans/<filename>.md`. Dos opciones de ejecuciÃ³n:**
>
> **1. Subagent-Driven (esta sesiÃ³n)** - Despacho un subagente por tarea, revisiÃ³n entre tareas, iteraciÃ³n rÃ¡pida.
>
> **2. Parallel Session (separada)** - Abre nueva sesiÃ³n con executing-plans, ejecuciÃ³n por lotes con checkpoints.
>
> **Â¿QuÃ© enfoque prefieres?**
Ş *cascade08Şã*cascade08ãæ *cascade08æç*cascade08çè *cascade08èí*cascade08íï *cascade08ï÷*cascade08÷ø *cascade08øù*cascade08ù† *cascade08†‡*cascade08‡ˆ *cascade08ˆŒ*cascade08Œ‘ *cascade08‘“*cascade08“” *cascade08”•*cascade08•– *cascade08–œ*cascade08œ¨ *cascade08¨©*cascade08©ª *cascade08ª¬*cascade08¬— *cascade08—¢*cascade08¢¶ *cascade08¶œ*cascade08œ¨ *cascade08¨ª*cascade08ª« *cascade08«¬*cascade08¬­ *cascade08­®*cascade08®º *cascade08º»*cascade08»¼ *cascade08¼¾*cascade08¾¿ *cascade08¿À*cascade08ÀÁ *cascade08ÁÄ*cascade08ÄÅ *cascade08ÅÏ*cascade08Ï× *cascade08×Ù*cascade08ÙÚ *cascade08ÚÛ*cascade08ÛÄ *cascade08ÄË*cascade08ËÑ *cascade08ÑÒ*cascade08ÒÓ *cascade08ÓÔ*cascade08ÔÕ *cascade08ÕØ*cascade08Øã *cascade08ãä*cascade08äå *cascade08åç*cascade08çè *cascade08èì*cascade08ìî *cascade08îï*cascade08ïğ *cascade08ğö*cascade08ö÷ *cascade08÷ù*cascade08ù€ *cascade08€‚*cascade08‚‰ *cascade08‰Š*cascade08Š“ *cascade08“–*cascade08–š *cascade08š›*cascade08›œ *cascade08œ*cascade08 *cascade08¦*cascade08¦§ *cascade08§ª*cascade08ª¾ *cascade08¾¿*cascade08¿Æ *cascade08ÆÏ*cascade08ÏÕ *cascade08ÕÖ*cascade08Ö× *cascade08×Ú*cascade08Ú² *cascade08²à*cascade08àø *cascade08øû*cascade08û• *cascade08•™*cascade08™š *cascade08šœ*cascade08œ¨ *cascade08¨©*cascade08©Ë *cascade08ËÏ*cascade08Ï¡ *cascade08¡¥*cascade08¥© *cascade08©¬*cascade08¬® *cascade08®±*cascade08±¹ *cascade08¹Ã*cascade08Ãõ *cascade08õù*cascade08ùı *cascade08ı*cascade08‚ *cascade08‚…*cascade08…‹ *cascade08‹*cascade08– *cascade08–*cascade08  *cascade08 ¡*cascade08¡¢ *cascade08¢£*cascade08£§ *cascade08§«*cascade08«¬ *cascade08¬¯*cascade08¯İ *cascade08İŞ*cascade08Şà *cascade08àâ*cascade08âã *cascade08ãä*cascade08äé *cascade08éë*cascade08ëì *cascade08ìï*cascade08ï— *cascade08—›*cascade08›Ÿ *cascade08Ÿ¢*cascade08¢¤ *cascade08¤¥*cascade08¥¦ *cascade08¦§*cascade08§² *cascade08²³*cascade08³´ *cascade08´¶*cascade08¶· *cascade08·¿*cascade08¿ø *cascade08øü*cascade08ü€ *cascade08€„*cascade08„… *cascade08…ˆ*cascade08ˆ *cascade08’*cascade08’™ *cascade08™ *cascade08 ¤ *cascade08¤¥*cascade08¥© *cascade08©­*cascade08­® *cascade08®±*cascade08±ß *cascade08ßà*cascade08àâ *cascade08âä*cascade08äå *cascade08åæ*cascade08æè *cascade08èğ*cascade08ğô *cascade08ôõ*cascade08õû *cascade08ûÿ*cascade08ÿÍ *cascade08ÍÎ*cascade08ÎÏ *cascade08ÏÓ*cascade08ÓÔ *cascade08ÔÕ*cascade08ÕØ *cascade08ØÙ*cascade08ÙÚ *cascade08ÚÜ*cascade08Üù *cascade08ùú*cascade08úû *cascade08ûü*cascade08üı *cascade08ıÿ*cascade08ÿƒ *cascade08ƒ…*cascade08…† *cascade08†*cascade08 *cascade08’*cascade08’³ *cascade08³µ*cascade08µ¶ *cascade08¶·*cascade08·¼ *cascade08¼¾*cascade08¾Å *cascade08ÅÇ*cascade08ÇÌ *cascade08ÌÍ*cascade08ÍÎ *cascade08ÎĞ*cascade08ĞÙ *cascade08ÙÚ*cascade08ÚÜ *cascade08Üİ*cascade08İá *cascade08áä*cascade08äê *cascade08êï*cascade08ïñ *cascade08ñò*cascade08òó *cascade08óô*cascade08ôø *cascade08øú*cascade08úü *cascade08üı*cascade08ıƒ *cascade08ƒ„*cascade08„… *cascade08…‡*cascade08‡ˆ *cascade08ˆ‘*cascade08‘µ *cascade08µ·*cascade08·½ *cascade08½À*cascade08ÀÃ *cascade08ÃÄ*cascade08ÄÅ *cascade08ÅÇ*cascade08ÇÌ *cascade08ÌÑ*cascade08Ñæ *cascade08æç*cascade08çê *cascade08êë*cascade08ëì *cascade08ìî*cascade08îğ *cascade08ğö*cascade08ö÷ *cascade08÷ı*cascade08ı‰ *cascade08‰Š*cascade08Š“ *cascade08“¡*cascade08¡¤ *cascade08¤«*cascade08«° *cascade082Xfile:///C:/Users/FDean/Antigravity/Generador_Skills/.agent/skills/writing-plans/SKILL.md