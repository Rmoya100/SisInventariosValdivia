from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.core.cache import cache

_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_SECONDS = 900  # 15 minutos

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        nombre   = request.POST.get('nombreUsu', '').strip()
        password = request.POST.get('password')

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown')).split(',')[0].strip()
        cache_key = f'login_attempts_{ip}'
        attempts = cache.get(cache_key, 0)

        if attempts >= _MAX_LOGIN_ATTEMPTS:
            messages.error(request, 'Demasiados intentos fallidos. Por favor espere 15 minutos antes de intentar nuevamente.')
            return render(request, 'inventory/login.html')

        usuario = authenticate(request, username=nombre, password=password)
        if usuario is not None:
            # Check if user is active (soft delete)
            if hasattr(usuario, 'activo') and not usuario.activo:
                messages.error(request, 'Usuario inactivo.')
                return render(request, 'inventory/login.html')
            cache.delete(cache_key)
            login(request, usuario)
            request.session.cycle_key()
            request.session.set_expiry(0)
            if getattr(usuario, 'must_change_password', False):
                return redirect('primer_ingreso_password')
            return redirect('index')
        else:
            cache.set(cache_key, attempts + 1, _LOCKOUT_SECONDS)
            remaining = _MAX_LOGIN_ATTEMPTS - (attempts + 1)
            if remaining > 0:
                messages.error(request, f'Usuario o contraseña incorrectos. ({remaining} intentos restantes)')
            else:
                messages.error(request, 'Has superado el límite de intentos. Cuenta bloqueada por 15 minutos.')
    return render(request, 'inventory/login.html')

@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')
