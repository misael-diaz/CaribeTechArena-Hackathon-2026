---
name: Balance Forecast with Pandas
description: Calculo avanzado de forecast de saldo con pandas, tendencias y patrones
type: project
---

**Decisión:** Se refactorizó el servicio de forecast de saldo para usar pandas con análisis avanzado.

**Why:** El usuario solicitó usar pandas para analisis mas sofisticado: deteccion de outliers, tendencias de gasto, patrones por dia de semana, y prediccion con media movil.

**How to apply:**
- **Service:** `student/services/balance_forecast_service.py` con pandas para analisis avanzado
- **Tool:** `chat/skill/get_balance_forecast/tool.py` integra el servicio con el chatbot
- **Dependencies:** pandas, numpy (instalados en venv)
- **Fallback:** Si pandas no esta disponible, usa calculo basico

**Caracteristicas implementadas:**
1. **Media movil de 7 dias** para suavizar variaciones y predecir mejor
2. **Deteccion de outliers** usando IQR (Q1 - 1.5*IQR, Q3 + 1.5*IQR)
3. **Tendencia de gasto**: 'increasing', 'decreasing', 'stable' (compara primera vs segunda mitad del periodo)
4. **Patron por dia de semana**: 'higher_on_weekends', 'higher_on_weekdays', 'no_pattern'
5. **Nivel de confianza**: 'high', 'medium', 'low' (basado en coeficiente de variacion y cantidad de transacciones)
6. **Margen de error**: Calculado como +/- 2 * desviacion estandar en terminos de dias
7. **Ajuste por tendencia**: Recarga recomendada aumenta 20% si tendencia es creciente

**Formula mejorada:**
```
1. Crear DataFrame pandas con transacciones
2. Agrupar por dia para obtener gasto diario
3. Calcular media movil de 7 dias
4. daily_average = ultima_media_movil (no promedio simple)
5. days_until_empty = saldo_actual / daily_average
6. margin_of_error = (std_dev / daily_average) * 2
7. recommended_reload = daily_average * 30 * trend_factor
```

**Tests:** 5/5 passed (`agent_test_balance_forecast_pandas.py`)

**Fecha de actualizacion:** 2026-05-17
