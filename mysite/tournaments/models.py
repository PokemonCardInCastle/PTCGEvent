from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User
import networkx as nx
from copy import copy
import random

# Create your models here.


# todo: is_active属性を利用した削除機能の実装

class Region(models.Model):
    name = models.CharField(max_length=50)


class Country(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=50)
    name_j = models.CharField(max_length=50)
    parent_region = models.ForeignKey(Region, on_delete=models.PROTECT)


class Prefecture(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=3)
    parent_country = models.ForeignKey(Country, on_delete=models.CASCADE)


class City(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=15)
    parent_prefecture = models.ForeignKey(Prefecture, on_delete=models.CASCADE)


class Venue(models.Model):
    def __str__(self):
        return self.name
    parent_city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)


class VenueRoom(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=50)
    parent_venue = models.ForeignKey(Venue, on_delete=models.CASCADE)


class Series(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=100)
    parent_series = models.ForeignKey("self", on_delete=models.PROTECT, null=True)
    admin_user = models.ManyToManyField(User)


class Tournament(models.Model):
    def __str__(self):
        name_gathered = self.name + " :" + self.parent_series.name
        return name_gathered

    # これは基底クラスです。
    # todo: 派生クラスでスイスドロー等のトーナメントの種類ごとの名前と操作をを定義する。
    name = models.CharField(max_length=100)
    parent_series = models.ForeignKey(Series, on_delete=models.PROTECT)
    venue_room = models.ManyToManyField(VenueRoom)
    is_active = models.BooleanField(default=True)

    max_player_count = models.IntegerField()
    top_cut_count = models.IntegerField(null=True)
    default_time_limit_in_sec = models.IntegerField(default=1500)
    max_round = models.IntegerField(default=-1)
    max_win_count_in_match = models.IntegerField(default=1)
    bye_win_count_in_match = models.IntegerField(default=1)

    def add_player(self, user_id):
        players = self.player_set.all()
        players_number = len(players)
        user = User.objects.get(id=user_id)

        if players.filter(user=user):
            return [players.get(user=user), False]

        elif players_number < self.max_player_count:
            new_player = Player(user=user, parent_tournament=self)
            new_player.save()
            return [new_player, True]

        else:
            return [None, False]

    # def start_tournament(self):
    #     if self.round_set.count() > 0:
    #         return False
    #
    #     else:
    #         round_1 = Round(parent_tournament=self, round_count=1)
    #         round_1.save()
    #
    #         return round_1

    def round_finish_check(self):
        rounds = self.round_set.all()
        if len(rounds) == 0:
            return True

        last_round = rounds.order_by("-round_count")[0]
        matches = last_round.match_set.filter(is_finished=False)

        if len(matches) > 0:
            return False
        else:
            return True

    def generate_next_round_and_match(self):
        if self.round_set.count() >= self.max_round:
            # exit if have reached the max round count.
            return False

        if not self.round_finish_check():
            # exit if have not finished the last round.
            return False

        player_queryset = self.player_set.filter(dropped=False)

        # remove bye first
        if len(player_queryset) % 2 == 1:
            bye = True

            new_query = copy(player_queryset)
            new_query = new_query.order_by("matches_win_count")
            new_query = new_query.order_by("swiss_point")
            for player_to_bye in new_query:
                if player_to_bye.bye_count == 0:
                    bye_player = player_to_bye
                    player_queryset = player_queryset.exclude(id=bye_player.id)
                    break
                else:
                    pass

        else:
            bye = False

        sorted(player_queryset, key=lambda x: random.random())

        graph = nx.Graph()
        self.passed = []
        self.added = []
        for player in player_queryset:
            for opponent in player_queryset:
                if opponent in player.paired_player.all():
                    self.passed.append([player.id, opponent.id])
                    pass
                else:
                    self.added.append([player.id, opponent.id])
                    graph.add_edge(player.id, opponent.id, weight=-1 * abs(player.swiss_point - opponent.swiss_point))

        result_edges = nx.max_weight_matching(graph, maxcardinality=True)

        match_max_game_count = self.max_win_count_in_match
        time_limit_in_seconds = self.default_time_limit_in_sec

        new_parent_round = Round(parent_tournament=self, round_count=self.round_set.count() + 1)
        new_parent_round.save()

        if bye:
            bye_dummy = Player.objects.get_or_create(user=None, parent_tournament=None, is_bye_dummy=True)[0]
            bye_dummy.save()

            m = Match(parent_round=new_parent_round, max_win_count=match_max_game_count,
                      player1=bye_player, player2=bye_dummy, is_bye=True)
            m.save()

        self.graph = graph
        self.result_edges = result_edges

        for (player_id_i, player_id_j) in result_edges:
            player_i = player_queryset.get(id=player_id_i)
            player_j = player_queryset.get(id=player_id_j)

            match = Match(parent_round=new_parent_round, max_win_count=match_max_game_count,
                          time_limit_in_second=time_limit_in_seconds, player1=player_i, player2=player_j
                          )
            match.save()

        return new_parent_round


class SwissRankDecisionPolicy(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=100)
    is_public = models.BooleanField(default=False)
    description = models.CharField(max_length=2000)


class SwissTournament(Tournament):
    win_point = models.IntegerField(default=3)
    draw_point = models.IntegerField(default=0)
    lose_point = models.IntegerField(default=0)
    rank_decision_policy = models.ForeignKey(SwissRankDecisionPolicy, on_delete=models.PROTECT)


class SingleEliminationTournament(Tournament):
    pass


class DoubleEliminationTournament(Tournament):
    decide_third = models.BooleanField(default=True)


class EntryConfig(models.Model):
    parent_tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT)
    entry_start_at = models.DateTimeField()
    entry_end_at = models.DateTimeField()
    max_entry_number = models.IntegerField()
    age_min = models.IntegerField()
    age_max = models.IntegerField()
    publish_attendant_list = models.BooleanField(default=True)
    is_lottery = models.BooleanField(default=False)
    min_team_member_number = models.IntegerField(default=1)
    max_team_member_number = models.IntegerField(default=1)


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    parent_tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT, null=True)
    dropped = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_present = models.BooleanField(default=False)
    is_bye_dummy = models.BooleanField(default=False)
    swiss_point = models.IntegerField(default=0)

    matches_win_count = models.IntegerField(default=0)
    matches_lose_count = models.IntegerField(default=0)
    draw_count = models.IntegerField(default=0)
    bye_count = models.IntegerField(default=0)
    paired_player = models.ManyToManyField("self")


class Deck(models.Model):
    parent_player = models.ForeignKey(Player, on_delete=models.PROTECT)
    deck_code = models.CharField(max_length=20)


class Round(models.Model):
    parent_tournament = models.ForeignKey(Tournament, on_delete=models.PROTECT)
    round_count = models.IntegerField()  # 1st round: round_count == 1

    def make_matching(self):
        return


class Match(models.Model):
    parent_round = models.ForeignKey(Round, on_delete=models.PROTECT)
    max_win_count = models.IntegerField(default=1)
    time_limit_in_second = models.IntegerField(default=1500)

    player1 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="player_1")
    player1_win_count_in_match = models.IntegerField(default=0)
    player1_lose_count_in_match = models.IntegerField(default=0)
    player1_draw_count_in_match = models.IntegerField(default=0)

    player2 = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="player_2")
    player2_win_count_in_match = models.IntegerField(default=0)
    player2_lose_count_in_match = models.IntegerField(default=0)
    player2_draw_count_in_match = models.IntegerField(default=0)

    is_finished = models.BooleanField(default=False)
    winner = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="match_winner", null=True)
    loser = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="match_loser", null=True)
    is_draw = models.BooleanField(default=False)
    is_bye = models.BooleanField(default=False)

    def close_match(self):
        if self.is_bye:
            win_count = len(self.game_set.filter(winner=self.player1))
            if win_count == self.parent_round.parent_tournament.bye_win_count_in_match:
                self.is_finished = True
                self.save()
                return self
            else:
                return False
        else:
            if (len(self.game_set.filter(winner=self.player1)) == self.max_win_count) or (
                    len(self.game_set.filter(winner=self.player2)) == self.max_win_count):
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

        if (len(self.game_set.filter(winner=self.player1)) < self.max_win_count) or (
                len(self.game_set.filter(winner=self.player2)) < self.max_win_count):

            # new game only if match is not finished.
            new_game = Game(parent_match=self, first_player=Player.objects.get(id=first_player_id), )
            new_game.save()
            return new_game

        else:
            self.is_finished = True
            self.save()
            return False

    def register_game_result(self, winner_id=None, loser_id=None, finished_in_time=True, is_draw=False, is_bye=False):
        """
        :param winner_id: Player.id of the winner of the game.
        :param loser_id: Player.id of the loser of the game.
        :param finished_in_time: Boolean
        :param is_draw: Boolean
        :param is_bye: Boolean
        :return: return False if the value sent is not valid to the data stored.
        :return: return [<Game>, Boolean], Boolean is True if new data saved and False if the data already exists.
        """
        game_to_edit = self.game_set.all().order_by("-id")[0]

        if not game_to_edit.finished_at:

            if is_bye:
                if self.is_bye:
                    game_to_edit.is_bye = True
                    game_to_edit.winner = Player.objects.get(id=self.player1_id)
                    game_to_edit.loser = Player.objects.get(id=self.player2_id)
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
                game_to_edit.winner = Player.objects.get(id=winner_id)
                game_to_edit.loser = Player.objects.get(id=loser_id)
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
                if not (game_to_edit.winner == Player.objects.get(id=winner_id) and game_to_edit.loser == Player.objects.get(id=loser_id)):
                    self.close_match()
                    return False

            self.close_match()
            return [game_to_edit, False]


class Game(models.Model):
    """
    Game instances must be generated from method of match class. (to avoid generating too many games.)
    """
    parent_match = models.ForeignKey(Match, on_delete=models.CASCADE)

    first_player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name="first_player")
    winner = models.ForeignKey(Player, on_delete=models.PROTECT, null=True, related_name="winner_player")
    loser = models.ForeignKey(Player, on_delete=models.PROTECT, null=True, related_name="loser_player")
    is_draw = models.BooleanField(default=False)
    is_bye = models.BooleanField(default=False)

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True)
    finished_in_time = models.BooleanField(default=True)


class DetailedGameResult(models.Model):
    parent_game = models.ForeignKey(Game, on_delete=models.CASCADE)
    parent_player = models.ForeignKey(Player, on_delete=models.PROTECT)

    prize_took = models.IntegerField(default=-1)
    prize_taken_by_opponent = models.IntegerField(default=-1)
    my_impression = models.CharField(default="Normal", max_length=30)
    opponent_impression = models.CharField(default="Normal", max_length=30)
    memo = models.CharField(default="", max_length=2000)

    is_accidental = models.BooleanField(default=False)
    opponent_accidental = models.BooleanField(default=False)


class UserInfo(models.Model):
    # todo: need to be implemented with the account management.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="active_player")
    display_name = models.CharField(max_length=100)
    official_player_id = models.CharField(max_length=20)

    # To resume when users reset their app or browser.
    active_player = models.OneToOneField(Player, on_delete=models.PROTECT, null=True)
    player_valid_until = models.DateTimeField(null=True)


