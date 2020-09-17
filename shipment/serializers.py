from rest_framework import serializers
from shipment.models import Shipment, ShipmentDocument


class DocumentSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField(source='document.url')

    class Meta:
        model = ShipmentDocument
        fields = ['id', 'url']


class ShipmentSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = ('receiver_name', 'receiver_country', 'receiver_address', 'estimated_shipping_date', 'state',
                  'tracking_id', 'scheduled_at', 'weight', 'lat', 'lon', 'documents', 'title')

        extra_kwargs = {
            'state': {
                'read_only': True
            },
            'tracking_id': {
                'read_only': True
            },
            'estimated_shipping_date': {
                'read_only': True
            },
            'scheduled_at': {
                'read_only': True
            }
        }

    def create(self, validated_data):
        """
        Create a Shipment object.

        Args:
            validated_data: a DICT contains Shipment data after the validation step.

        Returns:
            The created Shipment object.
        """

        shipment = Shipment(**validated_data)
        shipment.owner = self.context['request'].user
        shipment.save()
        return shipment
