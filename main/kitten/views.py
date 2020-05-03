from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .models import Game, Team, GameTemplate, Line, \
    GameInterval, Incident, TeamInvitation
from .forms import GameForm, TeamInvitationForm, InvitationAcceptanceForm
import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TeamAccessMixin(AccessMixin):
    permission_denied_message = 'Unauthorised Team'

    def handle_no_permission(self):
        return HttpResponse(self.get_permission_denied_message())


class IsTeamMemberMixin(TeamAccessMixin):
    """Verify that the current user is a member of team_id.
    Only works for ModelForms (update, delete) with model=Team """

    def dispatch(self, request, *args, **kwargs):
        team_id = kwargs.get('team_id', None) or kwargs.get('pk', None)
        if request.user and team_id and is_team_member(request, team_id):
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


def is_team_member(request, team_id):
    return Team.objects.filter(id=team_id, members=request.user).exists()


def game_has_team(team_id, game_id):
    return Game.objects.filter(id=game_id, teams=team_id).exists()


@login_required
def home(request):
    teams = request.user.teams.all()
    return render(request, 'kitten/home.html', {'teams': teams})


@login_required
def team_games(request, team_id):
    """ list games available to this team """
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    team = get_object_or_404(Team, pk=team_id)
    TeamInvitation.remove_expired()
    games = Game.objects.filter(teams__pk=team.pk)
    return render(request, 'kitten/team_games.html',
                  {'games': games, 'team': team})


class TeamNew(LoginRequiredMixin, CreateView):
    model = Team
    fields = ('name', 'description')

    def form_valid(self, form):
        form.save()
        form.instance.members.add(self.request.user)
        return super().form_valid(form)


class TeamUpdate(IsTeamMemberMixin, UpdateView):
    model = Team
    fields = ('name', 'description')


class TeamDelete(IsTeamMemberMixin, DeleteView):
    model = Team
    fields = ('name', 'description', 'games')
    success_url = reverse_lazy('home')


@login_required
def invitation_delete(request, team_id, invitation_id):

    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not TeamInvitation.objects.filter(id=invitation_id,
                                         team=team_id).exists:
        return HttpResponse("Unauthorised invitation", status=401)
    TeamInvitation.objects.filter(id=invitation_id).delete()
    return TeamUpdate.as_view()(request, pk=team_id)


@login_required
def invitation_accept(request, invitation_id):
    invitation = get_object_or_404(TeamInvitation, pk=invitation_id)
    if invitation.invitee_username != request.user:
        return HttpResponse("Unauthorised invitation", status=401)
    if request.method == 'POST':
        form = InvitationAcceptanceForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] == invitation.password:
                invitation.accept(request.user)
                return team_games(request, invitation.team.id)

            invitation.failed_attempts += 1
            if invitation.failed_attempts > invitation.MAX_PASSWORD_FAILURES:
                log.error("Too many failed attempts for %s. Deleted.",
                          invitation)
                invitation.delete()
                return HttpResponse(
                    "Too many failed attempts. Please ask the team"
                    " to re-issue the invitation.", status=429)

            form.add_error('password', 'The password is incorrect.  Please'
                            ' check and try again')
            invitation.save()
    else:
        form = InvitationAcceptanceForm()
    return render(request, 'kitten/invitation_accept.html',
                  {'form': form,
                   'invitation': invitation})


@login_required
def team_invitation_new(request, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    team = get_object_or_404(Team, id=team_id)
    if request.method == 'POST':
        form = TeamInvitationForm(request.POST)
        form.instance.team = team
        if form.is_valid():
            form.instance.invited_by = request.user
            form.save()
            return team_games(request, team_id)
    else:
        form = TeamInvitationForm(initial={"invited_by": request.user,
                                           "team": team})
    return render(request, 'kitten/team_invitation.html',
                  {'form': form, 'team': team})


@login_required
def team_member_remove(request, team_id, user_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    team = Team.objects.get(id=team_id)
    if team.members.count() <= 1:
        return HttpResponse("Cannot remove the only team member: delete team"
                            " instead.", status=403)
    if not Team.objects.filter(id=team_id, members=user_id).exists():
        return HttpResponse(f"User is not a member of {team.name}.",
                            status=400)
    team.members.remove(user_id)
    return TeamUpdate.as_view()(request, pk=team_id)


@login_required
def game_new(request, team_id):
    """ start a new game.
    Prompt for game template and teams, then create game """
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if request.method == 'POST':
        # handle form here .. create the game and then go to edit game
        # to further customise
        selected_template = request.POST.get('template')
        name = request.POST.get('name')
        if selected_template == "NONE":
            errors = "ERROR: You must select a network to base your game upon"
        elif selected_template is None:
            errors = "template field not included in POST data"
        else:
            errors = f"You selected {selected_template}"
            template = get_object_or_404(GameTemplate, pk=selected_template)
            team = get_object_or_404(Team, pk=team_id)
            game = Game.new_from_template(teams=[team], template=template,
                                          name=name)
            game.save()
            form = GameForm(instance=game)
            return render(request, 'kitten/game.html',
                          {'form': form, 'game': game, 'team_id': team.id})
    else:  # initial call with only team_id
        errors = ""
    team = get_object_or_404(Team, pk=team_id)
    game_templates = GameTemplate.objects.filter(level__lte=team.level)
    return render(request, 'kitten/game_new.html',
                  {'team': team, 'templates': game_templates,
                   'errors': errors})


@login_required
def game(request, game_id, team_id):
    """ load a specific game by pk """
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    game = get_object_or_404(Game, pk=game_id)
    if request.method == 'POST':  # handle incoming form
        form = GameForm(request.POST, instance=game)
        if form.is_valid():
            game = form.save()
    else:
        form = GameForm(instance=game)
    return render(request, 'kitten/game.html',
                  {'form': form, 'game': game, "team_id": team_id})


@login_required
def game_delete(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    return HttpResponse("Delete game not yet implemented.")


@login_required
def game_play(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    return HttpResponse("Play game not yet implemented.  Go to Operations"
                        "and press Tick to get an idea...")


@login_required
def game_tick(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    return game_operations(request, game_id, team_id,
                           tick_interval=GameInterval.TICK_SINGLE)


@login_required
def game_operations(request, game_id, team_id, tick_interval=None):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    team = get_object_or_404(Team, pk=team_id)
    game = get_object_or_404(Game, pk=game_id)
    if tick_interval is not None:
        game.run(tick_interval)
    lines = Line.objects.filter(game=game, operator=team)

    # details is {line([(trains_up, loc, trains_down)], [incidents])}
    details = {line: ([(trains_dir1, location, trains_dir2)
                      for location, (trains_dir1, trains_dir2)
                      in line.details().items()],
                      line.incidents.all())
               for line in lines
               }
    lines_other_op = Line.objects.filter(game=game).exclude(
        operator=team).order_by('operator')
    return render(request, 'kitten/operations.html',
                  {'game': game, 'team': team,
                   'details': details,
                   'lines_other_op': lines_other_op
                   })


@login_required
def game_scheduling(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    game = get_object_or_404(Game, pk=game_id)
    return render(request, 'kitten/scheduling.html',
                  {'game': game, 'team_id': team_id})


@login_required
def game_boardroom(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    game = get_object_or_404(Game, pk=game_id)
    return render(request, 'kitten/boardroom.html',
                  {'game': game, 'team_id': team_id})


@login_required
def game_hr(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    game = get_object_or_404(Game, pk=game_id)
    return render(request, 'kitten/hr.html',
                  {'game': game, 'team_id': team_id})


@login_required
def game_engineering(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    game = get_object_or_404(Game, pk=game_id)
    return render(request, 'kitten/engineering.html',
                  {'game': game, 'team_id': team_id})


@login_required
def game_stage(request, game_id, team_id):
    return game_operations(request, game_id, team_id,
                           tick_interval=GameInterval.TICK_STAGE)


@login_required
def incident(request, team_id, incident_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not Incident.objects.filter(
            id=incident_id, incident__line__game__teams=team_id).exists():
        return HttpResponse('Unauthorized game', status=401)
    try:
        incident = Incident.objects.get(id=incident_id,
                                        line__game__teams=team_id)
    except Incident.DoesNotExist:
        return HttpResponse('Unauthorised team', status=401)

    back_url = request.path  # save url to return to
    errors = None
    if request.method == "POST":
        # start new response
        back_url = request.POST.get('back-url', '/')
        response_id = request.POST.get("option")
        if not response_id:
            errors = "You must choose a response"
        else:
            incident.start_response(response_id)
            return HttpResponseRedirect(back_url)
    else:
        back_url = request.GET.get('back-url', None)
    return render(request, 'kitten/incident.html',
                  {'game': incident.line.game,
                   'team_id': team_id,
                   'incident': incident,
                   'response': incident.response,
                   'errors': errors,
                   'back_url': back_url})


@login_required
def game_incidents_clear(request, game_id, team_id):
    if not is_team_member(request, team_id):
        return HttpResponse("Unauthorised team", status=401)
    if not game_has_team(team_id, game_id):
        return HttpResponse('Unauthorized game', status=401)
    log.info("Deleting incidents for game id %s", game_id)
    Incident.objects.filter(line__game_id=game_id).delete()
    return game_operations(request, game_id, team_id)
