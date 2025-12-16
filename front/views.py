# student/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import *

# Authentication Views
def login_view(request):
    """Login sahifasi"""
    if request.user.is_authenticated:
        return redirect('student:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Muvaffaqiyatli kirdingiz!')
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect('student:home')
        else:
            messages.error(request, 'Foydalanuvchi nomi yoki parol xato!')

    return render(request, 'student/login.html')


def register_view(request):
    """Ro'yxatdan o'tish sahifasi"""
    if request.user.is_authenticated:
        return redirect('student:home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        school = request.POST.get('school')
        grade = request.POST.get('grade')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validations
        if password != password2:
            messages.error(request, 'Parollar mos kelmadi!')
            return render(request, 'student/register.html')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Bu foydalanuvchi nomi band!')
            return render(request, 'student/register.html')

        if CustomUser.objects.filter(phone_number=phone).exists():
            messages.error(request, 'Bu telefon raqam allaqachon ro\'yxatdan o\'tgan!')
            return render(request, 'student/register.html')

        # Create user
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            user_type='student'
        )

        # You might want to add school and grade to user profile
        # For now, we'll just save basic info

        messages.success(request, 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz! Endi tizimga kiring.')
        return redirect('student:login')

    return render(request, 'student/register.html')


def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'Tizimdan chiqdingiz!')
    return redirect('student:home')


# Public Pages
def home(request):
    """Bosh sahifa"""
    return render(request, 'student/index.html')


def about(request):
    """Biz haqimizda"""
    return render(request, 'student/about.html')


def contact(request):
    """Bog'lanish sahifasi"""
    contact_success = request.session.pop('contact_success', False)
    teacher_success = request.session.pop('teacher_success', False)

    context = {
        'contact_success': contact_success,
        'teacher_success': teacher_success,
    }

    return render(request, 'student/contact.html', context)


def contact_submit(request):
    """Contact form submission"""
    from .models import ContactMessage

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject', '')
        content = request.POST.get('content')

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            content=content,
            user=request.user if request.user.is_authenticated else None
        )

        request.session['contact_success'] = True
        return redirect('student:contact')

    return redirect('student:contact')


def teacher_apply(request):
    """Teacher application submission"""
    from .models import RequestToBecomeTeacher

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        experience_years = request.POST.get('experience_years')
        specialization = request.POST.get('specialization')
        content = request.POST.get('content')

        RequestToBecomeTeacher.objects.create(
            user=request.user if request.user.is_authenticated else None,
            f_name=first_name,
            l_name=last_name,
            phone_number=phone_number,
            experience_years=experience_years or 0,
            specialization=specialization,
            content=content,
            status='pending'
        )

        request.session['teacher_success'] = True
        return redirect('student:contact')

    return redirect('student:contact')


# Protected Pages - Login Required
@login_required(login_url='student:login')
def courses(request):
    """Kurslar sahifasi - faqat ochiq kurslar"""
    # Get filters from request
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    grade = request.GET.get('grade', '')
    page_number = request.GET.get('page', 1)

    # Base queryset - only OPEN courses
    courses_list = Course.objects.filter(type=Course.TYPE_OPEN).select_related('teacher', 'category').prefetch_related('students', 'lessons')

    # Apply filters
    if search_query:
        courses_list = courses_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__icontains=search_query)
        )

    if category_id:
        courses_list = courses_list.filter(category_id=category_id)

    if grade:
        courses_list = courses_list.filter(grade=grade)

    # Annotate with counts
    courses_list = courses_list.annotate(
        students_count=Count('students', distinct=True),
        lessons_count=Count('lessons', distinct=True)
    )

    # Pagination
    paginator = Paginator(courses_list, 9)  # 9 courses per page
    courses_page = paginator.get_page(page_number)

    # Get all categories for filter
    categories = CourseCategory.objects.all()

    # AJAX request - return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        courses_data = []
        for course in courses_page:
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'subject': course.subject,
                'grade': course.grade,
                'background_image': course.background_image.url if course.background_image else None,
                'teacher': {
                    'name': course.teacher.get_full_name(),
                    'initials': f"{course.teacher.first_name[0]}{course.teacher.last_name[0]}" if course.teacher.first_name and course.teacher.last_name else course.teacher.username[0:2].upper()
                },
                'students_count': course.students_count,
                'lessons_count': course.lessons_count
            })

        return JsonResponse({
            'courses': courses_data,
            'has_more': courses_page.has_next()
        })

    # Normal request - render template
    context = {
        'courses': courses_page,
        'categories': categories,
        'has_more': courses_page.has_next(),
        'search_query': search_query,
        'selected_category': category_id,
        'selected_grade': grade,
    }

    return render(request, 'student/courses.html', context)


@login_required(login_url='student:login')
def course_detail(request, course_id):
    """Kurs detallari"""
    course = get_object_or_404(Course, id=course_id, type=Course.TYPE_OPEN)

    # Get course lessons
    lessons = Lesson.objects.filter(course=course).order_by('order')

    # Check if user is enrolled
    is_enrolled = CourseStudent.objects.filter(user=request.user, course=course).exists()

    # Get statistics
    students_count = CourseStudent.objects.filter(course=course).count()
    lessons_count = lessons.count()

    # Get reviews if available
    try:
        from .models import Review
        reviews = Review.objects.filter(course=course).select_related('user').order_by('-created_at')[:5]
    except:
        reviews = []

    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'students_count': students_count,
        'lessons_count': lessons_count,
        'reviews': reviews,
    }

    return render(request, 'student/course_detail.html', context)


@login_required(login_url='student:login')
def course_enroll(request, course_id):
    """Kursga yozilish"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id, type=Course.TYPE_OPEN)

        # Check if already enrolled
        if not CourseStudent.objects.filter(user=request.user, course=course).exists():
            CourseStudent.objects.create(
                user=request.user,
                course=course
            )
            messages.success(request, f'{course.title} kursiga muvaffaqiyatli yozildingiz!')
        else:
            messages.info(request, 'Siz allaqachon bu kursga yozilgansiz.')

        return redirect('student:course_detail', course_id=course_id)

    return redirect('student:courses')


@login_required(login_url='student:login')
def teachers(request):
    """O'qituvchilar sahifasi"""
    from django.db.models import Avg

    # Get all teachers with courses count
    teachers_list = CustomUser.objects.filter(
        user_type='teacher'
    ).select_related().prefetch_related('courses').order_by('-rating')

    # Get unique specializations for filter
    specializations = CustomUser.objects.filter(
        user_type='teacher',
        specialization__isnull=False
    ).exclude(specialization='').values_list('specialization', flat=True).distinct()

    # Statistics
    total_teachers = teachers_list.count()
    total_courses = Course.objects.filter(teacher__user_type='teacher').count()
    avg_rating = teachers_list.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_experience = teachers_list.aggregate(avg=Avg('experience_years'))['avg'] or 0

    context = {
        'teachers': teachers_list,
        'specializations': specializations,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'avg_rating': avg_rating,
        'avg_experience': avg_experience,
    }

    return render(request, 'student/teachers.html', context)


# FIXED teacher_detail VIEW
# Replace in your views.py file

@login_required(login_url='student:login')
def teacher_detail(request, teacher_id):
    """O'qituvchi profili"""
    teacher = get_object_or_404(CustomUser, id=teacher_id, user_type='teacher')

    # Get teacher's courses - FIXED: use 'students' and 'lessons' (lowercase)
    courses = Course.objects.filter(
        teacher=teacher,
        type=Course.TYPE_OPEN
    ).annotate(
        students_count=Count('students'),  # FIX: was 'coursestudent'
        lessons_count=Count('lessons')      # FIX: was 'lesson'
    )

    # Statistics
    courses_count = courses.count()
    students_count = CourseStudent.objects.filter(course__teacher=teacher).values('user').distinct().count()
    lessons_count = Lesson.objects.filter(course__teacher=teacher).count()

    # Get teacher reviews - ADDED
    try:
        reviews = TeacherRating.objects.filter(teacher=teacher).select_related('user').order_by('-created_at')
    except:
        reviews = []

    context = {
        'teacher': teacher,
        'courses': courses,
        'courses_count': courses_count,
        'students_count': students_count,
        'lessons_count': lessons_count,
        'reviews': reviews,  # ADDED for template
    }

    return render(request, 'student/teacher_detail.html', context)


# BONUS: Add these views for teacher profile functionality

@login_required(login_url='student:login')
def rate_teacher(request, teacher_id):
    """O'qituvchini baholash"""
    if request.method == 'POST':
        teacher = get_object_or_404(CustomUser, id=teacher_id, user_type='teacher')
        rating_value = request.POST.get('rating')
        review_text = request.POST.get('review', '')

        # Create or update rating
        rating, created = TeacherRating.objects.update_or_create(
            user=request.user,
            teacher=teacher,
            defaults={
                'rating': int(rating_value),
                'review': review_text
            }
        )

        # Update teacher's average rating
        from django.db.models import Avg
        avg_rating = TeacherRating.objects.filter(teacher=teacher).aggregate(Avg('rating'))['rating__avg']
        total_ratings = TeacherRating.objects.filter(teacher=teacher).count()

        teacher.rating = round(avg_rating, 1) if avg_rating else 0
        teacher.total_ratings = total_ratings
        teacher.save()

        messages.success(request, 'Baholash muvaffaqiyatli saqlandi!')
        return redirect('student:teacher_detail', teacher_id=teacher_id)

    return redirect('student:teachers')


@login_required(login_url='student:login')
def contact_teacher(request, teacher_id):
    """O'qituvchiga xabar yuborish"""
    if request.method == 'POST':
        teacher = get_object_or_404(CustomUser, id=teacher_id, user_type='teacher')
        message = request.POST.get('message')

        ContactToTeacher.objects.create(
            user=request.user,
            teacher=teacher,
            message=message
        )

        messages.success(request, 'Xabar muvaffaqiyatli yuborildi!')
        return redirect('student:teacher_detail', teacher_id=teacher_id)

    return redirect('student:teachers')

# TEST SYSTEM VIEWS - Add to your views.py

@login_required(login_url='student:login')
def lesson_detail(request, lesson_id):
    """Dars tafsilotlari - test bilan"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Check enrollment
    is_enrolled = CourseStudent.objects.filter(user=request.user, course=course).exists()
    if not is_enrolled:
        messages.error(request, 'Avval kursga yoziling!')
        return redirect('student:course_detail', course_id=course.id)

    # Get all lessons
    all_lessons = Lesson.objects.filter(course=course).order_by('order')

    # Next lesson
    next_lesson = all_lessons.filter(order__gt=lesson.order).first()

    # Check if this is last lesson
    is_last_lesson = not next_lesson

    # Get course test
    course_test = None
    test_result = None
    if is_last_lesson:
        try:
            course_test = CourseTest.objects.filter(course=course).prefetch_related('questions__answers').first()

            # Check if user already took the test
            if course_test:
                try:
                    student_test = StudentTest.objects.get(course_test=course_test, user=request.user)
                    if student_test.completed:
                        # Calculate details for result display
                        test_result = {
                            'score': student_test.score,
                            'correct_answers': int(student_test.score / 100 * course_test.questions.count()),
                            'wrong_answers': course_test.questions.count() - int(student_test.score / 100 * course_test.questions.count()),
                            'total_questions': course_test.questions.count(),
                        }
                except StudentTest.DoesNotExist:
                    pass
        except:
            pass

    # Like/dislike stats
    likes_count = LessonLikeDislike.objects.filter(lesson=lesson, is_like=True).count()
    dislikes_count = LessonLikeDislike.objects.filter(lesson=lesson, is_like=False).count()

    # User reaction
    user_reaction = None
    try:
        user_like = LessonLikeDislike.objects.get(user=request.user, lesson=lesson)
        user_reaction = 'like' if user_like.is_like else 'dislike'
    except LessonLikeDislike.DoesNotExist:
        pass

    # Comments
    comments = Comment.objects.filter(course=course).select_related('user').order_by('-created_at')

    # Calculate course progress (simplified - just based on number of lessons viewed)
    total_lessons = all_lessons.count()
    current_lesson_index = list(all_lessons).index(lesson) + 1
    course_progress = int((current_lesson_index / total_lessons * 100)) if total_lessons > 0 else 0

    context = {
        'lesson': lesson,
        'course': course,
        'all_lessons': all_lessons,
        'next_lesson': next_lesson,
        'is_last_lesson': is_last_lesson,
        'course_test': course_test,
        'test_result': test_result,
        'course_progress': course_progress,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'user_reaction': user_reaction,
        'comments': comments,
    }

    return render(request, 'student/lesson_detail.html', context)


@login_required(login_url='student:login')
def start_test(request, test_id):
    """Start a test"""
    if request.method == 'POST':
        course_test = get_object_or_404(CourseTest, id=test_id)

        # Check if user already completed the test
        student_test = StudentTest.objects.filter(
            course_test=course_test,
            user=request.user
        ).first()

        if student_test and student_test.completed:
            messages.info(request, 'Siz bu testni allaqachon topshirgansiz!')
            # Redirect back to last lesson
            last_lesson = Lesson.objects.filter(course=course_test.course).order_by('-order').first()
            if last_lesson:
                return redirect('student:lesson_detail', lesson_id=last_lesson.id)
            return redirect('student:course_detail', course_id=course_test.course.id)

        # Get or create test attempt (incomplete)
        student_test, created = StudentTest.objects.get_or_create(
            course_test=course_test,
            user=request.user,
            defaults={'completed': False}
        )

        # If already exists but not completed, allow retake
        if not created and not student_test.completed:
            student_test.score = None
            student_test.save()

        return render(request, 'student/test_take.html', {'test': course_test})

    return redirect('student:courses')


@login_required(login_url='student:login')
def submit_test(request, test_id):
    """Submit test and calculate score with star rewards"""
    if request.method == 'POST':
        course_test = get_object_or_404(CourseTest, id=test_id)

        # Get or create student test
        student_test, created = StudentTest.objects.get_or_create(
            course_test=course_test,
            user=request.user,
            defaults={'completed': False}
        )

        if student_test.completed:
            messages.info(request, 'Siz bu testni allaqachon topshirgansiz!')
            last_lesson = Lesson.objects.filter(course=course_test.course).order_by('-order').first()
            return redirect('student:lesson_detail', lesson_id=last_lesson.id)

        # Calculate score
        total_questions = course_test.questions.count()
        correct_answers = 0

        for question in course_test.questions.all():
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                selected_answer = TestAnswer.objects.filter(id=selected_answer_id).first()
                if selected_answer and selected_answer.is_correct:
                    correct_answers += 1

        # Calculate percentage
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        # Award stars based on score (NO COINS!)
        stars_earned = 0
        if score >= 90:
            stars_earned = 5
        elif score >= 80:
            stars_earned = 4
        elif score >= 70:
            stars_earned = 3
        elif score >= 60:
            stars_earned = 2
        elif score >= 50:
            stars_earned = 1

        # Update user stars (NO COINS!)
        if stars_earned > 0:
            request.user.stars += stars_earned
            request.user.save()

        # Save test result
        student_test.score = score
        student_test.completed = True
        student_test.save()

        if stars_earned > 0:
            messages.success(request, f'Test yakunlandi! +{stars_earned} yulduz ⭐')
        else:
            messages.info(request, 'Test yakunlandi! Qayta urinib ko\'ring.')

        # Redirect to last lesson to show results
        last_lesson = Lesson.objects.filter(course=course_test.course).order_by('-order').first()
        if last_lesson:
            return redirect('student:lesson_detail', lesson_id=last_lesson.id)

        return redirect('student:course_detail', course_id=course_test.course.id)

    return redirect('student:courses')


# ALSO REMOVE COINS/STARS FROM lesson_complete:

@login_required(login_url='student:login')
def lesson_complete(request, lesson_id):
    """Darsni yakunlash - NO REWARDS"""
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Just mark as completed, NO coins or stars
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'is_completed': True}
        )

        if created or not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

            messages.success(request, 'Dars yakunlandi!')

        return redirect('student:lesson_detail', lesson_id=lesson_id)

    return redirect('student:courses')

@login_required(login_url='student:login')
def lesson_like(request, lesson_id):
    """Darsga like"""
    if request.method == 'POST':
        from .models import LessonLikeDislike
        lesson = get_object_or_404(Lesson, id=lesson_id)

        like_dislike, created = LessonLikeDislike.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'is_like': True}
        )

        if not created:
            if like_dislike.is_like:
                # Remove like
                like_dislike.delete()
            else:
                # Change from dislike to like
                like_dislike.is_like = True
                like_dislike.save()

        return redirect('student:lesson_detail', lesson_id=lesson_id)

    return redirect('student:courses')


@login_required(login_url='student:login')
def lesson_dislike(request, lesson_id):
    """Darsga dislike"""
    if request.method == 'POST':
        from .models import LessonLikeDislike
        lesson = get_object_or_404(Lesson, id=lesson_id)

        like_dislike, created = LessonLikeDislike.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'is_like': False}
        )

        if not created:
            if not like_dislike.is_like:
                # Remove dislike
                like_dislike.delete()
            else:
                # Change from like to dislike
                like_dislike.is_like = False
                like_dislike.save()

        return redirect('student:lesson_detail', lesson_id=lesson_id)

    return redirect('student:courses')


@login_required(login_url='student:login')
def lesson_comment(request, lesson_id):
    """Darsga izoh qoldirish"""
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        content = request.POST.get('content')

        if content:
            Comment.objects.create(
                user=request.user,
                course=lesson.course,
                content=content
            )
            messages.success(request, 'Izoh qo\'shildi!')

        return redirect('student:lesson_detail', lesson_id=lesson_id)

    return redirect('student:courses')


@login_required(login_url='student:login')
def rating(request):
    """Reyting sahifasi"""
    # Top students by coins
    top_students = CustomUser.objects.filter(user_type='student').order_by('-coins', '-stars')[:50]

    context = {
        'top_students': top_students,
    }

    return render(request, 'student/rating.html', context)


@login_required(login_url='student:login')
def profile(request):
    """Profil sahifasi"""
    user = request.user

    # Get user's enrolled courses
    enrolled_courses = CourseStudent.objects.filter(user=user).select_related('course', 'course__teacher')

    context = {
        'user': user,
        'enrolled_courses': enrolled_courses,
    }

    return render(request, 'student/profile.html', context)


@login_required(login_url='student:login')
def profile_update(request):
    """Profilni yangilash"""
    if request.method == 'POST':
        user = request.user

        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.telegram_username = request.POST.get('telegram_username', '')
        user.bio = request.POST.get('bio', '')

        # Date of birth
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            user.date_of_birth = date_of_birth

        user.save()
        messages.success(request, 'Profil muvaffaqiyatli yangilandi!')
        return redirect('student:profile')

    return redirect('student:profile')


@login_required(login_url='student:login')
def profile_picture_upload(request):
    """Profil rasmini yuklash"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        user = request.user
        user.profile_picture = request.FILES['profile_picture']
        user.save()

        return JsonResponse({'success': True, 'message': 'Rasm muvaffaqiyatli yuklandi!'})

    return JsonResponse({'success': False, 'message': 'Xatolik yuz berdi!'})