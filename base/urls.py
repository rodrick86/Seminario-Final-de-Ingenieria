from django.contrib.auth.views import PasswordChangeDoneView, PasswordResetDoneView, PasswordResetCompleteView, \
    LogoutView
from django.urls import path
from . import views
from .views import UserRegistrationView, UserLoginView, UserPasswordChangeView, UserPasswordResetView, \
    UserPasswrodResetConfirmView, ClienteListView, ClienteCreateView, ClienteUpdateView, \
    ClienteDeleteView, CrearOrden, DetalleOrden, EditarOrden, EliminarOrden, \
    contact, EditarPresupuesto, AprobacionExitosaView, RechazoExitosoView, planificacion, \
    asignar_tecnico, get_planificacion_data, manejar_orden, obtener_tiempo_total, actualizar_item, obtener_estado_orden, \
    get_estado_orden, CrearAuto, load_auto, dashboard_tecnico, metricas, UserLogoutView, EditarAuto, \
    obtener_ordenes_del_dia, horas_vendidas, establecer_objetivo_mensual, visualizar_presupuesto, cambiar_estado, \
    ordenes_entregadas

urlpatterns = [
    path('', views.index, name='index'),


    path('accounts/register/', UserRegistrationView.as_view(), name='register'),
    path('accounts/login/', UserLoginView.as_view(), name='login'),
    path('accounts/logout/', UserLogoutView.as_view(), name='logout'),

    path('accounts/password-change/', UserPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change-done/', PasswordChangeDoneView.as_view(
        template_name='accounts/auth-password-change-done.html'
    ), name="password_change_done"),

    path('accounts/password-reset/', UserPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
         UserPasswrodResetConfirmView.as_view(), name="password_reset_confirm"
         ),
    path('accounts/password-reset-done/', PasswordResetDoneView.as_view(
        template_name='accounts/auth-password-reset-done.html'
    ), name='password_reset_done'),
    path('accounts/password-reset-complete/', PasswordResetCompleteView.as_view(
        template_name='accounts/auth-password-reset-complete.html'
    ), name='password_reset_complete'),

    path('clientes', ClienteListView.as_view(), name='lista_clientes'),
    path('clientes/crear', ClienteCreateView.as_view(), name='crear_cliente'),
    path('clientes/editar/<int:pk>/', ClienteUpdateView.as_view(), name='editar_cliente'),
    path('clientes/eliminar/<int:pk>/', ClienteDeleteView.as_view(), name='eliminar_cliente'),
    path('load-clientes/', views.load_clientes, name='load-clientes'),


    path('dashboard/', dashboard_tecnico, name='dashboard_tecnico'),

    path('orden/<int:pk>', DetalleOrden.as_view(), name='orden'),
    path('crear-orden/', CrearOrden.as_view(), name='crear-orden'),
    path('editar-orden/<int:pk>', EditarOrden.as_view(), name='editar-orden'),
    path('eliminar-orden/<int:pk>', EliminarOrden.as_view(), name='eliminar-orden'),
    path('auto/<int:auto_id>/historial/', views.historial_ordenes_auto, name='historial_ordenes_auto'),
    path('save_intervencion/', DetalleOrden.as_view(), name='save_intervencion'),
    path('delete_intervencion/', DetalleOrden.as_view(), name='delete_intervencion'),
    path('cambiar_estado/', cambiar_estado, name='cambiar_estado'),
    path('ordenes_entregadas/', ordenes_entregadas, name='ordenes_entregadas'),

    path('crear_presupuesto/<int:orden_id>/', views.crear_presupuesto, name='crear-presupuesto'),
    path('editar-presupuesto/<int:pk>', EditarPresupuesto.as_view(), name='editar-presupuesto'),
    path('presupuestos/', views.listar_presupuestos, name='listar_presupuestos'),
    path('presupuesto/<int:presupuesto_id>/', visualizar_presupuesto, name='visualizar_presupuesto'),

    path('contact', contact, name='contact'),

    path('aprobar-presupuesto/<int:presupuesto_id>/<str:token>/', views.aprobar_presupuesto, name='aprobar_presupuesto'),

    path('rechazar-presupuesto/<int:presupuesto_id>/<str:token>/', views.rechazar_presupuesto, name='rechazar_presupuesto'),
    path('aprobacion-exitosa/<int:presupuesto_id>/', AprobacionExitosaView.as_view(), name='aprobacion_exitosa'),
    path('rechazo-exitoso/<int:presupuesto_id>/', RechazoExitosoView.as_view(), name='rechazo_exitoso'),

    path('planificacion/', planificacion, name='planificacion'),
    path('asignar_tecnico/', views.asignar_tecnico, name='asignar_tecnico'),
    path('buscar-tecnico/', views.buscar_tecnico, name='buscar_tecnico'),
    path('get_planificacion_data/', get_planificacion_data, name='get_planificacion_data'),
    path('orden/<int:orden_id>/', manejar_orden, name='manejar_orden'),
    path('orden/<int:orden_id>/tiempo-total/', obtener_tiempo_total, name='get_tiempo_total'),
    path('get_estado_orden/<int:orden_id>/', get_estado_orden, name='get_estado_orden'),
    path('actualizar_item/', actualizar_item, name='actualizar_item'),
    path('obtener_estado_orden/<int:orden_id>/', obtener_estado_orden, name='obtener_estado_orden'),

    path('crear_auto/', CrearAuto.as_view(), name='crear_auto'),
    path('auto/editar/<int:pk>/', EditarAuto.as_view(), name='editar_auto'),

    path('load-auto/', load_auto, name='load-auto'),

    path('metricas/', metricas, name='metricas'),
    path('ordenes-del-dia/', obtener_ordenes_del_dia, name='ordenes_del_dia'),
    path('horas-vendidas/', horas_vendidas, name='horas_vendidas'),
    path('establecer_objetivo_mensual/', establecer_objetivo_mensual, name='establecer_objetivo'),






]









