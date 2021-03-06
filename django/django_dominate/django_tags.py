import os

from dominate.tags import html_tag
from dominate.tags import script
from dominate.util import raw


class django_tag(html_tag):
    closing_tag = ""

    def get_opening_tag(self, tag_inner):
        raise

    def _render(self, rendered, indent=1, inline=False):
        from_index = len(rendered)
        tag_inner = self.children[0]
        del self.children[0]

        super(html_tag, self)._render(rendered, indent, inline)
        for i in range(2):
            rendered.pop()
            del rendered[from_index]
        rendered[from_index] = (
            self.get_opening_tag(tag_inner)
        )
        rendered[-1] = self.closing_tag
        return rendered


class django_block(django_tag):
    closing_tag = "{% endblock %}"

    def get_opening_tag(self, tag_inner):
        return "{%% block %s %%}" % tag_inner


class django_for(django_tag):
    closing_tag = "{% endfor %}"

    def get_opening_tag(self, tag_inner):
        return "{%% for %s %%}" % tag_inner


class django_with(django_tag):
    closing_tag = "{% endwith %}"

    def get_opening_tag(self, tag_inner):
        return "{%% with %s %%}" % tag_inner


class django_if(django_tag):
    closing_tag = "{% endif %}"

    def get_opening_tag(self, tag_inner):
        return "{%% if %s %%}" % tag_inner


class django_thumbnail(django_tag):
    closing_tag = "{% endthumbnail %}"

    def get_opening_tag(self, tag_inner):
        return "{%% thumbnail %s %%}" % tag_inner


class django_single(html_tag):
    tag = "undefined"

    def _render(self, rendered, indent=1, inline=False):
        from_index = len(rendered)
        super(html_tag, self)._render(rendered, indent, inline)
        for i in range(2):
            rendered.pop()
            del rendered[from_index]
        rendered[from_index] = self.tag
        del rendered[-1]
        return rendered


class django_else(django_single):
    tag = "{% else %}"


class django_empty(django_single):
    tag = "{% empty %}"


class django_csrf_token(django_single):
    tag = "{% csrf_token %}"


def inline_script(base_path, script_path):
    comment = (
        "\n// %s\n" % script_path
        if script_path else
        ""
    )

    with open(os.path.join(base_path, script_path)) as ifs:
        with script() as result:
            raw(comment + ifs.read())
        return result
