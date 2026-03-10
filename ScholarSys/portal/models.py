from django.db import models
from django.contrib.auth.models import User

class Classroom(models.Model):
    name = models.CharField(max_length=100)
    course_number = models.CharField(max_length=20, blank=True)
    section = models.CharField(max_length=50)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classes')
    units = models.IntegerField(default=3)
    schedule = models.TextField(blank=True) # Multi-line schedule info

    def __str__(self):
        return f"{self.course_number}: {self.name} - {self.section}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, blank=True, db_index=True)
    section = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')])

    @property
    def attendance_percentage(self):
        records = Attendance.objects.filter(student=self.user)
        if not records.exists():
            return 100.0
        present = records.filter(status='present').count()
        return (present / records.count()) * 100

    @property
    def formatted_name(self):
        if self.user.first_name:
            # Handle if first_name is already abbreviated or a full name
            first_initial = self.user.first_name[0].upper()
            if self.user.last_name:
                return f"{first_initial}. {self.user.last_name}"
            return self.user.first_name
        return self.user.username

    def __str__(self):
        return self.user.username

class PerformanceMonitoring(models.Model):
    PERFORMANCE_TYPES = [
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('activity', 'Activity'),
        ('others', 'Others'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performances')
    subject = models.CharField(max_length=100)
    grade = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    remarks = models.TextField(blank=True, help_text="Teacher's feedback after grading.")
    task_instructions = models.TextField(blank=True, help_text="Questions or instructions for the student.")
    performance_type = models.CharField(max_length=20, choices=PERFORMANCE_TYPES, default='others')
    date = models.DateField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True, help_text="Submission deadline.")

    class Meta:
        verbose_name = "All Performance Record"
        verbose_name_plural = "All Performance Records"

class AcademicRecord(PerformanceMonitoring):
    class Meta:
        proxy = True
        verbose_name = "Academic Record (Exam)"
        verbose_name_plural = "Academic Records (Exams)"

class StudentScore(PerformanceMonitoring):
    class Meta:
        proxy = True
        verbose_name = "Student Score (Quiz/Asst)"
        verbose_name_plural = "Student Scores (Quiz/Asst)"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.grade < 0:
            raise ValidationError({'grade': 'Grade cannot be negative.'})
        # Optional: Check if grade exceeds max_score
        # if self.grade > self.max_score:
        #    raise ValidationError({'grade': f'Grade cannot exceed the maximum score ({self.max_score}).'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.username} - {self.subject} ({self.performance_type})"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"

class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')])

    def __str__(self):
        return f"{self.student.username} - {self.classroom.name} - {self.date}"

class GradeAuditLog(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    old_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    new_grade = models.DecimalField(max_digits=5, decimal_places=2)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grade_changes')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grade change for {self.student.username} by {self.changed_by.username} at {self.timestamp}"

class TaskSubmission(models.Model):
    TASK_TYPES = [
        ('assignment', 'Assignment'),
        ('project', 'Project'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    performance_record = models.ForeignKey(PerformanceMonitoring, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    title = models.CharField(max_length=200) # Name of the specific assignment/project
    content = models.TextField(help_text="Submit links, text, or a summary of your work.", blank=True)
    submission_file = models.FileField(upload_to='submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    teacher_remarks = models.TextField(blank=True, help_text="Specific feedback for this submission.")

    def __str__(self):
        return f"{self.student.username} - {self.title} ({self.task_type})"

class ClassroomMaterial(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='materials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.title} - {self.classroom.name}"

class Announcement(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_priority = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.classroom.course_number})"

class SystemLog(models.Model):
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.username if self.user else 'System'} at {self.timestamp}"

class GlobalAnnouncement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    target_role = models.CharField(max_length=20, choices=[('all', 'All Users'), ('student', 'Students Only'), ('teacher', 'Teachers Only')], default='all')

    def __str__(self):
        return self.title

class SystemSetting(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
