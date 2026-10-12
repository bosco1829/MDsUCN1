from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('appOne', '0006_alter_dispositivo_options_alter_prestamo_options_and_more')]

    operations = [
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=180)),
                ('descripcion', models.TextField(blank=True)),
                ('tipo', models.CharField(max_length=10, choices=[('interna', 'Dentro de la universidad'), ('externa', 'Fuera de la universidad')])),
                ('lugar', models.CharField(max_length=200)),
                ('responsable', models.CharField(max_length=150)),
                ('inicio', models.DateTimeField(db_index=True)),
                ('fin', models.DateTimeField(db_index=True)),
                ('estado', models.CharField(max_length=12, default='planificada', choices=[('planificada', 'Planificada'), ('en_curso', 'En curso'), ('finalizada', 'Finalizada'), ('cancelada', 'Cancelada')])),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actividades_creadas', to=settings.AUTH_USER_MODEL)),
                ('equipos', models.ManyToManyField(blank=True, related_name='actividades', to='appOne.dispositivo')),
            ],
            options={'ordering': ['inicio'], 'verbose_name': 'Actividad universitaria', 'verbose_name_plural': 'Actividades universitarias'},
        ),
    ]
