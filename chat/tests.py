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

from parent.models import Parent
from product.models import Product, ProductAllergen
from student.models import StudentAllergen
from transaction.models import Transaction, Recarga
from chat.skill.get_childs.tool import get_childs
from chat.skill.get_student_balance.tool import get_student_balance
from chat.skill.get_student_allergens.tool import get_student_allergens
from chat.skill.get_healthy_recommendations.tool import get_healthy_recommendations
from chat.skill.get_recent_recharges.tool import get_recent_recharges
from django.utils import timezone
import datetime

class SkillsTestCase(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Colegio Test", nit="12345")
        
        self.student1 = Student.objects.create(name="Juan Perez", school=self.school, balance=Decimal("15000.00"))
        self.student2 = Student.objects.create(name="Maria Perez", school=self.school, balance=Decimal("2000.00"))
        
        self.parent = Parent.objects.create(phone_e164="+573001234567", name="Carlos Perez")
        self.parent.students.add(self.student1, self.student2)
        
        self.allergen1 = StudentAllergen.objects.create(student=self.student1, allergen_name="Mani")
        
        self.prod_healthy = Product.objects.create(name="Manzana", category="Fruta", price=Decimal("1500.00"))
        self.prod_allergy = Product.objects.create(name="Galleta de Mani", category="Snack", price=Decimal("2500.00"))
        ProductAllergen.objects.create(product=self.prod_allergy, allergen_name="Mani")
        
        self.recharge = Recarga.objects.create(student=self.student1, fecha=timezone.now().date(), valor=Decimal("20000.00"))
        self.tx = Transaction.objects.create(student=self.student1, product=self.prod_healthy, quantity=1, price=Decimal("1500.00"))

    def test_get_childs(self):
        result = get_childs.invoke({"phone_e164": "+573001234567"})
        self.assertIn("Juan Perez", result)
        self.assertIn("Maria Perez", result)

    def test_get_student_balance(self):
        result = get_student_balance.invoke({"parent_phone": "+573001234567", "student_name": "Juan"})
        self.assertIn("15000.00", result)

    def test_get_student_allergens(self):
        result = get_student_allergens.invoke({"parent_phone": "+573001234567", "student_name": "Juan"})
        self.assertIn("Mani", result)
        
        result2 = get_student_allergens.invoke({"parent_phone": "+573001234567", "student_name": "Maria"})
        self.assertIn("no tiene ninguna", result2)

    def test_get_recent_recharges(self):
        result = get_recent_recharges.invoke({"parent_phone": "+573001234567", "student_name": "Juan"})
        self.assertIn("20000.00", result)

    def test_get_healthy_recommendations(self):
        result = get_healthy_recommendations.invoke({"parent_phone": "+573001234567", "student_name": "Juan"})
        # Should contain Manzana but NOT Galleta de Mani
        self.assertIn("Manzana", result)
        self.assertNotIn("Galleta de Mani", result)
