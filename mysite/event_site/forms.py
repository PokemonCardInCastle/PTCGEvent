from django import forms
from event_site.models import TournamentPage, RoundPage, MatchPage, GamePage, PlayerPage, User

from django.views.generic.edit import UpdateView


class TournamentAdminEditForm(forms.ModelForm):
    class Meta:
        model = TournamentPage
        exclude = []


class RoundAdminEditForm(forms.ModelForm):
    class Meta:
        model = RoundPage
        exclude = []


class MatchEditForm(forms.ModelForm):

    winner = forms.ModelChoiceField(queryset=PlayerPage.objects.none())
    loser = forms.ModelChoiceField(queryset=PlayerPage.objects.none())

    def __init__(self, *args, **kwargs):
        super(MatchEditForm, self).__init__(*args, **kwargs)
        ins = kwargs.get("instance")
        player_ids = [ins.player1.id, ins.player2.id]
        qs = PlayerPage.objects.filter(id__in=player_ids)

        self.fields["winner"].queryset = qs
        self.fields["loser"].queryset = qs

    class Meta:
        model = MatchPage
        fields = ["is_finished", "winner", "loser", "is_draw"]
        exclude = []


class GameEditForm(forms.ModelForm):
    class Meta:
        model = GamePage
        exclude = []



