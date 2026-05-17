from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from io import StringIO
from django.core.management import call_command

from cafeteria.models import Inventory, CafeteriaAdmin
from cafeteria.services.stock_alert_service import StockAlertService
from school.models import School
from product.models import Product


class StockAlertServiceTest(TestCase):
    """Tests para el servicio de alertas de stock."""

    def setUp(self):
        self.school = School.objects.create(name='Test School')
        self.product = Product.objects.create(
            name='Test Product',
            category='Bebidas',
            price=1.50
        )
        self.admin = CafeteriaAdmin.objects.create(
            phone_e164='+573001234567',
            school=self.school
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            school=self.school,
            current_stock=5,
            minimum_stock=10
        )

    def test_check_and_alert_with_critical_stock(self):
        """El servicio envía alerta cuando current_stock <= minimum_stock."""
        service = StockAlertService()
        
        with patch('cafeteria.services.stock_alert_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.return_value = 'SM123456'
            
            alerts = service.check_and_alert(self.inventory)
            
            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0]['status'], 'sent')
            self.assertEqual(alerts[0]['admin_phone'], '+573001234567')
            self.assertEqual(alerts[0]['current_stock'], 5)
            self.assertEqual(alerts[0]['minimum_stock'], 10)

    def test_no_alert_when_stock_is_above_minimum(self):
        """No se envía alerta cuando current_stock > minimum_stock."""
        self.inventory.current_stock = 15
        self.inventory.save()
        
        service = StockAlertService()
        alerts = service.check_and_alert(self.inventory)
        
        self.assertEqual(len(alerts), 0)

    def test_no_alert_when_no_admins_registered(self):
        """No se envía alerta si no hay administradores registrados."""
        self.admin.delete()
        
        service = StockAlertService()
        alerts = service.check_and_alert(self.inventory)
        
        self.assertEqual(len(alerts), 0)

    def test_alert_sent_to_all_admins(self):
        """Se envía alerta a todos los administradores de la cafetería."""
        CafeteriaAdmin.objects.create(
            phone_e164='+573009876543',
            school=self.school
        )
        
        service = StockAlertService()
        
        with patch('cafeteria.services.stock_alert_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.return_value = 'SM123456'
            
            alerts = service.check_and_alert(self.inventory)
            
            self.assertEqual(len(alerts), 2)

    def test_mock_status_when_twilio_not_configured(self):
        """El servicio retorna status 'mock' cuando Twilio no está configurado."""
        service = StockAlertService()
        
        with patch('cafeteria.services.stock_alert_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.return_value = None
            
            alerts = service.check_and_alert(self.inventory)
            
            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0]['status'], 'mock')

    def test_failed_status_when_exception(self):
        """El servicio retorna status 'failed' cuando hay excepción."""
        service = StockAlertService()
        
        with patch('cafeteria.services.stock_alert_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.side_effect = Exception('Connection error')
            
            alerts = service.check_and_alert(self.inventory)
            
            self.assertEqual(len(alerts), 1)
            self.assertEqual(alerts[0]['status'], 'failed')
            self.assertIn('error', alerts[0])

    def test_check_all_critical_stock(self):
        """El método check_all_critical_stock verifica todos los inventarios críticos."""
        inventory2 = Inventory.objects.create(
            product=Product.objects.create(name='Product 2', category='Snacks', price=2.00),
            school=self.school,
            current_stock=3,
            minimum_stock=8
        )
        
        service = StockAlertService()
        
        with patch('cafeteria.services.stock_alert_service.TwilioService') as mock_twilio:
            mock_twilio.return_value.send_message.return_value = 'SM123456'
            
            all_alerts = service.check_all_critical_stock()
            
            self.assertEqual(len(all_alerts), 2)


class StockAlertSignalTest(TestCase):
    """Tests para el signal de alertas de stock."""

    def setUp(self):
        self.school = School.objects.create(name='Test School')
        self.product = Product.objects.create(
            name='Test Product',
            category='Bebidas',
            price=1.50
        )
        self.admin = CafeteriaAdmin.objects.create(
            phone_e164='+573001234567',
            school=self.school
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            school=self.school,
            current_stock=15,
            minimum_stock=10
        )

    @patch('cafeteria.signals.StockAlertService')
    def test_signal_triggered_on_inventory_save_critical(self, mock_service_class):
        """El signal se dispara al guardar inventario con stock crítico."""
        mock_service = MagicMock()
        mock_service.check_and_alert.return_value = [{'status': 'sent'}]
        mock_service_class.return_value = mock_service
        
        self.inventory.current_stock = 5
        self.inventory.save()
        
        mock_service.check_and_alert.assert_called_once_with(self.inventory)

    @patch('cafeteria.signals.StockAlertService')
    def test_signal_triggered_on_inventory_save_normal(self, mock_service_class):
        """El signal se dispara pero no envía alerta con stock normal."""
        mock_service = MagicMock()
        mock_service.check_and_alert.return_value = []
        mock_service_class.return_value = mock_service
        
        self.inventory.current_stock = 15
        self.inventory.save()
        
        mock_service.check_and_alert.assert_called_once_with(self.inventory)


class StockAlertCronJobTest(TestCase):
    """Tests para el cron job de alertas de stock."""

    def setUp(self):
        self.school = School.objects.create(name='Test School')
        self.product = Product.objects.create(
            name='Test Product',
            category='Bebidas',
            price=1.50
        )
        self.admin = CafeteriaAdmin.objects.create(
            phone_e164='+573001234567',
            school=self.school
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            school=self.school,
            current_stock=5,
            minimum_stock=10
        )

    def test_cron_job_dry_run(self):
        """El cron job en modo dry-run no envía mensajes reales."""
        out = StringIO()
        
        with patch('cafeteria.management.commands.alert_stock.StockAlertService') as mock_service:
            mock_service.return_value.check_and_alert.return_value = []
            
            call_command('alert_stock', '--dry-run', stdout=out)
            
            output = out.getvalue()
            self.assertIn('[DRY-RUN]', output)
            self.assertIn('MODO DRY-RUN', output)

    @patch('cafeteria.management.commands.alert_stock.StockAlertService')
    def test_cron_job_sends_alerts(self, mock_service_class):
        """El cron job envía alertas en modo normal."""
        mock_service = MagicMock()
        mock_service.check_and_alert.return_value = [{'status': 'sent', 'admin_phone': '+573001234567'}]
        mock_service_class.return_value = mock_service
        
        out = StringIO()
        call_command('alert_stock', stdout=out)
        
        output = out.getvalue()
        self.assertIn('✓ Alerta enviada', output)
        mock_service.check_and_alert.assert_called()

    def test_cron_job_no_critical_stock(self):
        """El cron job no envía alertas cuando no hay stock crítico."""
        self.inventory.current_stock = 20
        self.inventory.save()
        
        out = StringIO()
        call_command('alert_stock', stdout=out)
        
        output = out.getvalue()
        self.assertIn('0 productos con stock crítico', output)
