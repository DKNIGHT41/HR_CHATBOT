from django.urls import path
from . import views
from .views import chatbot_view, signup_view, login_view, logout_view, user_view, get_history_view

urlpatterns = [
    # path('', views.chat_view, name='chat'),
    # path('get_response/', views.get_response, name='get_response'),
    # path("chat/", views.chat_page, name="chat"),
    path("chat_api/", chatbot_view, name="chat"),
    path('api/signup/', signup_view, name='signup'),
    path('api/login/', login_view, name='login'),
    path('api/logout/', logout_view, name='logout'),
    path('api/user/', user_view, name='user'),
    path('api/history/', get_history_view, name='history'),

]
