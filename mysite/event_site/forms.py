from django import forms
from event_site.models import SeriesPage, TournamentPage, RoundPage, MatchPage, GamePage, PlayerPage, User
from django.utils.translation import gettext as _

from tempus_dominus.widgets import DatePicker, TimePicker, DateTimePicker
from django.views.generic.edit import UpdateView


class SeriesEditForm(forms.ModelForm):
    body = forms.Textarea()
    class Meta:
        model = SeriesPage
        fields = ["title", "intro", "body"]


class TournamentEditForm(forms.ModelForm):
    body = forms.Textarea()
    start_datetime = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=DateTimePicker(
            options={
                'useCurrent': True,
                'collapse': True,
            },
            attrs={
                'append': 'fa fa-calendar',
                'input_toggle': True,
                'icon_toggle': False,
            },
        )
    )

    class Meta:
        model = TournamentPage
        fields = ["title", "intro", "body", "start_datetime", "max_player_count", "top_cut_count", "default_time_limit_in_sec", "max_round", "max_win_count_in_match", "bye_win_count_in_match"]


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


class NewGameForm(forms.ModelForm):
    first_player = forms.ModelChoiceField(queryset=PlayerPage.objects.none())

    def __init__(self, parent_instance, *args, **kwargs):
        super(NewGameForm, self).__init__(*args, **kwargs)
        parent_match_ins = parent_instance
        player_ids = [parent_match_ins.player1.id, parent_match_ins.player2.id]
        qs = PlayerPage.objects.filter(id__in=player_ids)

        self.fields["first_player"].queryset = qs

    class Meta:
        model= GamePage
        fields = ["first_player"]


class GameEditForm(forms.ModelForm):
    winner = forms.ModelChoiceField(queryset=PlayerPage.objects.none())
    loser = forms.ModelChoiceField(queryset=PlayerPage.objects.none())
    finished_at = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=DateTimePicker(
            options={
                'useCurrent': True,
                'collapse': True,
            },
            attrs={
                'append': 'fa fa-calendar',
                'input_toggle': True,
                'icon_toggle': False,
            },
        )
    )

    def __init__(self, *args, **kwargs):
        super(GameEditForm, self).__init__(*args, **kwargs)
        ins = kwargs.get("instance")
        player_ids = [ins.parent_match.player1.id, ins.parent_match.player2.id]
        qs = PlayerPage.objects.filter(id__in=player_ids)

        self.fields["winner"].queryset = qs
        self.fields["loser"].queryset = qs

    class Meta:
        model = GamePage
        fields = ["first_player", "winner", "loser", "is_draw", "finished_in_time", "started_at", "is_the_last_game", "finished_at"]
        exclude = []
    #
    # def clean_is_draw(self):
    #     if self.cleaned_data["is_draw"]:
    #         raise forms.ValidationError("is_draw cannot be set true")

    def clean(self):

        cleaned_data = super().clean()
        if cleaned_data.get("winner") and cleaned_data.get("loser"):
            if cleaned_data.get("winner") == cleaned_data.get("loser"):
                msg = _("winnerとloserを同一プレイヤーに設定することはできません。")
                self.add_error("winner", msg)
                self.add_error("loser", msg)

        if cleaned_data.get("is_draw"):
            if cleaned_data.get("winner") or cleaned_data.get("loser"):
                msg = _("is_drawと、winnerまたはloserを同時に設定することはできません。")
                self.add_error("winner", msg)
                self.add_error("loser", msg)
                self.add_error("is_draw", msg)

            if cleaned_data.get("is_bye"):
                msg = _("is_drawとis_byeを同時に設定することはできません")
                self.add_error("is_bye", msg)
                self.add_error("is_draw", msg)
        return cleaned_data

