from rest_framework import serializers
from .utils import split_full_name
# from django.contrib.auth.models import User
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


class EduquestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EduquestUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'nickname', 'last_login',
                  'updated_at', 'is_superuser', 'is_active', 'is_staff']
        read_only_fields = ['first_name', 'last_name', 'is_superuser', 'updated_at',]

    def create(self, validated_data):
        username = validated_data['username']
        nickname = username.replace("#", "")
        first_name, last_name = split_full_name(nickname)
        # Default handling if nickname is not provided
        user = EduquestUser.objects.create(first_name=first_name, last_name=last_name, nickname=nickname, **validated_data)
        return user

    def update(self, instance, validated_data):
        first_name, last_name = split_full_name(validated_data.pop('nickname'))
        instance.first_name = first_name
        instance.last_name = last_name
        instance.save()
        return instance


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__'


class TermSerializer(serializers.ModelSerializer):
    academic_year = AcademicYearSerializer()
    class Meta:
        model = Term
        fields = '__all__'

    def create(self, validated_data):
        academic_year_data = validated_data.pop('academic_year')
        academic_year = AcademicYear.objects.get_or_create(**academic_year_data)
        term = Term.objects.create(academic_year=academic_year, **validated_data)
        return term


class CourseSerializer(serializers.ModelSerializer):
    term = TermSerializer()
    class Meta:
        model = Course
        fields = '__all__'

    def create(self, validated_data):
        term_data = validated_data.pop('term')
        academic_year_data = term_data.pop('academic_year')

        # Retrieve or create AcademicYear
        academic_year, academic_year_created = AcademicYear.objects.get_or_create(**academic_year_data)

        # Retrieve or create Term under the AcademicYear
        term, term_created = Term.objects.get_or_create(academic_year=academic_year, **term_data)

        # Create Course using the retrieved or newly created Term
        course = Course.objects.create(term=term, **validated_data)
        return course


class QuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'


class UserQuestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestAttempt
        fields = '__all__'


class UserQuestQuestionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestQuestionAttempt
        fields = '__all__'


class UserCourseCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCourseCompletion
        fields = '__all__'


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'
