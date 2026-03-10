import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from portal.models import UserProfile, Classroom

def populate():
    data = [
        ('A. Galiste', 'GEEC 112', 'Entrepreneurial Mind', 3, 'MWF 9:00-10:00 Rm5'),
        ('M. Pre', 'ISCC 105', 'Information Management 1', 3, 'MF 8:00-9:00 Rm5, TTh 9:30-11:00 Lab1'),
        ('R. Baro', 'ISPC 104', 'IT Infrastructure and Network Technologies', 3, 'T 3:00-4:00 Rm4, Th 11:00-12:00 Rm5, TTh 8:00-9:30 ORC'),
        ('G. Omo', 'ISCC 106', 'Application Development and Emerging Technologies', 3, 'MF 1:00-2:00 Rm5, TW 1:00-2:30 Lab1'),
        ('V. Haber', 'ISAE 102', 'IS Innovations and New Technologies', 3, 'T 4:00-5:00 Rm3, W 8:00-9:00 Rm5, MF 2:30-4:00 Lab1'),
        ('V. Haber', 'ISAE 103', 'Object Oriented Programming', 3, 'T 11:00-12:00 Rm5, W 10:00-11:00 ORC, W 11:00-12:30 ORC, Th 1:00-2:30 ORC'),
        ('E. Ebuenga', 'ISAE 104', 'Principles of Accounting', 3, 'MF 10:00-11:30 Rm5'),
        ('R. Victore', 'PATHFIT 104', 'Outdoor and Adventure Activities', 2, 'Th 3:00-5:00 TBA')
    ]
    section = 'BSIS IIB'
    
    for inst_name, code, title, units, sched in data:
        # Create user
        username = inst_name.lower().replace(' ', '').replace('.', '') + '@scholarsys.com'
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password('pass123')
            user.first_name = inst_name
            user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'teacher'})
        
        # Create classroom
        Classroom.objects.update_or_create(
            course_number=code,
            section=section,
            defaults={
                'name': title,
                'teacher': user,
                'units': units,
                'schedule': sched
            }
        )
        print(f"Created/Updated {code}: {title}")

if __name__ == "__main__":
    populate()
