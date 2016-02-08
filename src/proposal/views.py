from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template.defaultfilters import slugify
from django.views.generic import View
from goal.models import Goal, Member

from proposal.forms import CommentForm, RevisionForm, ProposalForm, ReviewForm
from proposal.models import Comment, Proposal, Review, Revision


class EditProposalView(View):
    def __get_or_create_draft(self, member, goal):
        draft = Proposal.objects.filter(
            is_draft=True, owner=member
        ).first()

        if not draft:
            draft = Proposal()
            draft.owner = member
            draft.goal = goal
            draft.save()

            revision = Revision()
            revision.proposal = draft
            revision.save()
        return draft

    def __get_posted_forms(self, request):
        return (
            RevisionForm(request.POST, request.FILES),
            ProposalForm(request.POST, request.FILES)
        )

    def __get_populated_forms(self, request, draft):
        return (
            RevisionForm(initial=draft.get_current_revision().__dict__),
            ProposalForm(
                initial=draft.__dict__,
                files=dict(image=draft.image)
            )
        )

    def __update_proposal_and_save(self, proposal, request):
        revision_form, proposal_form = self.__get_posted_forms(request)
        is_revision_form_valid = revision_form.is_valid()
        is_proposal_form_valid = proposal_form.is_valid()

        current_revision = proposal.get_current_revision()
        current_revision.title = revision_form['title'].value()
        current_revision.description = revision_form['description'].value()
        current_revision.save()

        if is_proposal_form_valid:
            if 'image' in request.FILES:
                proposal.image = proposal_form.cleaned_data['image']
            proposal.cropping = proposal_form.cleaned_data['cropping']

            if is_revision_form_valid and request.POST['submit'] == 'save':
                proposal.slug = slugify(proposal.get_current_revision().title)
                proposal.apply_cropping_to_image(replace_original=True)
                proposal.is_draft = False

            proposal.save()

        return is_revision_form_valid and is_proposal_form_valid

    def __create_new_revision(self, proposal, request):
        revision_form, proposal_form = self.__get_posted_forms(request)
        is_revision_form_valid = revision_form.is_valid()
        if is_revision_form_valid:
            revision = Revision()
            revision.title = revision_form['title'].value()
            revision.description = revision_form['description'].value()
            revision.proposal = proposal
            revision.save()

        return is_revision_form_valid

    def __on_cancel(self, goal_slug):
        # todo redirect to previous page
        return HttpResponseRedirect(
            reverse(
                'goal',
                kwargs=dict(
                    goal_slug=goal_slug
                )
            )
        )

    def __on_save(self, goal_slug, proposal_slug):
        return HttpResponseRedirect(
            reverse(
                'proposal',
                kwargs=dict(
                    goal_slug=goal_slug,
                    proposal_slug=proposal_slug
                )
            )
        )

    def get(self, request, goal_slug, proposal_slug=""):
        return self.handle(request, goal_slug, proposal_slug)

    def post(self, request, goal_slug, proposal_slug=""):
        return self.handle(request, goal_slug, proposal_slug)

    def handle(self, request, goal_slug, proposal_slug):
        goal = get_object_or_404(Goal, slug=goal_slug)
        member = get_object_or_404(Member, user=request.user)
        proposal = (
            get_object_or_404(Proposal, slug=proposal_slug) if proposal_slug
            else self.__get_or_create_draft(member, goal)
        )
        is_posting = request.method == 'POST'

        if is_posting:
            if proposal_slug:
                should_accept_data = request.POST['submit'] == 'cancel' or \
                    self.__create_new_revision(proposal, request)
            else:
                should_accept_data = \
                    self.__update_proposal_and_save(proposal, request)

            if request.POST['submit'] == 'cancel':
                return self.__on_cancel(goal.slug)
            elif request.POST['submit'] == 'save' and should_accept_data:
                return self.__on_save(goal.slug, proposal.slug)

        revision_form, proposal_form = (
            self.__get_posted_forms(request) if is_posting else
            self.__get_populated_forms(request, proposal)
        )

        context = {
            'goal': goal,
            'member': member,
            'revision_form': revision_form,
            'proposal_form': proposal_form,
        }
        return render(request, 'proposal/new_proposal.html', context)


class ProposalView(View):
    def __publish_review(
        self, member, proposal, rating, description, existing_review
    ):
        if existing_review:
            existing_review.delete()

    def __on_cancel_or_save(self, goal_slug, proposal_slug):
        return HttpResponseRedirect(
            reverse(
                'proposal',
                kwargs=dict(
                    goal_slug=goal_slug,
                    proposal_slug=proposal_slug
                )
            )
        )

    def __get_or_create_review(self, member, revision, all_reviews):
        review = all_reviews.filter(owner=member).first()
        if not review:
            review = Review()
            review.owner = member
            review.revision = revision
            review.save()

        return review

    def __update_review_and_save(self, review, request):
        form = ReviewForm(request.POST, request.FILES)
        is_form_valid = form.is_valid()
        if is_form_valid:
            review.rating = form.cleaned_data['rating']
            review.description = form.cleaned_data['description']

            if request.POST['submit'] == 'save':
                review.is_draft = False

            review.save()

        return is_form_valid

    def get(self, request, goal_slug, proposal_slug):
        return self.handle(request, goal_slug, proposal_slug)

    def post(self, request, goal_slug, proposal_slug):
        return self.handle(request, goal_slug, proposal_slug)

    def handle(self, request, goal_slug, proposal_slug):
        goal = get_object_or_404(Goal, slug=goal_slug)
        member = Member.objects.filter(user=request.user).first()
        proposal = get_object_or_404(Proposal, slug=proposal_slug)
        revision = proposal.get_current_revision()
        all_reviews = Review.objects.filter(revision__proposal=proposal)
        review = self.__get_or_create_review(member, revision, all_reviews)
        is_posting = request.method == 'POST'

        if is_posting:
            is_data_valid = self.__update_review_and_save(review, request)
            try_again = request.POST['submit'] == 'save' and not is_data_valid
            if not try_again:
                return self.__on_cancel_or_save(goal.slug, proposal.slug)

        form = (
            ReviewForm(request.POST, request.FILES) if is_posting
            else ReviewForm(initial=review.__dict__)
        )

        def inject_header_text(review, current_revision):
            def upperfirst(x):
                return x[0].upper() + x[1:]

            header = \
                "reviewed by " if review.description \
                else "rated by "
            header += review.owner.user.get_full_name()
            header += ", %s" % naturaltime(review.pub_date)

            setattr(
                review,
                'header',
                upperfirst(header) if review.revision_id == current_revision.pk
                else header
            )

            return review

        current_revision = proposal.get_current_revision()
        other_reviews = [
            inject_header_text(x, current_revision)
            for x in all_reviews.filter(~Q(pk=review.pk) & Q(is_draft=False))
        ]

        context = {
            'goal': goal,
            'proposal': proposal,
            'revision': revision,
            'member': member,
            'review': review,
            'post_button_label': "Submit" if review.is_draft else "Update",
            'form': form,
            'other_reviews': other_reviews,
        }
        return render(request, 'proposal/proposal.html', context)


class ReviewView(View):
    def __get_or_create_draft(self, member, review):
        draft = review.comments.filter(is_draft=True, owner=member).first()

        if not draft:
            draft = Comment()
            draft.owner = member
            draft.target = review
            draft.save()

        return draft

    def __inject_header_text(self, review):
        header = \
            "Review by " + review.owner.user.get_full_name() \
            + ", %s" % naturaltime(review.pub_date)

        setattr(review, 'header', header)
        return review

    def __update_comment_and_save(self, comment, request):
        form = CommentForm(request.POST, request.FILES)
        is_form_valid = form.is_valid()
        if is_form_valid:
            comment.body = form.cleaned_data['body']
            if request.POST['submit'] == 'save':
                comment.is_draft = False
            comment.save()

        return is_form_valid

    def __on_cancel_or_save(self, goal_slug, proposal_slug, review_pk):
        return HttpResponseRedirect(
            reverse(
                'review',
                kwargs=dict(
                    goal_slug=goal_slug,
                    proposal_slug=proposal_slug,
                    review_pk=review_pk
                )
            )
        )

    def get(self, request, goal_slug, proposal_slug, review_pk):
        return self.handle(request, goal_slug, proposal_slug, review_pk)

    def post(self, request, goal_slug, proposal_slug, review_pk):
        return self.handle(request, goal_slug, proposal_slug, review_pk)

    def handle(self, request, goal_slug, proposal_slug, review_pk):
        goal = get_object_or_404(Goal, slug=goal_slug)
        member = Member.objects.filter(user=request.user).first()
        review = get_object_or_404(Review, pk=review_pk)

        draft = self.__get_or_create_draft(member, review)
        is_posting = request.method == 'POST'

        if is_posting:
            is_data_valid = self.__update_comment_and_save(draft, request)
            try_again = request.POST['submit'] == 'save' and not is_data_valid
            if not try_again:
                return self.__on_cancel_or_save(
                    goal_slug, proposal_slug, review_pk)

        form = (
            CommentForm(request.POST, request.FILES) if is_posting
            else CommentForm(initial=draft.__dict__)
        )

        self.__inject_header_text(review)

        context = {
            'goal': goal,
            'proposal': review.revision.proposal,
            'member': member,
            'review': review,
            'comments': [x for x in review.comments.filter(is_draft=False)],
            'revision': review.revision,
            'form': form
        }
        return render(request, 'proposal/review.html', context)
