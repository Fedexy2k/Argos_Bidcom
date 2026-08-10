# Guía de Configuración y Control de Presupuesto OpenAI en Argos

## 1. Configuración de tu API Key de OpenAI

1. Abre el archivo `.env` en la raíz del proyecto Argos.
2. Reemplaza `tu_openai_key_aqui` por tu clave real de OpenAI (empieza con `sk-...`):

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
MAX_MONTHLY_AI_BUDGET_USD=5.00
```

---

## 2. Control y Protección Financiera

Argos cuenta con un sistema automático de **Protección de Presupuesto**:

- **Tope Configurable**: Con `MAX_MONTHLY_AI_BUDGET_USD=5.00`, el sistema establece un límite máximo de $5.00 USD al mes.
- **Bloqueo Automático**: Si el consumo acumulado en el mes alcanza este tope, la aplicación pausará automáticamente nuevas llamadas a la API de OpenAI para evitar cualquier cargo indeseado en tu tarjeta.
- **Caché Local ($0.00 USD)**: Si consultas o re-auditas un certificado idéntico, Argos servirá la respuesta desde la caché local sin consumir tokens ni dinero.

---

## 3. Endpoints REST Disponibles para el Frontend / Dashboard

- **`GET /api/budget/summary`**: Retorna el resumen del mes (período, tope, gasto acumulado y saldo disponible).
- **`GET /api/budget/ledger`**: Historial detallado de cada documento procesado, tokens usados y costo exacto en dólares.
- **`POST /api/ee/auto-extract`**: Envía el texto de un informe de ensayo de Eficiencia Energética para extraer la familia y campos automáticamente.
