�%---
name: ui-ux-design
description: Proporciona inteligencia de diseño para construir interfaces UI/UX profesionales en múltiples plataformas. Úsala para analizar requisitos, generar sistemas de diseño y verificar la calidad visual.
---

# Diseño UI/UX Profesional (Pro Max)

Esta habilidad proporciona un flujo de trabajo y reglas estrictas para garantizar interfaces de usuario de alta calidad, profesionales y bien diseñadas.

## Cuándo usar esta habilidad
- El usuario solicita diseñar, construir o mejorar una interfaz (UI/UX).
- Se necesita definir una paleta de colores, tipografía o sistema de diseño.
- Se requiere verificar la calidad de una implementación visual.

## Instrucciones

### 0. Idioma
- **Español de Latinoamérica**: Todas las interacciones, explicaciones y documentación generada deben estar en Español de Latinoamérica.

### 1. Flujo de Trabajo

#### Paso 1: Analizar Requisitos
Extrae la información clave de la solicitud del usuario:
- **Tipo de Producto**: SaaS, e-commerce, portfolio, dashboard, landing page, etc.
- **Palabras Clave de Estilo**: minimalista, lúdico, profesional, elegante, modo oscuro, etc.
- **Industria**: salud, fintech, gaming, educación, belleza.
- **Stack**: React, Vue, o por defecto `html-tailwind`.

#### Paso 2: Generar Sistema de Diseño
Antes de escribir código, define explícitamente el sistema de diseño basado en la industria y estilo:
- **Paleta de Colores**: Primario, Fondo, Texto (con buen contraste).
- **Tipografía**: Fuentes para títulos y cuerpo (Google Fonts).
- **Estilo Visual**: Bordes, sombras, glassmorphism, flat, etc.

#### Paso 3: Guías de Implementación (Stack Default: html-tailwind)
Si no se especifica otro, asume `html-tailwind`. Prioriza utilidades de Tailwind, diseño responsivo y accesibilidad.

### 2. Reglas Comunes para UI Profesional

#### Iconos y Elementos Visuales
| Regla | Hacer (Do) | No Hacer (Don't) |
|------|------------|------------------|
| **Sin emojis como iconos** | Usar iconos SVG (Heroicons, Lucide, Simple Icons) | Usar emojis como 🎨 🚀 ⚙️ como iconos de UI |
| **Estados hover estables** | Usar transiciones de color/opacidad | Usar transformaciones de escala que muevan el layout |
| **Logos de marca correctos** | Buscar SVG oficiales (Simple Icons) | Adivinar o usar rutas incorrectas |
| **Tamaño de iconos consistente** | Usar viewBox fijo (24x24) con `w-6 h-6` | Mezclar tamaños de iconos aleatoriamente |

#### Interacción y Cursor
| Regla | Hacer (Do) | No Hacer (Don't) |
|------|------------|------------------|
| **Cursor pointer** | Añadir `cursor-pointer` a todo elemento clicable | Dejar el cursor por defecto en interactivos |
| **Feedback en Hover** | Dar feedback visual (color, sombra) | Sin indicación de que es interactivo |
| **Transiciones suaves** | Usar `transition-colors duration-200` | Cambios de estado instantáneos o muy lentos |

#### Contraste y Modos (Claro/Oscuro)
| Regla | Hacer (Do) | No Hacer (Don't) |
|------|------------|------------------|
| **Glass card (Modo Claro)** | Usar `bg-white/80` o mayor opacidad | Usar `bg-white/10` (demasiado transparente) |
| **Texto (Modo Claro)** | Usar `#0F172A` (slate-900) para títulos | Usar `#94A3B8` (slate-400) para texto cuerpo |
| **Texto Muted (Modo Claro)** | Usar `#475569` (slate-600) mínimo | Usar gray-400 o más claro (ilegible) |
| **Visibilidad de Bordes** | Usar `border-gray-200` en claro | Usar `border-white/10` (invisible) |

#### Layout y Espaciado
| Regla | Hacer (Do) | No Hacer (Don't) |
|------|------------|------------------|
| **Navbar Flotante** | Añadir espaciado `top-4 left-4 right-4` | Pegar la navbar a `top-0 left-0` |
| **Padding de Contenido** | Considerar la altura de la navbar fija | Dejar que el contenido se oculte detrás |
| **Max-width consistente** | Usar el mismo `max-w-6xl` o `7xl` | Mezclar anchos de contenedor distintos |

### 3. Checklist Pre-Entrega
Verifica estos puntos antes de entregar el código:

#### Calidad Visual
- [ ] No se usan emojis como iconos (usar SVG).
- [ ] Todos los iconos son de un set consistente (Heroicons/Lucide).
- [ ] Logos de marca correctos.
- [ ] Colores de tema usados directamente (`bg-primary`), no harcodeados.

#### Interacción
- [ ] Todos los elementos clicables tienen `cursor-pointer`.
- [ ] Feedback visual claro en Hover.
- [ ] Transiciones suaves (150-300ms).
- [ ] Estados de foco visibles para navegación por teclado.

#### Accesibilidad y Layout
- [ ] Contraste suficiente en texto (4.5:1 mínimo).
- [ ] Imágenes con texto alternativo (`alt`).
- [ ] Inputs de formulario con etiquetas (`labels`).
- [ ] Responsivo en móviles (sin scroll horizontal).
�%*cascade082Wfile:///C:/Users/FDean/Antigravity/Generador_Skills/.agent/skills/ui-ux-design/SKILL.md