from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from .models import Post
import markdown

class LatestPostsFeed(Feed): 
    title = 'My blog'
    link = reverse_lazy('blog:post_list')
    description = 'New Posts on My Blog'

    def items(self): 
        return Post.published.all()[:5]

    def item_title(self, item): 
        return item.title

    def item_description(self, item):
        text = markdown.markdown(item.body) 
        return truncatewords_html(text, 30)