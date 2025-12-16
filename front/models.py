from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class UserLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    JUNIOR = 'junior', 'Junior'
    MIDDLE = 'middle', 'Middle'
    SENIOR = 'senior', 'Senior'


class UserType(models.TextChoices):
    STUDENT = 'student', 'Student'
    TEACHER = 'teacher', 'Teacher'


class CustomUser(AbstractUser):
    """Foydalanuvchi model (Custom)"""

    user_type = models.CharField(max_length=10, choices=UserType.choices, default=UserType.STUDENT)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    telegram_username = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Gamification / progress
    coins = models.PositiveIntegerField(default=0)
    stars = models.PositiveSmallIntegerField(default=0)
    level = models.CharField(max_length=15, choices=UserLevel.choices, default=UserLevel.BEGINNER)

    # Teacher-specific fields
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    total_ratings = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user_type"]),
            models.Index(fields=["level"]),
            models.Index(fields=["rating"])
        ]
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return self.get_full_name() or self.username


class CourseCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Kurs toifasi"
        verbose_name_plural = "Kurs toifalari"

    def __str__(self):
        return self.name


class Course(models.Model):
    TYPE_OPEN = 'open'
    TYPE_CLOSED = 'closed'
    TYPE_CHOICES = [(TYPE_OPEN, 'Open'), (TYPE_CLOSED, 'Closed')]

    background_image = models.ImageField(upload_to='course_backgrounds/', blank=True, null=True)
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, null=True, blank=True)
    grade = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_OPEN)

    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='courses')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['teacher']), models.Index(fields=['type'])]
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    order = models.PositiveIntegerField(default=0, help_text='Order of lesson inside the course')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    presentation_file = models.FileField(upload_to='lesson_presentations/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = (('course', 'order'),)
        verbose_name = "Dars"
        verbose_name_plural = "Darslar"

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class LessonProgress(models.Model):
    """Track student progress on lessons"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
        indexes = [models.Index(fields=['user', 'lesson'])]
        verbose_name = "Dars jarayoni"
        verbose_name_plural = "Dars jarayonlari"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Izoh"
        verbose_name_plural = "Izohlar"

    def __str__(self):
        return f"{self.user.username} — {self.course.title}"


class RequestToJoinCourse(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='course_requests')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='join_requests')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'course'),)
        verbose_name = "Kursga qo'shilish so'rovi"
        verbose_name_plural = "Kursga qo'shilish so'rovlari"

    def __str__(self):
        return f"{self.user.username} → {self.course.title}"


class RequestToBecomeTeacher(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Kutilmoqda'),
        (STATUS_APPROVED, 'Tasdiqlangan'),
        (STATUS_REJECTED, 'Rad etilgan')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teacher_requests')
    f_name = models.CharField(max_length=255)
    l_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20)
    content = models.TextField(blank=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        verbose_name = "O'qituvchi bo'lish so'rovi"
        verbose_name_plural = "O'qituvchi bo'lish so'rovlari"

    def __str__(self):
        return f"{self.user.username} — O'qituvchi bo'lish"


class CourseTest(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    time_limit_minutes = models.PositiveIntegerField(blank=True, null=True)
    passing_score = models.FloatField(default=50.0)

    class Meta:
        verbose_name = "Kurs testi"
        verbose_name_plural = "Kurs testlari"

    def __str__(self):
        return self.title


class TestQuestion(models.Model):
    test = models.ForeignKey(CourseTest, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=0)
    question_text = models.TextField()

    class Meta:
        ordering = ['order']
        unique_together = (('test', 'order'),)
        verbose_name = "Test savoli"
        verbose_name_plural = "Test savollari"

    def __str__(self):
        return self.question_text


class TestAnswer(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='answers')
    order = models.PositiveIntegerField(default=0)
    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        verbose_name = "Javob"
        verbose_name_plural = "Javoblar"

    def __str__(self):
        return self.answer_text


class StudentTest(models.Model):
    course_test = models.ForeignKey(CourseTest, on_delete=models.CASCADE, related_name='student_tests')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student_tests')
    score = models.FloatField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('course_test', 'user'),)
        ordering = ['-taken_at']
        verbose_name = "Talaba testi"
        verbose_name_plural = "Talaba testlari"

    def __str__(self):
        if self.completed:
            return f"{self.user.username} — {self.course_test.title} — {self.score} ball"
        return f"{self.user.username} — {self.course_test.title} — Jarayonda"


class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-published_at']
        verbose_name = "Yangilik"
        verbose_name_plural = "Yangiliklar"

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='contact_messages', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Aloqa xabari"
        verbose_name_plural = "Aloqa xabarlari"

    def __str__(self):
        sender = self.user.username if self.user else (self.name or 'Mehmon')
        return f"{sender}: {self.subject or 'Mavzu yoq'}"


class ContactToTeacher(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teacher_contacts')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student_contacts')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "O'qituvchiga murojaat"
        verbose_name_plural = "O'qituvchilarga murojaatlar"

    def __str__(self):
        return f"{self.user.username} → {self.teacher.username}"


class LessonLikeDislike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lesson_likes_dislikes')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='likes_dislikes')
    is_like = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name = "Like/Dislike"
        verbose_name_plural = "Like/Dislike lar"

    def __str__(self):
        return f"{self.user.username}: {'Like' if self.is_like else 'Dislike'} — {self.lesson.title}"


class CourseStudent(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='students')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        indexes = [models.Index(fields=['course']), models.Index(fields=['user'])]
        verbose_name = "Kurs talaba"
        verbose_name_plural = "Kurs talabalar"

    def __str__(self):
        return f"{self.user.username} — {self.course.title}"


class CustomUserCertificate(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='certificates')
    certificate_name = models.CharField(max_length=255)
    issued_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)

    class Meta:
        ordering = ['-issued_date']
        verbose_name = "Sertifikat"
        verbose_name_plural = "Sertifikatlar"

    def __str__(self):
        return f"{self.certificate_name} — {self.user.username}"


class TeacherRating(models.Model):
    """Rating system for teachers"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_ratings')
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_ratings')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'teacher')
        ordering = ['-created_at']
        verbose_name = "O'qituvchi baholash"
        verbose_name_plural = "O'qituvchi baholashlar"

    def __str__(self):
        return f"{self.user.username} → {self.teacher.username}: {self.rating}⭐"