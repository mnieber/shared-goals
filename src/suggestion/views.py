from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify
from django.views.generic import View
from django.utils.decorators import method_decorator

from goal.views import membership_required

from suggestion.forms import SuggestionForm
from suggestion.models import Suggestion, Revision


class PostSuggestionView(View):
    def get_posted_form(self, request, suggestion):
        def is_duplicate_title(title):
            return suggestion.goal.suggestions.filter(
                Q(slug=slugify(title)) & ~Q(pk=suggestion.pk)
            ).exists()

        form = SuggestionForm(request.POST, request.FILES)
        form.is_duplicate_title = is_duplicate_title

        return form

    def get_populated_form(self, request, suggestion):
        return SuggestionForm(
            instance=suggestion,
            initial=suggestion.get_current_revision().__dict__
        )

    def on_cancel(self, goal_slug):
        # todo redirect to previous page
        return HttpResponseRedirect(
            reverse(
                'goal',
                kwargs=dict(
                    goal_slug=goal_slug
                )
            )
        )

    def on_save(self, goal_slug, suggestion_slug):
        return HttpResponseRedirect(
            reverse(
                'suggestion',
                kwargs=dict(
                    goal_slug=goal_slug,
                    suggestion_slug=suggestion_slug
                )
            )
        )


class NewSuggestionView(PostSuggestionView):
    def get_or_create_draft(self, request):
        draft = Suggestion.objects.filter(
            is_draft=True, owner=request.member
        ).first()

        if not draft:
            draft = Suggestion()
            draft.owner = request.member
            draft.goal = request.goal
            draft.save()

            revision = Revision()
            revision.suggestion = draft
            revision.save()
        return draft

    def __update_suggestion_and_save(self, suggestion, request):
        form = self.get_posted_form(request, suggestion)
        is_form_valid = form.is_valid()

        current_revision = suggestion.get_current_revision()
        current_revision.title = form['title'].value()
        current_revision.description = form['description'].value()
        current_revision.save()

        if is_form_valid:
            # todo also save the cropping if the form is invalid
            suggestion.cropping = form.cleaned_data['cropping']
            if 'image' in request.FILES:
                suggestion.image = form.cleaned_data['image']

            if request.POST['submit'] == 'save':
                suggestion.slug = slugify(
                    suggestion.get_current_revision().title)
                suggestion.apply_cropping_to_image(replace_original=True)
                suggestion.is_draft = False

            suggestion.save()

        return is_form_valid

    @method_decorator(membership_required)
    @method_decorator(login_required)
    def get(self, request, goal_slug):
        return self.handle(request, goal_slug)

    @method_decorator(membership_required)
    @method_decorator(login_required)
    def post(self, request, goal_slug):
        return self.handle(request, goal_slug)

    def handle(self, request, goal_slug):
        suggestion = self.get_or_create_draft(request)
        is_saving = \
            request.method == 'POST' and request.POST['submit'] == 'save'

        if request.method == 'POST':
            should_accept_data = self.__update_suggestion_and_save(
                suggestion, request)

            if should_accept_data and is_saving:
                return self.on_save(request.goal.slug, suggestion.slug)
            elif request.POST['submit'] == 'cancel':
                return self.on_cancel(request.goal.slug)

        form = (
            self.get_posted_form(request, suggestion)
            if is_saving else
            self.get_populated_form(request, suggestion)
        )

        context = {
            'form': form,
            'show_image_form': True,
            'show_errors': is_saving,
            'cancel_button_label': "Save draft",
            'post_button_label': "Submit",
        }

        return render(request, 'suggestion/edit_suggestion.html', context)


class UpdateSuggestionView(PostSuggestionView):
    def __create_new_revision(self, suggestion, request):
        revision_form = self.get_posted_form(request, suggestion)
        is_form_valid = revision_form.is_valid()

        # todo see if duplication with update function can be removed
        if is_form_valid:
            revision = Revision()
            # todo use cleaned data
            revision.title = revision_form['title'].value()
            revision.description = revision_form['description'].value()
            revision.suggestion = suggestion
            revision.save()

        return is_form_valid

    @method_decorator(membership_required)
    @method_decorator(login_required)
    def get(self, request, goal_slug, suggestion_slug):
        return self.handle(request, goal_slug, suggestion_slug)

    @method_decorator(membership_required)
    @method_decorator(login_required)
    def post(self, request, goal_slug, suggestion_slug):
        return self.handle(request, goal_slug, suggestion_slug)

    def handle(self, request, goal_slug, suggestion_slug):
        suggestion = get_object_or_404(Suggestion, slug=suggestion_slug)
        is_posting = request.method == 'POST'

        if is_posting:
            should_accept_data = request.POST['submit'] == 'cancel' or \
                self.__create_new_revision(suggestion, request)

            if request.POST['submit'] == 'cancel':
                return self.on_cancel(request.goal.slug)
            elif request.POST['submit'] == 'save' and should_accept_data:
                return self.on_save(request.goal.slug, suggestion.slug)

        form = (
            self.get_posted_form(request, suggestion)
            if is_posting else
            self.get_populated_form(request, suggestion)
        )

        context = {
            'form': form,
            'show_image_form': False,
            'show_errors': True,
            'cancel_button_label': "Cancel",
            'post_button_label': "Update",
        }

        return render(request, 'suggestion/edit_suggestion.html', context)


class SuggestionView(View):
    def get(self, request, goal_slug, suggestion_slug):
        suggestion = get_object_or_404(Suggestion, slug=suggestion_slug)
        revision = suggestion.get_current_revision()

        context = {
            'suggestion': suggestion,
            'revision': revision,
        }
        return render(request, 'suggestion/suggestion.html', context)


class RevisionView(View):
    def get(self, request, goal_slug, suggestion_slug, revision_pk):
        revision = get_object_or_404(Revision, pk=revision_pk)

        context = {
            'suggestion': revision.suggestion,
            'revision': revision,
        }
        return render(request, 'suggestion/revision.html', context)