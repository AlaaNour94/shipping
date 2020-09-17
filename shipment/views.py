import io
import zipfile
import logging
from django.core.exceptions import ValidationError

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.http import HttpResponse
from .custom_permissions import (
    CanAttachDocument,
    CanCreateShipment,
    CanChangeShipmentState,
    CanPrintLabel,
    CanScheduleShipment,
)
from .serializers import ShipmentSerializer
from .models import Shipment, ShipmentDocument
from profiles.models import User

logger = logging.getLogger(__name__)


class ShipmentResource(viewsets.ModelViewSet):

    permission_classes_by_action = {
        'create': (CanCreateShipment, ),
        'list': (IsAuthenticated, ),
        'delete': (IsAdminUser, ),
    }
    serializer_class = ShipmentSerializer
    queryset = Shipment.objects.all()
    lookup_field = 'tracking_id'

    def get_queryset(self):
        return self.request.user.profile.get_all_shipments()

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def create(self, request, *args, **kwargs):
        """Create a Shipment"""

        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Error {e} while creating a new shipment")
            return Response({"error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=(IsAdminUser, ), url_path='(?P<tracking_id>[^/.]+)/assign_driver/(?P<driver_id>[^/.]+)') # noqa
    def assign_driver(self, request, tracking_id, driver_id):
        """Assign a Driver to a Shipment"""

        try:
            # assert request.data.get('driver_id'), "You should provide driver_id"
            driver = User.objects.get(id=driver_id)
            assert driver.role == User.DRIVER, "You should assign user of type `DRIVER`"

            shipment = self.get_object()
            shipment.driver = driver
            shipment.save()
            return Response({'success': True}, status=status.HTTP_200_OK)

        except AssertionError as e:
            return Response({'success': False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'success': False, "error": "Can not find driver with this id"},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(f"Error {e} while updating shipment state with tracking_id {tracking_id}")
            return Response({"error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=(CanChangeShipmentState, ))
    def update_state(self, request, tracking_id=None):
        """Change the state of a given Shipment"""

        try:
            shipment = self.get_object()
            shipment.update_state(request.data['state'])
            return Response({"success": True}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"success": False, "error": e.message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Error {e} while updating shipment state with tracking_id {tracking_id}")
            return Response({"success": False, "error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=(CanScheduleShipment, ))
    def schedule(self, request, tracking_id=None):
        """Schedule a Shipment"""

        try:
            shipment = self.get_object()
            shipment.schedule()
            return Response({"success": True, "estimated_shipping_date": shipment.estimated_shipping_date},
                            status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"success": False, "error": e.message}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Error {e} while scheduling shipment with tracking_id {tracking_id}")
            return Response({"success": False, "error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,
            methods=['post'],
            permission_classes=(CanAttachDocument, ),
            parser_classes=(MultiPartParser, ))
    def attach_documents(self, request, tracking_id):
        shipment = Shipment.objects.get(tracking_id=tracking_id)

        if not request.FILES.getlist('documents'):
            return Response({"error": "please attach some documents"}, status=status.HTTP_400_BAD_REQUEST)

        for file in request.FILES.getlist('documents'):
            ShipmentDocument.objects.create(document=file, shipment=shipment)

        data = self.serializer_class(shipment).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=(CanPrintLabel, ))
    def print(self, request):
        """Print labels for given tracking ids"""

        try:
            tracking_ids = request.GET.getlist("tracking_id", [])
            assert tracking_ids, "You should provide tracking_ids"
            shipments = self.get_queryset()
            shipments = shipments.filter(tracking_id__in=tracking_ids)

            result = io.BytesIO()

            with zipfile.ZipFile(result, 'w') as zf:
                for shipment in shipments:
                    label = shipment.get_label()
                    zf.writestr(f"{shipment.tracking_id}.pdf", label)

            res = HttpResponse(result.getvalue(), content_type='application/zip')
            res['Content-Disposition'] = 'attachment; filename="shipment_labels.zip"'
            return res

        except Exception as e:
            logger.exception(f"Error {e} while printing labels")
            return Response({"error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], permission_classes=(CanScheduleShipment, ))
    def estimate_delivery_date(self, request, tracking_id=None):
        """Calculate the estimated delivery date for the given shipment"""

        try:
            shipment = self.get_object()
            estimated_date = shipment.estimate_delivery_date()
            return Response({"date": estimated_date}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error {e} while estimating delivery date")
            return Response({"error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
