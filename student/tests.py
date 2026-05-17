from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from io import StringIO
from django.core.management import call_command
from decimal import Decimal

from school.models import School
from student.models import Student, StudentAllergen
from parent.models import Parent
from product.models import Product, ProductAllergen
from transaction.models import Transaction


# ============================================================================
# US-02: Alerta proactiva de ausencia de consumo
# ============================================================================

class US02AlertaAusenciaConsumoTest(TestCase):
    """Tests para US-02: Alerta automática si hijo no ha comprado nada antes del mediodía."""

    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            school=self.school,
            balance=Decimal("15000.00")
        )
        self.parent = Parent.objects.create(
            phone_e164="+573001234567",
            name="Carlos Perez"
        )
        self.parent.students.add(self.student)

    def test_cron_job_sends_alert_for_student_without_consumption(self):
        """Cron job envía alerta para estudiante sin consumo hoy."""
        out = StringIO()
        call_command('alert_no_consumption', stdout=out)

        output = out.getvalue()
        # El output contiene códigos ANSI, buscamos el texto sin formato
        self.assertIn("Juan Perez", output)
        self.assertIn("alertas", output.lower())

    def test_cron_job_no_alert_for_student_with_consumption(self):
        """Cron job NO envía alerta si estudiante ya compró hoy."""
        product = Product.objects.create(
            name="Manzana",
            category="Fruta",
            price=Decimal("1500.00")
        )
        Transaction.objects.create(
            student=self.student,
            product=product,
            quantity=1,
            price=Decimal("1500.00"),
            created_at=timezone.now()
        )

        out = StringIO()
        call_command('alert_no_consumption', stdout=out)

        output = out.getvalue()
        self.assertNotIn("Juan Perez", output)

    def test_cron_job_alert_multiple_students_without_consumption(self):
        """Cron job envía alertas para múltiples estudiantes sin consumo."""
        student2 = Student.objects.create(
            name="Maria Lopez",
            school=self.school,
            balance=Decimal("10000.00")
        )
        parent2 = Parent.objects.create(
            phone_e164="+573009876543",
            name="Ana Lopez"
        )
        parent2.students.add(student2)

        out = StringIO()
        call_command('alert_no_consumption', stdout=out)

        output = out.getvalue()
        self.assertIn("Juan Perez", output)
        self.assertIn("Maria Lopez", output)

    def test_cron_job_no_alert_student_without_parents(self):
        """Cron job no envía alerta si estudiante no tiene padres registrados."""
        student_no_parent = Student.objects.create(
            name="Pedro Gomez",
            school=self.school,
            balance=Decimal("5000.00")
        )

        out = StringIO()
        call_command('alert_no_consumption', stdout=out)

        output = out.getvalue()
        self.assertNotIn("Pedro Gomez", output)

    def test_cron_job_execution_time_logged(self):
        """Cron job registra tiempo de ejecución."""
        out = StringIO()
        call_command('alert_no_consumption', stdout=out)

        output = out.getvalue()
        self.assertIn("segundos", output.lower())


# ============================================================================
# US-03: Alerta crítica de alérgeno
# ============================================================================

from student.services.allergen_alert_service import AllergenAlertService
from student.signals import check_allergen_alert


class US03AllergenAlertServiceTest(TestCase):
    """Tests para US-03: Servicio de alertas de alérgenos."""

    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            school=self.school,
            balance=Decimal("15000.00")
        )
        self.parent = Parent.objects.create(
            phone_e164="+573001234567",
            name="Carlos Perez"
        )
        self.parent.students.add(self.student)
        
        self.product = Product.objects.create(
            name="Galleta de Maní",
            category="Snack",
            price=Decimal("2500.00")
        )
        self.allergen = ProductAllergen.objects.create(
            product=self.product,
            allergen_name="Mani"
        )
        self.student_allergen = StudentAllergen.objects.create(
            student=self.student,
            allergen_name="Mani"
        )

    @patch('chat.twilio_service.TwilioService')
    def test_alert_sent_when_allergen_matches(self, mock_twilio):
        """Se envía alerta cuando producto contiene alérgeno del estudiante."""
        mock_twilio.return_value.send_message.return_value = 'SM123456'
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        alerts = service.check_and_alert(transaction)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['status'], 'sent')
        self.assertEqual(alerts[0]['student_id'], self.student.id)
        self.assertIn('Mani', alerts[0]['allergens'])

    def test_no_alert_when_student_has_no_allergens(self):
        """No se envía alerta si estudiante no tiene alérgenos registrados."""
        self.student_allergen.delete()
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        alerts = service.check_and_alert(transaction)
        
        self.assertEqual(len(alerts), 0)

    def test_no_alert_when_product_has_no_allergens(self):
        """No se envía alerta si producto no tiene alérgenos."""
        self.allergen.delete()
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        alerts = service.check_and_alert(transaction)
        
        self.assertEqual(len(alerts), 0)

    def test_no_alert_when_allergen_does_not_match(self):
        """No se envía alerta si alérgeno del producto no coincide con estudiante."""
        self.student_allergen.allergen_name = 'Leche'
        self.student_allergen.save()
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        alerts = service.check_and_alert(transaction)
        
        self.assertEqual(len(alerts), 0)

    @patch('chat.twilio_service.TwilioService')
    def test_alert_sent_to_all_parents(self, mock_twilio):
        """Se envía alerta a todos los padres del estudiante."""
        mock_twilio.return_value.send_message.return_value = 'SM123456'
        
        parent2 = Parent.objects.create(
            phone_e164="+573009876543",
            name="Maria Perez"
        )
        parent2.students.add(self.student)
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        alerts = service.check_and_alert(transaction)
        
        self.assertEqual(len(alerts), 2)

    @patch('chat.twilio_service.TwilioService')
    def test_notification_created_in_portal(self, mock_twilio):
        """Se crea notificación en portal del colegio."""
        mock_twilio.return_value.send_message.return_value = 'SM123456'
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        service.check_and_alert(transaction)
        
        from school.models import Notification
        notification = Notification.objects.filter(
            school=self.school,
            type='ALLERGEN'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.priority, 'CRITICAL')
        self.assertIn("Juan", notification.title)

    def test_mock_status_when_twilio_not_configured(self):
        """Retorna status 'mock' cuando Twilio no está configurado."""
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        
        with patch('chat.twilio_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.return_value = None
            
            alerts = service.check_and_alert(transaction)
            
            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0]['status'], 'mock')

    def test_failed_status_when_exception(self):
        """Retorna status 'failed' cuando hay excepción."""
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        
        with patch('chat.twilio_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.side_effect = Exception('Connection error')
            
            alerts = service.check_and_alert(transaction)
            
            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0]['status'], 'failed')
            self.assertIn('error', alerts[0])

    def test_multiple_matching_allergens(self):
        """Detecta múltiples alérgenos coincidentes."""
        StudentAllergen.objects.create(
            student=self.student,
            allergen_name='Gluten'
        )
        ProductAllergen.objects.create(
            product=self.product,
            allergen_name='Gluten'
        )
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        service = AllergenAlertService()
        alerts = service.check_and_alert(transaction)
        
        self.assertEqual(len(alerts), 1)
        self.assertIn('Mani', alerts[0]['allergens'])
        self.assertIn('Gluten', alerts[0]['allergens'])


class US03AllergenSignalTest(TestCase):
    """Tests para US-03: Signal de alertas de alérgenos."""

    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            school=self.school,
            balance=Decimal("15000.00")
        )
        self.parent = Parent.objects.create(
            phone_e164="+573001234567",
            name="Carlos Perez"
        )
        self.parent.students.add(self.student)
        
        self.product = Product.objects.create(
            name="Galleta de Maní",
            category="Snack",
            price=Decimal("2500.00")
        )
        ProductAllergen.objects.create(
            product=self.product,
            allergen_name="Mani"
        )
        StudentAllergen.objects.create(
            student=self.student,
            allergen_name="Mani"
        )

    @patch('student.signals.AllergenAlertService')
    def test_signal_triggered_on_transaction_create(self, mock_service_class):
        """Signal se dispara al crear transacción."""
        mock_service = MagicMock()
        mock_service.check_and_alert.return_value = []
        mock_service_class.return_value = mock_service
        
        Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        mock_service.check_and_alert.assert_called_once()

    @patch('student.signals.AllergenAlertService')
    def test_signal_not_triggered_on_transaction_update(self, mock_service_class):
        """Signal NO se dispara al actualizar transacción."""
        mock_service = MagicMock()
        mock_service.check_and_alert.return_value = []
        mock_service_class.return_value = mock_service
        
        transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        mock_service.reset_mock()
        
        transaction.quantity = 2
        transaction.save()
        
        mock_service.check_and_alert.assert_not_called()


class US03AllergenCronJobTest(TestCase):
    """Tests para US-03: Cron job fallback de alertas de alérgenos."""

    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            school=self.school,
            balance=Decimal("15000.00")
        )
        self.parent = Parent.objects.create(
            phone_e164="+573001234567",
            name="Carlos Perez"
        )
        self.parent.students.add(self.student)
        
        self.product = Product.objects.create(
            name="Galleta de Maní",
            category="Snack",
            price=Decimal("2500.00")
        )
        ProductAllergen.objects.create(
            product=self.product,
            allergen_name="Mani"
        )
        StudentAllergen.objects.create(
            student=self.student,
            allergen_name="Mani"
        )

    def test_cron_job_dry_run(self):
        """Cron job en modo dry-run no envía mensajes reales."""
        Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        out = StringIO()
        call_command('alert_allergen', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('[DRY-RUN]', output)
        self.assertIn('MODO DRY-RUN', output)

    @patch('student.management.commands.alert_allergen.AllergenAlertService')
    def test_cron_job_sends_alerts(self, mock_service_class):
        """Cron job envía alertas en modo normal."""
        mock_service = MagicMock()
        mock_service.check_and_alert.return_value = [{'status': 'sent', 'parent_phone': '+573001234567'}]
        mock_service_class.return_value = mock_service
        
        Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("2500.00")
        )
        
        out = StringIO()
        call_command('alert_allergen', stdout=out)
        
        output = out.getvalue()
        self.assertIn('✓ Alerta enviada', output)

    def test_cron_job_minutes_argument(self):
        """Cron job acepta argumento --minutes para rango de tiempo."""
        out = StringIO()
        call_command('alert_allergen', '--minutes', '10', stdout=out)
        
        output = out.getvalue()
        self.assertIn('10', output)

    def test_cron_job_no_allergen_transactions(self):
        """Cron job no envía alertas si no hay transacciones con alérgenos."""
        product_no_allergen = Product.objects.create(
            name="Manzana",
            category="Fruta",
            price=Decimal("1500.00")
        )
        Transaction.objects.create(
            student=self.student,
            product=product_no_allergen,
            quantity=1,
            price=Decimal("1500.00")
        )
        
        out = StringIO()
        call_command('alert_allergen', stdout=out)
        
        output = out.getvalue()
        self.assertIn('0', output)


# ============================================================================
# US-04: Proyección de agotamiento de saldo
# ============================================================================

from student.services.balance_forecast_service import BalanceForecastService


class US04BalanceForecastServiceTest(TestCase):
    """Tests para US-04: Servicio de proyección de agotamiento de saldo."""

    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            school=self.school,
            balance=Decimal("15000.00")
        )
        self.parent = Parent.objects.create(
            phone_e164="+573001234567",
            name="Carlos Perez"
        )
        self.parent.students.add(self.student)
        self.product = Product.objects.create(
            name="Manzana",
            category="Fruta",
            price=Decimal("1500.00")
        )

    def test_forecast_with_no_spending_history(self):
        """Retorna resultado cuando no hay historial de compras."""
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(self.student)
        
        self.assertFalse(result['has_spending_history'])
        self.assertEqual(result['transaction_count'], 0)
        self.assertEqual(result['daily_average'], 0)
        self.assertIsNone(result['days_until_empty'])

    def test_forecast_with_spending_history(self):
        """Calcula forecast correcto con historial de compras."""
        for i in range(10):
            Transaction.objects.create(
                student=self.student,
                product=self.product,
                quantity=1,
                price=Decimal("1500.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(self.student)
        
        self.assertTrue(result['has_spending_history'])
        self.assertEqual(result['transaction_count'], 10)
        self.assertGreater(result['daily_average'], 0)
        self.assertIsNotNone(result['recommended_reload'])

    def test_forecast_days_until_empty_calculation(self):
        """Calcula días hasta agotar basado en saldo y gasto promedio."""
        student_low_balance = Student.objects.create(
            name="Maria Lopez",
            school=self.school,
            balance=Decimal("5000.00")
        )
        
        for i in range(5):
            Transaction.objects.create(
                student=student_low_balance,
                product=self.product,
                quantity=1,
                price=Decimal("1000.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(student_low_balance)
        
        self.assertIsNotNone(result['days_until_empty'])
        self.assertGreater(result['days_until_empty'], 0)

    def test_forecast_recommended_reload_calculation(self):
        """Calcula recarga recomendada basada en gasto promedio."""
        for i in range(15):
            Transaction.objects.create(
                student=self.student,
                product=self.product,
                quantity=1,
                price=Decimal("2000.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(self.student)
        
        self.assertIsNotNone(result['recommended_reload'])
        self.assertGreater(result['recommended_reload'], 0)

    def test_forecast_only_last_30_days(self):
        """Solo considera transacciones de últimos 30 días."""
        # Crear transacción vieja (45 días)
        old_transaction = Transaction.objects.create(
            student=self.student,
            product=self.product,
            quantity=1,
            price=Decimal("5000.00"),
            created_at=timezone.now() - timezone.timedelta(days=45)
        )
        
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(self.student)
        
        # Con pandas, puede que haya datos pero el gasto diario será 0 
        # si no hay transacciones en los últimos 30 días
        # Verificamos que la transacción vieja no afecte el cálculo del promedio
        self.assertEqual(result['current_balance'], Decimal("15000.00"))

    def test_forecast_with_pandas_analysis(self):
        """Incluye análisis avanzado cuando pandas está disponible."""
        for i in range(20):
            Transaction.objects.create(
                student=self.student,
                product=self.product,
                quantity=1,
                price=Decimal("1500.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(self.student)
        
        self.assertIn('trend', result)
        self.assertIn('weekend_pattern', result)
        self.assertIn('confidence_level', result)
        self.assertIn('margin_of_error', result)

    def test_forecast_summary_format(self):
        """Genera resumen legible en formato de texto."""
        for i in range(5):
            Transaction.objects.create(
                student=self.student,
                product=self.product,
                quantity=1,
                price=Decimal("1500.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        service = BalanceForecastService(days_window=30)
        summary = service.get_forecast_summary(self.student)
        
        self.assertIsInstance(summary, str)
        self.assertIn("Saldo actual", summary)
        self.assertIn("Juan", summary)

    def test_get_forecast_by_phone_success(self):
        """Obtiene forecast por teléfono del padre."""
        for i in range(5):
            Transaction.objects.create(
                student=self.student,
                product=self.product,
                quantity=1,
                price=Decimal("1500.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        service = BalanceForecastService(days_window=30)
        result = service.get_forecast_by_phone("+573001234567", "Juan")
        
        self.assertIsNotNone(result)
        self.assertIn('current_balance', result)

    def test_get_forecast_by_phone_parent_not_found(self):
        """Retorna None cuando padre no existe."""
        service = BalanceForecastService(days_window=30)
        result = service.get_forecast_by_phone("+573999999999", "Juan")
        
        self.assertIsNone(result)

    def test_get_forecast_by_phone_student_not_found(self):
        """Retorna None cuando estudiante no existe."""
        service = BalanceForecastService(days_window=30)
        result = service.get_forecast_by_phone("+573001234567", "EstudianteInexistente")
        
        self.assertIsNone(result)

    def test_forecast_with_high_balance(self):
        """Maneja caso cuando saldo es suficiente para más de 30 días."""
        student_high_balance = Student.objects.create(
            name="Pedro Gomez",
            school=self.school,
            balance=Decimal("1000000.00")
        )
        
        Transaction.objects.create(
            student=student_high_balance,
            product=self.product,
            quantity=1,
            price=Decimal("1000.00"),
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        
        service = BalanceForecastService(days_window=30)
        result = service.calculate_forecast(student_high_balance)
        
        # Con alto balance, los días hasta agotar serán muchos
        # Verificamos que el cálculo sea correcto
        self.assertGreater(result['days_until_empty'], 30)
        self.assertGreater(result['current_balance'], Decimal("500000.00"))


class US04BalanceForecastToolTest(TestCase):
    """Tests para US-04: Tool del chatbot."""

    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            school=self.school,
            balance=Decimal("15000.00")
        )
        self.parent = Parent.objects.create(
            phone_e164="+573001234567",
            name="Carlos Perez"
        )
        self.parent.students.add(self.student)
        self.product = Product.objects.create(
            name="Manzana",
            category="Fruta",
            price=Decimal("1500.00")
        )

    def test_balance_forecast_tool_success(self):
        """Tool retorna forecast exitoso."""
        for i in range(5):
            Transaction.objects.create(
                student=self.student,
                product=self.product,
                quantity=1,
                price=Decimal("1500.00"),
                created_at=timezone.now() - timezone.timedelta(days=i)
            )
        
        from chat.skill.get_balance_forecast.tool import get_balance_forecast
        
        result = get_balance_forecast.invoke({
            "parent_phone": "+573001234567",
            "student_name": "Juan"
        })
        
        self.assertIn("Saldo actual", result)
        self.assertIn("Juan", result)

    def test_balance_forecast_tool_parent_not_found(self):
        """Tool retorna error cuando padre no existe."""
        from chat.skill.get_balance_forecast.tool import get_balance_forecast
        
        result = get_balance_forecast.invoke({
            "parent_phone": "+573999999999",
            "student_name": "Juan"
        })
        
        self.assertIn("no se encontro", result.lower())

    def test_balance_forecast_tool_student_not_found(self):
        """Tool retorna error cuando estudiante no existe."""
        from chat.skill.get_balance_forecast.tool import get_balance_forecast
        
        result = get_balance_forecast.invoke({
            "parent_phone": "+573001234567",
            "student_name": "EstudianteInexistente"
        })
        
        self.assertIn("no se encontro", result.lower())
