import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core import management
from django.contrib.auth.models import User

from goal.models import GlobalUser, Member, Goal
from proposal.models import Comment, Proposal, Review, Revision

from .yoga_acrobatics import text as yoga_acrobatics_content
from .yoga_bend import text as yoga_bend_content
from .yoga_meditate import text as yoga_meditate_content
from .yoga_twist import text as yoga_twist_content
from .yoga_twist_2 import text as yoga_twist_2_content


# from django.core.management.base import CommandError


class Command(BaseCommand):
    help = \
        'Populates the database with example proposals'

    def add_arguments(self, parser):
        pass

    def __migrate(self):
        if settings.DATABASES['default']['NAME'] == ":memory:":
            management.call_command('migrate', '--run-syncdb')
        else:
            management.call_command('migrate', '--run-syncdb')
            management.call_command(
                'makemigrations', 'goal', 'proposal')
            management.call_command('migrate', '--fake-initial')

    def __make_global_user(self, username, password, first_name, last_name):
        user = User.objects.get_or_create(username=username)[0]
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        global_user = GlobalUser()
        global_user.user = user
        global_user.save()

        return global_user

    def __create_superuser(self):
        management.call_command(
            'createsuperuser',
            '--noinput',
            username='mnieber',
            email='hallomaarten@yahoo.com'
        )

        self.user_mnieber = self.__make_global_user(
            'mnieber', '***REMOVED***', 'Maarten', 'Nieber')

    def __create_users(self):
        self.user_anders_om = self.__make_global_user(
            "andersom", "***REMOVED***", "Anders", "Om")

        self.user_marie_houana = self.__make_global_user(
            "mhouana", "***REMOVED***", "Maria", "Houana")

    def __create_goal(self):
        self.become_a_yogi = Goal()
        self.become_a_yogi.owner = self.user_marie_houana
        self.become_a_yogi.title = "Become a yogi"
        self.become_a_yogi.save()

    def __create_members(self):
        self.yogi_mnieber = Member()
        self.yogi_mnieber.global_user = self.user_mnieber
        self.yogi_mnieber.goal = self.become_a_yogi
        self.yogi_mnieber.save()

        self.yogi_anders_om = Member()
        self.yogi_anders_om.global_user = self.user_anders_om
        self.yogi_anders_om.goal = self.become_a_yogi
        self.yogi_anders_om.save()

        self.yogi_marie_houana = Member()
        self.yogi_marie_houana.global_user = self.user_marie_houana
        self.yogi_marie_houana.goal = self.become_a_yogi
        self.yogi_marie_houana.save()

    def __create_proposals(self):
        self.yoga_bend = Proposal()
        self.yoga_bend.goal = self.become_a_yogi
        self.yoga_bend.owner = self.yogi_mnieber
        self.yoga_bend.is_draft = False
        self.yoga_bend.image = "proposals/KroukTom-710x300-crop.jpg"
        self.yoga_bend.slug = "bend-backwards"
        self.yoga_bend.save()

        yoga_bend = Revision()
        yoga_bend.title = "Bend backwards"
        yoga_bend.description = yoga_bend_content
        yoga_bend.proposal = self.yoga_bend
        yoga_bend.save()

        self.yoga_meditate = Proposal()
        self.yoga_meditate.goal = self.become_a_yogi
        self.yoga_meditate.owner = self.yogi_mnieber
        self.yoga_meditate.is_draft = False
        self.yoga_meditate.image = "proposals/Yoga_Nidra.jpg"
        self.yoga_meditate.slug = "meditate-often"
        self.yoga_meditate.save()

        yoga_meditate = Revision()
        yoga_meditate.title = "Meditate often"
        yoga_meditate.description = yoga_meditate_content
        yoga_meditate.proposal = self.yoga_meditate
        yoga_meditate.save()

        self.yoga_twist = Proposal()
        self.yoga_twist.goal = self.become_a_yogi
        self.yoga_twist.owner = self.yogi_anders_om
        self.yoga_twist.is_draft = False
        self.yoga_twist.image = "proposals/MC_AM06_00_sized2.jpg"
        self.yoga_twist.slug = "keep-twisting"
        self.yoga_twist.save()

        self.rev_yoga_twist = Revision()
        self.rev_yoga_twist.title = "Keep twisting"
        self.rev_yoga_twist.description = yoga_twist_content
        self.rev_yoga_twist.proposal = self.yoga_twist
        self.rev_yoga_twist.save()

        time.sleep(1)

        self.rev_yoga_twist_2 = Revision()
        self.rev_yoga_twist_2.title = "Keep twisting"
        self.rev_yoga_twist_2.description = yoga_twist_2_content
        self.rev_yoga_twist_2.proposal = self.yoga_twist
        self.rev_yoga_twist_2.save()

        self.yoga_acrobatics = Proposal()
        self.yoga_acrobatics.goal = self.become_a_yogi
        self.yoga_acrobatics.owner = self.yogi_marie_houana
        self.yoga_acrobatics.is_draft = False
        self.yoga_acrobatics.image = "proposals/yoga-acrobats.jpg"
        self.yoga_acrobatics.slug = "yoga-acrobatics"
        self.yoga_acrobatics.save()

        yoga_acrobatics = Revision()
        yoga_acrobatics.title = "Acrobatics"
        yoga_acrobatics.description = yoga_acrobatics_content
        yoga_acrobatics.proposal = self.yoga_acrobatics
        yoga_acrobatics.save()

    def __create_reviews(self):
        self.review_yoga_twist = Review()
        self.review_yoga_twist.owner = self.yogi_marie_houana
        self.review_yoga_twist.revision = self.rev_yoga_twist
        self.review_yoga_twist.rating = 2.5
        self.review_yoga_twist.description = "Not bad!"
        self.review_yoga_twist.is_draft = False
        self.review_yoga_twist.save()

        self.review_yoga_twist_2 = Review()
        self.review_yoga_twist_2.owner = self.yogi_mnieber
        self.review_yoga_twist_2.revision = self.rev_yoga_twist_2
        self.review_yoga_twist_2.rating = 4
        self.review_yoga_twist_2.description = "Good, good, good"
        self.review_yoga_twist_2.is_draft = False
        self.review_yoga_twist_2.save()

    def __create_comments(self):
        self.comment_1 = Comment()
        self.comment_1.owner = self.yogi_mnieber.global_user
        self.comment_1.body = "Thanks for the feedback"
        self.comment_1.target = self.review_yoga_twist
        self.comment_1.is_draft = False
        self.comment_1.save()

        self.comment_2 = Comment()
        self.comment_2.owner = self.yogi_anders_om.global_user
        self.comment_2.body = "I see your point"
        self.comment_2.target = self.review_yoga_twist
        self.comment_2.is_draft = False
        self.comment_2.save()

    def handle(self, *args, **options):
        self.__migrate()
        self.__create_superuser()
        self.__create_users()
        self.__create_goal()
        self.__create_members()
        self.__create_proposals()
        self.__create_reviews()
        self.__create_comments()