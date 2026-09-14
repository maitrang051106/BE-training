from django.urls import path

from library_api.apis import auth_api, books_api
from library_api.views.home import api_home


urlpatterns = [
    path('', api_home, name='api-home'),
    path('register/', auth_api.register, name='register'),
    path('login/', auth_api.login, name='login'),
    path('refresh/', auth_api.refresh, name='refresh'),
    path('logout/', auth_api.logout, name='logout'),
    #admin
    path('admin/users/', auth_api.list_users, name='list-users'),
    path('admin/users/create/', auth_api.create_user, name='create-user'),
    path('admin/users/<str:username>/', auth_api.manage_user, name='manage-user'),
    #books
    path('books/', books_api.list_books, name='list-books'),
    path('books/create/', books_api.create_book, name='create-book'),
    path('books/<int:id>/', books_api.get_book, name='get-book'),
]