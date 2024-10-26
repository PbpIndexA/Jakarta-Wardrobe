from django.shortcuts import render, get_object_or_404
from products.models import Product, Rating, Comment
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.db.models import Avg
from django.utils import timezone
import re
from user_choices.models import UserChoice

def show_products_by_price(request):
    products = Product.objects.annotate(avg_rating=Avg('rating__rating')).order_by('price')
    if request.user.is_authenticated:
        user_choices = UserChoice.objects.filter(user=request.user).values_list('selected_item',flat=True)
    else:
        user_choices = []
    context = {
        'products': products,
        'user_choices': user_choices,
    }
    return render(request, 'product_page.html', context)


def show_products_by_category(request, category_keyword):
    products = Product.objects.filter(category__iregex=r'\b{}\b'.format(re.escape(category_keyword))).annotate(avg_rating=Avg('rating__rating')).order_by('name')
    if request.user.is_authenticated:
        user_choices = UserChoice.objects.filter(user=request.user).values_list('selected_item',flat=True)
    else:
        user_choices = []
    context = {
        'products': products,
        'user_choices': user_choices,
    }
    return render(request, 'product_page.html', context)

def product_detail(request, product_id):
    try:
        product = Product.objects.get(uuid=product_id)
        response_data = {
            'name': product.name,
            'category': product.category,
            'price': product.price,
            'description': product.desc,
            'color': product.color,
            'stock': product.stock,
            'shop_name': product.shop_name,
            'location': product.location,
            'img_url': product.img_url, 
        }
        return JsonResponse(response_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Produk tidak ditemukan'}, status=404)


def review_products(request, id):
    product = get_object_or_404(Product, uuid=id)
    avg_rating = Rating.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
    ratings_with_users = Rating.objects.filter(product=product).select_related('user').order_by('-timestamp')
    comments = Comment.objects.filter(product=product).select_related('user').order_by('-timestamp')


    if avg_rating is not None:
        avg_rating_int = int(round(avg_rating))
    else:
        avg_rating_int = 0

    return render(request, 'review_products.html', {
        'product': product,
        'avg_rating': avg_rating,
        'avg_rating_int': avg_rating_int,
        'ratings_with_users': ratings_with_users,
        'comments': comments
        
    })

@login_required
@csrf_exempt
@require_POST
def add_rating(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        rating_value = int(request.POST.get('rating'))
        product = get_object_or_404(Product, uuid=product_id)

        rating_obj, created = Rating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating_value}
        )

        if not created:
            rating_obj.timestamp = timezone.now()
            rating_obj.save() 

        # Hitung rating rata-rata terbaru
        avg_rating = Rating.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
        ratings_with_users = Rating.objects.filter(product=product).select_related('user').order_by('-timestamp')

        ratings_data = [{
            'user': rating.user.username,
            'rating': rating.rating,
            'timestamp': rating.timestamp.strftime("%d %B %Y, %H:%M")
        } for rating in ratings_with_users]

        return JsonResponse({
            'message': 'Rating added successfully',
            'avg_rating': avg_rating,
            'ratings_with_users': ratings_data
        }, status=201)

    return JsonResponse({'message': 'Invalid request'}, status=400)
@login_required
@csrf_exempt
@require_POST
def add_comment(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        comment_text = request.POST.get('comment')
        product = get_object_or_404(Product, uuid=product_id)
        new_comment = Comment.objects.create(product=product, user=request.user, comment=comment_text)
        
        # Mengembalikan respons dengan data komentar yang baru
        return JsonResponse({
            'message': 'Comment added successfully',
            'user': new_comment.user.username,
            'comment': new_comment.comment,
            'timestamp': new_comment.timestamp.strftime("%d %B %Y, %H:%M")
        }, status=201)
    return JsonResponse({'message': 'Invalid request'}, status=400)

def get_ratings_comments(request, product_id):
    product = get_object_or_404(Product, uuid=product_id)
    ratings = product.rating_set.all()
    comments = product.comment_set.all()

    rating_list = list(ratings.values('rating', 'timestamp', 'user__username'))
    comment_list = list(comments.values('comment', 'timestamp', 'user__username'))

    return JsonResponse({'ratings': rating_list, 'comments': comment_list}, safe=False)

def show_five_products(request):
    products = Product.objects.all()[:7]
    return render(request, 'main.html', {'products': products})

from django.db.models import Q, Avg

def find_product(request):
    query = request.GET.get('q', '')  # Search query
    category = request.GET.get('category', '')  # Selected category
    shop_name = request.GET.get('shop_name', '')  # Selected shop name
    filter_type = request.GET.get('filter', '')  # Existing filter

    products = Product.objects.all()

    # Apply search filter if query is provided
    if query:
        products = products.filter(Q(name__icontains=query) )

    # Apply category filter if a category is selected
    if category:
        products = products.filter(category__iexact=category)

    # Apply shop_name filter if a shop_name is selected
    if shop_name:
        products = products.filter(shop_name__iexact=shop_name)

    # Handle other sorting filters like price and rating
    if filter_type == 'price_asc':
        products = products.order_by('price')
    elif filter_type == 'price_desc':
        products = products.order_by('-price')
    elif filter_type == 'rating':
        products = products.annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')

    return render(request, 'product_page.html', {'products': products})

def show_best_10_products(request):
    products = Product.objects.annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[:10]
    return render(request, 'main.html', {'products': products})