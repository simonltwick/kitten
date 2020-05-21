from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

import csv
import datetime as dt
import logging

from .models import (
    Bike, Ride, ComponentType, Component, Preferences, DistanceUnits,
    MaintenanceAction
    )
from .forms import RideSelectionForm

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


@login_required
def home(request):
    preferences_set = Preferences.objects.filter(user=request.user).exists()
    return render(request, 'bike/home.html',
                  context={'preferences_set': preferences_set})


@login_required
def bikes(request):
    today = dt.date.today()
    this_month = dt.date(year=today.year, month=today.month, day=1)
    sum_month = Sum('rides__distance', filter=Q(rides__date__gte=this_month))
    this_year = dt.date(year=today.year, month=1, day=1)
    sum_year = Sum('rides__distance', filter=Q(rides__date__gte=this_year))
    bikes = (Bike.objects.values('id', 'name', 'rides__distance_units')
             .annotate(distance=Sum('rides__distance'),
                       sum_month=sum_month,
                       sum_year=sum_year)
             .filter(owner=request.user))
    # change distance_units into distance
    """ sum for this month
    this_month=dt.date(year=dt.date.today().year, month=dt.date.today().month,
                       day=1)
    sum_month=Sum('rides__distance', filter=Q(rides__date__gte=this_month))
    bikes = Bike.objects.annotate(sum_month=sum_month).all()
    # but need to add values('rides__distance_units')
    """

    bikes = [row for row in bikes.all()]  # QuerySet -> List
    for row in bikes:
        if row['rides__distance_units'] is None:
            row['rides__distance_units'] = ''
        else:
            row['rides__distance_units'] = DistanceUnits(
                row['rides__distance_units']).name.lower()
    return render(request, 'bike/bikes.html',
                  context={'bikes': bikes})


class PreferencesCreate(LoginRequiredMixin, CreateView):
    model = Preferences
    fields = ['distance_units', 'ascent_units']

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        return super(PreferencesCreate, self).form_valid(form)


class PreferencesUpdate(LoginRequiredMixin, UpdateView):
    model = Preferences
    fields = ['distance_units', 'ascent_units']

    def dispatch(self, request, *args, **kwargs):
        if 'pk' not in kwargs:
            try:
                kwargs['pk'] = Preferences.objects.get(user=request.user).pk
            except Preferences.DoesNotExist:
                return HttpResponseRedirect(reverse('bike:preferences_new'))
        elif not Preferences.objects.filter(pk=kwargs['pk'],
                                            user=request.user).exists():
            return HttpResponse("Unauthorised preferences", status=401)
        return super(PreferencesUpdate, self).dispatch(request, *args,
                                                       **kwargs)

    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET['next']
        return super(PreferencesUpdate, self).get_success_url()


class BikeCreate(LoginRequiredMixin, CreateView):
    model = Bike
    fields = ['name', 'description']

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.owner = self.request.user
        return super(BikeCreate, self).form_valid(form)


class BikeUpdate(LoginRequiredMixin, UpdateView):
    model = Bike
    fields = ['name', 'description']

    def dispatch(self, request, *args, **kwargs):
        if not Bike.objects.filter(pk=kwargs['pk'],
                                   owner=request.user).exists():
            return HttpResponse("Unauthorised bike", status=401)
        return super(BikeUpdate, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['components'] = Component.objects.filter(bike_id=pk)
        return context

    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET['next']
        return super(BikeUpdate, self).get_success_url()


class BikeDelete(LoginRequiredMixin, DeleteView):
    model = Bike
    fields = ['name', 'description']
    success_url = reverse_lazy('bike:bikes')

    def dispatch(self, request, *args, **kwargs):
        if not Bike.objects.filter(pk=kwargs['pk'],
                                   owner=request.user).exists():
            return HttpResponse("Unauthorised bike", status=401)
        return super(BikeDelete, self).dispatch(request, *args, **kwargs)


def components(request):
    components = Component.objects.filter(owner=request.user).all()
    return render(request, 'bike/components.html',
                  context={'components': components})


class ComponentCreate(LoginRequiredMixin, CreateView):
    model = Component
    fields = ['type', 'name', 'bike', 'subcomponent_of', 'specification',
              'notes', 'supplier', 'date_acquired']

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(CreateView, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        bike_id = self.request.GET.get('bike')
        subcomp_of_id = self.request.GET.get('subcomponent_of')
        if bike_id or subcomp_of_id:
            initial = initial.copy()
            if bike_id is not None:
                bike = get_object_or_404(
                    Bike, pk=bike_id, owner=self.request.user)
                initial['bike'] = bike
            if subcomp_of_id is not None:
                subcomp_of = get_object_or_404(
                    Component, pk=subcomp_of_id, owner=self.request.user)
                initial['subcomponent_of'] = subcomp_of
        return initial

    def form_valid(self, form):
        bike_id = self.request.GET.get('bike')
        if bike_id:
            if not Bike.objects.filter(
                    pk=bike_id, owner=self.request.user).exists():
                return HttpResponse("Unauthorised or non-existent bike.",
                                    status=401)
                form.instance.bike_id = bike_id
        form.instance.owner = self.request.user
        return super(ComponentCreate, self).form_valid(form)

    def get_success_url(self):
        if self.request.method == 'POST':
            success_url = self.request.GET.get('success')
            if success_url:
                return success_url
        return super(ComponentCreate, self).get_success_url()


class ComponentUpdate(LoginRequiredMixin, UpdateView):
    model = Component
    fields = ['type', 'name', 'bike', 'subcomponent_of', 'specification',
              'notes', 'supplier', 'date_acquired']

    def dispatch(self, request, *args, **kwargs):
        if not Component.objects.filter(pk=kwargs['pk'],
                                        owner=request.user).exists():
            return HttpResponse("Unauthorised component", status=401)
        return super(ComponentUpdate, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET['next']
        return super(ComponentUpdate, self).get_success_url()

    def get_context_data(self):
        context_data = super(ComponentUpdate, self).get_context_data()
        subcomponents = Component.objects.filter(
            subcomponent_of=self.object).all()
        context_data['subcomponents'] = subcomponents
        return context_data


class ComponentDelete(LoginRequiredMixin, DeleteView):
    model = Component
    success_url = reverse_lazy('bike:components')

    def dispatch(self, request, *args, **kwargs):
        if not Component.objects.filter(pk=kwargs['pk'],
                                        owner=request.user).exists():
            return HttpResponse("Unauthorised component", status=401)
        return super(ComponentDelete, self).dispatch(request, *args, **kwargs)


def component_types(request):
    component_types = ComponentType.objects.filter(user=request.user).all()
    return render(request, 'bike/component_types.html',
                  context={'component_types': component_types})


class ComponentTypeCreate(LoginRequiredMixin, CreateView):
    model = ComponentType
    fields = ['type', 'subtype_of', 'description', 'maintenance_interval',
              'maint_interval_units']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(ComponentTypeCreate, self).form_valid(form)

    def get_success_url(self):
        url = super(ComponentTypeCreate, self).get_success_url()
        success_url = self.request.GET.get('success')
        if success_url:
            url += f'?success={success_url}'
        return url


class ComponentTypeUpdate(LoginRequiredMixin, UpdateView):
    model = ComponentType
    fields = ['type', 'subtype_of', 'description', 'maintenance_interval',
              'maint_interval_units']

    def dispatch(self, request, *args, **kwargs):
        if not ComponentType.objects.filter(pk=kwargs['pk'],
                                            user=request.user).exists():
            return HttpResponse("Unauthorised component", status=401)
        return super(ComponentTypeUpdate, self).dispatch(
            request, *args, **kwargs)

    def get_success_url(self):
        if 'success' in self.request.GET:
            return self.request.GET['success']
        return super(ComponentTypeUpdate, self).get_success_url()


class ComponentTypeDelete(LoginRequiredMixin, DeleteView):
    model = ComponentType
    success_url = reverse_lazy('bike:component_types')

    def dispatch(self, request, *args, **kwargs):
        if not ComponentType.objects.filter(pk=kwargs['pk'],
                                            user=request.user).exists():
            return HttpResponse("Unauthorised component", status=401)
        return super(ComponentTypeDelete, self).dispatch(
            request, *args, **kwargs)


class RideCreate(LoginRequiredMixin, CreateView):
    model = Ride
    fields = ['bike', 'date', 'description', 'distance', 'distance_units',
              'ascent', 'ascent_units']

    def get_initial(self):
        initial = super(RideCreate, self).get_initial()
        last_bike = Bike.objects.filter(
            owner=self.request.user).order_by('-rides__date').first()
        # copy, so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['bike'] = last_bike
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.rider = self.request.user
        return super(RideCreate, self).form_valid(form)


class RideUpdate(LoginRequiredMixin, UpdateView):
    model = Ride
    fields = ['bike', 'date', 'description', 'distance', 'distance_units',
              'ascent', 'ascent_units']

    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET['next']
        return super(RideUpdate, self).get_success_url()

    def dispatch(self, request, *args, **kwargs):
        if not Ride.objects.filter(pk=kwargs['pk'],
                                   rider=request.user).exists():
            return HttpResponse("Unauthorised ride", status=401)
        return super(RideUpdate, self).dispatch(request, *args, **kwargs)


class RideDelete(LoginRequiredMixin, DeleteView):
    model = Ride
    success_url = reverse_lazy('bike:rides')

    def dispatch(self, request, *args, **kwargs):
        if not Ride.objects.filter(pk=kwargs['pk'],
                                   rider=request.user).exists():
            return HttpResponse("Unauthorised ride", status=401)
        return super(RideDelete, self).dispatch(request, *args, **kwargs)


@login_required
def rides(request):
    if request.method == 'POST':
        form = RideSelectionForm(
            request.POST, bikes=Bike.objects.filter(owner=request.user).all())
        if form.is_valid():
            rides = Ride.objects.filter(rider=request.user)
            bike = form.cleaned_data['bike']
            if bike:
                rides = rides.filter(bike=bike)
            start_date = form.cleaned_data['start_date']
            if start_date:
                rides = rides.filter(date__gte=start_date)
            end_date = form.cleaned_data['end_date']
            if end_date:
                rides = rides.filter(date__lte=end_date)
            rides = rides.order_by('-date').all()
            num_rides = form.cleaned_data['num_rides']
            if num_rides:
                log.info("Applying filter num_rides=%d", num_rides)
                rides = rides[:num_rides]
            log.info("request.GET=%s", request.GET)
            if not rides.exists():
                form.add_error(None, "No rides found matching those criteria.")
            elif request.GET.get('action') == 'download_as_csv':
                log.info("csv download requested")
                fields = ['date', 'bike', 'distance', 'distance_units_display',
                          'ascent', 'ascent_units_display', 'description']
                return csv_data_response(request, 'rides.csv', rides, fields)
        else:
            rides = Ride.objects.order_by('-date').all()[:20]
    else:
        form = RideSelectionForm(
            bikes=Bike.objects.filter(owner=request.user).all())
        rides = Ride.objects.order_by('-date').all()[:20]
    return render(request, 'bike/rides.html',
                  context={'form': form, 'rides': rides})


def csv_data_response(request, filename, queryset, fields):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(fields)  # header row
    for row in queryset.all():
        csv_row = [getattr(row, field_name) for field_name in fields]
        writer.writerow(csv_row)
    return response


class MaintActionList(LoginRequiredMixin, ListView):
    model = MaintenanceAction
    ordering = ('bike', 'component', 'distance', 'due_date')

    def get_queryset(self):
        return MaintenanceAction.objects.filter(
            user=self.request.user, completed=False)


class MaintActionCreate(LoginRequiredMixin, CreateView):
    model = MaintenanceAction
    fields = ['bike', 'component', 'activity_type', 'description', 'due_date',
              'distance', 'distance_units', 'completed', 'completed_date',
              'completed_distance']

    def get_form(self, *args, **kwargs):
        form = super(MaintActionCreate, self).get_form(*args, **kwargs)
        form.fields['bike'].queryset = self.request.user.bikes
        form.fields['component'].queryset = self.request.user.components
        return form

    def get_initial(self):
        initial = super(MaintActionCreate, self).get_initial()
        last_bike = Bike.objects.filter(
            owner=self.request.user).order_by('-rides__date').first()
        # copy, so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['bike'] = last_bike
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        return super(MaintActionCreate, self).form_valid(form)


class MaintActionUpdate(LoginRequiredMixin, UpdateView):
    model = MaintenanceAction
    fields = MaintActionCreate.fields

    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET['next']
        return super(MaintActionUpdate, self).get_success_url()

    def dispatch(self, request, *args, **kwargs):
        if not MaintenanceAction.objects.filter(
                pk=kwargs['pk'], user=request.user).exists():
            return HttpResponse("Unauthorised maint. action", status=401)
        return super(
            MaintActionUpdate, self).dispatch(request, *args, **kwargs)


# TODO: acc maint actions to home and bike page
class MaintActionDelete(LoginRequiredMixin, DeleteView):
    model = MaintenanceAction
    success_url = reverse_lazy('bike:maint_actions')

    def dispatch(self, request, *args, **kwargs):
        if not MaintenanceAction.objects.filter(
                pk=kwargs['pk'], user=request.user).exists():
            return HttpResponse("Unauthorised maint. action", status=401)
        return super(
            MaintActionDelete, self).dispatch(request, *args, **kwargs)


@login_required
def mileage(request, pk=None):
    # odometer and recent mileage stuff for bikes / a bike ...
    return HttpResponse("odometer and recent mileage stuff for bikes / a bike "
                        "...not yet implemented.")
