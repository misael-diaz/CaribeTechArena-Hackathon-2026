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
            messages.success(request, f'Usuario {user.username} registrado correctamente.')
            return redirect('school:login')
    else:
        form = SchoolUserRegistrationForm()
    
    return render(request, 'school/register.html', {'form': form})


def _get_school_context_for_user(request):
    try:
        school_user = request.user.school_profile
        return school_user, school_user.school
    except SchoolUser.DoesNotExist:
        if request.user.is_superuser:
            return None, None
        return None, None


def _can_create_sale(request, school_user):
    if request.user.is_superuser:
        return True
    if not school_user:
        return False
    return school_user.role in ('ADMIN', 'CAFETERIA') or request.user.has_perm('school.can_manage_inventory')


@login_required
def create_sale(request):
    school_user, school = _get_school_context_for_user(request)

    if not _can_create_sale(request, school_user):
        messages.error(request, 'No tienes permisos para registrar ventas.')
        return redirect('school:dashboard')

    selected_school = None if request.user.is_superuser else school
    selected_school_id = request.POST.get('school') if request.method == 'POST' else request.GET.get('school')
    if request.user.is_superuser and selected_school_id:
        selected_school = get_object_or_404(School, id=selected_school_id)

    if request.method == 'POST':
        form = SaleForm(
            request.POST,
            school=school,
            selected_school=selected_school,
            is_superuser=request.user.is_superuser,
        )
        if form.is_valid():
            student = form.cleaned_data['student']
            inventory = form.cleaned_data['inventory']
            product = inventory.product
            quantity = form.cleaned_data['quantity']
            total = form.cleaned_data['total']

            if school and student.school_id != school.id:
                messages.error(request, 'No puedes registrar ventas para estudiantes de otro colegio.')
                return redirect('school:create_sale')

            with db_transaction.atomic():
                locked_student = Student.objects.select_for_update().get(id=student.id)
                locked_inventory = Inventory.objects.select_for_update().select_related('product').get(id=inventory.id)
                if locked_student.balance < total:
                    form.add_error(None, f'Saldo insuficiente. Saldo actual: ${locked_student.balance}, total venta: ${total}.')
                elif locked_inventory.current_stock < quantity:
                    form.add_error(None, f'Stock insuficiente. Disponible: {locked_inventory.current_stock}, solicitado: {quantity}.')
                else:
                    sale = Transaction.objects.create(
                        student=locked_student,
                        product=locked_inventory.product,
                        quantity=quantity,
                        price=locked_inventory.product.price,
                    )
                    locked_student.balance = locked_student.balance - total
                    locked_student.save(update_fields=['balance'])
                    locked_inventory.current_stock = locked_inventory.current_stock - quantity
                    locked_inventory.save(update_fields=['current_stock'])
                    messages.success(
                        request,
                        f'Venta #{sale.id} registrada: {quantity} x {locked_inventory.product.name} para {locked_student.name}.'
                    )
                    if request.user.is_superuser:
                        return redirect(f"{request.path}?school={locked_student.school_id}")
                    return redirect('school:create_sale')
    else:
        form = SaleForm(
            school=school,
            selected_school=selected_school,
            is_superuser=request.user.is_superuser,
        )

    recent_sales = Transaction.objects.select_related('student', 'student__school', 'product').order_by('-created_at')
    if selected_school:
        recent_sales = recent_sales.filter(student__school=selected_school)

    context = {
        'form': form,
        'school_user': school_user,
        'school': selected_school or school,
        'is_superuser': request.user.is_superuser,
        'selected_school': selected_school,
        'has_inventory': form.fields['inventory'].queryset.exists(),
        'recent_sales': recent_sales[:8],
    }
    return render(request, 'school/create_sale.html', context)


@login_required
def school_dashboard(request):
    # Verificar si es superusuario (admin de Django)
    is_superuser = request.user.is_superuser
    
    # Intentar obtener perfil de usuario de colegio
    try:
        school_user = request.user.school_profile
        school = school_user.school
    except SchoolUser.DoesNotExist:
        # Si es superusuario, permitir acceso pero en modo admin
        if is_superuser:
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
            'loans': Notification.objects.filter(type='LOAN', is_read=False).count(),
            'stock': Notification.objects.filter(type='STOCK', is_read=False).count(),
            'allergen': Notification.objects.filter(type='ALLERGEN', is_read=False).count(),
            'total': Notification.objects.filter(is_read=False).count(),
        }
        
        # Admin ve todos los prestamos
        recent_loans = []
        if request.user.has_perm('school.can_manage_loans'):
            from transaction.models import Loan
            recent_loans = Loan.objects.all().select_related('student', 'parent').order_by('-created_at')[:5]
        
        stats = {
            'total_students': Student.objects.count(),
            'unread_notifications': notification_stats['total'],
            'pending_loans': len(recent_loans),
        }
        transactions = Transaction.objects.all()
    else:
        # Usuario normal solo ve datos de su escuela
        unread_notifications = Notification.objects.filter(
            school=school,
            is_read=False
        ).select_related('user')[:10]
        
        notification_stats = {
            'loans': Notification.objects.filter(school=school, type='LOAN', is_read=False).count(),
            'stock': Notification.objects.filter(school=school, type='STOCK', is_read=False).count(),
            'allergen': Notification.objects.filter(school=school, type='ALLERGEN', is_read=False).count(),
            'total': Notification.objects.filter(school=school, is_read=False).count(),
        }
        
        recent_loans = []
        if request.user.has_perm('school.can_manage_loans'):
            from transaction.models import Loan
            recent_loans = Loan.objects.filter(
                parent__students__school=school
            ).select_related('student', 'parent').order_by('-created_at')[:5]
        
        stats = {
            'total_students': Student.objects.filter(school=school).count(),
            'unread_notifications': notification_stats['total'],
            'pending_loans': len(recent_loans),
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
    pie_gradient = ', '.join(pie_stops) if pie_stops else '#e2e8f0 0% 100%'

    month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    current_year = timezone.now().year
    month_totals = {row['month']: row['total'] or 0 for row in transactions.filter(created_at__year=current_year).annotate(month=ExtractMonth('created_at')).values('month').annotate(total=Sum(sale_amount))}
    max_month_total = max([float(value) for value in month_totals.values()] or [1])
    monthly_sales = []
    for month_number, month_name in enumerate(month_names, start=1):
        amount = month_totals.get(month_number, 0)
        monthly_sales.append({
            'name': month_name,
            'total': amount,
            'height': round((float(amount) / max_month_total) * 100) if max_month_total else 0,
        })

    stats.update({
        'total_sales': total_sales,
        'sales_transactions': transactions.count(),
        'top_category': category_sales[0]['name'] if category_sales else 'Sin ventas',
    })
    
    context = {
        'school_user': school_user,
        'school': school,
        'is_superuser': is_superuser,
        'dashboard_scope': 'Todos los colegios' if is_superuser and school_user is None else school.name,
        'unread_notifications': unread_notifications,
        'notification_stats': notification_stats,
        'recent_loans': recent_loans,
        'stats': stats,
        'category_sales': category_sales,
        'pie_gradient': pie_gradient,
        'monthly_sales': monthly_sales,
        'current_year': current_year,
    }
    
    return render(request, 'school/dashboard.html', context)


@login_required
def notifications_list(request):
    try:
        school_user = request.user.school_profile
    except SchoolUser.DoesNotExist:
        if request.user.is_superuser:
            school_user = None
        else:
            messages.error(request, 'Tu usuario no esta asociado a ningun colegio.')
            return redirect('school:logout')
    
    notification_type = request.GET.get('type', '')
    show_read = request.GET.get('show_read', 'false') == 'true'
    
    if request.user.is_superuser and school_user is None:
        notifications = Notification.objects.all()
    else:
        notifications = Notification.objects.filter(school=school_user.school)
    
    if notification_type:
        notifications = notifications.filter(type=notification_type)
    
    if not show_read:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.select_related('user').order_by('-priority', '-created_at')
    
    page = int(request.GET.get('page', 1))
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    notifications_page = notifications[start:end]
    has_next = end < notifications.count()
    
    context = {
        'notifications': notifications_page,  # ← Solo de esta escuela
        'has_next': has_next,
        'next_page': page + 1,
        'current_type': notification_type,
        'show_read': show_read,
    }
    
    return render(request, 'school/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    try:
        school_user = request.user.school_profile
    except SchoolUser.DoesNotExist:
        if request.user.is_superuser:
            school_user = None
        else:
            messages.error(request, 'Tu usuario no esta asociado a ningun colegio.')
            return redirect('school:logout')
    
    if request.user.is_superuser and school_user is None:
        notification = get_object_or_404(Notification, id=notification_id)
    else:
        notification = get_object_or_404(Notification, id=notification_id, school=school_user.school)
    
    notification.mark_as_read()
    messages.success(request, 'Notificacion marcada como leida.')
    
    next_url = request.GET.get('next', 'school:dashboard')
    return redirect(next_url)


@login_required
def mark_all_notifications_read(request):
    try:
        school_user = request.user.school_profile
    except SchoolUser.DoesNotExist:
        if request.user.is_superuser:
            school_user = None
        else:
            messages.error(request, 'Tu usuario no esta asociado a ningun colegio.')
            return redirect('school:logout')
    
    notifications = Notification.objects.filter(is_read=False)
    if not (request.user.is_superuser and school_user is None):
        notifications = notifications.filter(school=school_user.school)

    count = notifications.update(is_read=True, read_at=timezone.now())
    
    messages.success(request, f'{count} notificaciones marcadas como leidas.')
    return redirect('school:notifications')
