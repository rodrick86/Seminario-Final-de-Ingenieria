from django.contrib import admin
from .models import Presupuesto, Cliente, Orden, Tecnico, ItemSolicitado, Auto, Recepcionista, \
    Planificador, HorasVendidasPorMes

admin.site.register(Orden, )
admin.site.register(Presupuesto, )
admin.site.register(Cliente, )

# usuarios
admin.site.register(Recepcionista, )
admin.site.register(Planificador, )
admin.site.register(Tecnico, )

admin.site.register(HorasVendidasPorMes,)
admin.site.register(ItemSolicitado, )
admin.site.register(Auto, )
