from rest_framework import serializers
from profiles.models import User, AdminProfile, DeveloperProfile, DriverProfile
from django.contrib.auth.models import Group


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'id', 'role', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = super().create(validated_data)
        user.is_staff = user.role == User.ADMIN

        if 'password' in validated_data:
            user.set_password(validated_data['password'])

        user.save()

        Group.objects.get(name=user.role).user_set.add(user)

        if user.role == User.ADMIN:
            AdminProfile.objects.create(user=user)

        if user.role == User.DRIVER:
            DriverProfile.objects.create(user=user)

        if user.role == User.DEVELOPER:
            DeveloperProfile.objects.create(user=user)

        return user
