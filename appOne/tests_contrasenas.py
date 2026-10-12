from django.test import TestCase
from django.urls import reverse
from appOne.models import Usuario


class ContrasenasTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            correo_institucional='admin.contrasenas@example.edu',
            username='admin_contrasenas', nombre_completo='Administrador',
            codigo='TESTPASSADMIN', rol='Admin', password='PasswordAnterior123!'
        )
        self.usuario = Usuario.objects.create_user(
            correo_institucional='user.contrasenas@example.edu',
            username='user_contrasenas', nombre_completo='Usuario',
            codigo='TESTPASSUSER', rol='Docente', password='PasswordAnterior123!'
        )

    def test_cambio_personal_requiere_contrasena_actual(self):
        self.client.force_login(self.usuario)
        r = self.client.post(reverse('cambiar_mi_contrasena'), {
            'old_password': 'Incorrecta',
            'new_password1': 'NuevaClave123!Importante',
            'new_password2': 'NuevaClave123!Importante',
        })
        self.assertEqual(r.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('PasswordAnterior123!'))

    def test_usuario_cambia_su_contrasena_y_mantiene_sesion(self):
        self.client.force_login(self.usuario)
        r = self.client.post(reverse('cambiar_mi_contrasena'), {
            'old_password': 'PasswordAnterior123!',
            'new_password1': 'NuevaClave123!Importante',
            'new_password2': 'NuevaClave123!Importante',
        })
        self.assertEqual(r.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NuevaClave123!Importante'))
        self.assertEqual(self.client.get(reverse('cambiar_mi_contrasena')).status_code, 200)

    def test_usuario_no_puede_cambiar_otra_cuenta(self):
        self.client.force_login(self.usuario)
        r = self.client.post(reverse('admin_cambiar_contrasena', args=[self.admin.pk]), {
            'new_password1': 'NuevaClave123!Importante',
            'new_password2': 'NuevaClave123!Importante',
        })
        self.assertEqual(r.status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('PasswordAnterior123!'))

    def test_admin_puede_restablecer_usuario(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('admin_cambiar_contrasena', args=[self.usuario.pk]), {
            'new_password1': 'NuevaClave123!Importante',
            'new_password2': 'NuevaClave123!Importante',
        })
        self.assertEqual(r.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NuevaClave123!Importante'))

    def test_admin_no_puede_restablecerse_sin_clave_actual(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('admin_cambiar_contrasena', args=[self.admin.pk]))
        self.assertRedirects(r, reverse('cambiar_mi_contrasena'))
