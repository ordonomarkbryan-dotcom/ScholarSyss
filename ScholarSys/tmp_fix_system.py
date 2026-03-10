import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from portal.models import UserProfile, Classroom

def fix():
    # Fix Admin
    admin, created = User.objects.get_or_create(username='admin')
    admin.set_password('admin123')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    UserProfile.objects.get_or_create(user=admin, defaults={'role': 'admin'})
    print("✓ Reset admin password to admin123")

    # Connect Teacher (H. Pogi) to Haber's classes
    # 1. Find H. Pogi (Username: HABIR123, Name: HABIR POGI)
    pogi = User.objects.filter(username='HABIR123').first() or \
           User.objects.filter(first_name__icontains='HABIR', last_name__icontains='POGI').first()
    
    if not pogi:
        print("x Could not find 'H. Pogi' account (HABIR123).")
    else:
        # 2. Find Classes (They might be assigned to a non-existent teacher or another user)
        # Looking for classes that should belong to Pogi but aren't yet
        target_classes = Classroom.objects.filter(course_number__in=['ISAE 102', 'ISAE 103'])
        
        for cls in target_classes:
            cls.teacher = pogi
            cls.save()
            print(f"✓ Reassigned {cls.course_number}: {cls.name} to Teacher: {pogi.username}")

if __name__ == "__main__":
    fix()
