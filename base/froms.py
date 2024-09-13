from datetime import datetime

from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm, AuthenticationForm, UsernameField, \
    PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import User

from django.utils.translation import gettext_lazy as _
from django.forms import CharField, inlineformset_factory

from base.choices import ESTADO_PRESUPUESTO
from base.models import Cliente, Orden, Presupuesto, ItemSolicitado, Auto, HorasVendidasPorMes


class RegistrationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('tecnico', 'Técnico'),
        ('recepcionista', 'Recepcionista'),
        ('planificador', 'Planificador'),
    ]

    # Campo adicional para seleccionar el tipo de perfil
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label=_("Tipo de Perfil"),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    password1 = forms.CharField(  # Usar CharField de django.forms
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )
    password2 = forms.CharField(  # Usar CharField de django.forms
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')  # Añadimos 'role' aquí

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            })
        }

class LoginForm(AuthenticationForm):
    username = UsernameField(label=_("Your Username"),
                             widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}))
    password = forms.CharField(
        label=_("Your Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
    )


class UserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))


class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")


class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Old Password'
    }), label='Old Password')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")


class TecnicoCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class RecepcionistaCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class PlanificadorCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'email', 'dni', 'direccion', 'provincia', 'localidad']
        widgets = {

            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),





        }








class OrdenForms(forms.ModelForm):
    class Meta:
        model = Orden

        fields = [
             'auto', 'entrega', 'km', 'mano_de_obra'

        ]
        widgets = {

            'auto': forms.Select(attrs={'class': 'js-select_auto'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'entrega': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),

            'km': forms.TextInput(attrs={'class': 'form-control'}),
            'mano_de_obra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),


        }
        labels = {
            'auto': 'Vehículo',
        }

class ItemSolicitadoForm(forms.ModelForm):
    class Meta:
        model = ItemSolicitado
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'realizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

ItemSolicitadoFormSet = inlineformset_factory(
    Orden,
    ItemSolicitado,
    form=ItemSolicitadoForm,
    extra=1,  # Número de formularios vacíos que quieres mostrar por defecto
    can_delete=True
)

class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = [ 'detalle', 'precio','mano_de_obra_presupuesto']
        labels = { 'detalle':'detalle','precio': 'Precio', 'estado_presupuesto': 'Estado del presupuesto','mano_de_obra_presupuesto':'Mano de obra en horas'}

        widgets = {'detalle': forms.TextInput(attrs={'class': 'form-control'}),
                   'precio': forms.TextInput(attrs={'class': 'form-control'}),
                   'estado_presupuesto': forms.Select(choices=ESTADO_PRESUPUESTO, attrs={'class': 'form-control'}),
                   'tarea': forms.Select(attrs={'class': 'form-control'}),
                   'mano_de_obra_presupuesto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),

                   }



class TecnicoCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']



class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto

        fields = '__all__'

        widgets = {
            'cliente': forms.Select(attrs={'class': 'js-select_cliente'}),


            'garantia': forms.CheckboxInput(attrs={'class': 'form-control'}),
            'mano_de_obra': forms.TextInput(attrs={'class': 'form-control'}),
            'entrega': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),



            'anio': forms.Select(
                attrs={'class': 'form-control'},
                choices=[(year, year) for year in range(1990, datetime.now().year + 8)]
            ),
        }

class ObjetivoMensualForm(forms.ModelForm):
    class Meta:
        model = HorasVendidasPorMes
        fields = ['año', 'mes', 'objetivo_mensual']
        widgets = {
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            'mes': forms.NumberInput(attrs={'class': 'form-control'}),
            'objetivo_mensual': forms.NumberInput(attrs={'class': 'form-control'}),
        }