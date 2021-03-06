import calendar
import datetime
import pdb
from django.shortcuts import render, render_to_response
from blog.models import BlogPost, Comment, UserLikes
from blog.forms import userForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.core.serializers import serialize


def index(request):
    posts = BlogPost.objects.order_by('-pubDate')[:5]

    context_dict = {'posts': posts}
    return render(request, 'blog/index.html', context_dict)


def get_entries(request):
    page = int(request.POST.get('page_num'))
    start = page * 5
    end = start + 5
    posts = BlogPost.objects.order_by('-pubDate')[start:end]
    context_dict = {'posts': posts}

    return render_to_response('blog/post_template.html', context_dict)


def blog_post(request, blog_post_slug):
    context_dict = {}

    try:
        post = BlogPost.objects.get(slug=blog_post_slug)
        comments = Comment.objects.filter(parent=post)

        context_dict['post'] = post
        context_dict['comments'] = comments
        context_dict['num_comments'] = len(comments)

    except BlogPost.DoesNotExist:
        pass

    return render(request, 'blog/post.html', context_dict)


def archive(request, archive_slug):
    try:
        datestr = archive_slug.replace("-", " ")
        date = datetime.datetime.strptime(datestr, "%B %Y")
        last_day = calendar.monthrange(date.year, date.month)[1]
        start_date = datetime.date(date.year, date.month, date.day)
        end_date = datetime.date(date.year, date.month, last_day)
        posts = BlogPost.objects.filter(pubDate__range=(start_date, end_date))
        context_dict = {"posts": posts}

        return render(request, 'blog/archive.html', context_dict)
    except:
        return HttpResponse("There was an error in processing your request")


def register(request):
    context_dict = {}

    if request.method == "POST":
        form = userForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.save()

            return index(request)

    else:
        form = userForm()

    context_dict['form'] = form
    return render(request, 'blog/register.html', context_dict)


def user_login(request):
    if (request.method == "POST") and (not request.user.is_authenticated()):
        username = request.POST.get('user')
        password = request.POST.get('pass')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return index(request)
            else:
                return HttpResponse("Your account is disabled")
        else:
            return HttpResponse("Invalid login details")
    else:
        return render(request, 'blog/login.html', {})


@login_required
def user_logout(request):
    logout(request)
    return index(request)


@login_required
def post_comment(request):
    slug = request.POST.get('path').split('/')[-2]
    parent_post = BlogPost.objects.get(slug=slug)
    username = request.user.get_username()
    today = timezone.now()
    comment = request.POST.get('post_comment')

    posted_comment = Comment(parent=parent_post,
                             author=username,
                             pubDate=today,
                             body=comment,
                             likes=1)
    posted_comment.save()

    user = User.objects.get(username=username)
    isLiked = UserLikes(user=user, comment=posted_comment, liked=True)
    isLiked.save()

    context_dict = {}
    context_dict['comment'] = posted_comment
    context_dict['classes'] = "btn btn-success btn-xs likebtn liked"

    return render_to_response('blog/comment_template.html', context_dict)


@login_required
def like(request):
    comment_id = request.POST.get("id")
    comment = Comment.objects.get(pk=comment_id)
    username = request.user.get_username()
    user = User.objects.get(username=username)
    isLiked = UserLikes.objects.get_or_create(user=user, comment=comment)[0]
    if not isLiked.liked:
        comment.likes += 1
        comment.save()
        isLiked.liked = True
        isLiked.save()
    else:
        comment.likes -= 1
        comment.save()
        isLiked.liked = False
        isLiked.save()

    return HttpResponse(comment.likes)
