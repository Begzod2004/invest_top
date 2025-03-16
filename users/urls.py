from django.urls import path
from users.views import TelegramAuthView, send_message_to_user

urlpatterns = [
    path("auth/login/", TelegramAuthView.as_view(), name="telegram-login"),
    path("api/users/<int:user_id>/send-message/", send_message_to_user, name="send-message-to-user"),
]
