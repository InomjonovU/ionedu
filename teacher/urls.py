from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    # Authentication
    path('login/', views.teacher_login, name='login'),
    path('logout/', views.teacher_logout, name='logout'),

    # Dashboard
    path('', views.teacher_dashboard, name='dashboard'),
    path('dashboard/', views.teacher_dashboard, name='dashboard'),

    # Courses
    path('courses/', views.teacher_courses, name='teacher_courses'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),

    # Lessons
    path('courses/<int:course_id>/lessons/add/', views.add_lesson, name='add_lesson'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/edit/', views.edit_lesson, name='edit_lesson'),
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),

    # Tests
    path('courses/<int:course_id>/tests/add/', views.add_test, name='add_test'),
    path('tests/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('tests/<int:test_id>/delete/', views.delete_test, name='delete_test'),

    # Students
    path('students/', views.teacher_students, name='teacher_students'),
    path('students/<int:enrollment_id>/remove/', views.remove_student, name='remove_student'),

    # Settings
    path('settings/', views.teacher_settings, name='teacher_settings'),
    path('settings/profile/update/', views.update_profile, name='update_profile'),
    path('settings/notifications/update/', views.update_notifications, name='update_notifications'),
    path('settings/password/change/', views.change_password, name='change_password'),
    path('settings/account/delete/', views.delete_account, name='delete_account'),
]