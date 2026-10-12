from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from appOne.models import Prestamo
from .utils import es_administrador


@login_required
def calendario_reservas(request):
    return render(request, 'appOne/calendario.html')


@login_required
def api_reservas_eventos(request):
    """Cada préstamo aparece el día de uso solicitado, no el día de creación."""
    admin = es_administrador(request.user)
    prestamos = Prestamo.objects.select_related('dispositivo', 'usuario')
    if not admin:
        prestamos = prestamos.filter(usuario=request.user)

    colores = {
        'pendiente': '#ed8b16',
        'aprobado': '#15945a',
        'rechazado': '#dc3545',
        'devuelto': '#667085',
    }
    eventos = []
    for p in prestamos.order_by('fecha_uso', 'hora_inicio', 'id'):
        if not p.fecha_uso:
            continue
        inicio = datetime.combine(p.fecha_uso, p.hora_inicio)
        fin = datetime.combine(p.fecha_uso, p.hora_entrega)
        nombre = p.usuario.nombre_completo or p.usuario.username
        props = {
            'estado': p.get_estado_display(),
            'estado_codigo': p.estado,
            'dispositivo': p.dispositivo.nombre_dispositivo,
            'codigo_inventario': p.dispositivo.codigo_inventario,
            'marca': p.dispositivo.marca,
            'fecha_uso': p.fecha_uso.strftime('%d/%m/%Y'),
            'hora_inicio': p.hora_inicio.strftime('%H:%M'),
            'hora_entrega': p.hora_entrega.strftime('%H:%M'),
            'motivo': p.motivo,
            'fecha_solicitud': timezone.localtime(p.fecha_solicitud).strftime('%d/%m/%Y %H:%M') if p.fecha_solicitud else '',
            'fecha_devolucion_real': timezone.localtime(p.fecha_devolucion_real).strftime('%d/%m/%Y %H:%M') if p.fecha_devolucion_real else '',
            'observaciones_devolucion': p.observaciones_devolucion or '',
        }
        if admin:
            props['usuario'] = nombre
            props['correo'] = p.usuario.correo_institucional
            props['codigo_usuario'] = p.usuario.codigo
        else:
            props['usuario'] = 'Mi solicitud'

        eventos.append({
            'id': p.pk,
            'title': f"{p.dispositivo.nombre_dispositivo} · {p.get_estado_display()}",
            'start': inicio.isoformat(),
            'end': fin.isoformat(),
            'backgroundColor': colores.get(p.estado, '#1874c8'),
            'borderColor': colores.get(p.estado, '#1874c8'),
            'extendedProps': props,
        })
    return JsonResponse(eventos, safe=False)
