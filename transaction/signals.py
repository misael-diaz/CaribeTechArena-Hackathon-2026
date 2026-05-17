from django.db.models.signals import pre_save
from django.dispatch import receiver
from transaction.models import Transaction
from student.models import Student
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Transaction)
def check_balance_for_transaction(sender, instance, **kwargs):
    """
    Signal que verifica si el estudiante tiene saldo suficiente antes de crear una transaccion.
    
    Si el estudiante no tiene saldo, NO se crea la transaccion.
    El sistema de prestamos debe manejar esta situacion por separado.
    
    Nota: Este signal es informativo. La validacion real debe hacerse en el servicio.
    """
    if instance._state.adding:  # Solo en creacion, no en actualizacion
        student = instance.student
        total_price = float(instance.price) * instance.quantity
        
        if float(student.balance) < total_price:
            # Log para debugging, pero no prevenimos la transaccion aqui
            # La prevencion debe hacerse en el servicio que crea la transaccion
            logger.warning(
                f"Estudiante {student.name} intenta comprar ${total_price} "
                f"pero solo tiene ${float(student.balance)}. "
                f"Sugerir prestamo de ${total_price - float(student.balance)}"
            )
