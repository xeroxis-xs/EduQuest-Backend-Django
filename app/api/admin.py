from django.contrib import admin
from .models import (
    EduquestUser,
    AcademicYear,
    Term,
    Course,
    Quest,
    Question,
    Answer,
    AttemptAnswerRecord,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    UserCourse,
    Image,
    Badge,
    UserQuestBadge,
    UserCourseBadge
)


# Register your models here.
admin.site.register(EduquestUser)
admin.site.register(AcademicYear)
admin.site.register(Term)
admin.site.register(Course)
admin.site.register(UserCourse)
admin.site.register(Quest)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(AttemptAnswerRecord)
admin.site.register(UserQuestAttempt)
admin.site.register(UserQuestQuestionAttempt)
admin.site.register(Badge)
admin.site.register(UserQuestBadge)
admin.site.register(UserCourseBadge)
admin.site.register(Image)


