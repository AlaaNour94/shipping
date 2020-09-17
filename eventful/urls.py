from rest_framework import routers
from .views import EventResource

event_router = routers.SimpleRouter()
event_router.register(r'events', EventResource)
