from django.conf import settings

from django_dominate.django_tags import *

from dominate.tags import *
from dominate.util import text

from goal.templates.dominate_tags import *

from suggestion.templates.dominate_tags import *


def result():
    with django_block("content") as content:
        goal_header()

        with div(_class="row small-gap-below"):
            column(4)
            with column(4):
                suggestion_image("{{ revision.title }}")

        with div(_class="row small-gap-below"):
            column(2)
            with column(8):
                h5(
                    "Published by {{ suggestion.owner.global_user.name }}, "
                    "{{ suggestion.pub_date|naturaltime }}"
                )
                text("{{ revision.description|markdown }}")

        div(id="reviews")
        inline_script(settings.BASE_DIR, 'suggestion/load_reviews.js')

    return (
        "{% extends 'base.html' %}",
        "{% load staticfiles %}",
        "{% load markdown_deux_tags %}",
        "{% load humanize %}",
        content
    )

# done123