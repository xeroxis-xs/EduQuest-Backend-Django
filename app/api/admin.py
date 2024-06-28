from django.contrib import admin
from .models import (
    EduquestUser,
    AcademicYear,
    Term,
    Course,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    UserCourseCompletion,
    Badge
)


# Register your models here.
admin.site.register(EduquestUser)
admin.site.register(AcademicYear)
admin.site.register(Term)
admin.site.register(Course)
admin.site.register(Quest)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(UserQuestAttempt)
admin.site.register(UserQuestQuestionAttempt)
admin.site.register(UserCourseCompletion)
admin.site.register(Badge)


