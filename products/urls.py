from django.urls import path

from . import views
from .views import RatingList, CommentList, get_ratings_by_product, get_comments_by_product, show_products_by_price, show_products_by_category, review_products, add_rating, add_comment, get_ratings_comments, show_products_by_category, product_detail, find_product, add_comment_flutter, add_rating_flutter, find_product_json
from django.urls import path
app_name = 'products'

urlpatterns = [
    path('', show_products_by_price, name='show_products_by_price'),
    path('review_products/<uuid:id>/', review_products, name='review_products'),
    path('add_rating/', add_rating, name='add_rating'),
    path('add_comment/', add_comment, name='add_comment'),
    path('get_ratings_comments/<uuid:product_id>/', get_ratings_comments, name='get_ratings_comments'),
    path('detail/<uuid:product_id>/', product_detail, name='product_detail'),
    path('category/<str:category_keyword>/', show_products_by_category, name='show_products_by_category'),
    path('products/find/', find_product, name='find_product'),
    path('json/', views.product_list, name='product_list'),
    path('products/add_comment_flutter/', add_comment_flutter, name='add_comment'),  # Menambahkan URL untuk add_comment
    path('products/add_rating_flutter/', add_rating_flutter, name='add_rating'),  # Menambahkan URL untuk add_rating
    path('comments/', CommentList.as_view(), name='comment-list'),
    path('ratings/', RatingList.as_view(), name='rating-list'),
    path('products/<uuid:product_id>/comments/', get_comments_by_product, name='get_comments_by_product'),
    path('products/<uuid:product_id>/ratings/', get_ratings_by_product, name='get_ratings_by_product'),
    path('comments/delete/<str:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comments/edit/<uuid:comment_id>/', views.edit_comment, name='edit_comment'),
    path('ratings/delete/<str:rating_id>/', views.delete_rating, name='delete_rating'),
    path('products/find/json/', find_product_json, name='find_product_json'),



]