from django.test import TestCase
from .models import Conversation
from school.models import School
from student.models import Student
from decimal import Decimal

class BioFoodTest(TestCase):
    def setUp(self):
        # Setup basic data
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        self.student = Student.objects.create(
            name="Juan Perez",
            external_id="EXT001",
            school=self.school,
            balance=Decimal("5000.00")
        )

    def test_student_creation(self):
        self.assertEqual(self.student.name, "Juan Perez")
        self.assertEqual(self.student.balance, Decimal("5000.00"))

    def test_conversation_creation(self):
        conv = Conversation.objects.create(phone_e164="573001234567")
        self.assertEqual(conv.phone_e164, "573001234567")
        self.assertEqual(conv.session_json, {})

    def test_webhook_get(self):
        # Webhook should only allow POST
        response = self.client.get('/chat/webhook/')
        self.assertEqual(response.status_code, 405)
