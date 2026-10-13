from datetime import datetime, date, time, timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from appOne.models import Actividad, Dispositivo, Prestamo, Usuario
from appOne.views.actividades import ActividadForm


class ReservasCompartidasTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo_institucional='equipo.test@example.edu', username='equipo_test',
            nombre_completo='Docente Ejemplo', codigo='EQTEST1', rol='Docente',
            password='Password1234!'
        )
        self.equipo = Dispositivo.objects.create(
            nombre_dispositivo='Laptop de prueba', marca='Dell', codigo_inventario='TEST-ACT-01'
        )
        self.inicio = timezone.make_aware(datetime(2026, 11, 19, 9, 0))
        self.fin = self.inicio + timedelta(hours=3)
        self.actividad = Actividad.objects.create(
            titulo='Entrega de carpetas', tipo='interna', lugar='Auditorio',
            responsable='Coordinación', inicio=self.inicio, fin=self.fin,
            creado_por=self.usuario,
        )
        self.actividad.equipos.add(self.equipo)

    def test_modal_marca_ocupados_los_tres_rangos(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('modal_prestamo', args=[self.equipo.pk]), {'fecha_uso': '2026-11-19'})
        self.assertEqual(respuesta.status_code, 200)
        rangos = respuesta.context['horarios_tabla']
        self.assertTrue(all(rangos[h]['ocupado'] for h in [1, 2, 3]))
        self.assertEqual(rangos[1]['actividad'].titulo, 'Entrega de carpetas')
        self.assertFalse(rangos[0]['ocupado'])

    def test_prestamo_no_puede_solaparse_con_actividad(self):
        prestamo = Prestamo(
            usuario=self.usuario, dispositivo=self.equipo, motivo='Clase',
            fecha_uso=date(2026, 11, 19), hora_inicio=time(10),
            hora_entrega=time(11)
        )
        with self.assertRaises(ValidationError):
            prestamo.full_clean()

    def test_actividad_no_puede_utilizar_equipo_ocupado(self):
        otra = ActividadForm(data={
            'titulo': 'Otra actividad', 'tipo': 'externa', 'lugar': 'Sede',
            'responsable': 'Docente', 'inicio': '2026-11-19T10:00',
            'fin': '2026-11-19T11:00', 'estado': 'planificada',
            'equipos': [self.equipo.pk]
        })
        self.assertFalse(otra.is_valid())
        self.assertIn('equipos', otra.errors)

    def test_calendario_muestra_actividad_y_equipo(self):
        self.client.force_login(self.usuario)
        eventos = self.client.get(reverse('api_reservas_eventos')).json()
        self.assertEqual(len(eventos), 1)
        self.assertIn('Entrega de carpetas', eventos[0]['title'])
        self.assertEqual(eventos[0]['start'], self.inicio.isoformat())
