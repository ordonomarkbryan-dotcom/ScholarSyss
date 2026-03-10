from django.contrib import admin
from django.urls import path, include
from portal import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin Terminal Utilities
    path('admin/create-user/', views.admin_create_user, name='admin_create_user'),
    path('admin/bulk-upload/', views.admin_bulk_upload, name='admin_bulk_upload'),
    path('admin/global-announcement/', views.admin_post_global_announcement, name='admin_global_announcement'),
    path('admin/toggle-maintenance/', views.admin_toggle_maintenance, name='admin_toggle_maintenance'),
    path('admin/set-term/', views.admin_set_term, name='admin_set_term'),
    path('admin/export-scores/', views.export_raw_scores_csv, name='export_raw_scores_csv'),

    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_alias'),
    path('login/student/', views.student_login, name='student_login'),
    path('login/teacher/', views.teacher_login, name='teacher_login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('student/dashboard/', views.student_dash, name='student_dash'),
    path('teacher/dashboard/', views.teacher_dash, name='teacher_dash'),
    path('overview/', views.admin_dash, name='admin_dash'),
    path('classroom/<int:classroom_id>/', views.classroom_detail, name='classroom_detail'),
    path('classroom/<int:classroom_id>/bulk-attendance/', views.bulk_attendance, name='bulk_attendance'),
    path('classroom/<int:classroom_id>/upload-material/', views.upload_material, name='upload_material'),
    path('classroom/<int:classroom_id>/post-announcement/', views.post_announcement, name='post_announcement'),
    path('message/send/', views.send_message, name='send_message'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('grade/add/', views.add_grade, name='add_grade'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('students/', views.student_list_view, name='student_list'),
    path('students/record/<int:student_id>/', views.student_detail_view, name='student_records'),
    path('reports/raw-scores/', views.raw_scores_view, name='raw_scores'),
    path('student/submit/', views.submit_task, name='submit_task'),
    path('submissions/', views.submissions_list, name='submissions_list'),
    path('submissions/review/<int:submission_id>/', views.review_submission, name='review_submission'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='portal/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='portal/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='portal/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='portal/password_reset_complete.html'), name='password_reset_complete'),
    path('grade/calculate/', views.calculate_grade, name='calculate_grade'),
    path('performance/delete/<int:entry_id>/', views.delete_performance, name='delete_performance'),
    path('attendance/delete/<int:entry_id>/', views.delete_attendance, name='delete_attendance'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
