from rest_framework import routers

from .views import (CategoryViewSet, CommentsViewSet, GenreViewSet,
                    ReviewsViewSet, TitleViewSet, UserViewSet)

v1_router = routers.DefaultRouter()
v1_router.register(r'titles/(?P<titles_id>\d+)/reviews',
                   ReviewsViewSet, basename="comment-detail")
v1_router.register(r'titles/(?P<titles_id>\d+)/reviews/'
                   r'(?P<review_id>\d+)/comments',
                   CommentsViewSet, basename="comment-detail")
v1_router.register(r'categories', CategoryViewSet)
v1_router.register(r'genres', GenreViewSet)
v1_router.register(r'titles', TitleViewSet, basename='titles')
v1_router.register(r'users', UserViewSet)
