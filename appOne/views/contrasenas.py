from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from appOne.models import Usuario, BitacoraAuditoria
from .utils import es_administrador, registrar_auditoria


@login_required
@require_http_methods(["GET", "POST"])
def cambiar_mi_contrasena(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)
        registrar_auditoria(
            request, BitacoraAuditoria.ACCION_EDITAR, "Seguridad",
            usuario.pk, "El usuario cambió su propia contraseña"
        )
        messages.success(request, "Tu contraseña se actualizó correctamente.")
        return redirect("cambiar_mi_contrasena")
    for field in form.fields.values():
        field.widget.attrs.update({"class": "pwd-input", "autocomplete": "new-password"})
    form.fields["old_password"].widget.attrs["autocomplete"] = "current-password"
    return render(request, "appOne/cambiar_mi_contrasena.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def admin_cambiar_contrasena(request, id):
    if not es_administrador(request.user):
        raise PermissionDenied("No tienes permisos para cambiar contraseñas de otros usuarios.")

    usuario = get_object_or_404(Usuario, pk=id)
    if usuario.pk == request.user.pk:
        messages.info(request, "Para cambiar tu propia contraseña utiliza Mi contraseña.")
        return redirect("cambiar_mi_contrasena")
    if usuario.is_superuser and not request.user.is_superuser:
        raise PermissionDenied("Solo otro superusuario puede cambiar la contraseña de un superusuario.")

    form = SetPasswordForm(usuario, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar_auditoria(
            request, BitacoraAuditoria.ACCION_EDITAR, "Seguridad",
            usuario.pk, f"Contraseña restablecida por administrador para el usuario {usuario.pk}"
        )
        messages.success(request, f"Contraseña de {usuario.nombre_completo} actualizada correctamente.")
        return redirect("panel_usuarios")
    for field in form.fields.values():
        field.widget.attrs.update({"class": "pwd-input", "autocomplete": "new-password"})
    return render(request, "appOne/admin_cambiar_contrasena.html", {"form": form, "usuario_objetivo": usuario})
