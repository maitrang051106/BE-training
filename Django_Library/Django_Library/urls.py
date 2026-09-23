"""
URL configuration for MTT_Library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from library_api.apis import auth_api, books_api
from library_api.views.home import api_home

urlpatterns = [
    path('', api_home, name='api-home'),
    path('register/', auth_api.register, name='register'),
    path('login/', auth_api.login, name='login'),
    path('refresh/', auth_api.refresh, name='refresh'),
    path('logout/', auth_api.logout, name='logout'),
    path('admin/users/', auth_api.list_users, name='list-users'),
    path('admin/users/create/', auth_api.create_user, name='create-user'),
    path('admin/users/<str:username>/', auth_api.manage_user, name='manage-user'),
    path('books/', books_api.list_books, name='list-books'),
    path('books/create/', books_api.create_book, name='create-book'),
    path('books/<int:id>/', books_api.get_book, name='get-book'),
]
