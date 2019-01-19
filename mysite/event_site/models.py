from django.db import models
from django.utils import timezone

from django.shortcuts import render

from django.contrib.auth.models import User

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel

from wagtail.search import index

from copy import copy
import random
import networkx as nx


# Create your models here.


class RegionPage(Page):
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = RichTextField(blank=True, null=True)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
    ]


class CountryPage(Page):
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = RichTextField(blank=True, null=True)

    parent_region = models.ForeignKey(RegionPage, on_delete=models.PROTECT)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("parent_region"),
    ]


class PrefecturePage(Page):
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = RichTextField(blank=True, null=True)

    parent_country = models.ForeignKey(CountryPage, on_delete=models.PROTECT)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("parent_country"),
    ]


class CityPage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True)
    body = RichTextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    parent_prefecture = models.ForeignKey(PrefecturePage, on_delete=models.PROTECT)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("is_active"),
        FieldPanel("parent_prefecture"),
    ]


class VenuePage(Page):
    intro = models.CharField(max_length=250, null=True, blank=True)
    body = RichTextField(blank=True, null=True)

    parent_city = models.ForeignKey(CityPage, on_delete=models.PROTECT)

    zip = models.CharField(max_length=7)
    address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    website_url = models.CharField(max_length=2048, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.SearchField("phone_number"),
        index.SearchField("website_url")
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("parent_city"),
        FieldPanel("zip"),
        FieldPanel("address"),
        FieldPanel("phone_number"),
        FieldPanel("website_url"),
        FieldPanel("is_active"),
    ]


class VenueRoomPage(Page):
    # VenuePageにリダイレクトする予定。
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = RichTextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    parent_venue = models.ForeignKey(VenuePage, on_delete=models.PROTECT)

    search_fields = Page.search_fields + [
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("is_active"),
        FieldPanel("parent_venue"),
    ]


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
    admin_user = models.ManyToManyField(User, blank=True)

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


class TournamentPage(Page):
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    start_datetime = models.DateTimeField(default=timezone.now)

    admin_user = models.ManyToManyField(User, blank=True)

    parent_series = models.ForeignKey(SeriesPage, on_delete=models.PROTECT)
    venue_room = models.ManyToManyField(VenueRoomPage, blank=True)
    is_active = models.BooleanField(default=True)

    max_player_count = models.IntegerField()
    top_cut_count = models.IntegerField(null=True)
    default_time_limit_in_sec = models.IntegerField(default=1500)
    max_round = models.IntegerField(default=-1, null=True, blank=True)
    max_win_count_in_match = models.IntegerField(default=1)
    bye_win_count_in_match = models.IntegerField(default=1)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.SearchField("venue_room"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("admin_user"),
        FieldPanel("start_datetime"),
        FieldPanel("parent_series"),
        FieldPanel("venue_room"),
        FieldPanel("is_active"),
        FieldPanel("max_player_count"),
        FieldPanel("top_cut_count"),
        FieldPanel("default_time_limit_in_sec"),
        FieldPanel("max_round"),
        FieldPanel("max_win_count_in_match"),
        FieldPanel("bye_win_count_in_match"),
    ]

    def add_player(self, user_id):
        players = self.playerpage_set.all()
        players_number = len(players)
        user = User.objects.get(id=user_id)

        if players.filter(user=user):
            return [players.get(user=user), False]

        elif players_number < self.max_player_count:
            new_player = PlayerPage(user=user, parent_tournament=self, title=user.username)
            self.add_child(instance=new_player)
            return [new_player, True]

        else:
            return [None, False]

    def user_queryset(self):
        return User.objects.filter(playerpage__in=PlayerPage.objects.filter(parent_tournament=self))

    # def start_tournament(self):
    #     if self.round_set.count() > 0:
    #         return False
    #
    #     else:
    #         round_1 = RoundPage(parent_tournament=self, round_count=1)
    #         round_1.save()
    #
    #         return round_1

    def can_start_next_round(self):
        rounds = self.roundpage_set.all()
        if len(rounds) == 0:
            return True

        last_round = rounds.order_by("-round_count")[0]
        matches = last_round.matchpage_set.filter(is_finished=False)

        if len(matches) > 0:
            return False
        else:
            return True

    def generate_next_round_and_match(self):
        if 0 <= self.max_round <= self.roundpage_set.count():
            # exit if have reached the max round count.
            # if max_round < 0, round limit does not apply.
            return False

        if not self.can_start_next_round():
            # exit if have not finished the last round.
            return False

        playerpage_queryset = self.playerpage_set.filter(dropped=False)

        # remove bye first
        if len(playerpage_queryset) % 2 == 1:
            bye = True

            new_query = copy(playerpage_queryset)
            new_query = new_query.order_by("matches_win_count")
            new_query = new_query.order_by("swiss_point")
            for player_to_bye in new_query:
                if player_to_bye.bye_count == 0:
                    bye_player = player_to_bye
                    playerpage_queryset = playerpage_queryset.exclude(id=bye_player.id)
                    break
                else:
                    pass

        else:
            bye = False

        sorted(playerpage_queryset, key=lambda x: random.random())

        graph = nx.Graph()
        self.passed = []
        self.added = []
        for player in playerpage_queryset:
            for opponent in playerpage_queryset:
                if opponent in player.paired_player.all():
                    # self.passed.append([player.id, opponent.id])
                    pass
                else:
                    # self.added.append([player.id, opponent.id])
                    graph.add_edge(player.id, opponent.id, weight=-1 * abs(player.swiss_point - opponent.swiss_point))

        result_edges = nx.max_weight_matching(graph, maxcardinality=True)

        match_max_game_count = self.max_win_count_in_match
        time_limit_in_seconds = self.default_time_limit_in_sec

        round_count = self.roundpage_set.count() + 1
        new_parent_round = RoundPage(parent_tournament=self, round_count=round_count, title="round_" + str(round_count))
        self.add_child(instance=new_parent_round)

        if bye:
            bye_user = User.objects.get_or_create(username="dummy_user", password="dummy_user_pass")[0]
            bye_user.save()
            try:
                bye_dummy = \
                PlayerPage.objects.get(user=bye_user, parent_tournament=self, is_bye_dummy=True, title="bye_dummy")[0]

            except PlayerPage.DoesNotExist:
                bye_dummy = PlayerPage(user=bye_user, parent_tournament=self, is_bye_dummy=True, title="bye_dummy")
                self.add_child(instance=bye_dummy)

            match_no = self.roundpage_set.all().order_by("-id")[0].matchpage_set.count() + 1

            match = MatchPage(parent_round=new_parent_round, max_win_count=match_max_game_count,
                              time_limit_in_second=time_limit_in_seconds, player1=bye_player, player2=bye_dummy,
                              is_bye=True, title=str(match_no),
                              )
            new_parent_round.add_child(instance=match)
            match.player1.paired_player.add(match.player2)
            match.player2.paired_player.add(match.player1)

        self.graph = graph
        self.result_edges = result_edges

        for (player_id_i, player_id_j) in result_edges:
            player_i = playerpage_queryset.get(id=player_id_i)
            player_j = playerpage_queryset.get(id=player_id_j)

            match_no = self.roundpage_set.all().order_by("-id")[0].matchpage_set.count() + 1
            match = MatchPage(parent_round=new_parent_round, max_win_count=match_max_game_count,
                              time_limit_in_second=time_limit_in_seconds, player1=player_i, player2=player_j,
                              title=str(match_no),
                              )
            new_parent_round.add_child(instance=match)
            match.player1.paired_player.add(match.player2)
            match.player2.paired_player.add(match.player1)

        return new_parent_round


class SwissRankDecisionPolicyPage(Page):
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    is_public = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("is_public"),
    ]


class EntryConfigPage(Page):
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = RichTextField(blank=True, null=True)

    parent_tournament = models.ForeignKey(TournamentPage, on_delete=models.PROTECT)
    max_entry_number = models.IntegerField()
    publish_attendant_list = models.BooleanField(default=True)
    is_lottery = models.BooleanField(default=False)
    is_team = models.BooleanField(default=False)
    min_team_member_number = models.IntegerField(default=1)
    max_team_member_number = models.IntegerField(default=1)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        FieldPanel("parent_tournament"),
        FieldPanel("max_entry_number"),
        FieldPanel("publish_attendant_list"),
        FieldPanel("is_lottery"),
        FieldPanel("is_team"),
        FieldPanel("min_team_member_number"),
        FieldPanel("max_team_member_number"),
    ]


class PlayerPage(Page):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    parent_tournament = models.ForeignKey(TournamentPage, on_delete=models.PROTECT, null=True)
    dropped = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_present = models.BooleanField(default=False)
    is_bye_dummy = models.BooleanField(default=False)
    swiss_point = models.IntegerField(default=0)

    matches_win_count = models.IntegerField(default=0)
    matches_lose_count = models.IntegerField(default=0)
    draw_count = models.IntegerField(default=0)
    bye_count = models.IntegerField(default=0)
    paired_player = models.ManyToManyField("self", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("user"),
        FieldPanel("parent_tournament"),
        FieldPanel("dropped"),
        FieldPanel("is_active"),
        FieldPanel("is_present"),
        FieldPanel("is_bye_dummy"),
        FieldPanel("swiss_point"),
        FieldPanel("matches_win_count"),
        FieldPanel("matches_lose_count"),
        FieldPanel("draw_count"),
        FieldPanel("bye_count"),
        FieldPanel("paired_player"),
    ]


class DeckPage(Page):
    intro = models.CharField(max_length=250, blank=True, null=True)
    body = RichTextField(blank=True, null=True)

    parent_player = models.ForeignKey(PlayerPage, on_delete=models.PROTECT)
    deck_code = models.CharField(max_length=20)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("parent_player"),
        FieldPanel("deck_code"),
    ]


class RoundPage(Page):
    parent_tournament = models.ForeignKey(TournamentPage, on_delete=models.PROTECT)
    round_count = models.IntegerField()  # 1st round: round_count == 1

    content_panels = Page.content_panels + [
        FieldPanel("parent_tournament"),
        FieldPanel("round_count"),
    ]


class MatchPage(Page):
    parent_round = models.ForeignKey(RoundPage, on_delete=models.PROTECT)
    max_win_count = models.IntegerField(default=1)
    time_limit_in_second = models.IntegerField(default=1500)

    player1 = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, related_name="player_1")
    # player1_win_count_in_match = models.IntegerField(default=0)
    # player1_lose_count_in_match = models.IntegerField(default=0)
    # player1_draw_count_in_match = models.IntegerField(default=0)
    player1_approved = models.BooleanField(default=False)

    player2 = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, related_name="player_2")
    # player2_win_count_in_match = models.IntegerField(default=0)
    # player2_lose_count_in_match = models.IntegerField(default=0)
    # player2_draw_count_in_match = models.IntegerField(default=0)
    player2_approved = models.BooleanField(default=False)

    is_finished = models.BooleanField(default=False)
    winner = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, related_name="match_winner", null=True, blank=True)
    loser = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, related_name="match_loser", null=True, blank=True)
    is_draw = models.BooleanField(default=False)
    is_bye = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        FieldPanel("parent_round"),
        FieldPanel("max_win_count"),
        FieldPanel("time_limit_in_second"),

        FieldPanel("player1"),

        FieldPanel("player2"),

        FieldPanel("is_finished"),
        FieldPanel("winner"),
        FieldPanel("loser"),
        FieldPanel("is_draw"),
        FieldPanel("is_bye"),
    ]

    def serve(self, request, *args, **kwargs):
        from event_site.forms import MatchEditForm
        context_dict = {
            "page": self,
            "form": None,
            "player1_approve_alert": False,
            "player2_approve_alert": False,
            "player1_approve_thank_you": False,
            "player2_approve_thank_you": False,
            "message": "デフォルトメッセージ。これが表示されるときは問題があります。"
        }
        if request.user.id:
            current_user = User.objects.get(id=request.user.id)
        else:
            current_user = None
        if current_user == self.player1.user or current_user == self.player2.user:
            # Approve button and message starts from here.
            if current_user == self.player1.user:
                if not self.player1_approved:
                    context_dict["player1_approve_alert"] = True
            elif current_user == self.player2.user:
                if not self.player2_approved:
                    context_dict["player2_approve_alert"] = True

            # Edit form starts from here.
            if request.method == "POST":
                if "player1_approve" in request.POST or "player2_approve" in request.POST:
                    if "player1_approve" in request.POST:
                        self.player1_approved = True
                        self.save()
                        context_dict["player1_approve_thank_you"] = True

                    elif "player2_approve" in request.POST:
                        self.player2_approved = True
                        self.save()
                        context_dict["player2_approve_thank_you"] = True

                    return render(request, "event_site/match_page.html", context_dict)

                form = MatchEditForm(request.POST, instance=self)
                if form.is_valid:
                    form.save()
                    # 承認確認
                    if current_user == self.player1:
                        self.player2_approved = False
                        self.save()
                    elif current_user == self.player2:
                        self.player1_approved = False
                        self.save()

                    context_dict["form"] = form
                    context_dict["message"] = "メッセージ： マッチが保存されました！相手プレイヤーにマッチ内容の承認を依頼してください。（プレイヤー1 or プレイヤー2の編集後の画面。）"
                    return render(request, "event_site/match_page.html", context_dict)
            else:
                form = MatchEditForm(instance=self)
                context_dict["form"] = form
                context_dict["message"] = "メッセージ： プレイヤー1 or プレイヤー2の編集マッチ画面。"
                return render(request, "event_site/match_page.html", context_dict)
        else:
            context_dict["message"] = "メッセージ： 編集権のない人用メッセージ（テスト用）"
            return render(request, "event_site/match_page.html", context_dict)

    def close_match(self):
        if self.is_bye:
            win_count = len(self.gamepage_set.filter(winner=self.player1))
            if win_count == self.parent_round.parent_tournament.bye_win_count_in_match:
                self.is_finished = True
                self.save()
                return self
            else:
                return False
        else:
            if (len(self.gamepage_set.filter(winner=self.player1)) == self.max_win_count) or (
                    len(self.gamepage_set.filter(winner=self.player2)) == self.max_win_count):
                self.is_finished = True
                self.save()
                return self
            else:
                return False

    def start_game(self, first_player_id: int):
        """
        :param first_player_id:
        :return:
        """
        if self.is_finished:
            return False

        if (len(self.gamepage_set.filter(winner=self.player1)) < self.max_win_count) or (
                len(self.gamepage_set.filter(winner=self.player2)) < self.max_win_count):

            # new game only if match is not finished.
            new_game = GamePage(parent_match=self, first_player=PlayerPage.objects.get(id=first_player_id),
                                title=self.player1.title + ", " + self.player2.title)
            self.add_child(instance=new_game)
            return new_game

        else:
            self.is_finished = True
            self.save()
            return False

    def register_game_result(self, winner_id=None, loser_id=None, finished_in_time=True, is_draw=False, is_bye=False,
                             is_the_last_game=False):
        """
        :param winner_id: Player.id of the winner of the game.
        :param loser_id: Player.id of the loser of the game.
        :param finished_in_time: Boolean
        :param is_draw: Boolean
        :param is_bye: Boolean
        :return: return False if the value sent is not valid to the data stored.
        :return: return [<Game>, Boolean], Boolean is True if new data saved and False if the data already exists.
        """
        game_to_edit = self.gamepage_set.all().order_by("-id")[0]

        if not game_to_edit.finished_at:

            if is_bye:
                if self.is_bye:
                    game_to_edit.is_bye = True
                    game_to_edit.winner = PlayerPage.objects.get(id=self.player1_id)
                    game_to_edit.loser = PlayerPage.objects.get(id=self.player2_id)
                    game_to_edit.finished_at = timezone.now()
                    game_to_edit.finished_in_time = True
                else:
                    self.close_match()
                    return False

            elif is_draw:
                game_to_edit.is_draw = True
                game_to_edit.finished_at = timezone.now()
                game_to_edit.finished_in_time = finished_in_time

            else:
                game_to_edit.winner = PlayerPage.objects.get(id=winner_id)
                game_to_edit.loser = PlayerPage.objects.get(id=loser_id)
                game_to_edit.finished_at = timezone.now()
                game_to_edit.finished_in_time = finished_in_time

            game_to_edit.save()

            self.close_match()
            return [game_to_edit, True]

        else:
            if is_draw:
                if not game_to_edit.is_draw:
                    self.close_match()
                    return False

            elif is_bye:
                if not game_to_edit.is_bye:
                    self.close_match()
                    return False

            else:
                if not (game_to_edit.winner == PlayerPage.objects.get(
                        id=winner_id) and game_to_edit.loser == PlayerPage.objects.get(id=loser_id)):
                    self.close_match()
                    return False

            self.close_match()
            return [game_to_edit, False]


class GamePage(Page):
    """
    GamePage instances must be generated from method of match class. (to avoid generating too many games.)
    """
    # todo: implement force closing of match with is_the_last_game parameter.
    parent_match = models.ForeignKey(MatchPage, on_delete=models.PROTECT)

    first_player = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, related_name="first_player")
    winner = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, null=True, blank=True,
                               related_name="winner_player")
    loser = models.ForeignKey(PlayerPage, on_delete=models.PROTECT, null=True, blank=True, related_name="loser_player")
    is_draw = models.BooleanField(default=False)
    is_bye = models.BooleanField(default=False)

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    finished_in_time = models.BooleanField(default=True)
    is_the_last_game = models.BooleanField(default=None, null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("parent_match"),

        FieldPanel("first_player"),
        FieldPanel("winner"),
        FieldPanel("loser"),

        FieldPanel("is_draw"),
        FieldPanel("is_bye"),

        FieldPanel("started_at"),
        FieldPanel("finished_at"),
        FieldPanel("finished_in_time"),
    ]

    def serve(self, request, *args, **kwargs):
        from event_site.forms import GameEditForm
        current_user = User.objects.get(id=request.user.id)
        if current_user == self.parent_match.player1.user or current_user == self.parent_match.player2.user:
            if request.method == "POST":

                form = GameEditForm(request.POST, instance=self)
                if form.is_valid:
                    form.save()
                    # 承認確認
                    if current_user == self.parent_match.player1.user:
                        self.parent_match.player2_approved = False
                        self.parent_match.save()
                    elif current_user == self.parent_match.player2.user:
                        self.parent_match.player1_approved = False
                        self.parent_match.save()

                    return render(request, "event_site/game_page.html", {
                        "page": self,
                        "form": form,
                        "message": "メッセージ： 保存されました！相手プレイヤーに変更内容の承認を依頼してください。（プレイヤー1 or プレイヤー2の編集後の画面。）"
                    })
            else:
                form = GameEditForm(instance=self)
                return render(request, "event_site/game_page.html", {
                    "page": self,
                    "form": form,
                    "message": "メッセージ： プレイヤー1 or プレイヤー2の編集可能（編集直後以外）画面。"
                })

        else:
            return render(request, "event_site/game_page.html", {
                "page": self,
                "form": None,
                "message": "メッセージ： 編集県内人用メッセージ（テスト用）。"
            })
