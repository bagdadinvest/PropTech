from django.contrib import admin
from .models import MetroStation, BusStop, MetrobusStation


@admin.register(MetroStation)
class MetroStationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(MetrobusStation)
class MetrobusStationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
