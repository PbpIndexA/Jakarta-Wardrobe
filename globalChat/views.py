from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Forum, Comment
from .forms import ForumForm, CommentForm
from django.http import JsonResponse
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count
import json

# Global Chat: List all forums with pagination
def global_chat(request):
    filter_option = request.GET.get('filter', 'newest')

    # Check if user is authenticated before filtering by user-specific attributes
    if not request.user.is_authenticated:
        # Redirect to login if trying to access user-specific filters while not logged in
        if filter_option in ['your_posts', 'saved']:
            return redirect('main:login')

    if filter_option == 'your_posts':
        # Filter forums by the current user
        forums_list = Forum.objects.filter(user=request.user).order_by('-posted_time')
    elif filter_option == 'most_likes':
        # Sort forums by likes count in descending order
        forums_list = Forum.objects.annotate(num_likes=Count('likes')).order_by('-num_likes', '-posted_time')
    elif filter_option == 'saved':
        # Filter forums that are bookmarked by the current user
        forums_list = Forum.objects.filter(bookmarks=request.user).order_by('-posted_time')
    else:
        # Default to newest posts (all posts)
        forums_list = Forum.objects.all().order_by('-posted_time')

    paginator = Paginator(forums_list, 5)  # Show 5 forums per page
    page_number = request.GET.get('page')
    forums = paginator.get_page(page_number)

    context = {
        'forums': forums,
        'filter_option': filter_option,  # Pass the current filter to the template
    }
    return render(request, 'global_chat.html', context)

# Forum Detail View
@login_required(login_url="main:login")
def detail_chat(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    comments = Comment.objects.filter(forum=forum).order_by('-posted_time')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.forum = forum
            comment.user = request.user  # Menyimpan user yang berkomentar
            comment.save()
            return redirect('globalChat:detail_chat', forum_id=forum.id)
    else:
        form = CommentForm()

    context = {
        'forum': forum,
        'comments': comments,
        'form': form,
    }
    return render(request, 'detail_chat.html', context)

# Create a new forum post
@login_required(login_url="main:login")
def new_forum(request):
    if request.method == 'POST':
        form = ForumForm(request.POST)
        if form.is_valid():
            forum = form.save(commit=False)
            forum.user = request.user  # Set current logged-in user
            forum.save()
            return redirect('globalChat:global_chat')  # Redirect to global_chat after submit
        else:
            print(form.errors)  # Cetak errors untuk debugging
    else:
        form = ForumForm()

    return render(request, 'new_forum.html', {'form': form})


@login_required(login_url="main:login")
def toggle_like_forum(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    if request.user in forum.likes.all():
        forum.likes.remove(request.user)
        liked = False
    else:
        forum.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'like_count': forum.likes.count()})

@login_required(login_url="main:login")
def edit_forum(request, id):
    forum = get_object_or_404(Forum, id=id)
    if request.user != forum.user:
        return redirect('globalChat:global_chat')  # Redirect jika bukan pembuat forum

    if request.method == 'POST':
        form = ForumForm(request.POST, instance=forum)
        if form.is_valid():
            form.save()
            return redirect('globalChat:detail_chat', forum.id)
    else:
        form = ForumForm(instance=forum)
    
    return render(request, 'edit_forum.html', {'form': form, 'forum': forum})

@login_required(login_url="main:login")
def delete_forum(request, id):
    forum = get_object_or_404(Forum, id=id)
    if request.user == forum.user:
        forum.delete()
    return redirect('globalChat:global_chat')

@login_required(login_url="main:login")
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    forum = get_object_or_404(Forum, id=comment.forum.id)

    # Check if the logged-in user is either the comment owner or the forum owner
    if comment.user == request.user or forum.user == request.user:
        comment.delete()
        return redirect('globalChat:detail_chat', forum_id=forum.id)  # Redirect to the forum post after deleting the comment
    else:
        return redirect('globalChat:detail_chat', forum_id=forum.id)  # If not authorized, redirect back
    
@login_required(login_url="main:login")
def toggle_bookmark(request, forum_id):
    forum = get_object_or_404(Forum, id=forum_id)
    if request.user in forum.bookmarks.all():
        forum.bookmarks.remove(request.user)
        bookmarked = False
    else:
        forum.bookmarks.add(request.user)
        bookmarked = True
    return JsonResponse({'bookmarked': bookmarked})


## Flutter version
@csrf_exempt
def global_chat_flutter(request):
    filter_option = request.GET.get('filter', 'newest')
    page_number = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 5))

    forums = Forum.objects.all()

    if filter_option == 'your_posts' and request.user.is_authenticated:
        forums = forums.filter(user=request.user)
    elif filter_option == 'most_likes':
        forums = forums.annotate(like_count=Count('likes')).order_by('-like_count', '-posted_time')
    elif filter_option == 'saved' and request.user.is_authenticated:
        forums = forums.filter(bookmarks=request.user)

    forums = forums.order_by('-posted_time')

    paginator = Paginator(forums, per_page)
    page_obj = paginator.get_page(page_number)

    results = [
        {
            'id': forum.id,
            'title': forum.title,
            'description': forum.description,
            'purpose': forum.purpose,
            'user': forum.user.username,
            'posted_time': forum.posted_time.strftime('%Y-%m-%d %H:%M:%S'),
            'like_count': forum.likes.count(),
            'bookmark_count': forum.bookmarks.count(),
            'is_liked': request.user in forum.likes.all(),
            'is_bookmarked': request.user in forum.bookmarks.all(),

        }
        for forum in page_obj.object_list
    ]

    return JsonResponse({
        'forums': results,
        'total_pages': paginator.num_pages,
        'current_page': page_number,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next()
    })

@csrf_exempt
@csrf_exempt
def create_forum_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['title', 'description', 'purpose']
            
            # Periksa apakah semua field ada
            for field in required_fields:
                if field not in data:
                    return JsonResponse({"success": False, "message": f"Missing field: {field}"}, status=400)

            # Validasi tambahan (jika perlu)
            if not data['title'].strip():
                return JsonResponse({"success": False, "message": "Title cannot be empty"}, status=400)
            if not data['description'].strip():
                return JsonResponse({"success": False, "message": "Description cannot be empty"}, status=400)

            # Buat forum
            forum = Forum.objects.create(
                title=data['title'],
                description=data['description'],
                purpose=data['purpose'],
                user=request.user
            )

            return JsonResponse({
                "success": True,
                "message": "Forum created successfully",
                "forum": {
                    "id": forum.id,
                    "title": forum.title,
                    "description": forum.description,
                    "purpose": forum.purpose
                }
            }, status=201)
        except json.JSONDecodeError as e:
            return JsonResponse({"success": False, "message": "Invalid JSON payload"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def edit_forum_flutter(request, forum_id):
    if request.method == 'POST':
        try:
            forum = Forum.objects.get(pk=forum_id)

            if request.user != forum.user:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

            data = json.loads(request.body)

            forum.title = data.get('title', forum.title)
            forum.description = data.get('description', forum.description)
            forum.purpose = data.get('purpose', forum.purpose)
            forum.save()

            return JsonResponse({
                "success": True,
                "message": "Forum updated successfully",
                "forum": {
                    "id": forum.id,
                    "title": forum.title,
                    "description": forum.description,
                    "purpose": forum.purpose,
                    "posted_time": forum.posted_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=200)
        except Forum.DoesNotExist:
            return JsonResponse({"success": False, "message": "Forum not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def edit_forum_flutter(request, forum_id):
    if request.method == 'POST':
        try:
            forum = Forum.objects.get(pk=forum_id)

            if request.user != forum.user:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

            data = json.loads(request.body)

            forum.title = data.get('title', forum.title)
            forum.description = data.get('description', forum.description)
            forum.purpose = data.get('purpose', forum.purpose)
            forum.save()

            return JsonResponse({
                "success": True,
                "message": "Forum updated successfully",
                "forum": {
                    "id": forum.id,
                    "title": forum.title,
                    "description": forum.description,
                    "purpose": forum.purpose,
                    "posted_time": forum.posted_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=200)
        except Forum.DoesNotExist:
            return JsonResponse({"success": False, "message": "Forum not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def delete_forum_flutter(request, forum_id):
    if request.method == 'DELETE':
        try:
            forum = Forum.objects.get(pk=forum_id)

            if request.user != forum.user and not request.user.is_staff:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

            forum.delete()

            return JsonResponse({"success": True, "message": "Forum deleted successfully"}, status=200)
        except Forum.DoesNotExist:
            return JsonResponse({"success": False, "message": "Forum not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def toggle_like_forum_flutter(request, forum_id):
    if request.method == 'POST':
        try:
            forum = Forum.objects.get(pk=forum_id)

            if request.user in forum.likes.all():
                forum.likes.remove(request.user)
                liked = False
            else:
                forum.likes.add(request.user)
                liked = True

            return JsonResponse({
                "success": True,
                "liked": liked,
                "like_count": forum.likes.count()
            }, status=200)
        except Forum.DoesNotExist:
            return JsonResponse({"success": False, "message": "Forum not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def add_comment_flutter(request, forum_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            forum = Forum.objects.get(pk=forum_id)
            user = request.user

            if not user.is_authenticated:
                return JsonResponse({"success": False, "message": "User not authenticated"}, status=403)

            comment = Comment.objects.create(
                forum=forum,
                user=user,
                text=data['text']
            )

            return JsonResponse({
                "success": True,
                "message": "Comment added successfully",
                "comment": {
                    "id": comment.id,
                    "text": comment.text,
                    "user": comment.user.username,
                    "posted_time": comment.posted_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=201)
        except Forum.DoesNotExist:
            return JsonResponse({"success": False, "message": "Forum not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

@csrf_exempt
def get_comments_flutter(request, forum_id):
    try:
        forum = get_object_or_404(Forum, id=forum_id)
        comments = Comment.objects.filter(forum=forum).order_by('-posted_time')
        
        comments_data = [{
            'id': comment.id,
            'text': comment.text,
            'user': comment.user.username,
            'posted_time': comment.posted_time.strftime('%Y-%m-%d %H:%M:%S')
        } for comment in comments]
        
        return JsonResponse({
            'comments': comments_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@csrf_exempt
def delete_comment_flutter(request, comment_id):
    if request.method == 'POST':
        try:
            comment = get_object_or_404(Comment, id=comment_id)
            
            if request.user != comment.user and request.user != comment.forum.user:
                return JsonResponse({
                    'success': False,
                    'message': 'Unauthorized'
                }, status=403)
                
            comment.delete()
            return JsonResponse({
                'success': True,
                'message': 'Comment deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)