# student/urls.py
from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('teacher/apply/', views.teacher_apply, name='teacher_apply'),

    # Protected pages (login_required)
    path('courses/', views.courses, name='courses'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/complete/', views.lesson_complete, name='lesson_complete'),
    path('lessons/<int:lesson_id>/like/', views.lesson_like, name='lesson_like'),
    path('lessons/<int:lesson_id>/dislike/', views.lesson_dislike, name='lesson_dislike'),
    path('lessons/<int:lesson_id>/comment/', views.lesson_comment, name='lesson_comment'),
    path('teachers/', views.teachers, name='teachers'),
    path('teachers/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:teacher_id>/contact/', views.contact_teacher, name='contact_teacher'),
    path('teachers/<int:teacher_id>/rate/', views.rate_teacher, name='rate_teacher'),
    path('rating/', views.rating, name='rating'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/picture/', views.profile_picture_upload, name='profile_picture_upload'),
    path('test/<int:test_id>/start/', views.start_test, name='start_test'),
path('test/<int:test_id>/submit/', views.submit_test, name='submit_test'),
]