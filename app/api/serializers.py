from rest_framework import serializers
from .utils import split_full_name
from collections import OrderedDict
from django.utils import timezone
from datetime import datetime
from django.db import transaction
# from django.contrib.auth.models import User
from .models import (
    EduquestUser,
    Image,
    AcademicYear,
    Term,
    Course,
    Quest,
    Question,
    Answer,
    UserQuestAttempt,
    UserQuestQuestionAttempt,
    AttemptAnswerRecord,
    UserCourse,
    Badge,
    UserQuestBadge,
    UserCourseBadge,
    Document,
)


class BulkSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_mapping = {instance.id: instance for instance in instances}
        for item in validated_data:
            print("Validated Item: ", item)  # Debugging
            instance_id = item.get('id', None)
            if instance_id is not None and instance_id in instance_mapping:
                self.child.update(instance_mapping[instance_id], item)
            else:
                print("No instance ID found")  # Debugging
                pass
        # Optionally, handle deletions
        return instances


class EduquestUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Ensure id field is included

    class Meta:
        model = EduquestUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'nickname', 'last_login',
                  'updated_at', 'is_superuser', 'is_active', 'is_staff', 'total_points']
        read_only_fields = ['first_name', 'last_name', 'is_superuser', 'updated_at', 'username']

    def create(self, validated_data):
        username = validated_data['username']
        validated_data['email'] = validated_data['email'].upper()
        nickname = username.replace("#", "")
        first_name, last_name = split_full_name(nickname)
        # Default handling if nickname is not provided
        user = EduquestUser.objects.create(
            first_name=first_name,
            last_name=last_name,
            nickname=nickname,
            **validated_data
        )
        return user

    # def update(self, instance, validated_data):
    #     first_name, last_name = split_full_name(validated_data.pop('nickname'))
    #     instance.first_name = first_name
    #     instance.last_name = last_name
    #     instance.save()
    #     return instance


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'


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

    def update(self, instance, validated_data):
        academic_year_data = validated_data.pop('academic_year')
        academic_year = AcademicYear.objects.get(**academic_year_data)

        instance.academic_year = academic_year

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CourseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    term = TermSerializer(required=False)
    image = ImageSerializer(required=False)
    enrolled_users = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        extra_kwargs = {
            # Make the field optional during UserCourse create
            'name': {'required': False},
            'type': {'required': False},
            'description': {'required': False},
            'status': {'required': False},
        }

    # Course is created with empty enrolled_users
    def create(self, validated_data):
        term_data = validated_data.pop('term')
        image_data = validated_data.pop('image')
        # Remove enrolled_users from validated_data if there is any
        enrolled_users_data = validated_data.pop('enrolled_users', [])

        academic_year_data = term_data.pop('academic_year')

        # Retrieve AcademicYear
        academic_year = AcademicYear.objects.get(**academic_year_data)
        # Retrieve Term under the AcademicYear
        term = Term.objects.get(academic_year=academic_year, **term_data)
        # Retrieve Image
        image = Image.objects.get(**image_data)

        course = Course.objects.create(
            term=term,
            image=image,
            **validated_data
        )
        return course

    # Do not update enrolled_users since it can be updated separately using UserCourseSerializer
    def update(self, instance, validated_data):
        term_data = validated_data.pop('term', None)
        image_data = validated_data.pop('image', None)
        # Remove enrolled_users from validated_data if there
        enrolled_users_data = validated_data.pop('enrolled_users', [])

        if term_data:
            # Remove academic_year from term_data
            academic_year_data = term_data.pop('academic_year')
            term = Term.objects.get(**term_data)
            instance.term = term

        if image_data:
            image = Image.objects.get(**image_data)
            instance.image = image

        # If the status is changed from Active to Expired,
        # Set all active quests in the course to Expired
        status = validated_data.get('status', None)
        if instance.status == 'Active' and status == 'Expired':
            quests = Quest.objects.filter(from_course=instance, status='Active')
            expired_date = timezone.now()
            for quest in quests:
                quest.status = 'Expired'
                quest.expiration_date = expired_date
                quest.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer()
    user = EduquestUserSerializer()

    class Meta:
        model = UserCourse
        fields = '__all__'

    def create(self, validated_data):
        course_data = validated_data.pop('course')
        user_data = validated_data.pop('user')
        course = Course.objects.get(id=course_data['id'])
        user = EduquestUser.objects.get(id=user_data['id'])
        user_course = UserCourse.objects.create(course=course, user=user)
        return user_course


class QuestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    from_course = CourseSerializer(required=False)
    organiser = EduquestUserSerializer(required=False)
    image = ImageSerializer(required=False)
    total_max_score = serializers.SerializerMethodField(read_only=True)
    total_questions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Quest
        fields = '__all__'
        extra_kwargs = {
            # Make the field optional during UserQuestAttempt create
            'name': {'required': False},
            'description': {'required': False},
            'type': {'required': False},
            'status': {'required': False},
            'expiration_date': {'required': False},
            'max_attempts': {'required': False},
            'total_max_score': {'required': False},
            'total_questions': {'required': False},
        }

    def get_total_max_score(self, obj):
        return obj.total_max_score()

    def get_total_questions(self, obj):
        return obj.total_questions()

    def create(self, validated_data):
        from_course_data = validated_data.pop('from_course', None)
        from_course = None
        organiser = None
        image = None
        if from_course_data:
            enrolled_users_data = from_course_data.pop('enrolled_users', [])
            course_image_data = from_course_data.pop('image', None)
            term_data = from_course_data.pop('term', None)
            if term_data:
                academic_year_data = term_data.pop('academic_year')
                academic_year = AcademicYear.objects.get(**academic_year_data)

                from_course = Course.objects.get(
                    term=Term.objects.get(academic_year=academic_year, **term_data),
                    image=Image.objects.get(**course_image_data),
                    **from_course_data)

        organiser_data = validated_data.pop('organiser')
        if organiser_data:
            organiser = EduquestUser.objects.get(**organiser_data)

        image_data = validated_data.pop('image')
        if image_data:
            image = Image.objects.get(**image_data)

        # Create the Quest instance with the retrieved Course and EduquestUser
        if from_course and organiser and image:
            quest = Quest.objects.create(
                from_course=from_course,
                organiser=organiser,
                image=image,
                **validated_data
            )
            return quest

    def update(self, instance, validated_data):
        from_course_data = validated_data.pop('from_course', None)
        if from_course_data:
            enrolled_users_data = from_course_data.pop('enrolled_users', [])
            course_image_data = from_course_data.pop('image')
            term_data = from_course_data.pop('term')
            from_course = Course.objects.get(**from_course_data)
            instance.from_course = from_course

        image_data = validated_data.pop('image', None)
        if image_data:
            image = Image.objects.get(**image_data)
            instance.image = image

        # If the status is changed from Active to Expired,
        # update the expiration_date to the current time
        status = validated_data.get('status', None)
        if instance.status == 'Active' and status == 'Expired':
            instance.expiration_date = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class AnswerSerializer(serializers.ModelSerializer):
    # Explicitly include the id field
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Answer
        fields = '__all__'
        extra_kwargs = {
            'question': {'required': False}  # Make the question field optional during create
        }


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)
    id = serializers.IntegerField(required=False)  # Explicitly include the id field
    class Meta:
        model = Question
        fields = '__all__'
        list_serializer_class = BulkSerializer

    # Create question with new answers (without specifying answer IDs)
    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)

        # Note: Do not specify 'question' in each answer_data
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)

        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])

        # Handle nested answers
        for answer_data in answers_data:
            answer_id = answer_data.get('id', None)
            if answer_id:
                answer_instance = Answer.objects.get(id=answer_id, question=instance)

            else:
                answer_instance = Answer(question=instance)

            answer_instance.text = answer_data.get('text', answer_instance.text)
            answer_instance.is_correct = answer_data.get('is_correct', answer_instance.is_correct)
            answer_instance.save()

        # Update other fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserQuestAttemptSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    quest = QuestSerializer(required=False)
    # total_score_achieved = serializers.SerializerMethodField(required=False, read_only=True)
    time_taken = serializers.SerializerMethodField(required=False, read_only=True)
    total_score_achieved = serializers.FloatField(required=False)

    class Meta:
        model = UserQuestAttempt
        fields = '__all__'
        list_serializer_class = BulkSerializer

    # def get_total_score_achieved(self, obj):
    #     if isinstance(obj, OrderedDict):
    #         return None
    #     return obj.total_score_achieved()

    def get_time_taken(self, obj):
        if isinstance(obj, OrderedDict):
            return None
        return obj.time_taken()

    def create(self, validated_data):
        quest_data = validated_data.pop('quest')
        quest = Quest.objects.get(id=quest_data['id'])
        user_quest_attempt = UserQuestAttempt.objects.create(quest=quest, **validated_data)

        # Create a UserQuestQuestionAttempt instance with empty selected_answers for newly created UserQuestAttempt
        questions = Question.objects.filter(from_quest=user_quest_attempt.quest)

        # Create UserQuestQuestionAttempt for each question in the quest
        for question in questions:
            user_quest_question_attempt = UserQuestQuestionAttempt.objects.create(
                user_quest_attempt=user_quest_attempt,
                question=question,
                score_achieved=0,
            )
            # Create AttemptAnswerRecord for each answer in the question
            # Set is_selected to False for each answer
            answers = Answer.objects.filter(question=question)
            for answer in answers:
                AttemptAnswerRecord.objects.create(
                    user_quest_question_attempt=user_quest_question_attempt,
                    answer=answer,
                    is_selected=False  # Marking is_selected as False
                )

        return user_quest_attempt

    def update(self, instance, validated_data):
        # Exclude aggregated fields from the update process
        validated_data.pop('time_taken', None)

        # Get the user's highest score achieved for all quest attempted in this quest
        user_quest_attempts = UserQuestAttempt.objects.filter(user=instance.user, quest=instance.quest)
        highest_score_achieved = 0
        for user_quest_attempt in user_quest_attempts:
            if user_quest_attempt.total_score_achieved > highest_score_achieved:
                highest_score_achieved = user_quest_attempt.total_score_achieved

        # Aggregate the total_score_achieved when the all_questions_submitted is True from False
        all_questions_submitted = validated_data.get('all_questions_submitted', None)
        if all_questions_submitted and not instance.all_questions_submitted:
            validated_data.pop('all_questions_submitted', None)
            validated_data.pop('total_score_achieved', None)
            total_score_achieved = instance.calculate_total_score_achieved()
            instance.total_score_achieved = total_score_achieved
            instance.all_questions_submitted = True

            # Check if the user's total_score_achieved is higher than the highest_score_achieved
            # If it is, credit the amount to the user's total_points
            if total_score_achieved > highest_score_achieved and instance.quest.type != 'Private':
                instance.user.total_points += total_score_achieved - highest_score_achieved
                instance.user.save()

        # Update other fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class AttemptAnswerRecordSerializer(serializers.ModelSerializer):
    answer = AnswerSerializer()
    id = serializers.IntegerField(required=False)  # Explicitly include the id field
    class Meta:
        model = AttemptAnswerRecord
        fields = '__all__'

    def create(self, validated_data):
        answer_data = validated_data.pop('answer')
        answer = Answer.objects.get(id=answer_data['id'])
        attempt_answer_record = AttemptAnswerRecord.objects.create(
            user_quest_question_attempt=validated_data['user_quest_question_attempt'],
            answer=answer,
            is_selected=validated_data['is_selected']
        )
        return attempt_answer_record

    def update(self, instance, validated_data):
        answer_data = validated_data.pop('answer')
        answer = Answer.objects.get(id=answer_data['id'])
        instance.answer = answer

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserQuestQuestionAttemptSerializer(serializers.ModelSerializer):
    selected_answers = AttemptAnswerRecordSerializer(many=True, required=False)
    question = QuestionSerializer(required=False)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = UserQuestQuestionAttempt
        fields = '__all__'
        list_serializer_class = BulkSerializer

    def create(self, validated_data):
        question_data = validated_data.pop('question')
        question = Question.objects.get(id=question_data['id'])

        user_quest_question_attempt = UserQuestQuestionAttempt.objects.create(
            user_quest_attempt=validated_data['user_quest_attempt'],
            question=question,
            score_achieved=validated_data['score_achieved'],
            # submitted=validated_data['submitted']
        )
        return user_quest_question_attempt

    def update(self, instance, validated_data):
        selected_answers_data = validated_data.pop('selected_answers', [])

        # Handle nested selected_answers
        for selected_answer_data in selected_answers_data:
            attempt_answer_record_id = selected_answer_data.get('id')
            attempt_answer_record = AttemptAnswerRecord.objects.get(id=attempt_answer_record_id)

            # Ensure 'answer' is treated as a dictionary
            answer_data = selected_answer_data.get('answer')
            if isinstance(answer_data, dict):  # Ensure it's a dictionary
                answer_id = answer_data['id']
                answer_instance = Answer.objects.get(id=answer_id)
                attempt_answer_record.answer = answer_instance

            attempt_answer_record.is_selected = selected_answer_data['is_selected']
            attempt_answer_record.save()

        # Handle question data
        question_data = validated_data.pop('question')
        question = Question.objects.get(id=question_data['id'])
        instance.question = question

        # Update other fields as usual
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class BadgeSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    class Meta:
        model = Badge
        fields = '__all__'


class UserQuestBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()
    quest_attempted = UserQuestAttemptSerializer()
    class Meta:
        model = UserQuestBadge
        fields = '__all__'


class UserCourseBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()
    course_completed = UserCourseSerializer()
    class Meta:
        model = UserCourseBadge
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
