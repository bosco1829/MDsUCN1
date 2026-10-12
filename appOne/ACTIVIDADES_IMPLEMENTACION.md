# Actividades Universitarias — MDsUCN1

Implementación integrada en `main`.

## Funciones
- Actividades dentro y fuera de la universidad.
- Fechas y horarios de inicio y fin; lugar, responsable y estado.
- Selección de equipos del inventario, sin reservarlos automáticamente ni modificar préstamos.
- Calendario FullCalendar y tabla con filtros de tipo.
- Lectura para usuarios autenticados; alta, edición y borrado solo para administradores.
- Acciones registradas en bitácora de auditoría.

## Después de actualizar el proyecto
Conserva una copia de seguridad de `db.sqlite3` antes de migrar. Ejecuta en la raíz:

```powershell
python manage.py migrate
python manage.py check
python manage.py test appOne.tests_actividades
python manage.py runserver
```

Abre `/actividades/` después de iniciar sesión. El calendario carga FullCalendar desde CDN, por lo que el navegador necesita conexión a Internet.

## Nota sobre recursos
Seleccionar dispositivos es planificación y **no** bloquea automáticamente equipos ni genera préstamos. El proceso existente de solicitudes sigue siendo el responsable de autorizar su uso.

## Estado de verificación
Los archivos quedaron publicados en GitHub; la ejecución de migraciones y pruebas Django debe realizarse en un entorno con dependencias y base de datos configuradas.
