import logging
from typing import Optional, Tuple, Dict, Any
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from transaction.models import Transaction
from student.models import Student

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas no disponible. Usando fallback a calculo basico.")


class BalanceForecastService:
    """
    Servicio para calcular cuando se acabara el saldo de un estudiante
    y recomendar monto de recarga, con analisis avanzado usando pandas.

    Caracteristicas:
    - Calculo de promedio de gasto en ultimos 30 dias
    - Deteccion de outliers (compras atipicas)
    - Analisis de tendencia (increasing/decreasing/stable)
    - Patrones por dia de semana
    - Prediccion con media movil
    - Margen de error estimado
    """

    def __init__(self, days_window: int = 30):
        self.days_window = days_window

    def calculate_forecast(self, student: Student) -> Dict[str, Any]:
        """
        Calcula la fecha estimada de agotamiento del saldo y recomienda monto de recarga.
        """
        current_balance = float(student.balance)

        if not PANDAS_AVAILABLE:
            return self._calculate_forecast_basic(student, current_balance)

        return self._calculate_forecast_pandas(student, current_balance)

    def _calculate_forecast_pandas(self, student: Student, current_balance: float) -> Dict[str, Any]:
        """Calculo avanzado usando pandas para analisis de tendencias y patrones."""
        
        # Obtener transacciones de los ultimos 30 dias
        date_threshold = timezone.now() - timedelta(days=self.days_window)
        transactions = Transaction.objects.filter(
            student=student,
            created_at__gte=date_threshold
        ).order_by('created_at')

        transaction_count = transactions.count()

        # Sin historial
        if transaction_count == 0:
            return self._no_history_result(current_balance, student)

        # Crear DataFrame convirtiendo Decimal a float
        data = []
        for t in transactions:
            data.append({
                'created_at': t.created_at,
                'price': float(t.price),
                'quantity': t.quantity
            })
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        df['day_of_week'] = df['created_at'].dt.dayofweek
        df['total_price'] = df['price'] * df['quantity']

        # Calcular gasto por dia
        daily_spending = df.groupby('date')['total_price'].sum().reset_index()
        daily_spending.columns = ['date', 'daily_total']

        # Metricas basicas
        total_spent = df['total_price'].sum()
        daily_average = total_spent / self.days_window
        
        # Media movil de 7 dias para suavizar variaciones
        if len(daily_spending) >= 7:
            daily_spending['rolling_avg'] = daily_spending['daily_total'].rolling(window=7).mean()
            predicted_daily_avg = daily_spending['rolling_avg'].iloc[-1]
        else:
            predicted_daily_avg = daily_average

        # Deteccion de outliers usando IQR
        Q1 = df['total_price'].quantile(0.25)
        Q3 = df['total_price'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df['total_price'] < lower_bound) | (df['total_price'] > upper_bound)]
        outlier_count = len(outliers)

        # Calcular dias hasta agotar
        if predicted_daily_avg > 0:
            days_until_empty = current_balance / predicted_daily_avg
            estimated_empty_date = timezone.now() + timedelta(days=int(days_until_empty))
        else:
            days_until_empty = None
            estimated_empty_date = None

        # Analisis de tendencia
        trend = self._calculate_trend(daily_spending)

        # Patron por dia de semana
        weekend_pattern = self._calculate_weekend_pattern(df)

        # Nivel de confianza
        confidence_level = self._calculate_confidence(daily_spending, transaction_count)
        
        # Margen de error
        if len(daily_spending) > 1:
            std_dev = daily_spending['daily_total'].std()
            margin_of_error = round((std_dev / predicted_daily_avg) * 2, 1) if predicted_daily_avg > 0 else 3
        else:
            margin_of_error = 5

        # Calcular recarga recomendada con ajuste por tendencia
        trend_factor = 1.0
        if trend == 'increasing':
            trend_factor = 1.2
        elif trend == 'decreasing':
            trend_factor = 0.9
        
        recommended_reload = predicted_daily_avg * 30 * trend_factor

        # Recarga minima basada en ultimo producto comprado
        last_transaction = Transaction.objects.filter(student=student).order_by('-created_at').first()
        
        if last_transaction:
            min_reload = float(last_transaction.price) * 10
            recommended_reload = max(recommended_reload, min_reload)

        return {
            'current_balance': current_balance,
            'daily_average': round(predicted_daily_avg, 2),
            'days_until_empty': round(days_until_empty, 1) if days_until_empty else None,
            'estimated_empty_date': estimated_empty_date,
            'recommended_reload': round(recommended_reload, 2),
            'has_spending_history': True,
            'transaction_count': transaction_count,
            'total_spent_30d': round(total_spent, 2),
            'trend': trend,
            'weekend_pattern': weekend_pattern,
            'outlier_count': outlier_count,
            'confidence_level': confidence_level,
            'margin_of_error': margin_of_error,
            'uses_pandas': True
        }

    def _calculate_forecast_basic(self, student: Student, current_balance: float) -> Dict[str, Any]:
        """Fallback a calculo basico cuando pandas no esta disponible."""
        
        date_threshold = timezone.now() - timedelta(days=self.days_window)
        transactions = Transaction.objects.filter(
            student=student,
            created_at__gte=date_threshold
        )

        transaction_count = transactions.count()

        if transaction_count == 0:
            return self._no_history_result(current_balance, student)

        total_spent = sum(float(t.price) for t in transactions)
        daily_average = total_spent / self.days_window

        if daily_average > 0:
            days_until_empty = current_balance / daily_average
            estimated_empty_date = timezone.now() + timedelta(days=int(days_until_empty))
            recommended_reload = daily_average * 30
        else:
            days_until_empty = None
            estimated_empty_date = None
            recommended_reload = 5.00

        return {
            'current_balance': current_balance,
            'daily_average': round(daily_average, 2),
            'days_until_empty': round(days_until_empty, 1) if days_until_empty else None,
            'estimated_empty_date': estimated_empty_date,
            'recommended_reload': round(recommended_reload, 2),
            'has_spending_history': True,
            'transaction_count': transaction_count,
            'total_spent_30d': round(total_spent, 2),
            'trend': 'unknown',
            'weekend_pattern': 'unknown',
            'outlier_count': 0,
            'confidence_level': 'low',
            'margin_of_error': 5,
            'uses_pandas': False
        }

    def _no_history_result(self, current_balance: float, student: Student) -> Dict[str, Any]:
        """Resultado cuando no hay historial de compras."""
        
        last_transaction = Transaction.objects.filter(student=student).order_by('-created_at').first()

        if last_transaction:
            recommended_reload = float(last_transaction.price) * 10
        else:
            recommended_reload = 5.00

        return {
            'current_balance': current_balance,
            'daily_average': 0,
            'days_until_empty': None,
            'estimated_empty_date': None,
            'recommended_reload': round(recommended_reload, 2),
            'has_spending_history': False,
            'transaction_count': 0,
            'total_spent_30d': 0,
            'trend': 'unknown',
            'weekend_pattern': 'unknown',
            'outlier_count': 0,
            'confidence_level': 'low',
            'margin_of_error': None,
            'uses_pandas': False
        }

    def _calculate_trend(self, daily_spending) -> str:
        """Calcula la tendencia de gasto comparando primera y segunda mitad del periodo."""
        if len(daily_spending) < 4:
            return 'insufficient_data'

        mid_point = len(daily_spending) // 2
        first_half_avg = daily_spending['daily_total'].iloc[:mid_point].mean()
        second_half_avg = daily_spending['daily_total'].iloc[mid_point:].mean()

        if pd.isna(first_half_avg) or pd.isna(second_half_avg):
            return 'insufficient_data'

        change_pct = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0

        if change_pct > 0.2:
            return 'increasing'
        elif change_pct < -0.2:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_weekend_pattern(self, df) -> str:
        """Analiza patron de gasto por dia de semana vs fin de semana."""
        if len(df) < 5:
            return 'insufficient_data'

        weekday_spending = df[df['day_of_week'] < 5]['total_price'].mean()
        weekend_spending = df[df['day_of_week'] >= 5]['total_price'].mean()

        if pd.isna(weekday_spending) or pd.isna(weekend_spending):
            return 'insufficient_data'

        if weekend_spending > weekday_spending * 1.3:
            return 'higher_on_weekends'
        elif weekday_spending > weekend_spending * 1.3:
            return 'higher_on_weekdays'
        else:
            return 'no_pattern'

    def _calculate_confidence(self, daily_spending, transaction_count: int) -> str:
        """Calcula nivel de confianza basado en consistencia de datos."""
        if transaction_count < 5:
            return 'low'
        
        if len(daily_spending) < 3:
            return 'low'

        mean = daily_spending['daily_total'].mean()
        std = daily_spending['daily_total'].std()
        
        if pd.isna(mean) or mean == 0:
            return 'low'
        
        cv = std / mean if mean > 0 else 1

        if cv < 0.3 and transaction_count >= 15:
            return 'high'
        elif cv < 0.5 and transaction_count >= 10:
            return 'medium'
        else:
            return 'low'

    def get_forecast_by_phone(self, parent_phone: str, student_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene el forecast del saldo para un estudiante identificado por telefono del padre."""
        from parent.models import Parent

        try:
            parent = Parent.objects.filter(phone_e164=parent_phone).first()
            if not parent:
                return None

            student = parent.students.filter(name__icontains=student_name).first()
            if not student:
                return None

            return self.calculate_forecast(student)

        except Exception as e:
            logger.error(f"Error calculating forecast: {e}")
            return None

    def get_forecast_summary(self, student: Student) -> str:
        """Genera un resumen legible del forecast para mostrar al usuario."""
        result = self.calculate_forecast(student)

        lines = [
            f"Saldo actual de {student.name}: ${result['current_balance']:.2f}"
        ]

        if result['has_spending_history']:
            lines.append(f"Gasto promedio diario (30 dias): ${result['daily_average']:.2f}")
            lines.append(f"Total gastado en 30 dias: ${result['total_spent_30d']:.2f}")

            if result['days_until_empty'] is not None:
                margin = result['margin_of_error']
                date_str = result['estimated_empty_date'].strftime('%d/%m/%Y')
                lines.append(f"Se agotara en: {result['days_until_empty']:.0f} dias (+/-{margin} dias, {date_str})")
            else:
                lines.append("Saldo suficiente por mas de 30 dias")

            trend_emoji = {
                'increasing': '[SUBIENDO]',
                'decreasing': '[BAJANDO]',
                'stable': '[ESTABLE]',
                'insufficient_data': '[?]'
            }.get(result['trend'], '[?]')
            lines.append(f"Tendencia de gasto: {trend_emoji} {result['trend']}")

            if result['weekend_pattern'] == 'higher_on_weekends':
                lines.append("Patron: Gasta mas los fines de semana")
            elif result['weekend_pattern'] == 'higher_on_weekdays':
                lines.append("Patron: Gasta mas en dias de semana")

            if result['outlier_count'] > 0:
                lines.append(f"Atencion: {result['outlier_count']} compras atipicas detectadas")

            confidence_emoji = {
                'high': '[ALTA]',
                'medium': '[MEDIA]',
                'low': '[BAJA]'
            }.get(result['confidence_level'], '[?]')
            lines.append(f"Confianza: {confidence_emoji} {result['confidence_level']}")

            lines.append(f"Recarga recomendada: ${result['recommended_reload']:.2f}")
        else:
            lines.append("No hay compras registradas en los ultimos 30 dias")
            lines.append(f"Recarga sugerida: ${result['recommended_reload']:.2f}")

        return "\n".join(lines)
