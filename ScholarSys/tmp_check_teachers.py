from django.contrib.auth.models import User
from portal.models import UserProfile, Classroom

def check_teachers():
    print("--- User List ---")
    for user in User.objects.all():
        try:
            profile = user.userprofile
            print(f"ID: {user.id} | Username: {user.username} | Name: {user.first_name} {user.last_name} | Role: {profile.role} | Formatted: {profile.formatted_name}")
        except:
            print(f"ID: {user.id} | Username: {user.username} | Name: {user.first_name} {user.last_name} | Role: NO PROFILE")

    print("\n--- Classroom Assignments ---")
    for cls in Classroom.objects.all():
        print(f"Class: {cls.name} ({cls.course_number}) | Teacher: {cls.teacher.username} ({cls.teacher.userprofile.formatted_name if hasattr(cls.teacher, 'userprofile') else 'No Profile'})")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    check_teachers()
