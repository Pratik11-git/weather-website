from django.urls import path
from . import views

urlpatterns=[
    path('',views.login_view,name='login'),
    path('register/',views.registration_view,name='register'),
    path('logout/',views.logout_view,name='logout'),
    path('home/',views.home_view,name='home'),
    path('history/', views.search_history_view, name='search_history'),
    path('history/delete/<int:entry_id>/', views.delete_search_entry, name='delete_search_entry'),
]