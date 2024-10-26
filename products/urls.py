from django.urls import path
from .views import show_products_by_price, show_products_by_category, review_products, add_rating, add_comment, get_ratings_comments, show_products_by_category, product_detail, find_product

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
]
