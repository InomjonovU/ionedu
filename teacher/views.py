from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from front.models import *
from django.contrib.auth import authenticate, login, logout
from functools import wraps

# Custom decorator to check if user is teacher
def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('teacher:login')
        if request.user.user_type != UserType.TEACHER:
            messages.error(request, 'Faqat o\'qituvchilar kirishi mumkin!')
            logout(request)
            return redirect('teacher:login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Authentication views
def teacher_login(request):
    if request.user.is_authenticated:
        if request.user.user_type == UserType.TEACHER:
            return redirect('teacher:dashboard')
        else:
            logout(request)
            messages.error(request, 'Faqat o\'qituvchilar kirishi mumkin!')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.user_type == UserType.TEACHER:
                login(request, user)
                messages.success(request, 'Xush kelibsiz!')
                return redirect('teacher:dashboard')
            else:
                messages.error(request, 'Faqat o\'qituvchilar kirishi mumkin!')
        else:
            messages.error(request, 'Login yoki parol noto\'g\'ri!')

    return render(request, 'teacher/login.html')

def teacher_register(request):
    if request.user.is_authenticated:
        return redirect('teacher:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Parollar mos kelmadi!')
            return render(request, 'teacher/register.html')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Bu username band!')
            return render(request, 'teacher/register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Bu email allaqachon ro\'yxatdan o\'tgan!')
            return render(request, 'teacher/register.html')

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            user_type=UserType.TEACHER
        )

        login(request, user)
        messages.success(request, 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!')
        return redirect('teacher:dashboard')

    return render(request, 'teacher/register.html')

def teacher_logout(request):
    logout(request)
    messages.success(request, 'Tizimdan chiqdingiz!')
    return redirect('teacher:login')

# Dashboard
@teacher_required
def teacher_dashboard(request):
    courses = Course.objects.filter(teacher=request.user)
    total_courses = courses.count()
    total_students = CourseStudent.objects.filter(course__teacher=request.user).count()
    total_lessons = Lesson.objects.filter(course__teacher=request.user).count()
    recent_courses = courses[:5]

    context = {
        'total_courses': total_courses,
        'total_students': total_students,
        'total_lessons': total_lessons,
        'recent_courses': recent_courses,
    }
    return render(request, 'teacher/index.html', context)

# Courses
@teacher_required
def teacher_courses(request):
    courses = Course.objects.filter(teacher=request.user).prefetch_related('students', 'lessons')
    return render(request, 'teacher/courses.html', {'courses': courses})

@teacher_required
def create_course(request):
    if request.method == 'POST':
        course = Course()
        course.title = request.POST.get('title')
        course.subject = request.POST.get('subject', '')
        course.grade = request.POST.get('grade', '')
        course.description = request.POST.get('description')
        course.type = request.POST.get('type', 'open')
        course.teacher = request.user

        category_id = request.POST.get('category')
        if category_id:
            course.category_id = category_id

        if 'background_image' in request.FILES:
            course.background_image = request.FILES['background_image']

        course.save()
        messages.success(request, 'Kurs yaratildi!')
        return redirect('teacher:course_detail', course_id=course.id)

    categories = CourseCategory.objects.all()
    return render(request, 'teacher/create_course.html', {'categories': categories})

@teacher_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    return render(request, 'teacher/course_detail.html', {'course': course})

@teacher_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.subject = request.POST.get('subject', '')
        course.grade = request.POST.get('grade', '')
        course.description = request.POST.get('description')
        course.type = request.POST.get('type', 'open')

        category_id = request.POST.get('category')
        if category_id:
            course.category_id = category_id

        if request.POST.get('remove_image') == 'true' and course.background_image:
            course.background_image.delete()
            course.background_image = None

        if 'background_image' in request.FILES:
            if course.background_image:
                course.background_image.delete()
            course.background_image = request.FILES['background_image']

        course.save()
        messages.success(request, 'Kurs yangilandi!')
        return redirect('teacher:course_detail', course_id=course.id)

    categories = CourseCategory.objects.all()
    return render(request, 'teacher/edit_course.html', {'course': course, 'categories': categories})

@teacher_required
def delete_course(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        course.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

# Lessons
@teacher_required
def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == 'POST':
        try:
            lesson = Lesson()
            lesson.course = course
            lesson.title = request.POST.get('title')
            lesson.order = request.POST.get('order', course.lessons.count() + 1)
            lesson.content = request.POST.get('content', '')

            if 'video' in request.FILES:
                video = request.FILES['video']
                import os
                from django.conf import settings

                video_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
                os.makedirs(video_dir, exist_ok=True)

                video_path = os.path.join(video_dir, video.name)
                with open(video_path, 'wb+') as destination:
                    for chunk in video.chunks():
                        destination.write(chunk)

                lesson.video_url = f'/media/videos/{video.name}'

            if 'presentation' in request.FILES:
                lesson.presentation_file = request.FILES['presentation']

            lesson.save()
            messages.success(request, 'Dars qo\'shildi!')
            return redirect('teacher:course_detail', course_id=course.id)

        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')

    next_order = course.lessons.count() + 1
    return render(request, 'teacher/add_lesson.html', {'course': course, 'next_order': next_order})

@teacher_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)

    if request.method == 'POST':
        lesson.title = request.POST.get('title')
        lesson.order = request.POST.get('order', lesson.order)
        lesson.content = request.POST.get('content', '')

        if request.POST.get('remove_video') == 'true':
            lesson.video_url = None

        if 'video' in request.FILES:
            video = request.FILES['video']
            import os
            from django.conf import settings

            video_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
            os.makedirs(video_dir, exist_ok=True)

            video_path = os.path.join(video_dir, video.name)
            with open(video_path, 'wb+') as destination:
                for chunk in video.chunks():
                    destination.write(chunk)

            lesson.video_url = f'/media/videos/{video.name}'

        if request.POST.get('remove_presentation') == 'true' and lesson.presentation_file:
            lesson.presentation_file.delete()
            lesson.presentation_file = None

        if 'presentation' in request.FILES:
            if lesson.presentation_file:
                lesson.presentation_file.delete()
            lesson.presentation_file = request.FILES['presentation']

        lesson.save()
        messages.success(request, 'Dars yangilandi!')
        return redirect('teacher:course_detail', course_id=lesson.course.id)

    return render(request, 'teacher/edit_lesson.html', {'lesson': lesson})

@teacher_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
    return render(request, 'teacher/lesson_detail.html', {'lesson': lesson})

@teacher_required
def delete_lesson(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
        lesson.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

# Tests
@teacher_required
def add_test(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)

    if request.method == 'POST':
        try:
            test = CourseTest()
            test.course = course
            test.title = request.POST.get('title')
            test.description = request.POST.get('description', '')

            time_limit = request.POST.get('time_limit_minutes')
            if time_limit:
                test.time_limit_minutes = int(time_limit)

            test.passing_score = float(request.POST.get('passing_score', 50))
            test.save()

            question_nums = set()
            for key in request.POST.keys():
                if key.startswith('question_text_'):
                    question_nums.add(key.split('_')[-1])

            for order, q_num in enumerate(sorted(question_nums), start=1):
                question_text = request.POST.get(f'question_text_{q_num}')
                if not question_text:
                    continue

                question = TestQuestion()
                question.test = test
                question.order = order
                question.question_text = question_text
                question.save()

                correct_answers = request.POST.getlist(f'correct_answer_{q_num}')

                answer_order = 1
                for key in request.POST.keys():
                    if key.startswith(f'answer_{q_num}_'):
                        answer_text = request.POST.get(key)
                        if answer_text:
                            answer_num = key.split('_')[-1]

                            answer = TestAnswer()
                            answer.question = question
                            answer.order = answer_order
                            answer.answer_text = answer_text
                            answer.is_correct = answer_num in correct_answers
                            answer.save()

                            answer_order += 1

            messages.success(request, 'Test yaratildi!')
            return redirect('teacher:course_detail', course_id=course.id)

        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')

    return render(request, 'teacher/add_test.html', {'course': course})

@teacher_required
def edit_test(request, test_id):
    test = get_object_or_404(CourseTest, id=test_id, course__teacher=request.user)

    if request.method == 'POST':
        try:
            test.title = request.POST.get('title')
            test.description = request.POST.get('description', '')

            time_limit = request.POST.get('time_limit_minutes')
            test.time_limit_minutes = int(time_limit) if time_limit else None

            test.passing_score = float(request.POST.get('passing_score', 50))
            test.save()

            deleted_questions = request.POST.getlist('deleted_questions')
            if deleted_questions:
                TestQuestion.objects.filter(id__in=deleted_questions).delete()

            deleted_answers = request.POST.getlist('deleted_answers')
            if deleted_answers:
                TestAnswer.objects.filter(id__in=deleted_answers).delete()

            question_nums = set()
            for key in request.POST.keys():
                if key.startswith('question_text_'):
                    question_nums.add(key.split('_')[-1])

            for order, q_num in enumerate(sorted(question_nums), start=1):
                question_text = request.POST.get(f'question_text_{q_num}')
                if not question_text:
                    continue

                question_id = request.POST.get(f'question_id_{q_num}')

                if question_id:
                    question = TestQuestion.objects.get(id=question_id)
                    question.question_text = question_text
                    question.order = order
                    question.save()
                else:
                    question = TestQuestion()
                    question.test = test
                    question.order = order
                    question.question_text = question_text
                    question.save()

                correct_answers = request.POST.getlist(f'correct_answer_{q_num}')

                answer_order = 1
                for key in request.POST.keys():
                    if key.startswith(f'answer_{q_num}_'):
                        answer_text = request.POST.get(key)
                        if answer_text:
                            answer_num = key.split('_')[-1]
                            answer_id = request.POST.get(f'answer_id_{q_num}_{answer_num}')

                            if answer_id:
                                answer = TestAnswer.objects.get(id=answer_id)
                                answer.answer_text = answer_text
                                answer.order = answer_order
                                answer.is_correct = answer_num in correct_answers
                                answer.save()
                            else:
                                answer = TestAnswer()
                                answer.question = question
                                answer.order = answer_order
                                answer.answer_text = answer_text
                                answer.is_correct = answer_num in correct_answers
                                answer.save()

                            answer_order += 1

            messages.success(request, 'Test yangilandi!')
            return redirect('teacher:course_detail', course_id=test.course.id)

        except Exception as e:
            messages.error(request, f'Xatolik: {str(e)}')

    return render(request, 'teacher/edit_test.html', {'test': test})

@teacher_required
def delete_test(request, test_id):
    if request.method == 'POST':
        test = get_object_or_404(CourseTest, id=test_id, course__teacher=request.user)
        test.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=404)

# Students
@teacher_required
def teacher_students(request):
    courses = Course.objects.filter(teacher=request.user)
    students = CourseStudent.objects.filter(course__teacher=request.user).select_related('user', 'course')
    total_students = students.values('user').distinct().count()

    return render(request, 'teacher/students.html', {
        'courses': courses,
        'students': students,
        'total_students': total_students,
    })

@teacher_required
def remove_student(request, enrollment_id):
    if request.method == 'POST':
        enrollment = get_object_or_404(CourseStudent, id=enrollment_id, course__teacher=request.user)
        enrollment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

# Settings
@teacher_required
def teacher_settings(request):
    return render(request, 'teacher/settings.html')

@teacher_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.bio = request.POST.get('bio', '')
        user.telegram_username = request.POST.get('telegram_username', '')

        dob = request.POST.get('date_of_birth')
        if dob:
            user.date_of_birth = dob

        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']

        user.save()
        messages.success(request, 'Profil yangilandi!')

    return redirect('teacher:teacher_settings')

@teacher_required
def update_notifications(request):
    if request.method == 'POST':
        messages.success(request, 'Sozlamalar saqlandi!')
    return redirect('teacher:teacher_settings')

@teacher_required
def change_password(request):
    messages.success(request, 'Parol o\'zgartirildi!')
    return redirect('teacher:teacher_settings')

@teacher_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('teacher:login')
    return redirect('teacher:teacher_settings')