from rest_framework import serializers


class BookSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=255)
    authors = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=255),
        allow_empty=False,
    )
    publisher = serializers.CharField(min_length=1, max_length=255)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Title must not be empty.')
        return value

    def validate_publisher(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Publisher must not be empty.')
        return value

    def validate_authors(self, value):
        authors = [author.strip() for author in value]
        if any(not author for author in authors):
            raise serializers.ValidationError('Authors must not be empty.')
        return authors