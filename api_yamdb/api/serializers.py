import re
from datetime import datetime as dt

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title, User


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        exclude = ('id', )
        model = Category


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        exclude = ('id', )
        model = Genre


class GetTitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'genre', 'category',)
        model = Title


class CreateEditDeleteTitleSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(read_only=True)
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )

    class Meta:
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'genre', 'category',)
        model = Title

    def validate_year(self, value):
        year = dt.now().year
        if value > year:
            raise serializers.ValidationError('Проверьте год издания!')
        return value


class ReviewsSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    def validate(self, data, *args, **kwargs):
        request = self.context['request']
        author = request.user
        title_id = self.context['view'].kwargs.get('titles_id')
        title = get_object_or_404(Title, pk=title_id)

        if request.method == 'POST':
            if Review.objects.filter(title=title, author=author).exists():
                raise serializers.ValidationError(
                    {"detail": "Ревью можно отправлять только одно"}
                )
        return data

    class Meta:
        fields = ('id', 'text', 'author', 'score', 'pub_date',)
        model = Review


class CommentsSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date',)
        model = Comment


class SendCodeSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[],
    )
    email = serializers.EmailField(
        max_length=254,
    )

    def validate(self, data):
        errors = {}
        if not data.get("username", False):
            errors["username"] = "Это поле обязательно"
        if not data.get("email", False):
            errors["email"] = "Это поле обязательно"
        user = data.get("username", False)
        if user.lower() == "me":
            raise serializers.ValidationError("Username 'me' is not valid")
        if re.search(r'^[\w.@+-]+$', user) is None:
            raise ValidationError(
                (f'Не допустимые символы <{user}> в нике.'),
                params={'value': user},
            )
        if errors:
            raise serializers.ValidationError(errors)
        if User.objects.filter(email=data["email"]):
            user = User.objects.get(email=data["email"])
            if user.username != data["username"]:
                raise serializers.ValidationError(
                    {"user": "Данный username уже зарегистрирован"}
                )
        elif User.objects.filter(username=data["username"]):
            user = User.objects.get(username=data["username"])
            if user.email != data["email"]:
                raise serializers.ValidationError(
                    {"email": "Данный email уже зарегистрирован"}
                )
        return data


class CheckConfirmationCodeSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        max_length=200)
    confirmation_code = serializers.CharField(
        required=True)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role')


class IsNotAdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role')
        read_only_fields = ('role',)
