from rest_framework import permissions


class CanCreateShipment(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("shipment.add_shipment")


class CanPrintLabel(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("shipment.print_shipment_labels")


class CanScheduleShipment(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("shipment.schedule_shipment")


class CanSubscribeWebhook(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("shipment.subscribe_webhook")


class CanAttachDocument(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("shipment.attach_documents")


class CanChangeShipmentState(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("shipment.change_shipment_state")
