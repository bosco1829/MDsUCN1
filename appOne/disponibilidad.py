"""Reglas compartidas de ocupación de equipos entre préstamos y actividades."""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from appOne.models import Actividad, Prestamo

ESTADOS_ACTIVIDAD_RESERVAN = ('planificada', 'en_curso')
ESTADOS_PRESTAMO_RESERVAN = ('pendiente', 'aprobado')


def actividades_en_rango(dispositivo_ids, inicio, fin, excluir_actividad=None):
    """Actividades no canceladas que se solapan con el intervalo [inicio, fin)."""
    qs = Actividad.objects.filter(
        equipos__id__in=dispositivo_ids,
        estado__in=ESTADOS_ACTIVIDAD_RESERVAN,
        inicio__lt=fin, fin__gt=inicio
    ).distinct()
    if excluir_actividad:
        qs = qs.exclude(pk=excluir_actividad)
    return qs


def prestamos_en_rango(dispositivo_ids, inicio, fin):
    """Préstamos pendientes o aprobados solapados, incluso en días adyacentes."""
    zona = timezone.get_current_timezone()
    fecha = timezone.localtime(inicio, zona).date()
    ultima = timezone.localtime(fin - timedelta(microseconds=1), zona).date()
    condiciones = Q(pk__in=[])
    while fecha <= ultima:
        dia_inicio = timezone.make_aware(datetime.combine(fecha, datetime.min.time()), zona)
        dia_fin = dia_inicio + timedelta(days=1)
        limite_inicio = max(inicio, dia_inicio)
        limite_fin = min(fin, dia_fin)
        condiciones |= Q(
            fecha_uso=fecha,
            hora_inicio__lt=timezone.localtime(limite_fin, zona).time() if limite_fin < dia_fin else datetime.max.time(),
            hora_entrega__gt=timezone.localtime(limite_inicio, zona).time() if limite_inicio > dia_inicio else datetime.min.time(),
        )
        fecha += timedelta(days=1)
    return Prestamo.objects.filter(
        condiciones, dispositivo_id__in=dispositivo_ids,
        estado__in=ESTADOS_PRESTAMO_RESERVAN
    )


def ocupacion_por_hora(dispositivo, fecha, desde, hasta):
    """Recupera una actividad reservada que ocupa esta celda horaria."""
    zona = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(fecha, desde), zona)
    fin = timezone.make_aware(datetime.combine(fecha, hasta), zona)
    return actividades_en_rango([dispositivo.pk], inicio, fin).order_by('inicio').first()
