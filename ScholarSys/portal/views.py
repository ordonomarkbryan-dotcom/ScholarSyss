from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, Classroom, PerformanceMonitoring, Message, Attendance, GradeAuditLog, TaskSubmission, ClassroomMaterial, Announcement, SystemLog
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from functools import wraps
import re
import csv
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from .models import UserProfile, Classroom, PerformanceMonitoring, Message, Attendance, GradeAuditLog, TaskSubmission, ClassroomMaterial, Announcement, SystemLog, GlobalAnnouncement, SystemSetting

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                profile = request.user.userprofile
            except UserProfile.DoesNotExist:
                messages.error(request, "Your account is missing a profile. Please contact admin.")
                return redirect('login')
            if profile.role not in allowed_roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def login_view(request):
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
            role_display = role.capitalize()
            dash_map = {'student': 'student_dash', 'teacher': 'teacher_dash', 'admin': 'admin_dash'}
            return render(request, 'portal/login.html', {
                'continue_as': role_display,
                'role_type': 'General',
                'redirect_url': dash_map.get(role, 'dashboard')
            })
        except UserProfile.DoesNotExist:
            pass

    # This remains as a general login or can redirect to specific login
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=identifier, password=password)
        
        if not user and '@' in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
                
        if user:
            login(request, user)
            try:
                profile = user.userprofile
                if profile.role == 'student': return redirect('student_dash')
                if profile.role == 'teacher': return redirect('teacher_dash')
                if profile.role == 'admin': return redirect('admin_dash')
            except UserProfile.DoesNotExist:
                pass
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password. Please try again.")
    return render(request, 'portal/login.html', {'role_type': 'General'})

def student_login(request):
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
            role_display = role.capitalize()
            # Map role to its dashboard
            dash_map = {'student': 'student_dash', 'teacher': 'teacher_dash', 'admin': 'admin_dash'}
            return render(request, 'portal/login.html', {
                'continue_as': role_display,
                'role_type': 'Student',
                'redirect_url': dash_map.get(role, 'dashboard')
            })
        except UserProfile.DoesNotExist:
            pass
            
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=identifier, password=password)
        
        if not user and '@' in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
                
        if user:
            try:
                if user.userprofile.role == 'student':
                    login(request, user)
                    return redirect('student_dash')
                else:
                    messages.error(request, "This login is for students only.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Profile not found.")
        else:
            messages.error(request, "Invalid credentials.")
            
    return render(request, 'portal/student_login.html', {'role_type': 'Student'})

def teacher_login(request):
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
            role_display = role.capitalize()
            # Map role to its dashboard
            dash_map = {'student': 'student_dash', 'teacher': 'teacher_dash', 'admin': 'admin_dash'}
            return render(request, 'portal/login.html', {
                'continue_as': role_display,
                'role_type': 'Teacher',
                'redirect_url': dash_map.get(role, 'dashboard')
            })
        except UserProfile.DoesNotExist:
            pass

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=identifier, password=password)
        
        if not user and '@' in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
                
        if user:
            try:
                if user.userprofile.role == 'teacher':
                    login(request, user)
                    return redirect('teacher_dash')
                else:
                    messages.error(request, "This login is for teachers only.")
            except UserProfile.DoesNotExist:
                messages.error(request, "Profile not found.")
        else:
            messages.error(request, "Invalid credentials.")
            
    return render(request, 'portal/teacher_login.html', {'role_type': 'Teacher'})

def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        section = request.POST.get('section', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', '').strip()
        
        # Prepare context for error re-render
        context = {
            'form_data': {
                'full_name': full_name,
                'username': username,
                'student_id': student_id,
                'section': section,
                'email': email,
                'role': role,
                'is_student': role == 'student',
                'is_teacher': role == 'teacher',
            }
        }

        # Role-based Validation
        if role == 'student':
            if not student_id:
                messages.error(request, "Student ID is required for students.")
                return render(request, 'portal/signup.html', context)
            if not re.match(r'^\d{3}-\d{4}-\d{1}$', student_id):
                messages.error(request, "Invalid Student ID format. Must be XXX-XXXX-X.")
                return render(request, 'portal/signup.html', context)
            if not section:
                messages.error(request, "Section is required for students.")
                return render(request, 'portal/signup.html', context)
            
            # Check for existing student ID
            if UserProfile.objects.filter(student_id=student_id).exists():
                messages.error(request, "This Student ID is already registered.")
                return render(request, 'portal/signup.html', context)
                
        elif role == 'teacher':
            pass # No extra requirements
        else:
            messages.error(request, "Please select a valid role (Student or Teacher).")
            return render(request, 'portal/signup.html', context)
            
        # Validate password pattern
        password_pattern = r'^(?=.*[a-zA-Z])(?=.*\d).{8,32}$'
        if not re.match(password_pattern, password):
            messages.error(request, "Invalid password! Password must be 8-32 characters and contain both letters and numbers.")
            return render(request, 'portal/signup.html', context)

        # Check for existing username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, 'portal/signup.html', context)

        try:
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.create(
                user=user, 
                role=role, 
                student_id=student_id if role == 'student' else "",
                section=section if role == 'student' else ""
            )
            messages.success(request, f"Successfully created {role} account for {username}! Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred during account creation: {str(e)}")
            return render(request, 'portal/signup.html', context)

    role_from_get = request.GET.get('role', '')
    context = {
        'form_data': {
            'role': role_from_get,
            'is_student': role_from_get == 'student',
            'is_teacher': role_from_get == 'teacher',
        }
    }
    return render(request, 'portal/signup.html', context)

@login_required
def dashboard_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, "Your account profile is missing. Please contact support.")
        return redirect('login')
        
    if profile.role == 'student':
        return redirect('student_dash')
    elif profile.role == 'teacher':
        return redirect('teacher_dash')
    elif profile.role == 'admin':
        return redirect('admin_dash')
    return redirect('login')

@login_required
@role_required(['student'])
def student_dash(request):
    profile = request.user.userprofile
    courses = Classroom.objects.filter(section=profile.section)
    total_units = sum(c.units for c in courses)
    performances = PerformanceMonitoring.objects.filter(student=request.user)
    attendance = Attendance.objects.filter(student=request.user)
    msg_list = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    
    # Build grade records with split course code / title and units lookup
    # Separate lists for detail views
    quizzes = []
    exams = []
    assignments_projects = []
    
    # Pivot data for Gradebook Summary (Main Table)
    # Key: course_number, Value: dict
    course_grade_map = {}
    
    # Initialize with enrolled courses
    for c in courses:
        course_grade_map[c.course_number] = {
            'course_code': c.course_number,
            'descriptive_title': c.name,
            'units': c.units,
            'exam_grade': None,
            'assignment_grade': None,
            'quiz_grade': None,
            'activity_grade': None,
            'final_grade': None,
            'remarks': '-',
        }

    # To calculate averages, we accumulate scores per category
    # course_code -> { category -> [scores] }
    categorized_scores = {}

    # Get all student submissions to check status
    student_submissions = TaskSubmission.objects.filter(student=request.user)
    submission_map = {sub.performance_record_id: sub for sub in student_submissions if sub.performance_record_id}

    # Build classroom lookup for teacher info
    classroom_map = {}
    for c in courses:
        classroom_map[c.course_number] = c

    for perf in performances:
        parts = perf.subject.split(': ', 1)
        code = parts[0]
        desc = parts[1] if len(parts) > 1 else perf.subject
        
        has_submitted = perf.id in submission_map
        
        classroom_obj = classroom_map.get(code)
        teacher_name = classroom_obj.teacher.userprofile.formatted_name if classroom_obj else 'Unknown'
        teacher_id = classroom_obj.teacher.id if classroom_obj else None
        
        record = {
            'id': perf.id,
            'course_code': code,
            'descriptive_title': desc,
            'performance_type': perf.get_performance_type_display(),
            'type_code': perf.performance_type,
            'grade': float(perf.grade),
            'max_score': float(perf.max_score),
            'remarks': perf.remarks,
            'task_instructions': perf.task_instructions,
            'date': perf.date,
            'due_date': perf.due_date,
            'has_submitted': has_submitted,
            'teacher_name': teacher_name,
            'teacher_id': teacher_id,
            'classroom_id': classroom_obj.id if classroom_obj else None
        }
        
        if perf.performance_type == 'exam':
            exams.append(record)
        elif perf.performance_type == 'quiz':
            quizzes.append(record)
        elif perf.performance_type in ['assignment', 'project', 'activity']:
            assignments_projects.append(record)
            
        if code in course_grade_map:
            if code not in categorized_scores:
                categorized_scores[code] = {'quiz': [], 'exam': [], 'activity': [], 'assignment': []}
            
            p_type = perf.performance_type
            if p_type == 'project': p_type = 'assignment' # Group project with assignment
            
            if p_type in categorized_scores[code]:
                categorized_scores[code][p_type].append(float(perf.grade))
                if p_type == 'exam':
                    course_grade_map[code]['remarks'] = perf.remarks

    # Now calculate averages and final grade for each course
    for code, scores in categorized_scores.items():
        avg_q = sum(scores['quiz']) / len(scores['quiz']) if scores['quiz'] else 0
        avg_e = sum(scores['exam']) / len(scores['exam']) if scores['exam'] else 0
        avg_ac = sum(scores['activity']) / len(scores['activity']) if scores['activity'] else 0
        avg_as = sum(scores['assignment']) / len(scores['assignment']) if scores['assignment'] else 0
        
        course_grade_map[code]['quiz_grade'] = avg_q
        course_grade_map[code]['exam_grade'] = avg_e
        course_grade_map[code]['activity_grade'] = avg_ac
        course_grade_map[code]['assignment_grade'] = avg_as
        
        # Weighted Final Grade: Q:20%, E:40%, Ac:30%, As:10%
        final = (avg_q * 0.2) + (avg_e * 0.4) + (avg_ac * 0.3) + (avg_as * 0.1)
        course_grade_map[code]['final_grade'] = final

    grade_summary = list(course_grade_map.values())
    
    # Calculate GPA based on Final Grades present in summary
    final_scores = [c['final_grade'] for c in grade_summary if c['final_grade'] is not None and c['final_grade'] > 0]
    gpa = f"{sum(final_scores) / len(final_scores):.2f}" if final_scores else ''
    
    # New Dashboard Data
    announcements = Announcement.objects.filter(classroom__in=courses).order_by('-created_at')[:5]
    materials = ClassroomMaterial.objects.filter(classroom__in=courses).order_by('-uploaded_at')[:5]
    upcoming_deadlines = PerformanceMonitoring.objects.filter(
        student=request.user, 
        due_date__gte=timezone.now()
    ).order_by('due_date')[:5]

    # Global Alerts
    global_alerts = GlobalAnnouncement.objects.filter(
        Q(target_role='all') | Q(target_role='student'),
        is_active=True
    ).order_by('-created_at')[:3]

    # Messages
    msg_list = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:10]

    return render(request, 'portal/student_dash.html', {
        'courses': courses,
        'total_units': total_units,
        'performances': performances,
        'grade_records': grade_summary, 
        'quizzes': quizzes,
        'exams': exams,
        'assignments_projects': assignments_projects,
        'gpa': gpa,
        'attendance': attendance,
        'msg_list': msg_list,
        'announcements': announcements,
        'materials': materials,
        'upcoming_deadlines': upcoming_deadlines,
        'global_alerts': global_alerts,
    })

@login_required
@role_required(['teacher', 'admin'])
def teacher_dash(request):
    if request.user.userprofile.role == 'admin':
        classrooms = Classroom.objects.all()
    else:
        classrooms = Classroom.objects.filter(teacher=request.user)
        
    messages_data = Message.objects.filter(receiver=request.user).order_by('-timestamp')
    
    global_alerts = GlobalAnnouncement.objects.filter(
        Q(target_role='all') | Q(target_role='teacher'),
        is_active=True
    ).order_by('-created_at')[:3]

    return render(request, 'portal/teacher_dash.html', {
        'classrooms': classrooms,
        'messages': messages_data,
        'global_alerts': global_alerts
    })

@login_required
@role_required(['teacher'])
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    students = User.objects.filter(userprofile__section=classroom.section, userprofile__role='student')
    materials = classroom.materials.all().order_by('-uploaded_at')
    announcements = classroom.announcements.all().order_by('-created_at')
    
    return render(request, 'portal/classroom_detail.html', {
        'classroom': classroom,
        'students': students,
        'materials': materials,
        'announcements': announcements
    })

@login_required
def send_message(request):
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        receiver = get_object_or_404(User, id=receiver_id)
        Message.objects.create(sender=request.user, receiver=receiver, content=content)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    return redirect('dashboard')

@login_required
@role_required(['teacher'])
def mark_attendance(request):
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom_id')
        student_id = request.POST.get('student_id')
        date = request.POST.get('date')
        status = request.POST.get('status')
        
        classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
        student = get_object_or_404(User, id=student_id)
        
        Attendance.objects.update_or_create(
            student=student,
            classroom=classroom,
            date=date,
            defaults={'status': status}
        )
        
        # Early Warning Alert Logic (stateless calculation)
        profile = student.userprofile
        if profile.attendance_percentage < 80:
            Message.objects.create(
                sender=request.user,
                receiver=student,
                content=f"Early Warning: Your attendance has fallen to {profile.attendance_percentage:.1f}%. Please contact your instructor."
            )
            
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    return redirect('dashboard')

@login_required
@role_required(['teacher'])
def add_grade(request):
    from django.core.exceptions import ValidationError
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject = request.POST.get('subject')
        grade = request.POST.get('grade')
        max_score = request.POST.get('max_score', 100)
        performance_type = request.POST.get('performance_type', 'others')
        remarks = request.POST.get('remarks', '')
        
        student = get_object_or_404(User, id=student_id)
        
        try:
            # Audit Logging: Capture pre-save state if exists (simplified for new entry)
            GradeAuditLog.objects.create(
                student=student,
                subject=subject,
                old_grade=None, 
                new_grade=grade,
                changed_by=request.user
            )
            
            perf = PerformanceMonitoring(
                student=student,
                subject=subject,
                grade=grade,
                max_score=max_score,
                performance_type=performance_type,
                remarks=remarks
            )
            perf.full_clean() # Force validation (0-100 check)
            perf.save()
            messages.success(request, f"Successfully added {performance_type} score for {student.username}.")
        except ValidationError as e:
            # Extract error message cleanly
            msg = e.message_dict.get('grade', ['Invalid input'])[0] if hasattr(e, 'message_dict') else str(e)
            messages.error(request, f"Error adding grade: {msg}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred.")
            
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    return redirect('dashboard')

@login_required
def profile_update(request):
    if request.method == 'POST':
        full_name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        
        if full_name:
            # Handle multiple spaces or just one name
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                request.user.first_name = name_parts[0]
                request.user.last_name = " ".join(name_parts[1:])
            else:
                request.user.first_name = name_parts[0]
                request.user.last_name = ""
        
        if email:
            request.user.email = email
            
        request.user.save()
        
        # Profile fields (readonly for students but good to be safe)
        try:
            profile = request.user.userprofile
            student_id = request.POST.get('student_id')
            section = request.POST.get('section')
            if student_id is not None: profile.student_id = student_id
            if section is not None: profile.section = section
            profile.save()
        except UserProfile.DoesNotExist:
            pass
            
        messages.success(request, "Profile updated successfully!")
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
@role_required(['teacher', 'admin'])
def student_list_view(request):
    query = request.GET.get('q', '').strip()
    students = User.objects.filter(userprofile__role='student')
    
    if query:
        students = students.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(userprofile__student_id__icontains=query)
        )
    
    return render(request, 'portal/student_list.html', {
        'students': students,
        'query': query
    })

@login_required
@role_required(['teacher', 'admin'])
def student_detail_view(request, student_id):
    student = get_object_or_404(User, id=student_id, userprofile__role='student')
    performances = PerformanceMonitoring.objects.filter(student=student).order_by('-date')
    attendance = Attendance.objects.filter(student=student).order_by('-date')
    
    # Calculate summary stats
    total_attendance = attendance.count()
    present_count = attendance.filter(status='present').count()
    attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 100
    
    # Subject-wise weighted calculation
    subject_map = {}
    for p in performances:
        if p.subject not in subject_map:
            subject_map[p.subject] = {'q': 0, 'e': 0, 'ac': 0, 'asgn': 0}
        
        val = float(p.grade)
        if p.performance_type == 'quiz': subject_map[p.subject]['q'] = val
        elif p.performance_type == 'exam': subject_map[p.subject]['e'] = val
        elif p.performance_type == 'activity': subject_map[p.subject]['ac'] = val
        elif p.performance_type == 'assignment': subject_map[p.subject]['asgn'] = val

    final_grades = []
    for sub, scores in subject_map.items():
        # Weighted calculation
        total = (scores['q'] * 0.2) + (scores['e'] * 0.4) + (scores['ac'] * 0.3) + (scores['asgn'] * 0.1)
        final_grades.append(total)
    
    avg_grade = sum(final_grades) / len(final_grades) if final_grades else 0

    return render(request, 'portal/student_records.html', {
        'student': student,
        'performances': performances,
        'attendance': attendance,
        'attendance_rate': round(attendance_rate, 1),
        'avg_grade': round(avg_grade, 2),
        'subject_summaries': subject_map # For template use if needed
    })

@login_required
@role_required(['admin'])
def admin_dash(request):
    total_students = User.objects.filter(userprofile__role='student').count()
    total_teachers = User.objects.filter(userprofile__role='teacher').count()
    total_classes = Classroom.objects.count()
    recent_logs = GradeAuditLog.objects.all().order_by('-timestamp')[:10]
    
    # NEW: System activity feed
    system_activity = SystemLog.objects.all().order_by('-timestamp')[:15]
    
    # NEW: Global Announcements
    global_announcements = GlobalAnnouncement.objects.all().order_by('-created_at')[:5]
    
    # NEW: System Settings
    maintenance_mode = SystemSetting.objects.filter(key='maintenance_mode').first()
    maintenance_status = maintenance_mode.value == 'True' if maintenance_mode else False
    
    current_term = SystemSetting.objects.filter(key='current_term').first()
    term_name = current_term.value if current_term else "Not Set"

    return render(request, 'portal/admin_dash.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'recent_logs': recent_logs,
        'system_activity': system_activity,
        'global_announcements': global_announcements,
        'maintenance_status': maintenance_status,
        'term_name': term_name,
    })

@login_required
@role_required(['student'])
def submit_task(request):
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom_id')
        performance_record_id = request.POST.get('performance_record_id')
        task_type = request.POST.get('task_type')
        title = request.POST.get('title')
        content = request.POST.get('content')
        submission_file = request.FILES.get('submission_file')
        
        if not classroom_id or not classroom_id.isdigit():
            messages.error(request, "Invalid classroom specified.")
            return redirect('student_dash')
            
        classroom = get_object_or_404(Classroom, id=classroom_id)
        perf_record = None
        if performance_record_id and performance_record_id.isdigit():
            perf_record = get_object_or_404(PerformanceMonitoring, id=performance_record_id, student=request.user)
        
        TaskSubmission.objects.create(
            student=request.user,
            classroom=classroom,
            performance_record=perf_record,
            task_type=task_type,
            title=title,
            content=content,
            submission_file=submission_file
        )
        messages.success(request, f"{task_type.title()} submitted successfully!")
        return redirect('student_dash')
    return redirect('student_dash')

@login_required
@role_required(['teacher', 'admin'])
def submissions_list(request):
    if request.user.userprofile.role == 'admin':
        submissions = TaskSubmission.objects.all().order_by('-submitted_at')
    else:
        # Teacher only sees submissions for their classes
        my_classes = Classroom.objects.filter(teacher=request.user)
        submissions = TaskSubmission.objects.filter(classroom__in=my_classes).order_by('-submitted_at')
    
    return render(request, 'portal/submissions_list.html', {
        'submissions': submissions
    })

@login_required
@role_required(['teacher', 'admin'])
def review_submission(request, submission_id):
    submission = get_object_or_404(TaskSubmission, id=submission_id)
    
    # Check permission (Teacher must own the classroom)
    if request.user.userprofile.role == 'teacher' and submission.classroom.teacher != request.user:
        messages.error(request, "You do not have permission to review this submission.")
        return redirect('submissions_list')
        
    if request.method == 'POST':
        grade = request.POST.get('grade')
        remarks = request.POST.get('remarks')
        
        # Update linked performance record
        if submission.performance_record:
            perf = submission.performance_record
            perf.grade = grade
            perf.remarks = remarks
            perf.save()
            
            # Update submission status
            submission.is_reviewed = True
            submission.teacher_remarks = remarks
            submission.save()
            
            messages.success(request, f"Score updated for {submission.student.userprofile.formatted_name}.")
        else:
            messages.error(request, "This submission is not linked to a performance record.")
            
        return redirect('submissions_list')
    
    return redirect('submissions_list')

@login_required
@role_required(['teacher', 'admin'])
def raw_scores_view(request):
    # Requirement: List each student alphabetically
    # Category = performance_type_display, Raw Score = grade, Remarks replaces Max
    performances = PerformanceMonitoring.objects.all().select_related('student__userprofile').prefetch_related('submissions').order_by('student__last_name', 'student__first_name', 'date')
    
    return render(request, 'portal/raw_scores.html', {
        'performances': performances
    })

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@role_required(['teacher', 'admin'])
def calculate_grade(request):
    final_grade = None
    if request.method == 'POST':
        try:
            quiz = float(request.POST.get('quiz', 0))
            exam = float(request.POST.get('exam', 0))
            activity = float(request.POST.get('activity', 0))
            assignment = float(request.POST.get('assignment', 0))
            
            # Defining weights
            w_q, w_e, w_ac, w_as = 0.20, 0.40, 0.30, 0.10
            
            # Computation
            final_grade = (quiz * 0.20) + (exam * 0.40) + (activity * 0.30) + (assignment * 0.10)
            final_grade = round(final_grade, 2)
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                from django.http import JsonResponse
                return JsonResponse({'final_grade': final_grade})
        except ValueError:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'error': 'Invalid input'}, status=400)
            messages.error(request, "Invalid input. Please enter numbers only.")

    return render(request, 'portal/grade_calculator.html', {'final_grade': final_grade})


@login_required
@role_required(['teacher', 'admin'])
def delete_performance(request, entry_id):
    entry = get_object_or_404(PerformanceMonitoring, id=entry_id)
    student_id = entry.student.id
    entry.delete()
    messages.success(request, "Performance record deleted successfully.")
    return redirect('student_records', student_id=student_id)

@login_required
@role_required(['teacher', 'admin'])
def delete_attendance(request, entry_id):
    entry = get_object_or_404(Attendance, id=entry_id)
    student_id = entry.student.id
    entry.delete()
    messages.success(request, "Attendance record deleted successfully.")
    return redirect('student_records', student_id=student_id)

@login_required
@role_required(['admin'])
def admin_create_user(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'student')
        student_id = request.POST.get('student_id', '')
        section = request.POST.get('section', '')

        if not username or not password or not role:
            messages.error(request, "Missing required fields.")
            return redirect('admin_dash')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('admin_dash')

        try:
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            UserProfile.objects.create(
                user=user,
                role=role,
                student_id=student_id if role == 'student' else "",
                section=section if role == 'student' else ""
            )
            
            # Audit Log
            SystemLog.objects.create(
                user=request.user,
                action='USER_CREATE',
                details=f"Created {role} account: {username}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Account for {username} ({role}) created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")

    return redirect('admin_dash')

@login_required
@role_required(['teacher'])
def bulk_attendance(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    students = User.objects.filter(userprofile__section=classroom.section, userprofile__role='student')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'present')
            Attendance.objects.update_or_create(
                student=student,
                classroom=classroom,
                date=date,
                defaults={'status': status}
            )
        messages.success(request, f"Attendance for {date} updated for all students.")
        return redirect('classroom_detail', classroom_id=classroom.id)
        
    return render(request, 'portal/bulk_attendance.html', {
        'classroom': classroom,
        'students': students
    })

@login_required
@role_required(['teacher'])
def upload_material(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        ClassroomMaterial.objects.create(
            classroom=classroom,
            title=title,
            description=description,
            file=file,
            uploaded_by=request.user
        )
        SystemLog.objects.create(
            action="Upload Material",
            user=request.user,
            details=f"Uploaded '{title}' to {classroom.name}"
        )
        messages.success(request, "Material uploaded successfully.")
    return redirect('classroom_detail', classroom_id=classroom.id)

@login_required
@role_required(['teacher'])
def post_announcement(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_priority = request.POST.get('is_priority') == 'on'
        Announcement.objects.create(
            classroom=classroom,
            title=title,
            content=content,
            created_by=request.user,
            is_priority=is_priority
        )
        SystemLog.objects.create(
            action="Post Announcement",
            user=request.user,
            details=f"Posted '{title}' to {classroom.name}"
        )
        messages.success(request, "Announcement posted.")
    return redirect('classroom_detail', classroom_id=classroom.id)


@login_required
@role_required(['admin'])
def admin_bulk_upload(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        
        count = 0
        for row in reader:
            try:
                # Expected columns: username, email, full_name, role, password, student_id, section
                username = row.get('username')
                email = row.get('email')
                full_name = row.get('full_name', '')
                role = row.get('role', 'student')
                password = row.get('password', 'ScholarPass123')
                student_id = row.get('student_id', '')
                section = row.get('section', '')
                
                if User.objects.filter(username=username).exists():
                    continue
                
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    student_id=student_id if role == 'student' else "",
                    section=section if role == 'student' else ""
                )
                count += 1
            except Exception as e:
                pass
        
        SystemLog.objects.create(
            action="Bulk CSV Upload",
            user=request.user,
            details=f"Successfully uploaded {count} users via CSV."
        )
        messages.success(request, f"Successfully uploaded {count} users.")
    return redirect('admin_dash')

@login_required
@role_required(['admin'])
def admin_post_global_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_role = request.POST.get('target_role', 'all')
        
        GlobalAnnouncement.objects.create(
            title=title,
            content=content,
            created_by=request.user,
            target_role=target_role
        )
        
        SystemLog.objects.create(
            action="Post Global Announcement",
            user=request.user,
            details=f"Posted global alert: '{title}' for {target_role}"
        )
        messages.success(request, "Global announcement posted.")
    return redirect('admin_dash')

@login_required
@role_required(['admin'])
def admin_toggle_maintenance(request):
    setting, created = SystemSetting.objects.get_or_create(key='maintenance_mode', defaults={'value': 'False'})
    new_val = 'True' if setting.value == 'False' else 'False'
    setting.value = new_val
    setting.save()
    
    SystemLog.objects.create(
        action="Toggle Maintenance Mode",
        user=request.user,
        details=f"Maintenance mode set to {new_val}"
    )
    messages.info(request, f"System Maintenance Mode is now {'ON' if new_val == 'True' else 'OFF'}.")
    return redirect('admin_dash')

@login_required
@role_required(['admin'])
def admin_set_term(request):
    if request.method == 'POST':
        term_name = request.POST.get('term_name')
        setting, created = SystemSetting.objects.get_or_create(key='current_term')
        setting.value = term_name
        setting.save()
        
        SystemLog.objects.create(
            action="Change Term/Semester",
            user=request.user,
            details=f"Current term set to '{term_name}'"
        )
        messages.success(request, f"Academic term updated to: {term_name}")
    return redirect('admin_dash')

@login_required
@role_required(['admin'])
def export_raw_scores_csv(request):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ScholarSys_Raw_Scores_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Student ID', 'Section', 'Subject', 'Date', 'Type', 'Score', 'Max Score', 'Remarks'])

    performances = PerformanceMonitoring.objects.all().select_related('student__userprofile').order_by('student__last_name', 'student__first_name', 'date')

    for perf in performances:
        writer.writerow([
            perf.student.userprofile.formatted_name,
            perf.student.userprofile.student_id,
            perf.student.userprofile.section,
            perf.subject,
            perf.date.strftime('%Y-%m-%d'),
            perf.get_performance_type_display(),
            perf.grade,
            perf.max_score,
            perf.remarks
        ])

    SystemLog.objects.create(
        action="Export Scores",
        user=request.user,
        details="Exported full raw scores database to CSV."
    )

    return response


