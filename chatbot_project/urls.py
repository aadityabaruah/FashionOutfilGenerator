from django.contrib import admin
from django.urls import path
from chatbot_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.chat_interface, name='chat_interface'),
    path('send_message/', views.send_message, name='send_message'),
    path('generate_images_for_idea/', views.generate_images_for_idea, name='generate_images_for_idea'),  # Add this line
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
