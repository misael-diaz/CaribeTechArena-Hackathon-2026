from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import ExtractMonth
from .forms import SaleForm, SchoolAuthenticationForm, SchoolUserRegistrationForm
from .models import SchoolUser, Notification, School
from cafeteria.models import Inventory
from student.models import Student
from transaction.models import Transaction
from .decorators import track_endpoint


def school_login(request):
    if request.user.is_authenticated:
        return redirect('school:dashboard')

    if request.method == 'POST':
        form = SchoolAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username}!')
            next_url = request.GET.get('next', 'school:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contrasena incorrectos.')
    else:
        form = SchoolAuthenticationForm()

    return render(request, 'school/login.html', {'form': form})


def school_logout(request):
    logout(request)
    messages.info(request, 'Sesion cerrada correctamente.')
    return redirect('school:login')


def school_register(request):
    if not request.user.is_superuser and not request.user.has_perm('school.can_manage_inventory'):
        messages.error(request, 'No tienes permisos para registrar usuarios.')
        return redirect('school:login')

    if request.method == 'POST':
        form = SchoolUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} creado exitosamente.')
            return redirect('school:login')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = SchoolUserRegistrationForm()

    return render(request, 'school/register.html', {'form': form})


@login_required
@track_endpoint
def school_dashboard(request):
    # Verificar si es superusuario (admin de Django)
    is_superuser = request.user.is_superuser

    # Intentar obtener perfil de usuario de colegio
    try:
        school_user = request.user.school_profile
        school = school_user.school
    except User.school_profile.RelatedObjectDoesNotExist:
        # Si el usuario no tiene SchoolUser vinculado
        if is_superuser:
            # Superusuario puede acceder como admin
            school = School.objects.first()
            school_user = None  # Indica que es modo admin
        else:
            messages.error(request, 'Tu usuario no esta asociado a ningun colegio.')
            return redirect('school:logout')

    # AISLAMIENTO: Solo notificaciones de ESTA escuela (o todas si es admin)
    if is_superuser and school_user is None:
        # Admin ve todas las notificaciones
        unread_notifications = Notification.objects.filter(
            is_read=False
        ).select_related('school', 'user')[:10]

        notification_stats = {
            'loans': 0,
            'stock': Notification.objects.filter(type='STOCK', is_read=False).count(),
            'allergen': Notification.objects.filter(type='ALLERGEN', is_read=False).count(),
            'total': Notification.objects.filter(is_read=False).count(),
        }

        # Admin ve todos los prestamos → [ELIMINADO: sistema de préstamos retirado]
        recent_loans = []

        stats = {
            'total_students': Student.objects.count(),
            'unread_notifications': notification_stats['total'],
            'pending_loans': 0,
        }
        transactions = Transaction.objects.all()
    else:
        # Usuario normal solo ve datos de su escuela
        unread_notifications = Notification.objects.filter(
            school=school,
            is_read=False
        ).select_related('user')[:10]

        notification_stats = {
            'loans': 0,
            'stock': Notification.objects.filter(school=school, type='STOCK', is_read=False).count(),
            'allergen': Notification.objects.filter(school=school, type='ALLERGEN', is_read=False).count(),
            'total': Notification.objects.filter(school=school, is_read=False).count(),
        }

        # Usuario normal ve todos los prestamos → [ELIMINADO: sistema de préstamos retirado]
        recent_loans = []

        stats = {
            'total_students': Student.objects.filter(school=school).count(),
            'unread_notifications': notification_stats['total'],
            'pending_loans': 0,
        }
        transactions = Transaction.objects.filter(student__school=school)

    sale_amount = ExpressionWrapper(
        F('price') * F('quantity'),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    total_sales = transactions.aggregate(total=Sum(sale_amount))['total'] or 0

    category_rows = list(
        transactions.values('product__category')
        .annotate(total=Sum(sale_amount), quantity=Sum('quantity'), transactions_count=Count('id'))
        .order_by('-total')[:6]
    )
    category_sales = []
    for index, row in enumerate(category_rows):
        total = row['total'] or 0
        percent = round((float(total) / float(total_sales) * 100), 1) if total_sales else 0
        category_sales.append({
            'name': row['product__category'] or 'Sin categoria',
            'total': total,
            'quantity': row['quantity'] or 0,
            'count': row['transactions_count'],
            'percent': percent,
            'color': ['#10b981', '#0f172a', '#34d399', '#64748b', '#a7f3d0', '#cbd5e1'][index],
        })

    pie_stops = []
    cursor = 0
    for category in category_sales:
        next_cursor = cursor + category['percent']
        pie_stops.append(f"{category['color']} {cursor:.1f}% {next_cursor:.1f}%")
        cursor = next_cursor

    context = {
        'school': school,
        'is_superuser': is_superuser,
        'unread_notifications': unread_notifications,
        'notification_stats': notification_stats,
        'stats': stats,
        'recent_sales': transactions.order_by('-created_at')[:8],
        'total_sales': total_sales,
        'category_sales': category_sales,
        'pie_stops': pie_stops,
        'recent_loans': recent_loans,
    }
    return render(request, 'school/dashboard.html', context)


@login_required
def create_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST, is_superuser=request.user.is_superuser)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    inventory = form.cleaned_data['inventory']
                    student = form.cleaned_data['student']
                    quantity = form.cleaned_data['quantity']
                    total = form.cleaned_data['total']

                    # Actualizar stock
                    inventory.current_stock -= quantity
                    inventory.save()

                    # Crear transaccion
                    transaction = Transaction.objects.create(
                        student=student,
                        product=inventory.product,
                        quantity=quantity,
                        price=inventory.product.price,
                        created_at=timezone.now(),
                    )

                    # Actualizar saldo del estudiante
                    student.balance -= total
                    student.save()

                    messages.success(request, f'Venta registrada: {inventory.product.name} x{quantity}')
                    return redirect('school:create_sale')
            except Exception as e:
                messages.error(request, f'Error al procesar la venta: {e}')
    else:
        form = SaleForm(is_superuser=request.user.is_superuser)

    context = {
        'form': form,
        'recent_sales': Transaction.objects.order_by('-created_at')[:8],
    }
    return render(request, 'school/create_sale.html', context)


@login_required
def notifications_list(request):
    school_user = request.user.school_profile
    school = school_user.school

    notifications = Notification.objects.filter(
        school=school
    ).select_related('user').order_by('-created_at')

    # Marcar como leidas
    Notification.objects.filter(
        school=school,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    context = {
        'notifications': notifications,
        'school': school,
    }
    return render(request, 'school/notifications.html', context)


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.mark_as_read()
    return redirect('school:notifications_list')


@login_required
def dashboard_chart_data(request):
    # Datos para gráfico de ventas por categoría
    school_user = request.user.school_profile
    school = school_user.school

    transactions = Transaction.objects.filter(
        student__school=school
    )

    sale_amount = ExpressionWrapper(
        F('price') * F('quantity'),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    total_sales = transactions.aggregate(total=Sum(sale_amount))['total'] or 0

    category_rows = list(
        transactions.values('product__category')
        .annotate(total=Sum(sale_amount), quantity=Sum('quantity'), transactions_count=Count('id'))
        .order_by('-total')[:6]
    )
    category_sales = []
    for index, row in enumerate(category_rows):
        total = row['total'] or 0
        percent = round((float(total) / float(total_sales) * 100), 1) if total_sales else 0
        category_sales.append({
            'name': row['product__category'] or 'Sin categoria',
            'total': total,
            'quantity': row['quantity'] or 0,
            'count': row['transactions_count'],
            'percent': percent,
            'color': ['#10b981', '#0f172a', '#34d399', '#64748b', '#a7f3d0', '#cbd5e1'][index],
        })

    return JsonResponse({'data': category_sales})


from django.http import JsonResponse


@login_required
def dashboard_chart_data(request):
    # Datos para gráfico de ventas por categoría
    school_user = request.user.school_profile
    school = school_user.school

    transactions = Transaction.objects.filter(
        student__school=school
    )

    sale_amount = ExpressionWrapper(
        F('price') * F('quantity'),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    total_sales = transactions.aggregate(total=Sum(sale_amount))['total'] or 0

    category_rows = list(
        transactions.values('product__category')
        .annotate(total=Sum(sale_amount), quantity=Sum('quantity'), transactions_count=Count('id'))
        .order_by('-total')[:6]
    )
    category_sales = []
    for index, row in enumerate(category_rows):
        total = row['total'] or 0
        percent = round((float(total) / float(total_sales) * 100), 1) if total_sales else 0
        category_sales.append({
            'name': row['product__category'] or 'Sin categoria',
            'total': total,
            'quantity': row['quantity'] or 0,
            'count': row['transactions_count'],
            'percent': percent,
            'color': ['#10b981', '#0f172a', '#34d399', '#64748b', '#a7f3d0', '#cbd5e1'][index],
        })

    return JsonResponse({'data': category_sales})


@login_required
def metrics_list(request):
    """
    Vista protegida para ver métricas de endpoints.
    Solo accesible para superusuarios o usuarios con permiso 'can_view_dashboard'.
    """
    # Verificar permisos
    if not (request.user.is_superuser or request.user.has_perm('school.can_view_dashboard')):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acceso denegado.")

    from school.models import EndpointMetric

    # Obtener métricas recientes
    metrics = EndpointMetric.objects.all().order_by('-created_at')[:100]

    context = {
        'metrics': metrics,
        'total_count': EndpointMetric.objects.count(),
        'last_24h': EndpointMetric.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(hours=24)).count(),
    }
    return render(request, 'school/metrics.html', context)