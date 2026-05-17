from langchain.tools import tool
from django.db import connection, transaction
from decimal import Decimal


@tool
def buy_product(parent_phone: str, student_name: str, product_name: str, quantity: int = 1) -> str:
    """
    PROCESA UNA COMPRA: compra un producto de la cafeteria para un hijo usando su saldo digital.
    Verifica saldo suficiente y stock disponible antes de hacer la compra.
    Usa esta herramienta cuando el padre quiera comprar algo para su hijo.
    NO digas que no puedes comprar. USA esta herramienta para procesar la compra.
    """
    if quantity < 1:
        return "La cantidad debe ser al menos 1."

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT s.id, s.name, s.balance, s.school_id
                    FROM parent_parent p
                    JOIN parent_parent_students pps ON p.id = pps.parent_id
                    JOIN student_student s ON pps.student_id = s.id
                    WHERE p.phone_e164 = %s AND UPPER(s.name) LIKE UPPER(%s)
                    LIMIT 1
                """, [parent_phone, f'%{student_name}%'])
                student = cursor.fetchone()

            if not student:
                return f"No se encontro un estudiante llamado *{student_name}* vinculado a tu numero."

            student_id, student_name, balance, school_id = student
            balance = Decimal(str(balance))

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, price
                    FROM product_product
                    WHERE UPPER(name) LIKE UPPER(%s)
                    LIMIT 1
                """, [f'%{product_name}%'])
                product = cursor.fetchone()

            if not product:
                return f"No se encontro un producto llamado *{product_name}*."

            product_id, product_name_db, price = product
            price = Decimal(str(price))
            total = price * quantity

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, current_stock
                    FROM cafeteria_inventory
                    WHERE product_id = %s AND school_id = %s
                    LIMIT 1
                """, [product_id, school_id])
                inventory = cursor.fetchone()

            if not inventory:
                inventory_id = None
                current_stock = 0
            else:
                inventory_id, current_stock = inventory

            if current_stock < quantity:
                return (f"No hay suficiente stock de *{product_name_db}*. "
                        f"Disponible: {current_stock}, solicitado: {quantity}.")

            if balance < total:
                return (f"Saldo insuficiente. *{student_name}* tiene ${float(balance):.2f} "
                        f"y el total es ${float(total):.2f}.")

            from django.utils import timezone
            from transaction.models import Transaction

            tx = Transaction.objects.create(
                student_id=student_id,
                product_id=product_id,
                quantity=quantity,
                price=price,
                created_at=timezone.now(),
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE student_student SET balance = balance - %s WHERE id = %s",
                    [total, student_id]
                )

            if inventory_id:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE cafeteria_inventory SET current_stock = current_stock - %s WHERE id = %s",
                        [quantity, inventory_id]
                    )

            new_balance = balance - total
            return (f"*Compra exitosa!* {product_name_db} x{quantity} "
                    f"para *{student_name}* \u2014 Total: ${float(total):.2f}\n"
                    f"Saldo restante: ${float(new_balance):.2f}")

    except Exception as e:
        return f"Error al procesar la compra: {str(e)}"
