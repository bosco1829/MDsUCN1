from datetime import date, time
from django.test import TestCase
from django.urls import reverse
from appOne.models import Usuario, Dispositivo, Prestamo


class CalendarioPrestamosTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            correo_institucional='admin.calendar@example.edu', username='admin_calendar',
            nombre_completo='Administrador', codigo='CALADMIN', rol='Admin', password='Prueba1234!'
        )
        self.usuario = Usuario.objects.create_user(
            correo_institucional='user.calendar@example.edu', username='user_calendar',
            nombre_completo='Solicitante', codigo='CALUSER', rol='Docente', password='Prueba1234!'
        )
        self.otro = Usuario.objects.create_user(
            correo_institucional='other.calendar@example.edu', username='other_calendar',
            nombre_completo='Otra Persona', codigo='CALOTHER', rol='Docente', password='Prueba1234!'
        )
        self.dispositivo = Dispositivo.objects.create(
            nombre_dispositivo='Proyector', marca='Marca X', codigo_inventario='CAL-001'
        )
        self.prestamo = Prestamo.objects.create(
            usuario=self.usuario, dispositivo=self.dispositivo, motivo='Presentación',
            fecha_uso=date(2026, 11, 18), hora_inicio=time(9), hora_entrega=time(11)
        )

    def test_evento_en_fecha_solicitada_y_detalles(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('api_reservas_eventos'))
        self.assertEqual(respuesta.status_code, 200)
        evento = respuesta.json()[0]
        self.assertEqual(evento['start'], '2026-11-18T09:00:00')
        self.assertEqual(evento['end'], '2026-11-18T11:00:00')
        self.assertEqual(evento['extendedProps']['motivo'], 'Presentación')
        self.assertEqual(evento['extendedProps']['usuario'], 'Solicitante')

    def test_usuario_solo_ve_sus_prestamos(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(reverse('api_reservas_eventos')).json(), [])

    def test_requiere_inicio_de_sesion(self):
        self.assertEqual(self.client.get(reverse('api_reservas_eventos')).status_code, 302)
