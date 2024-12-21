from django.urls import path
from . import views

app_name = 'globalChat'

urlpatterns = [
    path('', views.global_chat, name='global_chat'),  # Routing untuk Global Chat page
    path('new/', views.new_forum, name='new_post'), 
    path('forum/<int:forum_id>/', views.detail_chat, name='detail_chat'),  # Routing untuk detail chat
    path('forum/edit/<int:id>/', views.edit_forum, name='edit_forum'),
    path('forum/delete/<int:id>/', views.delete_forum, name='delete_forum'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('forum/<int:forum_id>/like/', views.toggle_like_forum, name='toggle_like_forum'),
    path('forum/<int:forum_id>/bookmark/', views.toggle_bookmark, name="toggle_bookmark"),
    
    # API untuk Flutter
    path('api/global_chat/', views.global_chat_flutter, name='global_chat_flutter'),  # List semua forum (API JSON)
    path('api/forum/create/', views.create_forum_flutter, name='create_forum_flutter'),  # Buat forum baru (API JSON)
    path('api/forum/edit/<int:forum_id>/', views.edit_forum_flutter, name='edit_forum_flutter'),  # Edit forum (API JSON)
    path('api/forum/delete/<int:forum_id>/', views.delete_forum_flutter, name='delete_forum_flutter'),  # Hapus forum (API JSON)
    path('api/forum/<int:forum_id>/like/', views.toggle_like_forum_flutter, name='toggle_like_forum_flutter'),  # Like/unlike forum (API JSON)
    path('api/forum/<int:forum_id>/comment/', views.add_comment_flutter, name='add_comment_flutter'),  # Tambahkan komentar (API JSON)
    path('api/forum/<int:forum_id>/comments/', views.get_comments_flutter, name='get_comments_flutter'),
    path('api/comment/delete/<int:comment_id>/', views.delete_comment_flutter, name='delete_comment_flutter'),
]
