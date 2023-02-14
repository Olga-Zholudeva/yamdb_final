from csv import DictReader

from django.core.management import BaseCommand
from reviews.models import Category, Comment, Genre, Review, Title, User


class Command(BaseCommand):
    def handle(self, *args, **options):
        for row in DictReader(open('static/data/users.csv')):
            User.objects.create(id=row['id'], username=row['username'],
                                email=row['email'], role=row['role'],
                                bio=row['bio'], first_name=row['first_name'],
                                last_name=row['last_name'],)

        for row in DictReader(open('static/data/genre.csv')):
            Genre.objects.create(id=row['id'], name=row['name'],
                                 slug=row['slug'],)

        for row in DictReader(open('static/data/category.csv')):
            Category.objects.create(id=row['id'],
                                    name=row['name'], slug=row['slug'])

        for row in DictReader(open('static/data/titles.csv')):
            category = Category.objects.get(id=row['category'])
            Title.objects.create(id=row['id'], name=row['name'],
                                 year=row['year'],
                                 category=category)

        for row in DictReader(open('static/data/genre_title.csv')):
            obj = Genre.objects.get(id=row['genre_id'])
            Title.objects.get(id=row['title_id']).genre.add(obj)

        for row in DictReader(open('static/data/review.csv')):
            title = Title.objects.get(id=row['title_id'])
            author = User.objects.get(id=row['author'])
            Review.objects.create(id=row['id'], text=row['text'],
                                  author=author, titles=title,
                                  score=row['score'],
                                  pub_date=row['pub_date'])

        for row in DictReader(open('static/data/comments.csv')):
            review = Review.objects.get(id=row['review_id'])

            author = User.objects.get(id=row['author'])
            Comment.objects.create(id=row['id'], reviews=review,
                                   text=row['text'], author=author,
                                   pub_date=row['pub_date'])
