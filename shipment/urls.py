from rest_framework import routers
from .views import ShipmentResource

shipment_router = routers.SimpleRouter()
shipment_router.register(r'shipments', ShipmentResource)
