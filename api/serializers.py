from rest_framework import serializers

from api.models import Label, Note, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'is_verified')
        read_only_fields = ('id', 'is_verified')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save()
        return instance


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ('id', 'title', 'description', 'user')
        read_only_fields = ('id',)


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'title', 'color', 'author', 'note')
        read_only_fields = ('id',)
