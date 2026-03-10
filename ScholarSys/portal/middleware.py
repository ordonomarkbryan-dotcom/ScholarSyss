from django.shortcuts import render, redirect
from django.urls import reverse
from .models import SystemSetting

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to admin and login/logout paths even in maintenance
        exempt_paths = [
            reverse('admin_dash'),
            reverse('login'),
            reverse('logout'),
            reverse('login_alias'),
            '/admin/', # Django admin
        ]
        
        # Check if current path is exempt
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # Check maintenance mode
        maintenance_setting = SystemSetting.objects.filter(key='maintenance_mode').first()
        is_maintenance = maintenance_setting.value == 'True' if maintenance_setting else False
        
        if is_maintenance:
            # Only allow users with 'admin' role to bypass maintenance
            # This requires user to be logged in
            if request.user.is_authenticated:
                try:
                    if request.user.userprofile.role == 'admin':
                        return self.get_response(request)
                except Exception:
                    pass
            
            # Show maintenance page
            return render(request, 'portal/maintenance.html')

        return self.get_response(request)
