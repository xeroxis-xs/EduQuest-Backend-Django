from django.contrib import admin
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    UserCourseGroupEnrollment,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserAnswerAttempt,
    Badge,
    UserQuestBadge,
    UserCourseBadge,
    Document
)


# Register your models here.
admin.site.register(EduquestUser)
admin.site.register(AcademicYear)
admin.site.register(Term)
admin.site.register(Course)
admin.site.register(UserCourseGroupEnrollment)
admin.site.register(Quest)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(UserAnswerAttempt)
admin.site.register(UserQuestAttempt)
admin.site.register(Badge)
admin.site.register(UserQuestBadge)
admin.site.register(UserCourseBadge)
admin.site.register(Image)
admin.site.register(Document)


