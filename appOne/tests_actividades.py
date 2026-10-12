from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from appOne.models import Actividad, Usuario


class ActividadesTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            correo_institucional='admin.actividades@example.edu',
            username='admin_actividades',
            nombre_completo='Administrador Actividades',
            codigo='ACTADMIN1',
            rol='Admin',
            password='testpassword123',
        )
        self.docente = Usuario.objects.create_user(
            correo_institucional='docente.actividades@example.edu',
            username='docente_actividades',
            nombre_completo='Docente Ejemplo',
            codigo='ACTDOC1',
            rol='Docente',
            password='testpassword123',
        )

    def test_autenticacion_requerida(self):
        response = self.client.get(reverse('actividades'))
        self.assertEqual(response.status_code, 302)

    def test_docente_puede_ver_pero_no_crear(self):
        self.client.force_login(self.docente)
        response = self.client.get(reverse('actividades'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('actividades'), {'titulo': 'No permitida'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Actividad.objects.exists())

    def test_admin_puede_crear_y_api_muestra_evento(self):
        self.client.force_login(self.admin)
        inicio = timezone.localtime(timezone.now() + timedelta(days=3)).replace(second=0, microsecond=0)
        fin = inicio + timedelta(hours=2)
        response = self.client.post(reverse('actividades'), {
            'titulo': 'Feria universitaria',
            'descripcion': 'Actividad de prueba',
            'tipo': 'interna',
            'lugar': 'Auditorio',
            'responsable': 'Coordinación',
            'inicio': inicio.strftime('%Y-%m-%dT%H:%M'),
            'fin': fin.strftime('%Y-%m-%dT%H:%M'),
            'estado': 'planificada',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Actividad.objects.count(), 1)
        events = self.client.get(reverse('api_actividades'))
        self.assertEqual(events.status_code, 200)
        self.assertEqual(events.json()[0]['title'], 'Feria universitaria')

    def test_fecha_final_debe_ser_posterior(self):
        self.client.force_login(self.admin)
        ahora = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
        self.client.post(reverse('actividades'), {
            'titulo': 'Fechas inválidas', 'tipo': 'externa', 'lugar': 'Sede externa',
            'responsable': 'Coordinación', 'inicio': ahora.strftime('%Y-%m-%dT%H:%M'),
            'fin': (ahora - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'estado': 'planificada',
        })
        self.assertFalse(Actividad.objects.exists())
