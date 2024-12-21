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

    products = Product.objects.annotate(avg_rating=Avg('rating__rating'))

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

def find_product_json(request):
    query = request.GET.get('q', '')  # Search query
    category = request.GET.get('category', '')  # Selected category
    shop_name = request.GET.get('shop_name', '')  # Selected shop name
    filter_type = request.GET.get('filter', '')  # Existing filter

    products = Product.objects.annotate(avg_rating=Avg('rating__rating'))

    # Apply search filter if query is provided
    if query:
        products = products.filter(Q(name__icontains=query))

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

    # Convert product queryset to a list of dictionaries to return as JSON
    product_list = list(products.values('uuid', 'name', 'price', 'category', 'shop_name', 'avg_rating'))

    return JsonResponse({'products': product_list})

def show_best_10_products(request):
    products = Product.objects.annotate(avg_rating=Avg('rating__rating')).order_by('-avg_rating')[:10]
    return render(request, 'main.html', {'products': products})

from django.http import JsonResponse
from .models import Product
import json
from .models import Comment

def product_list(request):
    products = Product.objects.all()
    data = []
    for product in products:
        data.append({
            "uuid": str(product.uuid),
            "category": product.category,
            "name": product.name,
            "price": float(product.price),
            "desc": product.desc,
            "color": product.color,
            "stock": product.stock,
            "shop_name": product.shop_name,
            "location": product.location,
            "img_url": product.img_url,
        })
    return JsonResponse(data, safe=False)

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product, Comment
from django.contrib.auth.models import User

@login_required
@csrf_exempt
@require_POST
def add_comment_flutter(request):
    if request.method == 'POST':
        try:
            # Mengambil data JSON dari body request
            data = json.loads(request.body)

            # Mendapatkan data dari body JSON
            product_id = data['product_id']
            comment_text = data['comment']

            # Ambil produk berdasarkan UUID yang diberikan
            product = Product.objects.get(uuid=product_id)

            # Membuat dan menyimpan komentar baru
            new_comment = Comment.objects.create(
                product=product,
                user=request.user,  # Menggunakan user yang sedang login
                comment=comment_text
            )
            new_comment.save()

            return JsonResponse({
                "status": "success",
                "message": "Comment added successfully",
                "comment_id": new_comment.uuid,
                "user": new_comment.user.username,
                "timestamp": new_comment.timestamp.strftime("%d %B %Y, %H:%M"),
            }, status=200)
        except KeyError as e:
            return JsonResponse({"status": "error", "message": f"Missing field: {str(e)}"}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Product not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

@login_required
@csrf_exempt
@require_POST
@csrf_exempt
def add_rating_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            rating_value = data.get('rating')

            # Validasi input
            if not product_id or not rating_value:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            # Cari produk terkait
            product = Product.objects.filter(uuid=product_id).first()
            if not product:
                return JsonResponse({'error': 'Product not found'}, status=404)

            # Simpan rating
            Rating.objects.create(product=product, user=request.user, rating=rating_value)
            return JsonResponse({'message': 'Rating submitted successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Comment

from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['uuid', 'product', 'user', 'comment', 'timestamp']

class CommentList(APIView):
    def get(self, request, format=None):
        # Ambil semua komentar
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['RATING_CHOICES', 'uuid', 'product', 'user', 'rating', 'timestamp']

class RatingList(APIView):
    def get(self, request, format=None):
        # Ambil semua rating
        ratings = Rating.objects.all()
        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator

@require_GET
def get_comments_by_product(request, product_id):
    try:
        # Cari produk berdasarkan UUID
        product = Product.objects.get(uuid=product_id)

        # Ambil semua komentar untuk produk tersebut
        comments = Comment.objects.filter(product=product).select_related('user').order_by('-timestamp')

        # Serialisasi komentar menjadi JSON
        comments_data = [
            {
                'uuid': str(comment.uuid),
                'user': comment.user.username,
                'comment': comment.comment,
                'timestamp': comment.timestamp.strftime('%d %B %Y, %H:%M')
            }
            for comment in comments
        ]

        return JsonResponse({'comments': comments_data}, safe=False, status=200)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_GET
def get_ratings_by_product(request, product_id):
    try:
        # Cari produk berdasarkan UUID
        product = Product.objects.get(uuid=product_id)

        # Ambil semua rating untuk produk tersebut
        ratings = Rating.objects.filter(product=product).select_related('user').order_by('-timestamp')

        # Serialisasi rating menjadi JSON
        ratings_data = [
            {
                'uuid': str(rating.uuid),
                'user': rating.user.username,
                'rating': rating.rating,
                'timestamp': rating.timestamp.strftime('%d %B %Y, %H:%M')
            }
            for rating in ratings
        ]

        return JsonResponse({'ratings': ratings_data}, safe=False, status=200)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def delete_comment(request, comment_id):
    try:
        # Ambil komentar berdasarkan ID
        comment = get_object_or_404(Comment, uuid=comment_id)

        # Hanya izinkan user pemilik komentar untuk menghapus
        if request.user != comment.user:
            return JsonResponse(
                {'message': 'You are not allowed to delete this comment'},
                status=403
            )

        # Hapus komentar
        comment.delete()

        return JsonResponse({'message': 'Comment deleted successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)
    
@csrf_exempt
@login_required
def delete_rating(request, rating_id):
    try:
        # Ambil rating berdasarkan ID
        rating = get_object_or_404(Rating, uuid=rating_id)

        # Hanya izinkan user pemilik rating untuk menghapus
        if request.user != rating.user:
            return JsonResponse(
                {'message': 'You are not allowed to delete this rating'},
                status=403
            )

        # Hapus rating
        rating.delete()

        return JsonResponse({'message': 'Rating deleted successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'message': str(e)}, status=400)


@csrf_exempt
@login_required
@require_POST
def edit_comment(request, comment_id):
    try:
        new_comment_text = request.POST.get('comment')
        if not new_comment_text:
            return JsonResponse({"status": "error", "message": "No comment text provided"}, status=400)

        comment = Comment.objects.get(uuid=comment_id)
        if comment.user != request.user:
            return JsonResponse({"status": "error", "message": "You do not have permission to edit this comment"}, status=403)

        comment.comment = new_comment_text
        comment.timestamp = timezone.now()
        comment.save()

        return JsonResponse({
            "status": "success",
            "message": "Comment edited successfully",
            "comment_id": str(comment.uuid),
            "user": comment.user.username,
            "comment": comment.comment,
            "timestamp": comment.timestamp.strftime("%d %B %Y, %H:%M"),
        }, status=200)

    except Comment.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Comment not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
