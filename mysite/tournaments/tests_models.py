import os
import sys
import django
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "../../")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings.dev')
django.setup()
from django.test import TestCase
from django.contrib.auth.models import User
from tournaments.models import *
import random


class SeriesTestCase(TestCase):
    def setUp(self):
        user_1 = User()
        user_1.save()

        series_1 = Series(name="series_1", parent_series=None)
        series_1.save()
        series_1.admin_user.add(user_1)

        series_2 = Series(name="series_2", parent_series=Series.objects.filter(name="series_1")[0])
        series_2.save()
        self.series_2 = series_2
        series_2.admin_user.add(user_1)

    def test_parent_series(self):
        parent = Series.objects.get(name="series_1")
        self.assertEqual(parent, Series.objects.get(name="series_2").parent_series)

    def test_str(self):
        self.assertEqual(str(self.series_2), self.series_2.name)


class TournamentTestCase(TestCase):
    def setUp(self):
        self.user_1 = User(username="user_1", password="1")
        self.user_1.save()

        self.user_2 = User(username="user_2", password="2")
        self.user_2.save()

        self.user_3 = User(username="user_3", password="3")
        self.user_3.save()

        self.user_4 = User(username="user_4", password="4")
        self.user_4.save()

        self.user_5 = User(username="user_5", password="5")
        self.user_5.save()

        self.series_1 = Series(name="series_1", parent_series=None)
        self.series_1.save()
        self.series_1.admin_user.add(self.user_1)

        self.series_2 = Series(name="series_2", parent_series=Series.objects.filter(name="series_1")[0])
        self.series_2.save()
        self.series_2.admin_user.add(self.user_1)

        self.tournament = Tournament(name="Tournament_1", parent_series=self.series_2, max_player_count=3, top_cut_count=1, default_time_limit_in_sec=1000, max_round=2)
        self.tournament.save()

        self.tournament_for_5 = Tournament(name="Tournament_1", parent_series=self.series_2, max_player_count=5,
                                     top_cut_count=1, default_time_limit_in_sec=1000, max_round=3, bye_win_count_in_match=2, max_win_count_in_match=2)
        self.tournament_for_5.save()

    def test_str(self):
        self.assertEqual(str(self.tournament), self.tournament.name + " :" + self.tournament.parent_series.name)

    def test_add_player(self):
        add_result = self.tournament.add_player(self.user_1.id)

        self.assertEqual(add_result, [Player.objects.get(user=self.user_1, parent_tournament=self.tournament), True])

    def test_add_existing_player(self):
        add_before = self.tournament.add_player(self.user_1.id)

        player_num_before = self.tournament.player_set.count()
        add_result = self.tournament.add_player(self.user_1.id)
        player_num_after = self.tournament.player_set.count()

        self.assertEqual(player_num_before, player_num_after)
        self.assertEqual(add_result, [Player.objects.get(user=self.user_1, parent_tournament=self.tournament), False])

    def test_add_too_many_players(self):
        add_before = self.tournament.add_player(self.user_1.id)
        add_before = self.tournament.add_player(self.user_2.id)
        add_before = self.tournament.add_player(self.user_3.id)

        player_num_before = self.tournament.player_set.count()

        add_result = self.tournament.add_player(self.user_4.id)

        player_num_after = self.tournament.player_set.count()

        self.assertEqual(player_num_before, 3)
        self.assertEqual(player_num_after, 3)
        self.assertEqual(add_result, [None, False])

    # def test_start_tournament_valid(self):
    #     rounds_before = self.tournament.round_set.all()
    #     self.assertEqual(len(rounds_before), 0)
    #
    #     self.tournament.start_tournament()
    #     rounds_after = self.tournament.round_set.all()
    #
    #     self.assertEqual(len(rounds_after), 1)
    #     self.assertEqual(rounds_after[0].round_count, 1)
    #
    # def test_start_tournament_invalid(self):
    #     # set up the round 1
    #     rounds_before = self.tournament.round_set.all()
    #     self.assertEqual(len(rounds_before), 0)
    #
    #     self.tournament.start_tournament()
    #     rounds_after = self.tournament.round_set.all()
    #
    #     self.assertEqual(len(rounds_after), 1)
    #     self.assertEqual(rounds_after[0].round_count, 1)
    #     # end set up
    #
    #     rounds_before = self.tournament.round_set.all()
    #     self.assertEqual(len(rounds_before), 1)
    #
    #     start_result = self.tournament.start_tournament()
    #     self.assertEqual(start_result, False)
    #
    #     rounds_after = self.tournament.round_set.all()
    #
    #     self.assertEqual(len(rounds_after), 1)

    def test_generate_next_round_and_match_1st(self):

        add_before = self.tournament.add_player(self.user_1.id)
        add_before = self.tournament.add_player(self.user_2.id)
        add_before = self.tournament.add_player(self.user_3.id)

        player_num = self.tournament.player_set.count()

        self.assertEqual(player_num, 3)

        rounds_before = self.tournament.round_set.all()
        self.assertEqual(len(rounds_before), 0)

        match_result = self.tournament.generate_next_round_and_match()

        self.assertEqual(match_result, Round.objects.get(parent_tournament=self.tournament))

        rounds_after = self.tournament.round_set.all()

        self.assertEqual(len(rounds_after), 1)

        round_1 = rounds_after[0]
        self.assertEqual(self.tournament.round_set.all()[0].match_set.count(), 2)

    def test_generate_next_round_and_match_three_times(self):
        add_player = self.tournament_for_5.add_player(self.user_1.id)
        add_player = self.tournament_for_5.add_player(self.user_2.id)
        add_player = self.tournament_for_5.add_player(self.user_3.id)
        add_player = self.tournament_for_5.add_player(self.user_4.id)
        add_player = self.tournament_for_5.add_player(self.user_5.id)

        self.games = []

        rounds_before = self.tournament_for_5.round_set.all()
        self.assertEqual(len(rounds_before), 0)

        match_result = self.tournament_for_5.generate_next_round_and_match()

        rounds_after = self.tournament_for_5.round_set.all()

        self.assertEqual(match_result, rounds_after[0])
        self.assertEqual(len(rounds_after), 1)

        round_1 = rounds_after[0]

        matches_for_round_1 = self.tournament_for_5.round_set.all()[0].match_set.all()

        self.assertEqual(matches_for_round_1.count(), 3)

        for match in matches_for_round_1:
            for i in range(self.tournament_for_5.max_win_count_in_match * 10):
                if match.is_bye:
                    game = match.start_game(first_player_id=match.player1_id)
                    if game:
                        game = match.register_game_result(is_bye=True)[0]
                        if game:
                            self.games.append(game)

                else:
                    game = match.start_game(first_player_id=match.player2_id if random.random() < 0.5 else match.player1_id)
                    if game:
                        win_decider = random.random()
                        if win_decider < 0.1:
                            game_saved = match.register_game_result(winner_id=None, loser_id=None, finished_in_time=True, is_draw=True)
                        elif 0.1 <= win_decider < 0.2:
                            game_saved = match.register_game_result(winner_id=None, loser_id=None, finished_in_time=False, is_draw=True)
                        elif 0.2 <= win_decider < 0.6:
                            game_saved = match.register_game_result(winner_id=match.player1_id, loser_id=match.player2_id, finished_in_time=False, is_draw=False)
                        elif 0.6 <= win_decider < 1.0:
                            game_saved = match.register_game_result(winner_id=match.player2_id, loser_id=match.player1_id,
                                                       finished_in_time=False, is_draw=False)
                        if game_saved:
                            self.games.append(game_saved[0])

            self.assertEqual(match.is_finished, True)

        rounds_2_before = self.tournament_for_5.round_set.all()
        self.assertEqual(len(rounds_2_before), 1)

        round_2_match_result = self.tournament_for_5.generate_next_round_and_match()

        rounds_2_after = self.tournament_for_5.round_set.all().order_by("-id")

        self.assertEqual(round_2_match_result, rounds_2_after[0])
        self.assertEqual(len(rounds_2_after), 2)

        matches_for_round_2 = self.tournament_for_5.round_set.all().order_by("-id")[0].match_set.all()

        self.assertEqual(matches_for_round_2.count(), 3)

        for match in matches_for_round_2:
            for i in range(self.tournament_for_5.max_win_count_in_match * 10):
                if match.is_bye:
                    game = match.start_game(first_player_id=match.player1_id)
                    if game:
                        game = match.register_game_result(is_bye=True)[0]
                        if game:
                            self.games.append(game)

                else:
                    game = match.start_game(
                        first_player_id=match.player2_id if random.random() < 0.5 else match.player1_id)
                    if game:
                        win_decider = random.random()
                        if win_decider < 0.1:
                            game_saved = match.register_game_result(winner_id=None, loser_id=None,
                                                                    finished_in_time=True, is_draw=True)
                        elif 0.1 <= win_decider < 0.2:
                            game_saved = match.register_game_result(winner_id=None, loser_id=None,
                                                                    finished_in_time=False, is_draw=True)
                        elif 0.2 <= win_decider < 0.6:
                            game_saved = match.register_game_result(winner_id=match.player1_id,
                                                                    loser_id=match.player2_id, finished_in_time=False,
                                                                    is_draw=False)
                        elif 0.6 <= win_decider < 1.0:
                            game_saved = match.register_game_result(winner_id=match.player2_id,
                                                                    loser_id=match.player1_id,
                                                                    finished_in_time=False, is_draw=False)
                        if game_saved:
                            self.games.append(game_saved[0])

            self.assertEqual(match.is_finished, True)

    def test_generate_next_round_before_finish(self):
        add_player = self.tournament_for_5.add_player(self.user_1.id)
        add_player = self.tournament_for_5.add_player(self.user_2.id)
        add_player = self.tournament_for_5.add_player(self.user_3.id)
        add_player = self.tournament_for_5.add_player(self.user_4.id)
        add_player = self.tournament_for_5.add_player(self.user_5.id)

        self.games = []

        rounds_before = self.tournament_for_5.round_set.all()
        self.assertEqual(len(rounds_before), 0)

        match_result = self.tournament_for_5.generate_next_round_and_match()
        self.assertEqual(bool(match_result), True)
        match_result_2 = self.tournament_for_5.generate_next_round_and_match()
        self.assertEqual(bool(match_result_2), False)

    def test_match_is_bye_variant_is_set(self):
        add_player = self.tournament_for_5.add_player(self.user_1.id)
        add_player = self.tournament_for_5.add_player(self.user_2.id)
        add_player = self.tournament_for_5.add_player(self.user_3.id)
        add_player = self.tournament_for_5.add_player(self.user_4.id)
        add_player = self.tournament_for_5.add_player(self.user_5.id)

        self.games = []

        rounds_before = self.tournament_for_5.round_set.all()
        self.assertEqual(len(rounds_before), 0)

        match_result = self.tournament_for_5.generate_next_round_and_match()

        rounds_after = self.tournament_for_5.round_set.all()

        self.assertEqual(match_result, rounds_after[0])
        self.assertEqual(len(rounds_after), 1)

        round_1 = rounds_after[0]

        matches_for_round_1 = self.tournament_for_5.round_set.all()[0].match_set.all()

        for match in matches_for_round_1:
            if match.player2.is_bye_dummy:
                self.assertEqual(match.is_bye, True)

            else:
                self.assertEqual(match.is_bye, False)




class SwissRankDecisionPolicyTestCase(TestCase):
    def setUp(self):
        self.policy = SwissRankDecisionPolicy(name="Default", is_public=True, description="piyo")

    def test_str(self):
        self.assertEqual(str(self.policy), self.policy.name)



