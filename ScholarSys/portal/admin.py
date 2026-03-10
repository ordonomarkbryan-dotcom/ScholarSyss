from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.forms import ModelChoiceField
from .models import (
    Classroom, UserProfile, PerformanceMonitoring,
    Message, Attendance, GradeAuditLog,
    AcademicRecord, StudentScore, TaskSubmission,
    ClassroomMaterial, Announcement, SystemLog
)

class StudentChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            return obj.userprofile.formatted_name
        except UserProfile.DoesNotExist:
            return obj.get_full_name() or obj.username

class ScoreForm(forms.ModelForm):
    student = StudentChoiceField(queryset=User.objects.filter(userprofile__role='student'))
    
    class Meta:
        model = PerformanceMonitoring
        fields = '__all__'

class AttendanceForm(forms.ModelForm):
    student = StudentChoiceField(queryset=User.objects.filter(userprofile__role='student'))
    
    class Meta:
        model = Attendance
        fields = '__all__'



admin.site.site_header = "ScholarSys+ Administration"
admin.site.site_title = "ScholarSys+ Admin"
admin.site.index_title = "System Management"


# ──────────────────────────────────────────────
# Inline: UserProfile inside User admin
# ──────────────────────────────────────────────
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Profile"
    verbose_name_plural = "Profile Details"
    fieldsets = (
        ('Role & Identity', {
            'fields': ('role', 'student_id', 'section'),
        }),
    )


# ──────────────────────────────────────────────
# Extend the default User admin
# ──────────────────────────────────────────────
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_active')
    list_filter = ('is_active', 'is_staff', 'userprofile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'userprofile__student_id')

    @admin.display(description='Role', ordering='userprofile__role')
    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
        except UserProfile.DoesNotExist:
            return "-"

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ──────────────────────────────────────────────
# Classroom / Courses
# ──────────────────────────────────────────────
@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('course_number', 'name', 'section', 'get_teacher', 'units', 'short_schedule')
    list_filter = ('section', 'units', 'teacher')
    search_fields = ('name', 'course_number', 'section', 'teacher__first_name', 'teacher__last_name')
    ordering = ('course_number',)
    list_per_page = 20

    fieldsets = (
        ('Course Information', {
            'fields': ('course_number', 'name', 'units'),
        }),
        ('Assignment', {
            'fields': ('teacher', 'section'),
        }),
        ('Schedule', {
            'fields': ('schedule',),
            'description': 'Enter one schedule entry per line. Format: Day Time Room (e.g., MWF 9:00-10:00 Rm5)',
        }),
    )

    @admin.display(description='Instructor', ordering='teacher__last_name')
    def get_teacher(self, obj):
        return obj.teacher.userprofile.formatted_name

    @admin.display(description='Schedule')
    def short_schedule(self, obj):
        if obj.schedule:
            lines = obj.schedule.strip().split('\n')
            return lines[0] + (' ...' if len(lines) > 1 else '')
        return "-"


# ──────────────────────────────────────────────
# User Profiles (standalone view)
# ──────────────────────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'student_id', 'section', 'get_attendance')
    list_filter = ('role', 'section')
    search_fields = ('user__username', 'user__email', 'student_id', 'section')
    ordering = ('role', 'user__username')
    list_per_page = 25
    readonly_fields = ('get_attendance',)

    fieldsets = (
        ('Account', {
            'fields': ('user', 'role'),
        }),
        ('Academic Info', {
            'fields': ('student_id', 'section'),
        }),
    )

    @admin.display(description='Attendance %')
    def get_attendance(self, obj):
        pct = obj.attendance_percentage
        if pct >= 90:
            return f"{pct:.1f}% (Good)"
        elif pct >= 80:
            return f"{pct:.1f}% (Warning)"
        else:
            return f"{pct:.1f}% (Critical)"


# ──────────────────────────────────────────────
# Performance / Grades (Base Logic)
# ──────────────────────────────────────────────
class PerformanceBaseAdmin(admin.ModelAdmin):
    form = ScoreForm
    list_display = ('get_student', 'subject', 'performance_type', 'display_grade', 'date', 'short_remarks')
    list_filter = ('performance_type', 'subject', 'date')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'subject')
    ordering = ('-date', 'student__username')
    list_per_page = 30
    date_hierarchy = 'date'

    fieldsets = (
        ('Student & Subject', {
            'fields': ('student', 'subject'),
        }),
        ('Grade Details', {
            'fields': ('performance_type', 'grade', 'max_score', 'task_instructions', 'due_date', 'remarks'),
        }),
    )

    @admin.display(description='Student', ordering='student__username')
    def get_student(self, obj):
        return obj.student.userprofile.formatted_name


    @admin.display(description='Remarks')
    def short_remarks(self, obj):
        if obj.remarks:
            return obj.remarks[:50] + ('...' if len(obj.remarks) > 50 else '')
        return "-"

    @admin.display(description='Score', ordering='grade')
    def display_grade(self, obj):
        from django.utils.html import format_html
        if obj.performance_type in ['assignment', 'project'] and not obj.submissions.exists():
            return format_html('<span style="color: #94a3b8; font-style: italic;">Pending</span>')
        return obj.grade

@admin.register(PerformanceMonitoring)
class AllPerformanceAdmin(PerformanceBaseAdmin):
    pass

@admin.register(AcademicRecord)
class AcademicRecordAdmin(PerformanceBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(performance_type='exam')

@admin.register(StudentScore)
class StudentScoreAdmin(PerformanceBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).exclude(performance_type='exam')


# ──────────────────────────────────────────────
# Messaging
# ──────────────────────────────────────────────
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_sender', 'get_receiver', 'short_content', 'timestamp', 'read_status')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    ordering = ('-timestamp',)
    list_per_page = 30
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Participants', {
            'fields': ('sender', 'receiver'),
        }),
        ('Message', {
            'fields': ('content', 'is_read', 'timestamp'),
        }),
    )

    @admin.display(description='From', ordering='sender__username')
    def get_sender(self, obj):
        return obj.sender.username

    @admin.display(description='To', ordering='receiver__username')
    def get_receiver(self, obj):
        return obj.receiver.username

    @admin.display(description='Content')
    def short_content(self, obj):
        return obj.content[:60] + ('...' if len(obj.content) > 60 else '')

    @admin.display(description='Read', boolean=True)
    def read_status(self, obj):
        return obj.is_read


# ──────────────────────────────────────────────
# Attendance
# ──────────────────────────────────────────────
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceForm
    list_display = ('get_student', 'get_course', 'date', 'status')
    list_filter = ('status', 'classroom', 'date')
    search_fields = ('student__username', 'student__first_name', 'classroom__name', 'classroom__course_number')
    ordering = ('-date', 'student__username')
    list_per_page = 30
    date_hierarchy = 'date'

    fieldsets = (
        ('Student & Course', {
            'fields': ('student', 'classroom'),
        }),
        ('Record', {
            'fields': ('date', 'status'),
        }),
    )

    @admin.display(description='Student', ordering='student__username')
    def get_student(self, obj):
        return obj.student.userprofile.formatted_name

    @admin.display(description='Course', ordering='classroom__course_number')
    def get_course(self, obj):
        return f"{obj.classroom.course_number} - {obj.classroom.name}"


# ──────────────────────────────────────────────
# Audit Logs (Read-Only)
# ──────────────────────────────────────────────
@admin.register(GradeAuditLog)
class GradeAuditLogAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'subject', 'old_grade', 'new_grade', 'get_changed_by', 'timestamp')
    list_filter = ('subject', 'timestamp')
    search_fields = ('student__username', 'subject', 'changed_by__username')
    ordering = ('-timestamp',)
    list_per_page = 30
    date_hierarchy = 'timestamp'
    readonly_fields = ('student', 'subject', 'old_grade', 'new_grade', 'changed_by', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Student', ordering='student__username')
    def get_student(self, obj):
        return obj.student.username

    @admin.display(description='Changed By', ordering='changed_by__username')
    def get_changed_by(self, obj):
        return obj.changed_by.username if obj.changed_by else "System"
@admin.register(ClassroomMaterial)
class ClassroomMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'uploaded_at', 'uploaded_by')
    list_filter = ('classroom', 'uploaded_at')
    search_fields = ('title', 'description', 'classroom__name')
    ordering = ('-uploaded_at',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'created_at', 'is_priority', 'created_by')
    list_filter = ('is_priority', 'classroom', 'created_at')
    search_fields = ('title', 'content', 'classroom__name')
    ordering = ('-created_at',)

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp', 'short_details')
    list_filter = ('action', 'timestamp')
    search_fields = ('action', 'details', 'user__username')
    ordering = ('-timestamp',)
    readonly_fields = ('action', 'details', 'user', 'timestamp')

    @admin.display(description='Details')
    def short_details(self, obj):
        return obj.details[:100] + ('...' if len(obj.details) > 100 else '')

    def has_add_permission(self, request):
        return False
