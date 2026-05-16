import os
import django
import psycopg2
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Byte.settings')
django.setup()

from school.models import School
from student.models import Student
from product.models import Product
from transaction.models import Transaction, Recarga

def clean_decimal(val):
    if val is None: return Decimal('0.00')
    if isinstance(val, (int, float, Decimal)): return Decimal(str(val))
    try:
        s = str(val).strip().replace(',', '.')
        return Decimal(s)
    except:
        return Decimal('0.00')

def clean_int(val):
    if val is None: return 0
    try:
        s = str(val).strip().replace(',', '.')
        return int(float(s))
    except:
        return 0

def import_data():
    pg_conn = None
    try:
        print("Connecting to external database...")
        pg_conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_DATABASE'),
            user=os.getenv('DB_USERNAME'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        # Use a server-side cursor to handle millions of rows
        pg_cur = pg_conn.cursor(name='huge_import_cursor')
        pg_cur.itersize = 5000
        
        # 1. Caches
        print("Caching Schools...")
        school_map = {s.name: s for s in School.objects.all()}
        print("Caching Products...")
        product_map = {p.name: p for p in Product.objects.all()}
        print("Caching Students...")
        student_cache = {s.external_id: s for s in Student.objects.all()}

        # 2. Process Recargas (305k rows)
        print("Processing ALL Recargas...")
        pg_cur.execute("SELECT usuario_identificacion, nombre_estudiante, identificacion_padre, nombre_padre, colegio, fecha, valor FROM hackaton_recargas")
        
        count = 0
        for row in pg_cur:
            ext_id, name, p_id, p_name, s_name, fecha, valor = row
            ext_id = str(ext_id).strip() if ext_id else None
            # Get or create student in cache
            if ext_id not in student_cache:
                s_name_clean = s_name.strip() if s_name else ""
                school = school_map.get(s_name_clean)
                if not school and s_name_clean:
                    school, _ = School.objects.get_or_create(name=s_name_clean)
                    school_map[s_name_clean] = school
                
                student, _ = Student.objects.get_or_create(
                    external_id=ext_id,
                    defaults={
                        'name': name.strip() if name else 'Unknown',
                        'grade': 'N/A',
                        'school': school or School.objects.first(),
                        'parent_id': str(p_id).strip() if p_id else None,
                        'parent_name': p_name.strip() if p_name else None,
                        'balance': Decimal('0.00')
                    }
                )
                student_cache[ext_id] = student
            
            student = student_cache[ext_id]
            val = clean_decimal(valor)
            # Use get_or_create to avoid duplicates on re-run
            _, created = Recarga.objects.get_or_create(
                student=student, 
                fecha=fecha, 
                valor=val
            )
            if created:
                student.balance += val
                student.save()
            
            count += 1
            if count % 2000 == 0: print(f"Processed {count} recargas...")

        # 3. Process ALL Ventas (4.2M rows)
        print("Processing ALL Ventas (4.2 million rows)... This will take a while.")
        pg_cur.execute("SELECT usuario_identificacion, nombre_producto, fecha, cantidad, precio, nombre_estudiante, identificacion_padre, nombre_padre, colegio FROM hackaton_ventas")
        
        count = 0
        transactions_to_create = []
        for row in pg_cur:
            ext_id, prod_name, fecha_str, cant_str, precio_str, s_name, p_id, p_name, col_name = row
            ext_id = str(ext_id).strip()            # Ensure student exists
            if ext_id not in student_cache:
                # Create student if missing (though they should be in recargas mostly)
                col_name_clean = col_name.strip() if col_name else ""
                school = school_map.get(col_name_clean)
                if not school and col_name_clean:
                    school, _ = School.objects.get_or_create(name=col_name_clean)
                    school_map[col_name_clean] = school
                
                student, _ = Student.objects.get_or_create(
                    external_id=ext_id,
                    defaults={
                        'name': s_name.strip() if s_name else 'Unknown',
                        'grade': 'N/A',
                        'school': school or School.objects.first(),
                        'parent_id': str(p_id).strip() if p_id else None,
                        'parent_name': p_name.strip() if p_name else None,
                        'balance': Decimal('0.00')
                    }
                )
                student_cache[ext_id] = student
            
            student = student_cache[ext_id]
            prod_name_clean = prod_name.strip() if prod_name else "Unknown Product"
            if prod_name_clean not in product_map:
                product, _ = Product.objects.get_or_create(
                    name=prod_name_clean, 
                    defaults={'price': clean_decimal(precio_str), 'category': 'General'}
                )
                product_map[prod_name_clean] = product
            
            product = product_map[prod_name_clean]
            qty = clean_int(cant_str)
            prc = clean_decimal(precio_str)
            
            transactions_to_create.append(Transaction(
                student=student,
                product=product,
                quantity=qty,
                price=prc
            ))
            
            # For 4M rows, we can't save each student one by one, it's too slow.
            # We'll need a better way to update balances later or just do it in batches.
            # But student.balance is important. I'll do it every 1000.
            student.balance -= (prc * qty)
            student.save()
            
            count += 1
            if len(transactions_to_create) >= 2000:
                Transaction.objects.bulk_create(transactions_to_create)
                transactions_to_create = []
                print(f"Processed {count} ventas...")

        if transactions_to_create:
            Transaction.objects.bulk_create(transactions_to_create)

        print("TOTAL IMPORT COMPLETED!")

    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    import_data()
