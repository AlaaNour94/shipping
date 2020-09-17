import logging

from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import UserSerializer
from .models import User

logger = logging.getLogger(__name__)


class UserResource(viewsets.ModelViewSet):

    permission_classes = (IsAdminUser, )
    parser_classes = (JSONParser, )
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, permission_classes=(IsAuthenticated, ))
    def me(self, request):
        """Return User data for the requester"""

        try:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.exception(f"Error {e} while getting user")
            return Response({"error": "error happened please try again later"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
