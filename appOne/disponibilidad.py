"""Reglas compartidas de ocupación de equipos entre préstamos y actividades."""
from datetime import datetime, timedelta
from django.utils import timezone
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
    dias = []
    d = timezone.localtime(inicio).date()
    ultimo = timezone.localtime(fin - timedelta(microseconds=1)).date()
    while d <= ultimo:
        dias.append(d)
        d += timedelta(days=1)
    return Prestamo.objects.filter(
        dispositivo_id__in=dispositivo_ids,
        fecha_uso__in=dias,
        estado__in=ESTADOS_PRESTAMO_RESERVAN,
        hora_inicio__lt=timezone.localtime(fin).time() if len(dias) == 1 else datetime.max.time(),
        hora_entrega__gt=timezone.localtime(inicio).time() if len(dias) == 1 else datetime.min.time()
    )


def ocupacion_por_hora(dispositivo, fecha, desde, hasta):
    """Recupera una actividad reservada que ocupa esta celda horaria."""
    zona = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(fecha, desde), zona)
    fin = timezone.make_aware(datetime.combine(fecha, hasta), zona)
    return actividades_en_rango([dispositivo.pk], inicio, fin).order_by('inicio').first()
