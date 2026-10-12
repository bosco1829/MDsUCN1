from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['fin'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['equipos'].queryset = Dispositivo.objects.exclude(
            estado__in=['mantenimiento', 'danado']
        ).order_by('nombre_dispositivo')
        for field in self.fields.values():
            field.widget.attrs['class'] = 'actividad-input'


@login_required
def actividades(request):
    puede_editar = es_administrador(request.user)
    actividad_editar = None
    if request.GET.get('editar') and puede_editar:
        actividad_editar = get_object_or_404(Actividad, pk=request.GET['editar'])
    form = ActividadForm(instance=actividad_editar)

    if request.method == 'POST':
        if not puede_editar:
            messages.error(request, 'No tienes permiso para administrar actividades.')
            return redirect('actividades')
        pk = request.POST.get('actividad_id')
        objeto = get_object_or_404(Actividad, pk=pk) if pk else None
        form = ActividadForm(request.POST, instance=objeto)
        if form.is_valid():
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
    return render(request, 'appOne/actividades.html', {
        'actividades': registros, 'form': form, 'editar': actividad_editar,
        'puede_editar': puede_editar, 'tipo_actual': tipo,
    })


@login_required
@require_POST
def eliminar_actividad(request, pk):
    if not es_administrador(request.user):
        messages.error(request, 'No tienes permiso para eliminar actividades.')
        return redirect('actividades')
    actividad = get_object_or_404(Actividad, pk=pk)
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
