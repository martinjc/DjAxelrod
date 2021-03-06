from django.views.generic import (
    DetailView,
    ListView,
    UpdateView,
    CreateView,
    TemplateView
)
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from djaxelrod import tasks
from .models import Tournament, TournamentDefinition
from .forms import TournamentDefinitionForm


class HomeView(ListView):
    model = Tournament
    template_name = 'core/tournament_list.html'


class TournamentListView(ListView):
    model = Tournament
    queryset = Tournament.objects.select_related('tournament_definition')


class TournamentCreateView(CreateView):
    model = TournamentDefinition
    form_class = TournamentDefinitionForm
    template_name = 'core/tournament_form.html'

    def get_initial(self):
        now = timezone.now()
        return {
            'name': u"{0.first_name}{0.last_name}-{1}".format(
                self.request.user, now.isoformat())
        }

    def form_valid(self, form):
        self.object = form.save()
        tournament = Tournament.objects.create(
            tournament_definition=self.object)
        tournament.save()

        tasks.tournament_task.apply_async([
            tournament.pk])

        return super(TournamentCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('core_tournament_list')

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(TournamentCreateView, cls).as_view(**initkwargs)
        return login_required(view)


class TournamentDetailView(DetailView):
    model = Tournament
    queryset = Tournament.objects.select_related('tournament_definition')


class TournamentResultsView(TournamentDetailView):

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a JSON responseof the tournament results
        """
        tournament = self.get_object(self.get_queryset())
        return JsonResponse(tournament.to_json())
