
from django.db import models
from django.contrib.auth.models import User

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel

from wagtail.search import index

from tournaments.models import Series, Tournament
# Create your models here.


# Create your models here.
class SeriesIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro", classname="full")
    ]


class SeriesPage(Page):
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    parent_series = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    admin_user = models.ManyToManyField(User, null=True, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("admin_user"),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("parent_series"),
    ]

