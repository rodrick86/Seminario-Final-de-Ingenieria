from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db import models, transaction
from django.contrib.auth.models import User
from datetime import timedelta

from django.db.models import Sum
from django.forms import forms, inlineformset_factory
from django.utils import timezone
from .choices import MODELO_VEHICULO, ESTADO_ORDEN, ESTADO_PRESUPUESTO


class Tecnico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Otros campos específicos para técnicos

    def __str__(self):
        return f'Técnico: {self.user.username}'

class Recepcionista(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Otros campos específicos para recepcionistas

    def __str__(self):
        return f'Recepcionista: {self.user.username}'

class Planificador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Otros campos específicos para planificadores

    def __str__(self):
        return f'Planificador: {self.user.username}'

def get_user_role(user):
    if hasattr(user, 'tecnico'):
        return 'tecnico'
    elif hasattr(user, 'recepcionista'):
        return 'recepcionista'
    elif hasattr(user, 'planificador'):
        return 'planificador'
    return 'ninguno'

User.get_role = property(get_user_role)


class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                null=True,
                                blank=True)
    nombre = models.CharField(max_length=15)
    apellido = models.CharField(max_length=15)
    dni = models.CharField(max_length=15, unique=True)
    telefono = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=30, unique=True)
    direccion = models.CharField(max_length=15)

    vehiculo = models.CharField(choices=MODELO_VEHICULO, null=False, blank=False, max_length=20, default='seleccione '
                                                                                                         'un modelo')
    provincia = models.CharField(max_length=15, null=True, blank=True)
    localidad = models.CharField(max_length=15, null=True, blank=True)


    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f'{self.nombre} - {self.apellido}'



class Auto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='autos')
    matricula = models.CharField(max_length=15, unique=True)  # Asegurarse de que la matrícula sea única
    vehiculo = models.CharField(choices=MODELO_VEHICULO, max_length=20, default='seleccione un modelo')
    chasis = models.CharField(max_length=16, unique=True)
    anio = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Auto'
        verbose_name_plural = 'Autos'

    def __str__(self):
        return f'{self.matricula}'







class Orden(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    id = models.AutoField(primary_key=True)
    intervencion = models.TextField(blank=True, null=True)

    modifacado = models.DateTimeField(auto_now=True)
    entrega = models.DateTimeField(auto_now_add=False, default=None, null=True, blank=True)
    mano_de_obra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(choices=ESTADO_ORDEN, null=False, blank=False, max_length=20, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)

    km = models.IntegerField(null=True, blank=True)

    tecnico = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True)
    hora_asignada = models.TimeField(null=True, blank=True)

    hora_inicio = models.DateTimeField(null=True, blank=True)
    hora_final = models.DateTimeField(null=True, blank=True)
    tiempo_total = models.DurationField(null=True, blank=True, default=timedelta)
    timer_running = models.BooleanField(default=False)
    progreso = models.FloatField(default=0)
    auto = models.ForeignKey(Auto, on_delete=models.CASCADE, null=True, blank=True)  # Cambio aquí


    def iniciar_temporizador(self):
        if not self.timer_running:
            self.hora_inicio = timezone.now()
            self.estado = 'en proceso'
            self.timer_running = True
            self.save()
            print(f'Temporizador iniciado en {self.hora_inicio}')

    def pausar_temporizador(self):
        if self.timer_running:
            tiempo_transcurrido = timezone.now() - self.hora_inicio
            self.tiempo_total += tiempo_transcurrido
            self.timer_running = False
            self.save()

    def detener_temporizador(self):
        if self.timer_running:
            tiempo_transcurrido = timezone.now() - self.hora_inicio
            self.tiempo_total += tiempo_transcurrido
            self.hora_final = timezone.now()
            self.timer_running = False
            self.estado = 'detenido'
            self.save()

    def finalizar_orden(self):
        if not self.timer_running:
            self.estado = 'finalizado'
            self.fecha_finalizacion = timezone.now()  # Establecer la fecha de finalización
            self.save()
            print(f'Orden finalizada. Estado cambiado a {self.estado}')

            # Actualizar horas vendidas por mes
            if self.mano_de_obra:
                año = self.fecha_finalizacion.year  # Utilizar la fecha de finalización
                mes = self.fecha_finalizacion.month
                with transaction.atomic():
                    horas_registradas, created = HorasVendidasPorMes.objects.get_or_create(año=año, mes=mes)
                    horas_registradas.horas_totales += self.mano_de_obra
                    horas_registradas.save()
                    print(f'Horas vendidas actualizadas: {horas_registradas.horas_totales}')




    def get_tecnico_photo_url(self):
        if self.tecnico and self.tecnico.user and self.tecnico.user.profile.photo:
            return self.tecnico.user.profile.photo.url
        return None

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Ordenes'

    def __str__(self):
        return f'{self.auto}'


class ItemSolicitado(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='items')
    realizado = models.BooleanField(default=False)
    descripcion = models.CharField(max_length=255)




class Presupuesto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                null=True,
                                blank=True)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, null=True, blank=True)

    id = models.AutoField(primary_key=True)
    detalle = models.TextField(null=True, )
    precio = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    estado_presupuesto = models.CharField(choices=ESTADO_PRESUPUESTO, null=False, blank=False, max_length=20,
                                          default='pendiente de envio')
    repuestos = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    token_rechazo = models.CharField(max_length=255, blank=True, null=True)
    mano_de_obra_presupuesto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)



    def __str__(self):
        return f'{self.orden}'


class HorasVendidasPorMes(models.Model):
    año = models.IntegerField()
    mes = models.IntegerField()
    horas_totales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    objetivo_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('año', 'mes')
        verbose_name = 'Horas Vendidas por Mes'
        verbose_name_plural = 'Horas Vendidas por Mes'

    def __str__(self):
        return  f"{self.mes}/{self.año} - {self.horas_totales} horas"
