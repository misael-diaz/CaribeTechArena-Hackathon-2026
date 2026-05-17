---
name: Chatbot Skills Architecture V2
description: Nueva arquitectura de skills con servicios compartidos y tools compuestos
type: project
---

**Decisión:** Se refactorizó la arquitectura de skills del chatbot para agregar servicios compartidos y tools compuestos que reducen duplicacion de codigo.

**Why:** El usuario identifico que la arquitectura original tenia: (1) tools muy especificos, (2) duplicacion de logica, (3) falta de composicion. Se creo una capa de servicios para logica reutilizable.

**How to apply:**
- **Servicios compartidos:** `student/services/utils.py`, `product/services/nutrition_service.py`, `chat/services/student_summary_service.py`
- **Tools nuevos:** 4 tools agregados (Sprint 1 completado)
- **Tools totales:** 12 (eran 8, ahora 12)

**Nuevos Servicios:**

```
student/services/
├── allergen_alert_service.py (existente)
├── balance_forecast_service.py (existente)
├── utils.py (NUEVO - logica compartida)
└── __init__.py (exports actualizado)

product/services/
├── nutrition_service.py (NUEVO)
└── __init__.py

chat/services/
├── student_summary_service.py (NUEVO - services compuestos)
└── __init__.py
```

**Nuevos Tools (Sprint 1):**

| Tool | Descripcion | Reemplaza/Combina |
|------|-------------|-------------------|
| `check_allergen_safety` | Verifica si producto es seguro para estudiante | - |
| `suggest_healthy_alternatives` | Sugiere alternativas saludables | - |
| `get_student_summary` | Resumen completo (saldo+forecast+compras+alergenos) | get_student_balance + get_recent_recharges + get_student_allergens |
| `get_multi_student_summary` | Resumen de todos los hijos de un padre | - |

**Arquitectura actualizada:**

```
chat/ai_service.py (12 tools)
├── Legacy tools (8)
│   ├── get_one_today_meals
│   ├── get_childs
│   ├── get_student_balance
│   ├── get_student_allergens
│   ├── get_recent_recharges
│   ├── get_healthy_recommendations
│   ├── get_balance_forecast
│   └── get_product_nutrition
└── New tools (4)
    ├── check_allergen_safety
    ├── suggest_healthy_alternatives
    ├── get_student_summary
    └── get_multi_student_summary
```

**Servicios usados por tools:**

```
check_allergen_safety
├── student.services.get_student_by_parent_phone
└── product.services.NutritionService.is_product_safe_for_student

suggest_healthy_alternatives
└── product.services.NutritionService.get_healthy_alternatives

get_student_summary
└── chat.services.StudentSummaryService.get_full_summary

get_multi_student_summary
└── chat.services.StudentSummaryService.get_multi_student_summary
```

**Tests:** Todos los imports y servicios verificados (agent_verify_services.py)

**Fecha de implementacion:** 2026-05-17

**Proximos pasos (Sprint 2):**
- `compare_products_nutrition` - Comparar 2-3 productos
- `get_weekly_spending_report` - Reporte semanal de gasto
