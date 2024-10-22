from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm

# Create your views here.

def post_detail(request, year, month, day, post): 
    post = get_object_or_404(Post, slug=post,
                                    status='published', 
                                    publish__year=year,
                                    publish__month=month,
                                    publish__day=day)
    
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST': 
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid(): 
            new_comment = comment_form.save(commit=False)

            new_comment.post = post

            new_comment.save()
    
    else: 
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                                    .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                .order_by('-same_tags', '-publish')[:4]

    return render(request,
                'blog/post/detail.html',
                {'post': post, 
                'comments': comments,
                'new_comment': new_comment,
                'comment_form': comment_form,
                'similar_posts': similar_posts})


def post_share(request, post_id): 
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST': 
        #Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            #Form fields passed validation
            cd = form.cleaned_data
            #... send email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends your read " \
                f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n "\
                f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'bigdub@localhost.com', [cd['to']])
            sent = True
    else: 
        form = EmailPostForm()
    
    return render(request, 'blog/post/share.html', {'post': post, 
                                                    'form': form,
                                                    'sent': sent})

def post_list(request, tag_slug=None): 
    object_list = Post.published.all()
    tag = None

    if tag_slug: 
        print(tag_slug)
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in =[tag])
    
    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    try: 
        posts = paginator.page(page)
    except PageNotAnInteger: 
        posts = paginator.page(1)
    except EmptyPage: 
        posts = paginator.page(paginator.num_pages)


    return render(request, 'blog/post/list.html',
                            {'posts': posts,
                            'page': page,
                            'tag': tag})

"""
def post_detail(request, year, month, day, post): 
    post = get_object_or_404(Post, slug=post, 
                                    status='published', 
                                    publish__year=year,
                                    publish__month=month,
                                    publish__day=day)
    
    return render(request, 'blog/post/detail.html',{'post': post})
"""

class PostListView(ListView): 
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3 
    template_name = 'blog/post/list.html'



def post_search(request): 
    form = SearchForm()
    query = None
    results = []
    result_list = []
    page = 1
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid(): 
            query = form.cleaned_data['query']
            page = form.cleaned_data['page']
            
            # Search Parameters
            search_vector = SearchVector('title', 'body')
            search_query = SearchQuery(query)
            search_rank = SearchRank(search_vector, search_query)
            
            result_list = Post.published.annotate(
                                                search = search_vector,
                                                rank = search_rank
                                                ).filter(
                                                    search=query
                                                    ).order_by(
                                                        '-rank'
                                                )
    paginator = Paginator(result_list, 3)
    page = request.GET.get('page')
    try: 
        results = paginator.page(page)
    except PageNotAnInteger: 
        results = paginator.page(1)
    except EmptyPage: 
        result = paginator.page(paginator.num_pages)                                                         
    return render (request, 
                    'blog/post/search.html',
                        {
                        'page': page,
                        'form': form,
                        'query': query,
                        'results': results
                        }
                    )                                               


    