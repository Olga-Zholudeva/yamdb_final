from api.filters import TitleFilter
from api.permission import (IsAdmin, IsAdminOrReadOnly,
                            IsAuthorOrModeratorOrAdmin)
from api.serializers import (CategorySerializer,
                             CheckConfirmationCodeSerializer,
                             CommentsSerializer,
                             CreateEditDeleteTitleSerializer, GenreSerializer,
                             GetTitleSerializer, IsNotAdminUserSerializer,
                             ReviewsSerializer, SendCodeSerializer,
                             UserSerializer)
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Comment, Genre, Review, Title, User

from api_yamdb.settings import EMAIL


class ListCreateDelet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Кастомный набор действий с категориями и жанрами."""
    pass


class CategoryViewSet(ListCreateDelet):
    """Обрабатываем запросы к БД с категориями произведений."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)


class GenreViewSet(ListCreateDelet):
    """Обрабатываем запросы к БД с жанрами произведений."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (IsAdminOrReadOnly,)


class TitleViewSet(viewsets.ModelViewSet):
    """Обрабатываем запросы к БД с произведениями."""
    queryset = Title.objects.all().annotate(rating=Avg('reviews__score'))
    serializer_class = CreateEditDeleteTitleSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GetTitleSerializer
        return CreateEditDeleteTitleSerializer


class ReviewsViewSet(viewsets.ModelViewSet):
    """Обрабатываем запросы к БД с отзывами"""
    serializer_class = ReviewsSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAuthorOrModeratorOrAdmin)

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.
                                  get("titles_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        title=get_object_or_404
                        (Title, pk=self.kwargs.get("titles_id")))


class CommentsViewSet(viewsets.ModelViewSet):
    """Обрабатываем запросы к БД с комментариями"""
    queryset = Comment.objects.all()
    serializer_class = CommentsSerializer
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAuthorOrModeratorOrAdmin)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        reviews=get_object_or_404
                        (Review, pk=self.kwargs.get("review_id")))


@api_view(["POST"])
@permission_classes([AllowAny])
def get_jwt(request):
    username = request.data.get("username")
    confirmation_code = request.data.get("confirmation_code")
    serializer = CheckConfirmationCodeSerializer(data=request.data)

    if serializer.is_valid():
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(serializer.errors,
                            status=status.HTTP_404_NOT_FOUND)
        if default_token_generator.check_token(user, confirmation_code):
            token = AccessToken.for_user(user)
            user.confirmation_code = 0
            user.save()
            return Response({"access": str(token)})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def send_code(request):
    serializer = SendCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = request.data.get("email", False)
    username = request.data.get("username", False)
    user = User.objects.get_or_create(username=username, email=email)[0]
    token = default_token_generator.make_token(user)
    user.confirmation_code = token
    user.save()
    send_mail(
        "Code",
        token,
        EMAIL,
        [email],
        fail_silently=False,
    )
    return Response(
        serializer.initial_data, status=status.HTTP_200_OK
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdmin,)
    lookup_field = 'username'
    filter_backends = (SearchFilter, )
    search_fields = ('username', )
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me')
    def get_current_user_info(self, request):
        serializer = UserSerializer(request.user)
        if request.method == 'PATCH':
            if request.user.is_admin:
                serializer = UserSerializer(
                    request.user,
                    data=request.data,
                    partial=True)
            else:
                serializer = IsNotAdminUserSerializer(
                    request.user,
                    data=request.data,
                    partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data)

    def patch(self, request):
        if request.user.is_authenticated:
            user = get_object_or_404(User, id=request.user.id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        return Response('Вы не авторизованы',
                        status=status.HTTP_401_UNAUTHORIZED)
