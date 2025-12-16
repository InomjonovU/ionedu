from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter, RangeDateTimeFilter, RelatedDropdownFilter
from .models import (
    CustomUser, CourseCategory, Course, Lesson, Comment,
    RequestToJoinCourse, RequestToBecomeTeacher, CourseTest,
    TestQuestion, TestAnswer, StudentTest, News, ContactMessage,
    ContactToTeacher, LessonLikeDislike, CourseStudent, CustomUserCertificate
)


# ============= CUSTOM USER ADMIN =============
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = ['username', 'email', 'display_user_type', 'display_level', 'coins', 'stars', 'is_active']
    list_filter = [
        'user_type',
        'level',
        'is_staff',
        'is_active',
        ('created_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'bio', 'profile_picture', 'date_of_birth', 'telegram_username')
        }),
        ('Gamification', {
            'fields': ('coins', 'stars', 'level')
        }),
    )

    @display(description="User Type", label=True)
    def display_user_type(self, obj):
        colors = {
            'student': 'info',
            'teacher': 'success'
        }
        return obj.get_user_type_display(), colors.get(obj.user_type, 'default')

    @display(description="Level", label=True)
    def display_level(self, obj):
        colors = {
            'beginner': 'warning',
            'junior': 'info',
            'middle': 'primary',
            'senior': 'success'
        }
        return obj.get_level_display(), colors.get(obj.level, 'default')


# ============= COURSE CATEGORY =============
@admin.register(CourseCategory)
class CourseCategoryAdmin(ModelAdmin):
    list_display = ['name', 'display_course_count']
    search_fields = ['name']

    @display(description="Courses")
    def display_course_count(self, obj):
        return obj.courses.count()


# ============= COURSE =============
class LessonInline(TabularInline):
    model = Lesson
    extra = 0
    fields = ['order', 'title', 'video_url']


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ['title', 'teacher', 'category', 'display_type', 'display_student_count', 'created_at']
    list_filter = [
        'type',
        ('category', RelatedDropdownFilter),
        ('teacher', RelatedDropdownFilter),
        ('created_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['title', 'subject', 'teacher__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [LessonInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subject', 'grade', 'description')
        }),
        ('Settings', {
            'fields': ('type', 'category', 'teacher', 'background_image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @display(description="Type", label=True)
    def display_type(self, obj):
        colors = {
            'open': 'success',
            'closed': 'warning'
        }
        return obj.get_type_display(), colors.get(obj.type, 'default')

    @display(description="Students")
    def display_student_count(self, obj):
        return obj.students.count()


# ============= LESSON =============
@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ['title', 'course', 'order', 'display_has_video', 'created_at']
    list_filter = [
        ('course', RelatedDropdownFilter),
        ('created_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']

    @display(description="Video", boolean=True)
    def display_has_video(self, obj):
        return bool(obj.video_url)


# ============= COMMENT =============
@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ['user', 'course', 'content_preview', 'created_at']
    list_filter = [('created_at', RangeDateTimeFilter)]
    list_filter_submit = True
    search_fields = ['user__username', 'course__title', 'content']

    @display(description="Content")
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


# ============= REQUEST TO JOIN COURSE =============
@admin.register(RequestToJoinCourse)
class RequestToJoinCourseAdmin(ModelAdmin):
    list_display = ['user', 'course', 'display_status', 'created_at']
    list_filter = [
        'is_approved',
        ('created_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['user__username', 'course__title']
    actions = ['approve_requests', 'reject_requests']

    @display(description="Status", label=True)
    def display_status(self, obj):
        if obj.is_approved:
            return "Approved", "success"
        return "Pending", "warning"

    @admin.action(description="Approve selected requests")
    def approve_requests(self, request, queryset):
        for req in queryset:
            req.is_approved = True
            req.save()
            CourseStudent.objects.get_or_create(user=req.user, course=req.course)
        self.message_user(request, f'{queryset.count()} requests approved.')

    @admin.action(description="Reject selected requests")
    def reject_requests(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} requests rejected.')


# ============= REQUEST TO BECOME TEACHER =============
@admin.register(RequestToBecomeTeacher)
class RequestToBecomeTeacherAdmin(ModelAdmin):
    list_display = ['user', 'f_name', 'l_name', 'phone_number', 'display_status', 'created_at']
    list_filter = [
        'is_processed',
        ('created_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['user__username', 'f_name', 'l_name', 'phone_number']
    actions = ['mark_as_processed', 'approve_as_teacher']

    @display(description="Status", label=True)
    def display_status(self, obj):
        if obj.is_processed:
            return "Processed", "success"
        return "Pending", "warning"

    @admin.action(description="Mark as processed")
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
        self.message_user(request, f'{queryset.count()} requests marked as processed.')

    @admin.action(description="Approve as teacher")
    def approve_as_teacher(self, request, queryset):
        for req in queryset:
            req.user.user_type = 'teacher'
            req.user.save()
            req.is_processed = True
            req.save()
        self.message_user(request, f'{queryset.count()} users approved as teachers.')


# ============= COURSE TEST =============
class TestQuestionInline(TabularInline):
    model = TestQuestion
    extra = 0


@admin.register(CourseTest)
class CourseTestAdmin(ModelAdmin):
    list_display = ['title', 'course', 'time_limit_minutes', 'passing_score', 'display_question_count']
    list_filter = [('course', RelatedDropdownFilter)]
    list_filter_submit = True
    search_fields = ['title', 'course__title']
    inlines = [TestQuestionInline]

    @display(description="Questions")
    def display_question_count(self, obj):
        return obj.questions.count()


# ============= TEST QUESTION =============
class TestAnswerInline(TabularInline):
    model = TestAnswer
    extra = 0


@admin.register(TestQuestion)
class TestQuestionAdmin(ModelAdmin):
    list_display = ['question_text', 'test', 'order']
    list_filter = [('test', RelatedDropdownFilter)]
    list_filter_submit = True
    search_fields = ['question_text']
    inlines = [TestAnswerInline]


# ============= TEST ANSWER =============
@admin.register(TestAnswer)
class TestAnswerAdmin(ModelAdmin):
    list_display = ['answer_text', 'question', 'display_is_correct', 'order']
    list_filter = ['is_correct']
    search_fields = ['answer_text']

    @display(description="Correct", boolean=True)
    def display_is_correct(self, obj):
        return obj.is_correct


# ============= STUDENT TEST =============
@admin.register(StudentTest)
class StudentTestAdmin(ModelAdmin):
    list_display = ['user', 'course_test', 'score', 'display_status', 'taken_at']
    list_filter = [
        'completed',
        ('taken_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['user__username', 'course_test__title']
    readonly_fields = ['taken_at']

    @display(description="Status", label=True)
    def display_status(self, obj):
        if obj.completed:
            return "Completed", "success"
        return "In Progress", "info"


# ============= NEWS =============
@admin.register(News)
class NewsAdmin(ModelAdmin):
    list_display = ['title', 'published_at', 'display_has_image']
    list_filter = [('published_at', RangeDateTimeFilter)]
    list_filter_submit = True
    search_fields = ['title', 'content']

    @display(description="Image", boolean=True)
    def display_has_image(self, obj):
        return bool(obj.image)


# ============= CONTACT MESSAGE =============
@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ['display_sender', 'subject', 'created_at']
    list_filter = [('created_at', RangeDateTimeFilter)]
    list_filter_submit = True
    search_fields = ['name', 'email', 'subject', 'content']
    readonly_fields = ['created_at']

    @display(description="Sender")
    def display_sender(self, obj):
        return obj.user.username if obj.user else obj.name


# ============= CONTACT TO TEACHER =============
@admin.register(ContactToTeacher)
class ContactToTeacherAdmin(ModelAdmin):
    list_display = ['user', 'teacher', 'message_preview', 'created_at']
    list_filter = [('created_at', RangeDateTimeFilter)]
    list_filter_submit = True
    search_fields = ['user__username', 'teacher__username', 'message']

    @display(description="Message")
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message


# ============= LESSON LIKE/DISLIKE =============
@admin.register(LessonLikeDislike)
class LessonLikeDislikeAdmin(ModelAdmin):
    list_display = ['user', 'lesson', 'display_reaction', 'created_at']
    list_filter = [
        'is_like',
        ('created_at', RangeDateTimeFilter),
    ]
    list_filter_submit = True
    search_fields = ['user__username', 'lesson__title']

    @display(description="Reaction", label=True)
    def display_reaction(self, obj):
        if obj.is_like:
            return "👍 Like", "success"
        return "👎 Dislike", "danger"


# ============= COURSE STUDENT =============
@admin.register(CourseStudent)
class CourseStudentAdmin(ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at']
    list_filter = [
        ('enrolled_at', RangeDateTimeFilter),
        ('course', RelatedDropdownFilter),
    ]
    list_filter_submit = True
    search_fields = ['user__username', 'course__title']


# ============= USER CERTIFICATE =============
@admin.register(CustomUserCertificate)
class CustomUserCertificateAdmin(ModelAdmin):
    list_display = ['certificate_name', 'user', 'issued_date', 'display_validity']
    list_filter = [('issued_date', RangeDateFilter)]
    list_filter_submit = True
    search_fields = ['certificate_name', 'user__username']

    @display(description="Status", label=True)
    def display_validity(self, obj):
        if not obj.expiry_date:
            return "No Expiry", "success"
        from django.utils import timezone
        if obj.expiry_date > timezone.now().date():
            return "Valid", "success"
        return "Expired", "danger"