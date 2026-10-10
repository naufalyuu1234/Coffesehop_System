from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme

# Login Section
def login_views(request):
    # Cek jika user sudah terautentikasi, redirect ke 'dashboard:index'
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    # Jika HTTP method adalah POST
    if request.method == 'POST':
        # Ambil username dan password user
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Melakukan Auth user
        user = authenticate(request, username=username, password=password)

        # Cek apakah user berhasil login atau tidak
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(next_url)

            return redirect('dashboard:index')
        else:
            messages.error(request, "Username atau password salah")
            return redirect('login')

    return render(request, 'auth/login.html')

# Logout Section
def logout_view(request):
    logout(request)
    messages.info(request, "Anda berhasil Logout")
    return redirect('accounts:login')
    

