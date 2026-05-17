---
name: Nutrition Facts Models
description: Modelo NutritionFact para informacion nutricional de productos + tool para chatbot
type: project
---

**Decisión:** Se agrego el modelo `NutritionFact` para almacenar informacion nutricional de productos de la cafetería, basado en datos existentes en `nutrition.db` y `data/products.txt`.

**Why:** El repo tenia una base de datos SQLite `nutrition.db` con informacion nutricional de 61 productos, pero no habia modelo Django. Se creo el modelo para poder consultar esta informacion desde el chatbot.

**How to apply:**
- **Modelo:** `product/models.py` con `NutritionFact` (high_sugar, high_sodium, high_fat)
- **Tool:** `chat/skill/get_product_nutrition/tool.py` para consultar desde el chatbot
- **Datos:** 15 productos importados desde `data/products.txt`
- **Migracion:** `product/migrations/0003_nutritionfact.py`

**Estructura:**
```
product/models.py:
  - NutritionFact
    - product_name (unique, indexed)
    - high_sugar (boolean)
    - high_sodium (boolean)
    - high_fat (boolean)
    - is_healthy() method
    - get_flags() method
```

**Datos importados:**
- Total: 15 productos
- Altos en azucar: 12
- Altos en sodio: 3
- Altos en grasa: 10

**Ejemplos de productos:**
- coca-cola 400ml: alto en azucar
- papas margarita 45g: alto en sodio, grasa
- galletas festival 40g: alto en azucar

**Uso desde chatbot:**
Padre pregunta: "¿La coca-cola es saludable?" → Tool `get_product_nutrition` responde: "coca-cola sabor original 400ml: ALTO EN: azucar"

**Fecha de implementacion:** 2026-05-17
