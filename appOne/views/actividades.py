from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from appOne.disponibilidad import actividades_en_rango, prestamos_en_rango
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from appOne.models import Actividad, Dispositivo
from .utils import es_administrador, registrar_auditoria


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'descripcion', 'tipo', 'lugar', 'responsable', 'inicio', 'fin', 'estado', 'equipos']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'inicio': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'fin': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'equipos': forms.SelectMultiple(attrs={'size': '5'}),
        }

    def clean(self):
        data = super().clean()
        inicio, fin = data.get('inicio'), data.get('fin')
        equipos = data.get('equipos')
        if inicio and fin and equipos is not None:
            if fin <= inicio:
                self.add_error('fin', 'La fecha de fin debe ser posterior al inicio.')
            elif data.get('estado') in ('planificada', 'en_curso'):
                ids = [equipo.pk for equipo in equipos]
                if ids:
                    otras = actividades_en_rango(ids, inicio, fin, self.instance.pk).first()
                    prestamo = prestamos_en_rango(ids, inicio, fin).first()
                    if otras:
                        self.add_error('equipos', f'El equipo ya está asignado a la actividad "{otras.titulo}" en ese horario.')
                    if prestamo:
                        self.add_error('equipos', f'Hay un préstamo pendiente o aprobado para {prestamo.dispositivo.nombre_dispositivo} en ese horario.')
        return data

    def __init__(self, *args, administrador=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not administrador:
            self.fields['tipo'].choices = [('externa', 'Fuera de la universidad')]
            self.fields['tipo'].initial = 'externa'
            self.fields['estado'].choices = [('planificada', 'Planificada')]
        self.fields['inicio'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['fin'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['equipos'].queryset = Dispositivo.objects.exclude(
            estado__in=['mantenimiento', 'danado']
        ).order_by('nombre_dispositivo')
        for field in self.fields.values():
            field.widget.attrs['class'] = 'actividad-input'


@login_required
def actividades(request):
    administrador = es_administrador(request.user)
    puede_editar = True
    actividad_editar = None
    if request.GET.get('editar'):
        actividad_editar = get_object_or_404(Actividad, pk=request.GET['editar'])
        if not administrador and (actividad_editar.creado_por_id != request.user.pk or actividad_editar.tipo != 'externa'):
            return HttpResponseForbidden('Solo puedes editar tus propias actividades externas.')
    form = ActividadForm(instance=actividad_editar, administrador=administrador)

    if request.method == 'POST':
        # Validar permisos en el servidor, no solo en el formulario.
        pk = request.POST.get('actividad_id')
        objeto = get_object_or_404(Actividad, pk=pk) if pk else None
        if objeto and not administrador and (objeto.creado_por_id != request.user.pk or objeto.tipo != 'externa'):
            return HttpResponseForbidden('No puedes modificar esta actividad.')
        form = ActividadForm(request.POST, instance=objeto, administrador=administrador)
        if form.is_valid():
            if not administrador and (form.cleaned_data['tipo'] != 'externa' or form.cleaned_data['estado'] != 'planificada'):
                return HttpResponseForbidden('Solo puedes solicitar actividades externas planificadas.')
            actividad = form.save(commit=False)
            if not actividad.creado_por_id:
                actividad.creado_por = request.user
            actividad.save()
            form.save_m2m()
            registrar_auditoria(request, 'EDITAR' if objeto else 'CREAR', 'Actividad', actividad.pk, actividad.titulo)
            messages.success(request, 'Actividad guardada correctamente.')
            return redirect('actividades')

    tipo = request.GET.get('tipo', '')
    registros = Actividad.objects.prefetch_related('equipos').all()
    if tipo in ('interna', 'externa'):
        registros = registros.filter(tipo=tipo)
    for actividad in registros:
        actividad.puede_gestionar = administrador or (actividad.tipo == 'externa' and actividad.creado_por_id == request.user.pk)
    return render(request, 'appOne/actividades.html', {
        'actividades': registros, 'form': form, 'editar': actividad_editar,
        'puede_editar': puede_editar, 'es_administrador': administrador, 'tipo_actual': tipo,
    })


@login_required
@require_POST
def eliminar_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if not es_administrador(request.user) and (actividad.tipo != 'externa' or actividad.creado_por_id != request.user.pk):
        return HttpResponseForbidden('No puedes eliminar esta actividad.')
    registrar_auditoria(request, 'ELIMINAR', 'Actividad', actividad.pk, actividad.titulo)
    actividad.delete()
    messages.success(request, 'Actividad eliminada.')
    return redirect('actividades')


@login_required
def api_actividades(request):
    registros = Actividad.objects.prefetch_related('equipos').all()
    tipo = request.GET.get('tipo')
    if tipo in ('interna', 'externa'):
        registros = registros.filter(tipo=tipo)
    colores = {'interna': '#059669', 'externa': '#2563eb'}
    data = [{
        'id': a.pk, 'title': a.titulo,
        'start': a.inicio.isoformat(), 'end': a.fin.isoformat(),
        'backgroundColor': colores[a.tipo], 'borderColor': colores[a.tipo],
        'extendedProps': {
            'tipo': a.get_tipo_display(), 'lugar': a.lugar, 'responsable': a.responsable,
            'estado': a.get_estado_display(), 'descripcion': a.descripcion,
            'equipos': [d.nombre_dispositivo for d in a.equipos.all()],
        },
    } for a in registros]
    return JsonResponse(data, safe=False)
