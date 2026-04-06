---
name: brainstorming
description: Explores user intent, requirements, and design concepts before implementation via collaborative dialogue. Use for feature creation or architectural planning.
---

# Brainstorming & Design Strategy

## When to use this skill
- User initiates creative work (creating features, building components).
- User asks to help design or plan a new capability.
- Requirements are ambiguous and need clarification.

## Workflow
- [ ] **Contextualize**: Analyze current project state (files, docs).
- [ ] **Clarify**: Ask single-threaded questions to refine intent.
- [ ] **Options**: Propose 2-3 with trade-offs.
- [ ] **Draft**: Present design in 200-300 word chunks.
- [ ] **Finalize**: Commit design doc to `docs/plans/`.

## Instructions

### 0. Language
- **Latin American Spanish**: ALL interactions, questions, and the final design document MUST be in Latin American Spanish.

### 1. Understanding
- **One Question Rule**: Never ask multiple questions in one message.
- **Format**: Prefer multiple-choice to lower cognitive load.
- **Goal**: Specific understanding of purpose, constraints, and success criteria.

### 2. Exploration
- Always provide 2-3 distinct approaches (e.g., "Quick & Dirty" vs. "Robust & Scalable").
- Explicitly state trade-offs.
- Recommend one and justify.

### 3. Presentation
- Do not dump a full design.
- Present in logical sections (Architecture -> API -> UI).
- **Validation Loop**: Ask "Does this look right so far?" (¿Te parece bien hasta ahora?) after each chunk.
- Cover: Architecture, Components, Data Flow, Error Handling, Testing.

### 4. Output
- Create a design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.
- **Do not** start implementation until the design doc is saved.

## Principles
- **Conciseness**: Designs should be dense but readable.
- **YAGNI**: Ruthlessly remove unnecessary features.
- **Flexibility**: Be ready to pivot if a design chunk is rejected.

