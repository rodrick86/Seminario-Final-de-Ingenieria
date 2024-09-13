import hashlib
import logging
import smtplib
import threading
from datetime import timedelta
from decimal import Decimal
from socket import socket

import self
from Tools.scripts.make_ctype import values
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordResetView, LogoutView, PasswordChangeView
from django.core.checks import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.db.models import Q, Value, Func, Sum, Count, F
from django.contrib import messages
from django.db.models.functions import Concat, datetime
from django.forms import CharField
from django.http import HttpResponseRedirect, JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, LogoutView
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import strip_tags
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, DetailView, TemplateView

from base.choices import ESTADO_ORDEN
from base.froms import UserSetPasswordForm, UserPasswordChangeForm, LoginForm, RegistrationForm, UserPasswordResetForm, \
    ClienteForm, OrdenForms, PresupuestoForm, ItemSolicitadoFormSet, AutoForm, RecepcionistaCreationForm, \
    PlanificadorCreationForm, ObjetivoMensualForm
from base.models import Cliente, Orden, Presupuesto, Tecnico, ItemSolicitado, Auto, Recepcionista, Planificador, \
    HorasVendidasPorMes
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from datetime import datetime, timedelta
import json
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def index(request):
    user = request.user
    tecnico = None

    if hasattr(user, 'tecnico'):
        tecnico = user.tecnico

    hoy = timezone.now().date()
    manana = hoy + timedelta(days=1)

    usuario_filtrado = request.GET.get('usuario')
    tecnico_filtrado = request.GET.get('tecnico')
    estado_filtrado = request.GET.get('estado')
    auto_filtrado = request.GET.get('auto')
    cliente_filtrado = request.GET.get('cliente')

    # Excluir órdenes con estado 'Entregado'
    ordenes = Orden.objects.exclude(estado='entregado')

    if usuario_filtrado:
        ordenes = ordenes.filter(usuario_id=usuario_filtrado)
    if tecnico_filtrado:
        ordenes = ordenes.filter(tecnico_id=tecnico_filtrado)
    if estado_filtrado:
        ordenes = ordenes.filter(estado=estado_filtrado)
    if auto_filtrado:
        ordenes = ordenes.filter(auto_id=auto_filtrado)
    if cliente_filtrado:
        ordenes = ordenes.filter(auto__cliente_id=cliente_filtrado)

    # Filtrar órdenes asignadas al técnico y creadas por el usuario, excluyendo 'Entregado'
    ordenes_asignadas_o_creadas = (ordenes.filter(tecnico=tecnico) | ordenes.filter(usuario=user)).distinct()

    # Ordenes asignadas que NO tienen el estado 'entregado'
    ordenes_no_entregadas = ordenes_asignadas_o_creadas.exclude(estado='entregado')

    ordenes_hoy = Orden.objects.filter(entrega__date=hoy).exclude(estado='entregado')
    ordenes_manana = Orden.objects.filter(entrega__date=manana).exclude(estado='entregado')

    horas_acumuladas = actualizar_acumulado_horas()

    usuarios_sin_tecnico = User.objects.exclude(tecnico__isnull=False)
    tecnicos = Tecnico.objects.all()
    clientes = Cliente.objects.all()
    autos = Auto.objects.all()

    # Ordenar las órdenes por fecha de creación en orden descendente
    ordenes = ordenes.order_by('-fecha_creacion')

    context = {
        'clientes': clientes,
        'ordenes': ordenes.distinct(),
        'presupuestos': Presupuesto.objects.all(),
        'ordenes_asignadas': ordenes_asignadas_o_creadas,
        'ordenes_no_entregadas': ordenes_no_entregadas,  # Agregar órdenes no entregadas al contexto
        'tecnicos': tecnicos,
        'user_role': user.get_role,
        'ordenes_hoy': ordenes_hoy,
        'ordenes_manana': ordenes_manana,
        'horas_acumuladas': horas_acumuladas,
        'usuarios': usuarios_sin_tecnico,
        'estados_orden': ESTADO_ORDEN,
        'autos': autos,
    }

    return render(request, 'index.html', context)


def obtener_ordenes_del_dia(request):
    hoy = timezone.now().date()
    manana = hoy + timedelta(days=1)

    ordenes_hoy = Orden.objects.filter(entrega__date=hoy)
    ordenes_manana = Orden.objects.filter(entrega__date=manana)

    # Agregar información de depuración
    print("Órdenes para hoy:", ordenes_hoy)
    print("Órdenes para mañana:", ordenes_manana)

    return render(request, 'obtener_ordenes_del_dia.html', {
        'ordenes_hoy': ordenes_hoy,
        'ordenes_manana': ordenes_manana,
    })




class UserRegistrationView(UserPassesTestMixin, CreateView):
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('index')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, 'Solo los administradores pueden registrar nuevos usuarios.')
        return render(self.request, self.template_name, )

    def form_valid(self, form):
        # Crear usuario
        user = form.save(commit=False)
        role = form.cleaned_data.get('role')

        # Asignar rol al usuario
        user.save()  # Guarda el usuario primero

        if role == 'tecnico':
            Tecnico.objects.create(user=user)
        elif role == 'recepcionista':
            Recepcionista.objects.create(user=user)
        elif role == 'planificador':
            Planificador.objects.create(user=user)

        messages.success(self.request, 'Usuario creado exitosamente.')
        return redirect(self.success_url)


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    reditect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('index')


class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/auth-reset-password.html'
    form_class = UserPasswordResetForm


class UserPasswrodResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/auth-password-reset-confirm.html'
    form_class = UserSetPasswordForm


class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/auth-change-password.html'
    form_class = UserPasswordChangeForm


class UserLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'accounts/logout.html'
    next_page = reverse_lazy('login')





def buscar_tecnico(request):
    tecnicos = Tecnico.objects.all()  # Obtén todos los técnicos
    tecnico_seleccionado = None
    user = request.user
    ordenes_asignadas = []

    if request.method == 'POST':
        tecnico_id = request.POST.get('tecnico')
        if tecnico_id:
            tecnico_seleccionado = Tecnico.objects.get(id=tecnico_id)
            ordenes_asignadas = Orden.objects.filter(tecnico=tecnico_seleccionado)

    context = {
        'tecnicos': tecnicos,
        'tecnico_seleccionado': tecnico_seleccionado,
        'ordenes_asignadas': ordenes_asignadas,
        'user_role': user.get_role,
    }

    return render(request, 'tecnico/buscar_tecnico.html', context)


@login_required
def dashboard_tecnico(request):
    # Obtener el usuario logueado
    user = request.user

    # Verificar si el usuario tiene un perfil de técnico asociado
    tecnico = None
    if hasattr(user, 'tecnico'):
        tecnico = user.tecnico  # Aquí se obtiene el objeto Tecnico relacionado con el usuario

    # Si el usuario es un técnico, obtener las órdenes asignadas a él que no están finalizadas
    if tecnico:
        # Excluir órdenes con estado 'finalizado'
        ordenes_asignadas = Orden.objects.filter(tecnico=tecnico).exclude(estado__exact='finalizado')
    else:
        ordenes_asignadas = None
        messages.error(request, "No tienes un perfil de técnico asociado.")

    context = {
        'ordenes_asignadas': ordenes_asignadas,
        'user_role': user.get_role,
    }

    return render(request, 'tecnico/dashboard_tecnico.html', context)



class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    success_url = reverse_lazy('lista_clientes')

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Cliente.objects.filter(
                Q(nombre__icontains=query) |
                Q(apellido__icontains=query) |
                Q(dni__icontains=query) |
                Q(telefono__icontains=query)
                # Agrega otros campos según tus necesidades
            )
        else:
            return Cliente.objects.all()


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('index')


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('lista_clientes')

def load_clientes(request):
    search = request.GET.get('term', '')
    clientes = Cliente.objects.annotate(
        full_name=Concat('nombre', Value(' '), 'apellido', output_field=CharField())
    ).filter(full_name__icontains=search)[:10]

    data = [
        {
            'id': cliente.id,
            'text': f"{cliente.full_name}",
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'direccion': cliente.direccion,
            'provincia': cliente.provincia,
            'localidad': cliente.localidad,
            'dni':cliente.dni,
        }
        for cliente in clientes
    ]

    return JsonResponse({'results': data}, safe=False)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('lista_clientes')


class CrearAuto(CreateView):
    model = Auto
    form_class = AutoForm
    template_name = 'auto/auto_form.html'
    success_url = reverse_lazy('index')  # O la URL a la que quieras redirigir después de guardar
class EditarAuto(UpdateView):
    model = Auto
    form_class = AutoForm
    template_name = 'auto/auto_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Auto, id=self.kwargs.get('pk'))

    def form_valid(self, form):
        response = super().form_valid(form)
        next_url = self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return response

    def get_success_url(self):
        # Redirige a 'index' si no se encuentra 'next' en los parámetros
        return reverse_lazy('index')



def load_auto(request):
    term = request.GET.get('term', '')
    autos = Auto.objects.filter(matricula__icontains=term).select_related('cliente')[:10]

    data = [
        {
            'id': auto.id,
            'text': auto.matricula,
            'matricula': auto.matricula,
            'chasis':auto.chasis,
            'anio':auto.anio,
            'vehiculo':auto.vehiculo,
            'cliente_nombre': auto.cliente.nombre,
            'cliente_apellido': auto.cliente.apellido,
            'cliente_telefono': auto.cliente.telefono,
            'cliente_email': auto.cliente.email,
            'cliente_direccion': auto.cliente.direccion,
            'cliente_dni': auto.cliente.dni,
        }
        for auto in autos
    ]

    return JsonResponse({'results': data}, safe=False)







class CrearOrden(LoginRequiredMixin, CreateView):
    model = Orden
    form_class = OrdenForms
    template_name = 'orden/orden_form.html'
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = ItemSolicitadoFormSet(self.request.POST, instance=self.object)
        else:
            context['items_formset'] = ItemSolicitadoFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        # Asignar el usuario actual a la orden
        form.instance.usuario = self.request.user
        self.object = form.save()  # Guarda la instancia de Orden con el usuario asignado

        # Crear y validar el formset
        items_formset = ItemSolicitadoFormSet(self.request.POST, instance=self.object)
        print("POST data for formset:", self.request.POST)
        print("Formset is valid:", items_formset.is_valid())

        if items_formset.is_valid():
            print("Formset cleaned data:", [form.cleaned_data for form in items_formset])
            items_formset.save()
            return super().form_valid(form)
        else:
            # Imprimir errores de validación del formset en la consola
            print("Formset errors:", items_formset.errors)
            return self.form_invalid(form)


class DetalleOrden(LoginRequiredMixin, DetailView):
    model = Orden
    context_object_name = 'orden'
    template_name = 'orden/orden.html'



    def post(self, request, *args, **kwargs):
        orden_id = request.POST.get('orden_id')
        intervencion_text = request.POST.get('intervencion')

        if orden_id and intervencion_text:
            try:
                orden = get_object_or_404(Orden, pk=orden_id)
                orden.intervencion = intervencion_text
                orden.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})

    def get_context_data(self, **kwargs):
        user = self.request.user



        context = super().get_context_data(**kwargs)


        context['auto'] = Auto.objects.all()
        context['orden'] = self.get_object()
        context['presupuestos'] = Presupuesto.objects.filter(orden=self.get_object()).order_by('-fecha_creacion')
        context['clientes'] = Cliente.objects.all()
        context['items_solicitados'] = ItemSolicitado.objects.filter(orden=self.get_object())

        context['user_role'] = user.get_role


        return context


def actualizar_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        realizado = request.POST.get('realizado') == 'true'

        item = ItemSolicitado.objects.get(id=item_id)
        item.realizado = realizado
        item.save()

        # Calcular el porcentaje de progreso
        total_items = ItemSolicitado.objects.filter(orden=item.orden).count()
        items_realizados = ItemSolicitado.objects.filter(orden=item.orden, realizado=True).count()
        porcentaje = (items_realizados / total_items) * 100 if total_items > 0 else 0

        # Actualizar el progreso en la orden
        orden = item.orden
        orden.progreso = porcentaje
        orden.save()

        return JsonResponse({'success': True, 'porcentaje': porcentaje})
    return JsonResponse({'success': False})

def obtener_estado_orden(request, orden_id):
    orden = Orden.objects.get(id=orden_id)
    return JsonResponse({'success': True, 'progreso': orden.progreso})


class EditarOrden(LoginRequiredMixin, UpdateView):
    model = Orden
    form_class = OrdenForms
    template_name = 'orden/editar_orden.html'



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        # Asegúrate de que obtienes la instancia actual de la orden
        context['orden'] = self.get_object()

        # Cargar ítems solicitados relacionados con la orden
        context['items_solicitados'] = ItemSolicitado.objects.filter(orden=self.get_object())

        # Formset de ítems solicitados para editar en el template
        if self.request.POST:
            context['items_formset'] = ItemSolicitadoFormSet(self.request.POST, instance=self.object)
        else:
            context['items_formset'] = ItemSolicitadoFormSet(instance=self.object)

        # Asegurar que los autos y clientes están disponibles para el select
        context['auto'] = Auto.objects.all()
        context['clientes'] = Cliente.objects.all()


        return context

    def get_success_url(self):
        # Redirecciona a la vista de detalle de la orden editada
        return reverse_lazy('editar-orden', kwargs={'pk': self.object.pk})


class EliminarOrden(LoginRequiredMixin, DeleteView):
    model = Orden
    template_name = 'orden/orden_confirm_delete.html'
    context_object_name = 'orden'
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['orden'] = self.get_object()


        return context

@csrf_exempt
def cambiar_estado(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        orden_id = data.get('orden_id')
        nuevo_estado = data.get('nuevo_estado')

        try:
            orden = Orden.objects.get(id=orden_id)
            orden.estado = nuevo_estado
            orden.save()
            return JsonResponse({'success': True})
        except Orden.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Orden no encontrada'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def ordenes_entregadas(request):
    # Obtener parámetros de filtro
    auto_id = request.GET.get('auto')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    cliente_id = request.GET.get('cliente')

    # Filtrar las órdenes con el estado 'entregado'
    ordenes = Orden.objects.filter(estado='entregado')

    # Aplicar filtros si se proporcionan
    if auto_id:
        ordenes = ordenes.filter(auto_id=auto_id)
    if fecha_inicio:
        fecha_inicio = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        ordenes = ordenes.filter(fecha_creacion__gte=fecha_inicio)
    if fecha_fin:
        fecha_fin = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        ordenes = ordenes.filter(fecha_creacion__lte=fecha_fin)
    if cliente_id:
        ordenes = ordenes.filter(auto__cliente_id=cliente_id)

    autos = Auto.objects.all()
    clientes = Cliente.objects.all()

    context = {
        'ordenes': ordenes,
        'autos': autos,
        'clientes': clientes,
    }
    return render(request, 'orden/ordenes_entregadas.html', context)

@login_required
def historial_ordenes_auto(request, auto_id):
    auto = get_object_or_404(Auto, id=auto_id)
    ordenes = Orden.objects.filter(auto=auto)


    # Crear un diccionario para almacenar los ítems solicitados por cada orden
    items_por_orden = {}
    for orden in ordenes:
        items_por_orden[orden.id] = ItemSolicitado.objects.filter(orden=orden)

    context = {
        'auto': auto,
        'ordenes': ordenes,
        'items_por_orden': items_por_orden,

    }
    return render(request, 'orden/historial_ordenes_auto.html', context)

@login_required
def crear_presupuesto(request, orden_id):
    clientes = Cliente.objects.all()
    orden = get_object_or_404(Orden, id=orden_id)


    try:
        if request.method == 'POST':
            form = PresupuestoForm(request.POST)
            if form.is_valid():
                presupuesto = form.save(commit=False)
                presupuesto.orden = orden
                presupuesto.token = generar_token_aprobacion(presupuesto)
                presupuesto.token_rechazo = generar_token_rechazo(presupuesto)
                presupuesto.save()

                # Construir la URL de aprobación utilizando build_absolute_uri
                url_aprobacion = request.build_absolute_uri(
                    reverse('aprobar_presupuesto', kwargs={'presupuesto_id': presupuesto.id, 'token': presupuesto.token}))
                url_rechazo = request.build_absolute_uri(
                    reverse('rechazar_presupuesto', kwargs={'presupuesto_id': presupuesto.id, 'token': presupuesto.token}))

                # Renderizar la plantilla de correo electrónico
                detalle_presupuesto = form.cleaned_data.get('detalle', 'precio')
                context = {'presupuesto': presupuesto, 'detalle_presupuesto': detalle_presupuesto,
                           'url_aprobacion': url_aprobacion,'url_rechazo': url_rechazo}
                html_message = render_to_string('correo/presupuesto_email.html', context)
                plain_message = strip_tags(html_message)

                # Enviar correo electrónico al cliente
                subject = 'Presupuesto para Orden #{}'.format(orden.id)
                from_email = 'rodrydiaz086@gmail.com'  # Reemplaza con tu dirección de correo
                to_email = [orden.auto.cliente.email]

                # Configurar el correo con contenido HTML y de texto plano
                email = EmailMultiAlternatives(subject, plain_message, from_email, to_email)
                email.attach_alternative(html_message, "text/html")

                # Enviar el correo electrónico
                email.send()

                # Cambiar el estado del presupuesto a "enviado"
                presupuesto.estado_presupuesto = 'enviado'
                orden.estado= 'presupuestado'

                orden.save()
                presupuesto.save()

                messages.success(request, 'Presupuesto creado y enviado correctamente al cliente.')

                return redirect('visualizar-orden', pk=orden.id)
        else:
            form = PresupuestoForm()

    except Exception as e:
        # Manejar el error de falta de conexión a internet
        messages.error(request, 'Error de conexión a internet. Por favor, revisa tu conexión e intenta nuevamente.')
        return redirect('index')

    context = {'form': form,
               'orden': orden,
               'clientes': clientes,

               }
    return render(request, 'presupuesto/crear_presupuesto.html', context)




class EditarPresupuesto(LoginRequiredMixin, UpdateView):
    model = Presupuesto
    form_class = PresupuestoForm
    template_name = 'presupuesto/crear_presupuesto.html'

    def get_success_url(self):
        # Use kwargs for keyword arguments
        return reverse_lazy('crear-presupuesto', kwargs={'orden_id': self.object.orden.id})


logger = logging.getLogger(__name__)


@login_required
def visualizar_presupuesto(request, presupuesto_id):
    # Obtener el presupuesto o devolver un error 404 si no existe
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)
    user = request.user  # Acceder al usuario desde el objeto request

    # Pasar el presupuesto al contexto para su visualización
    context = {
        'presupuesto': presupuesto,
        'user_role': user.get_role  # Eliminar los paréntesis si get_role es un atributo o una propiedad
    }
    return render(request, 'presupuesto/visualizar_presupuesto.html', context)

@login_required
def listar_presupuestos(request):

    estado = request.GET.get('estado', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')

    presupuestos = Presupuesto.objects.all()

    if estado:
        presupuestos = presupuestos.filter(estado_presupuesto=estado)

    if fecha_inicio:
        fecha_inicio = parse_date(fecha_inicio)
        presupuestos = presupuestos.filter(orden__fecha_creacion__gte=fecha_inicio)

    if fecha_fin:
        fecha_fin = parse_date(fecha_fin)
        presupuestos = presupuestos.filter(orden__fecha_creacion__lte=fecha_fin)

    context = {
        'presupuestos': presupuestos,

    }
    return render(request, 'presupuesto/listar_presupuestos.html', context)

def contact(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            template = render_to_string('correo/email_template.html', {
                'name': name,
                'email': email,
                'message': message,
            })

            email = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ['rodrydiaz086@gmail.com']
            )

            email.fail_silently = False
            email.send()

            messages.success(request, 'Correo enviado correctamente')

            print(email)
            return redirect('crear-presupuesto')

        except smtplib.SMTPException as e:
            logger.error(f"Error al enviar el correo electrónico: {e}")
            messages.error(request, 'Error al enviar el correo electrónico. Por favor, inténtelo de nuevo más tarde.')
            return redirect('crear-presupuesto')


@csrf_exempt
def aprobar_presupuesto(request, presupuesto_id, token):
    print("Entrando a la vista de aprobar_presupuesto")  # Agrega esta línea
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)

    # Obtén el token almacenado en el objeto Presupuesto
    token_existente = presupuesto.token

    if token_existente == token:
        print("Token válido. Aprobando presupuesto.")  # Agrega esta línea
        presupuesto.aprobado = True
        presupuesto.estado_presupuesto = 'aprobado'
        presupuesto.save()
        messages.success(request, 'Presupuesto aprobado exitosamente.')

        print("URL de Redirección:", reverse('aprobacion_exitosa', kwargs={'presupuesto_id': presupuesto.id}))

        # Usa HttpResponseRedirect para redirigir a la URL relativa
        return HttpResponseRedirect(reverse('aprobacion_exitosa', kwargs={'presupuesto_id': presupuesto.id}))
    else:
        print("Token inválido. Error al aprobar el presupuesto.")  # Agrega esta línea
        messages.error(request, 'Error al aprobar el presupuesto. El enlace es inválido.')

    # Redirige a la URL relativa sin construir una URL absoluta
    return redirect('aprobacion_exitosa', presupuesto_id=presupuesto.id)


@csrf_exempt
def rechazar_presupuesto(request, presupuesto_id, token):
    print("Entrando a la vista de rechazo_presupuesto")  # Agrega esta línea
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)

    # Obtén el token almacenado en el objeto Presupuesto
    token_existente = presupuesto.token

    if token_existente == token:
        print("Token válido. Aprobando presupuesto.")  # Agrega esta línea
        presupuesto.aprobado = False
        presupuesto.estado_presupuesto = 'rechazado'
        presupuesto.save()
        messages.success(request, 'Presupuesto rechazado exitosamente.')

        print("URL de Redirección:", reverse('rechazo_exitoso', kwargs={'presupuesto_id': presupuesto.id}))

        # Usa HttpResponseRedirect para redirigir a la URL relativa
        return HttpResponseRedirect(reverse('rechazo_exitoso', kwargs={'presupuesto_id': presupuesto.id}))
    else:
        print("Token inválido. Error al rechazar el presupuesto.")  # Agrega esta línea
        messages.error(request, 'Error al rechazar el presupuesto. El enlace es inválido.')

    # Redirige a la URL relativa sin construir una URL absoluta
    return redirect('rechazo_exitoso', presupuesto_id=presupuesto.id)


def generar_token_aprobacion(presupuesto):
    token = hashlib.sha256(f"{presupuesto.id}-{presupuesto.orden.id}".encode()).hexdigest()
    print("Token generado:", token)
    return token

def generar_token_rechazo(presupuesto):
    token = hashlib.sha256(f"{presupuesto.id}-{presupuesto.orden.id}".encode()).hexdigest()
    print("Token generado:", token)
    return token



class AprobacionExitosaView(TemplateView):
    template_name = 'presupuesto/aprobacion_exitosa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, id=kwargs['presupuesto_id'])
        context['presupuesto'] = presupuesto
        return context


class RechazoExitosoView(TemplateView):
    template_name = 'presupuesto/rechazo_exitoso.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        presupuesto = get_object_or_404(Presupuesto, id=kwargs['presupuesto_id'])
        context['presupuesto'] = presupuesto
        return context




@login_required
def planificacion(request):
    start_time = datetime.strptime("08:30", "%H:%M")
    end_time = datetime.strptime("17:30", "%H:%M")
    step = timedelta(minutes=30)
    hours = [(start_time + i * step).strftime("%H:%M") for i in range(int((end_time - start_time) / step))]
    user = request.user

    # Excluir órdenes con estado 'entregado'
    ordenes = Orden.objects.exclude(estado='entregado')

    context = {
        'hours': hours,
        'ordenes': ordenes,
        'ordenes_asignadas': ordenes.exclude(tecnico__isnull=True),
        'tecnicos': Tecnico.objects.all(),
        'user_role': user.get_role,
    }

    return render(request, 'planificacion/planificacion.html', context)


from django.db import transaction


def verificar_disponibilidad(tecnico_id, hour_str):
    hour = datetime.strptime(hour_str, '%H:%M').time()

    # Obtener la fecha actual para la verificación
    today = datetime.now().date()

    # Buscar órdenes que se solapan en la misma hora para el técnico
    conflicting_orders = Orden.objects.filter(
        tecnico_id=tecnico_id,
        fecha_inicio__lte=today,
        fecha_finalizacion__gte=today,
        hora_asignada=hour
    )

    # Si hay órdenes conflictivas, no está disponible
    if conflicting_orders.exists():
        return False

    return True

@csrf_exempt
def asignar_tecnico(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            validar_datos_entrada(data)

            orden_id = data['ordenId']
            tecnico_id = data.get('tecnicoId')
            hour_str = data.get('hour')

            orden = Orden.objects.get(id=orden_id)

            if tecnico_id is None:  # Si no se asigna un técnico, cambia el estado a "pendiente"
                orden.tecnico = None
                orden.hora_asignada = None
                orden.estado = 'pendiente'
                orden.save()
                return JsonResponse({'success': True, 'ordenId': orden.id, 'estado': 'pendiente'})
            else:
                # Verifica si la asignación es válida
                if not verificar_disponibilidad(tecnico_id, hour_str):
                    return JsonResponse({'error': 'El técnico no está disponible en la hora seleccionada'}, status=400)

                # Asignar técnico y hora
                asignar_tecnico_y_hora(orden, tecnico_id, hour_str)

                return JsonResponse({
                    'success': True,
                    'ordenId': orden.id,
                    'horaAsignada': hour_str,
                })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def validar_datos_entrada(data):
    required_fields = ['ordenId', 'tecnicoId', 'hour']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f'Datos de entrada incompletos. Falta el campo {field}.')


def obtener_y_validar_orden(orden_id, tecnico_id, hour_str):
    orden = Orden.objects.get(id=orden_id)
    if orden.tecnico and orden.tecnico.id != int(tecnico_id):
        verificar_conflictos(orden.hora_asignada, tecnico_id, orden_id)
    return orden


def asignar_tecnico_y_hora(orden, tecnico_id, hour_str):
    hour = datetime.strptime(hour_str, '%H:%M').time()
    orden.tecnico = Tecnico.objects.get(id=tecnico_id)
    orden.hora_asignada = hour
    orden.estado = 'asignado'  # Cambiar el estado a "asignado"
    orden.save()
    return orden


def verificar_conflictos(hour_str, tecnico_id, orden_id):
    existing_orders = Orden.objects.filter(hora_asignada=hour_str).exclude(id=orden_id)
    if existing_orders.exists():
        for order in existing_orders:
            if order.tecnico_id != tecnico_id:
                return
        raise ValidationError('Conflicto detectado al asignar la orden a la misma hora con el mismo técnico.')


@csrf_exempt
def get_planificacion_data(request):
    if request.method == 'GET':
        try:
            ordenes = Orden.objects.all().values('id', 'tecnico_id', 'hora_asignada')
            data = {
                'ordenes': list(ordenes),
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def manejar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        try:
            if accion == 'iniciar':
                orden.iniciar_temporizador()
                orden.estado = 'en progreso'  # Actualiza el estado a "en progreso"
            elif accion == 'pausar':
                orden.pausar_temporizador()
                orden.estado = 'pausado'  # Actualiza el estado a "pausa"
            elif accion == 'detener':
                orden.detener_temporizador()
                orden.estado = 'frenado'  # Actualiza el estado a "frenado"
            elif accion == 'finalizar':
                orden.finalizar_orden()
                orden.estado = 'finalizado'  # Actualiza el estado a "finalizado"

            orden.save()  # Guarda la orden con el nuevo estado

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    context = {
        'orden': orden,
    }
    return render(request, 'orden/orden.html', context)

def finalizar_orden(self):
    if not self.timer_running:
        self.estado = 'finalizado'
        self.save()
        print(f'Orden finalizada. Estado cambiado a {self.estado}')

def obtener_tiempo_total(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    tiempo_total_str = str(orden.tiempo_total) if orden.tiempo_total else '0:00:00'
    return JsonResponse({
        'success': True,
        'tiempo_total': tiempo_total_str
    })

def get_tiempo_total(request, orden_id):
    try:
        orden = Orden.objects.get(id=orden_id)
        tiempo_total = orden.tiempo_total  # Asegúrate de que este campo está actualizado
        return JsonResponse({'success': True, 'tiempo_total': tiempo_total})
    except Orden.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Orden no encontrada'})

def get_estado_orden(request, orden_id):
    try:
        orden = Orden.objects.get(id=orden_id)
        estado = orden.estado  # Asumiendo que tienes un campo llamado 'estado'
        return JsonResponse({'success': True, 'estado': estado})
    except Orden.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Orden no encontrada'})


def horas_vendidas(request):
    año = timezone.now().year
    mes = timezone.now().month

    # Obtén el registro correspondiente al año y mes actuales
    horas_vendidas_mes = HorasVendidasPorMes.objects.filter(año=año, mes=mes).first()
    total_horas = horas_vendidas_mes.horas_totales if horas_vendidas_mes else 0

    return JsonResponse({'total_horas': total_horas})


def actualizar_acumulado_horas():
    hoy = timezone.now().date()

    # Obtenemos las horas de mano de obra de las órdenes finalizadas
    horas_ordenes = Orden.objects.filter(
        estado__in=['finalizado', 'entregado'],
        fecha_finalizacion__year=hoy.year,
        fecha_finalizacion__month=hoy.month
    ).aggregate(Sum('mano_de_obra'))['mano_de_obra__sum'] or Decimal('0.0')  # Convertimos a Decimal

    # Obtenemos las horas de mano de obra de los presupuestos aprobados
    horas_presupuestos = Presupuesto.objects.filter(
        estado_presupuesto='aprobado',
        fecha_creacion__year=hoy.year,
        fecha_creacion__month=hoy.month
    ).aggregate(Sum('mano_de_obra_presupuesto'))['mano_de_obra_presupuesto__sum'] or Decimal(
        '0.0')  # Convertimos a Decimal

    # Calculamos el total de horas (asegurando que todos los valores sean Decimal)
    horas_este_mes = horas_ordenes + horas_presupuestos

    logger.debug(f"Horas calculadas este mes (órdenes + presupuestos): {horas_este_mes}")

    # Actualizamos o creamos el registro de HorasVendidasPorMes
    obj, created = HorasVendidasPorMes.objects.update_or_create(
        año=hoy.year,
        mes=hoy.month,
        defaults={'horas_totales': horas_este_mes}
    )

    logger.debug(f"Registro de HorasVendidasPorMes actualizado: {obj.horas_totales}")

    return obj.horas_totales



def obtener_horas_acumuladas_mes_anterior():
    hoy = timezone.now().date()
    primer_dia_del_mes_anterior = (hoy.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)

    horas_mes_anterior = HorasVendidasPorMes.objects.filter(
        año=primer_dia_del_mes_anterior.year,
        mes=primer_dia_del_mes_anterior.month
    ).first()

    total_horas_mes_anterior = horas_mes_anterior.horas_totales if horas_mes_anterior else 0
    return total_horas_mes_anterior




def metricas(request):
    # Obtener el mes y año seleccionados del formulario (o usar el mes y año actuales como predeterminado)
    mes = int(request.GET.get('mes', timezone.now().month))
    año = int(request.GET.get('año', timezone.now().year))

    # Obtener las horas acumuladas del mes actual
    hoy = timezone.now().date()
    primer_dia_del_mes_actual = hoy.replace(day=1)
    horas_acumuladas_mes_actual = HorasVendidasPorMes.objects.filter(
        año=primer_dia_del_mes_actual.year,
        mes=primer_dia_del_mes_actual.month
    ).first()

    horas_acumuladas_mes_actual_total = horas_acumuladas_mes_actual.horas_totales if horas_acumuladas_mes_actual else 0

    # Obtener el objetivo mensual del mes actual
    objetivo_mensual = horas_acumuladas_mes_actual.objetivo_mensual if horas_acumuladas_mes_actual else 0

    # Calcular el porcentaje alcanzado y el porcentaje restante
    porcentaje_alcanzado, porcentaje_restante = calcular_porcentaje_restante(objetivo_mensual, horas_acumuladas_mes_actual_total)

    # Obtener las horas acumuladas del mes anterior
    horas_acumuladas_mes_anterior = obtener_horas_acumuladas_mes_anterior()

    # Obtener las horas acumuladas del mes y año seleccionados
    horas_acumuladas = HorasVendidasPorMes.objects.filter(año=año, mes=mes).first()

    # Obtener la cantidad de órdenes finalizadas del mes actual
    cantidad_ordenes_finalizadas_mes = cantidad_ordenes_finalizadas_mes_actual(mes=mes, año=año)

    # Obtener la cantidad de órdenes frenadas del mes actual
    cantidad_ordenes_frenadas = cantidad_ordenes_frenadas_mes_actual(mes=mes, año=año)

    # Obtener la cantidad de presupuestos rechazados del mes seleccionado
    cantidad_presupuestos_rechazados_mes = cantidad_presupuestos_rechazados(mes=mes, año=año)

    # Obtener las órdenes finalizadas por técnico
    tecnicos_con_ordenes = obtener_ordenes_terminadas_por_tecnico(mes, año)

    # Obtener el tiempo total acumulado de todas las órdenes en el mes seleccionado
    tiempo_total_acumulado = obtener_tiempo_total_acumulado_mes(mes, año)

    # Convertir tiempo total acumulado a horas con dos decimales
    tiempo_total_acumulado = convertir_timedelta_a_horas(tiempo_total_acumulado)

    # Obtener el tiempo total acumulado de órdenes por técnico en el mes seleccionado
    tecnicos_con_tiempo = obtener_tiempo_total_por_tecnico(mes, año)

    cantidad_ordenes_a_tiempo, cantidad_ordenes_fuera_de_tiempo = obtener_ordenes_a_tiempo_fuera_de_tiempo(mes, año)

    # Obtener las órdenes finalizadas por técnico
    tecnicos_con_ordenes = obtener_ordenes_terminadas_por_tecnico(mes, año)

    # Obtener las órdenes a tiempo y fuera de tiempo por técnico
    tecnicos_con_tiempos = obtener_ordenes_a_tiempo_por_tecnico(mes, año)

    # Combina los datos y calcula porcentajes
    for tecnico in tecnicos_con_ordenes:
        tecnico_tiempo = next(
            (t for t in tecnicos_con_tiempos if t['tecnico__user__username'] == tecnico['tecnico__user__username']), {})
        tecnico['cantidad_a_tiempo'] = tecnico_tiempo.get('cantidad_a_tiempo', 0)
        tecnico['cantidad_fuera_de_tiempo'] = tecnico_tiempo.get('cantidad_fuera_de_tiempo', 0)

        # Calcula el porcentaje de órdenes completadas
        total_ordenes_tecnico = tecnico['total_ordenes']
        tecnico['porcentaje_completado'] = (
            (total_ordenes_tecnico / cantidad_ordenes_finalizadas_mes) * 100
            if cantidad_ordenes_finalizadas_mes > 0
            else 0
        )

        # Calcula el porcentaje de órdenes a tiempo y fuera de tiempo
        tecnico['porcentaje_a_tiempo'] = (
            (tecnico['cantidad_a_tiempo'] / total_ordenes_tecnico) * 100
            if total_ordenes_tecnico > 0
            else 0
        )
        tecnico['porcentaje_fuera_de_tiempo'] = (
            (tecnico['cantidad_fuera_de_tiempo'] / total_ordenes_tecnico) * 100
            if total_ordenes_tecnico > 0
            else 0
        )

    context = {
        'horas_acumuladas': horas_acumuladas.horas_totales if horas_acumuladas else 0,
        'horas_acumuladas_mes_actual': horas_acumuladas_mes_actual_total,
        'objetivo_mensual': objetivo_mensual,
        'porcentaje_alcanzado': porcentaje_alcanzado,
        'porcentaje_restante': porcentaje_restante,
        'mes': mes,
        'año': año,
        'años': range(2020, timezone.now().year + 1),  # Generar opciones de año (ajusta el rango según tu necesidad)
        'horas_acumuladas_mes_anterior': horas_acumuladas_mes_anterior,
        'cantidad_ordenes_finalizadas_mes': cantidad_ordenes_finalizadas_mes,
        'cantidad_ordenes_frenadas_mes': cantidad_ordenes_frenadas_mes_actual,
        'cantidad_presupuestos_rechazados_mes': cantidad_presupuestos_rechazados_mes,
        'rating_tecnicos': tecnicos_con_ordenes,
        'tiempo_total_acumulado': tiempo_total_acumulado,
        'tiempo_total_por_tecnico': tecnicos_con_tiempo,
        'cantidad_ordenes_a_tiempo': cantidad_ordenes_a_tiempo,
        'cantidad_ordenes_fuera_de_tiempo': cantidad_ordenes_fuera_de_tiempo,
    }

    return render(request, 'metricas/metricas.html', context)



def cantidad_ordenes_finalizadas_mes_actual(mes=None, año=None):
    hoy = timezone.now().date()

    if not mes:
        mes = hoy.month
    if not año:
        año = hoy.year
    # Filtramos las órdenes finalizadas en el mes y año actuales
    cantidad_ordenes_finalizadas = Orden.objects.filter(
        estado__in=['finalizado', 'entregado'],
        fecha_finalizacion__year=año,
        fecha_finalizacion__month=mes
    ).count()

    return cantidad_ordenes_finalizadas

def cantidad_ordenes_frenadas_mes_actual(mes=None, año=None):
    hoy = timezone.now().date()

    if not mes:
        mes = hoy.month
    if not año:
        año = hoy.year
    # Filtramos las órdenes finalizadas en el mes y año actuales
    cantidad_ordenes_frenadas = Orden.objects.filter(
        estado= 'frenado',
        fecha_finalizacion__year=año,
        fecha_finalizacion__month=mes
    ).count()

    return cantidad_ordenes_frenadas


def cantidad_presupuestos_rechazados(mes=None, año=None):
    hoy = timezone.now().date()

    # Usa el mes y año actuales como predeterminados si no se proporcionan
    if not mes:
        mes = hoy.month
    if not año:
        año = hoy.year

    # Filtrar presupuestos rechazados en el mes y año seleccionados
    cantidad_rechazados = Presupuesto.objects.filter(
        estado_presupuesto='rechazado',
        fecha_creacion__year=año,
        fecha_creacion__month=mes
    ).count()

    return cantidad_rechazados


def obtener_ordenes_terminadas_por_tecnico(mes, año):
    # Filtra las órdenes que fueron finalizadas en el mes y año seleccionados
    ordenes_finalizadas = Orden.objects.filter(
        estado__in=['finalizado', 'entregado'],
        fecha_finalizacion__year=año,
        fecha_finalizacion__month=mes
    )

    # Anota la cantidad de órdenes por técnico
    tecnicos_con_ordenes = ordenes_finalizadas.values('tecnico__user__username').annotate(
        total_ordenes=Count('id')
    ).order_by('-total_ordenes')  # Ordena por el total de órdenes de forma descendente

    return tecnicos_con_ordenes


def obtener_tiempo_total_acumulado_mes(mes, año):
    # Calcula el tiempo total acumulado de todas las órdenes finalizadas en el mes y año especificados
    tiempo_total = Orden.objects.filter(
        estado__in=['finalizado', 'entregado'],
        fecha_finalizacion__year=año,
        fecha_finalizacion__month=mes
    ).aggregate(tiempo_acumulado=Sum('tiempo_total'))['tiempo_acumulado'] or timedelta(0)

    return tiempo_total


def obtener_tiempo_total_por_tecnico(mes, año):
    tecnicos_con_tiempo = Orden.objects.filter(
        estado__in=['finalizado', 'entregado'],
        fecha_finalizacion__year=año,
        fecha_finalizacion__month=mes
    ).values('tecnico__user__username').annotate(
        tiempo_acumulado=Sum('tiempo_total')
    ).order_by('-tiempo_acumulado')

    # Convertir timedelta a horas y redondear a 2 decimales
    for tecnico in tecnicos_con_tiempo:
        if tecnico['tiempo_acumulado']:
            tecnico['tiempo_acumulado'] = convertir_timedelta_a_horas(tecnico['tiempo_acumulado'])
        else:
            tecnico['tiempo_acumulado'] = 0

    return tecnicos_con_tiempo

def convertir_timedelta_a_horas(timedelta_obj):
    total_segundos = timedelta_obj.total_seconds()
    horas = total_segundos / 3600  # 3600 segundos en una hora
    return round(horas, 2)


def establecer_objetivo_mensual(request):
    año = request.GET.get('año', timezone.now().year)
    mes = request.GET.get('mes', timezone.now().month)

    try:
        # Obtener la instancia existente si existe
        horas_vendidas = HorasVendidasPorMes.objects.get(año=año, mes=mes)
    except HorasVendidasPorMes.DoesNotExist:
        # Crear una nueva instancia si no existe
        horas_vendidas = HorasVendidasPorMes(año=año, mes=mes)

    if request.method == 'POST':
        form = ObjetivoMensualForm(request.POST, instance=horas_vendidas)
        if form.is_valid():
            form.save()
            messages.success(request, f"Objetivo mensual para {mes}/{año} actualizado a {form.cleaned_data['objetivo_mensual']} horas.")
            return redirect('metricas')  # Cambia a la URL o nombre de ruta correspondiente
    else:
        form = ObjetivoMensualForm(instance=horas_vendidas)

    return render(request, 'metricas/establecer_objetivo.html', {'form': form, 'año': año, 'mes': mes})



def calcular_porcentaje_restante(objetivo_mensual, horas_acumuladas_mes_actual):
    """
    Calcula el porcentaje de avance en relación al objetivo mensual.
    Retorna el porcentaje alcanzado y el porcentaje restante.
    """
    if objetivo_mensual > 0:
        porcentaje_alcanzado = (horas_acumuladas_mes_actual / objetivo_mensual) * 100
        porcentaje_restante = max(0, 100 - porcentaje_alcanzado)
    else:
        porcentaje_alcanzado = 0
        porcentaje_restante = 100

    return porcentaje_alcanzado, porcentaje_restante

def obtener_ordenes_a_tiempo_fuera_de_tiempo(mes, año):
    # Obtener el primer y último día del mes seleccionado con timezone aware
    primer_dia_del_mes = timezone.make_aware(timezone.datetime(año, mes, 1))
    ultimo_dia_del_mes = (primer_dia_del_mes + relativedelta(months=1)) - timedelta(days=1)

    # Calcular la cantidad de órdenes entregadas a tiempo
    cantidad_a_tiempo = Orden.objects.filter(
        entrega__range=(primer_dia_del_mes, ultimo_dia_del_mes),
        fecha_finalizacion__isnull=False,
        fecha_finalizacion__lte=F('entrega')
    ).count()

    # Calcular la cantidad de órdenes entregadas fuera de tiempo
    cantidad_fuera_de_tiempo = Orden.objects.filter(
        entrega__range=(primer_dia_del_mes, ultimo_dia_del_mes),
        fecha_finalizacion__isnull=False,
        fecha_finalizacion__gt=F('entrega')
    ).count()

    return cantidad_a_tiempo, cantidad_fuera_de_tiempo


def obtener_ordenes_a_tiempo_por_tecnico(mes, año):
    tecnicos = Orden.objects.filter(
        estado__in=['finalizado', 'entregado'],
        fecha_finalizacion__year=año,
        fecha_finalizacion__month=mes
    ).values('tecnico__user__username').annotate(
        cantidad_a_tiempo=Count('id', filter=Q(fecha_finalizacion__lte=F('entrega'))),
        cantidad_fuera_de_tiempo=Count('id', filter=Q(fecha_finalizacion__gt=F('entrega')))
    ).order_by('tecnico__user__username')


    return tecnicos
