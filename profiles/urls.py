from rest_framework import routers
from .views import UserResource

user_router = routers.SimpleRouter()
user_router.register(r'users', UserResource)
