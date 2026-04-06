---
name: Diseño UI/UX Profesional
description: Guía de principios y criterios para diseñar interfaces de usuario profesionales, accesibles y amigables en aplicaciones de escritorio (CustomTkinter) y web. Aplica cuando el usuario pide mejorar, revisar o diseñar cualquier componente visual.
---

# Skill: Diseño UI/UX Profesional

## Cuándo usar esta skill

Activar cuando:
- El usuario pide mejorar el diseño de una pantalla o componente
- Hay problemas de legibilidad, contraste o alineación
- Se diseña una nueva vista o formulario
- El usuario menciona que algo "no se ve bien" o "queda raro"

---

## Principios Fundamentales

### 1. Contraste y Legibilidad
- **Texto sobre fondo oscuro**: siempre usar `text_primary` (blanco/claro), NUNCA `text_secondary` (gris) para labels de campos
- **Labels de sección**: color de acento (`accent_secondary`) para destacar jerarquía
- **Hints/ayudas**: `text_secondary` (gris) en fuente 9-10pt — nunca para contenido principal
- **Contraste mínimo WCAG AA**: ratio 4.5:1 para texto normal, 3:1 para texto grande
- **Dropdowns y entries**: siempre especificar `text_color=colors["text_primary"]` explícitamente

### 2. Densidad y Espaciado
- **Formularios compactos**: `pady=2-4` entre filas, `padx=8-12` interno
- **Altura de inputs**: 32-36px para entries y combos — ni muy chicos ni muy grandes
- **Fuente de campos**: 12pt para labels y valores, 9-10pt para hints
- **Fuente de secciones**: 13-14pt bold para encabezados de sección
- **Evitar**: frames con `width` fijo + `pack_propagate(False)` → genera espacio vacío
- **Preferir**: grid con `minsize` + `weight=1` para columnas proporcionales

### 3. Jerarquía Visual
- **Nivel 1**: Título de sección (14pt bold, color acento, con línea divisoria)
- **Nivel 2**: Label de campo (12pt bold, text_primary)
- **Nivel 3**: Hint/ayuda (9pt, text_secondary, wraplength ajustado al ancho)
- **Nivel 4**: Valor/input (12pt, text_primary, fondo bg_tertiary)
- Separar secciones con `pady=(18, 4)` arriba de cada encabezado

### 4. Feedback Visual
- **Campos editables clave**: borde de color acento (`accent_primary`) para distinguirlos
- **Auto-detectados**: badge `✓ auto` en verde (`success`) junto al label
- **Estados**: OK=verde, WARNING=amarillo, FAIL=rojo — siempre con ícono
- **Acciones principales**: botón grande (height=50-55px), color primario, texto bold 14-16pt

### 5. Texto Largo y Wrap
- **Nunca** usar `wraplength=0` en CTkLabel — el texto se sale del frame
- **Para texto corto** (< 60 chars): `CTkLabel` con `wraplength` calculado al ancho del frame
- **Para texto largo** (direcciones, specs, normas): usar `CTkTextbox` read-only con `wrap="word"`, `border_width=0`, `fg_color="transparent"`, `activate_scrollbars=False`
- Calcular altura del textbox dinámicamente según líneas de contenido

### 6. Alineación en Grids
- Usar `uniform="group_name"` en columnas que deben tener el mismo ancho
- `sticky="nsew"` para que los frames se estiren correctamente
- Evitar mezclar `pack` y `grid` en el mismo frame padre
- Para columnas de comparación (DATASHEET vs CERTIFICADO): `weight=1, uniform="data_cols"`

### 7. Formularios de Edición
- Agrupar campos relacionados en secciones con encabezado claro
- Cada sección debe tener un hint de 1 línea explicando qué va ahí
- Campos que el usuario DEBE revisar: borde azul (`accent_primary`)
- Campos auto-detectados: badge verde, pero igualmente editables
- Orden lógico: Identificación → Producto → Certificado → Auto-detectados → Acciones

---

## Checklist de Revisión UX

Antes de entregar cualquier cambio de UI, verificar:

- [ ] ¿Todos los labels de campos usan `text_primary` (no `text_secondary`)?
- [ ] ¿Los dropdowns tienen `text_color=colors["text_primary"]`?
- [ ] ¿El texto largo usa CTkTextbox con word wrap?
- [ ] ¿Las columnas paralelas tienen `uniform` para alinearse?
- [ ] ¿Los campos editables clave tienen borde de acento?
- [ ] ¿Cada sección tiene un hint explicativo?
- [ ] ¿El padding es consistente (pady=2-4 entre filas)?
- [ ] ¿La fuente es legible (mínimo 11pt, preferible 12pt)?
- [ ] ¿El botón de acción principal es prominente (height≥50)?
- [ ] ¿Syntax check pasa sin errores?

---

## Patrones Comunes en Argos (CustomTkinter)

### Campo de formulario compacto
```python
row = ctk.CTkFrame(parent, fg_color=colors["bg_secondary"], corner_radius=6)
row.pack(fill="x", pady=2)
row.grid_columnconfigure(0, minsize=150, weight=0)
row.grid_columnconfigure(1, weight=1)

# Label
lbl = ctk.CTkFrame(row, fg_color="transparent")
lbl.grid(row=0, column=0, sticky="nw", padx=(10, 5), pady=6)
ctk.CTkLabel(lbl, text="Campo", font=("Roboto", 12, "bold"),
             text_color=colors["text_primary"]).pack(anchor="w")
ctk.CTkLabel(lbl, text="Hint explicativo", font=("Roboto", 9),
             text_color=colors["text_secondary"], wraplength=145).pack(anchor="w")

# Entry
entry = ctk.CTkEntry(row, font=("Roboto", 12), height=32,
                     fg_color=colors["bg_tertiary"],
                     text_color=colors["text_primary"])
entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=6)
```

### Texto largo con wrap (verificación)
```python
textbox = ctk.CTkTextbox(
    parent, font=("Roboto", 11), text_color=colors["text_primary"],
    fg_color="transparent", border_width=0,
    wrap="word", activate_scrollbars=False,
    height=calc_height(text)  # ~20px por línea
)
textbox.insert("1.0", text)
textbox.configure(state="disabled")
```

### Columnas alineadas (comparación)
```python
row.grid_columnconfigure(0, minsize=260, weight=0)
row.grid_columnconfigure(1, weight=1, uniform="data_cols")
row.grid_columnconfigure(2, minsize=10, weight=0)
row.grid_columnconfigure(3, weight=1, uniform="data_cols")
```

### Sección con hint
```python
frame = ctk.CTkFrame(parent, fg_color="transparent")
frame.pack(fill="x", pady=(18, 4))
ctk.CTkLabel(frame, text="📋 TÍTULO SECCIÓN",
             font=("Roboto", 14, "bold"), text_color=colors["accent_secondary"]).pack(anchor="w")
ctk.CTkLabel(frame, text="  Descripción de qué va en esta sección",
             font=("Roboto", 10), text_color=colors["text_secondary"]).pack(anchor="w", pady=(1,0))
ctk.CTkFrame(frame, height=1, fg_color=colors["border"]).pack(fill="x", pady=(4, 0))
```
