from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from school.models import School, SchoolUser
from cafeteria.models import Inventory
from student.models import Student


class SchoolAuthenticationForm(AuthenticationForm):
    """
    Formulario de login para usuarios de colegios.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Usuario'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })

    def confirm_login_allowed(self, user):
        """Verifica que el usuario sea activo y pertenezca a un colegio."""
        super().confirm_login_allowed(user)
        
        if not hasattr(user, 'school_profile'):
            raise forms.ValidationError(
                "Este usuario no está asociado a ningún colegio.",
                code='invalid_login'
            )
        
        if not user.school_profile.is_active:
            raise forms.ValidationError(
                "Esta cuenta ha sido desactivada. Contacta al administrador.",
                code='inactive'
            )


class SchoolUserRegistrationForm(UserCreationForm):
    """
    Formulario de registro para nuevos usuarios de colegios.
    """
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label='Colegio',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=[
            ('ADMIN', 'Administrador'),
            ('CAFETERIA', 'Admin Cafetería'),
            ('SECRETARIA', 'Secretaría'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57...'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'school', 'role', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuario'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Crear perfil de usuario de colegio
            SchoolUser.objects.create(
                user=user,
                school=self.cleaned_data['school'],
                role=self.cleaned_data['role'],
                phone=self.cleaned_data['phone']
            )
            
            # Asignar permisos segun rol
            self._assign_permissions(user)
        
        return user

    def _assign_permissions(self, user):
        """Asigna permisos segun el rol del usuario."""
        from django.contrib.auth.models import Permission
        
        role = self.cleaned_data['role']
        permissions = []
        
        # Permisos basicos para todos
        permissions.extend([
            'can_view_dashboard',
            'can_view_notifications',
        ])
        
        # Permisos adicionales segun rol
        if role == 'ADMIN':
            permissions.extend([
                'can_manage_loans',
                'can_manage_inventory',
            ])
        elif role == 'CAFETERIA':
            permissions.append('can_manage_inventory')
        
        # Asignar permisos
        for codename in permissions:
            try:
                perm = Permission.objects.get(codename=codename, content_type__app_label='school')
                user.user_permissions.add(perm)
            except Permission.DoesNotExist:
                pass


class InventoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.product.name} - stock {obj.current_stock} - ${obj.product.price}'


class SaleForm(forms.Form):
    school = forms.ModelChoiceField(
        queryset=School.objects.order_by('name'),
        label='Escuela',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        label='Estudiante',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    inventory = InventoryChoiceField(
        queryset=Inventory.objects.none(),
        label='Producto',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Cantidad',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )

    def __init__(self, *args, school=None, selected_school=None, is_superuser=False, **kwargs):
        super().__init__(*args, **kwargs)
        active_school = selected_school or school

        if is_superuser:
            self.fields['school'].required = True
            if active_school:
                self.fields['school'].initial = active_school
        else:
            self.fields.pop('school')

        students = Student.objects.select_related('school').order_by('school__name', 'name')
        inventory = Inventory.objects.select_related('product', 'school').filter(
            current_stock__gt=0
        ).order_by('product__category', 'product__name')

        if active_school is not None:
            students = students.filter(school=active_school)
            inventory = inventory.filter(school=active_school)
        elif is_superuser:
            students = Student.objects.none()
            inventory = Inventory.objects.none()

        self.fields['student'].queryset = students
        self.fields['inventory'].queryset = inventory

    def clean(self):
        cleaned_data = super().clean()
        school = cleaned_data.get('school')
        student = cleaned_data.get('student')
        inventory = cleaned_data.get('inventory')
        quantity = cleaned_data.get('quantity') or 0

        if school and student and student.school_id != school.id:
            raise forms.ValidationError('El estudiante no pertenece a la escuela seleccionada.')

        if school and inventory and inventory.school_id != school.id:
            raise forms.ValidationError('El producto no pertenece al inventario de la escuela seleccionada.')

        if student and inventory and student.school_id != inventory.school_id:
            raise forms.ValidationError('El estudiante y el producto deben pertenecer a la misma escuela.')

        if inventory and quantity and inventory.current_stock < quantity:
            raise forms.ValidationError(
                f'Stock insuficiente. Disponible: {inventory.current_stock}, solicitado: {quantity}.'
            )

        if student and inventory and quantity:
            total = inventory.product.price * quantity
            cleaned_data['total'] = total
            if student.balance < total:
                raise forms.ValidationError(
                    f'Saldo insuficiente. Saldo actual: ${student.balance}, total venta: ${total}.'
                )

        return cleaned_data
