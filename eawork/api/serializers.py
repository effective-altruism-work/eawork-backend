from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from eawork.models import PostJobTag
from eawork.models import PostJobTagTypeEnum
from eawork.models import PostJobVersion
from eawork.models import PostJobTagType


class TagTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = PostJobTagType
        fields = [
            "type",
        ]


class TagSerializer(serializers.ModelSerializer):
    types = TagTypeSerializer(many=True)

    class Meta:
        model = PostJobTag
        fields = [
            "pk",
            "name",
            "types",
            "count",
        ]


class PostJobVersionSerializer(serializers.ModelSerializer):

    for tag_type_enum in PostJobTagTypeEnum:
        locals()[f"tags_{tag_type_enum.value}"] = TagSerializer(
            many=True, required=False
        )
        locals()[f"tags_{tag_type_enum.value}_pks"] = PrimaryKeyRelatedField(
            many=True,
            queryset=PostJobTag.objects.filter(types__type=tag_type_enum),
            source=f"tags_{tag_type_enum.value}",
            required=False,
        )

    class Meta:
        model = PostJobVersion
        fields = []
        for tag_type_enum in PostJobTagTypeEnum:
            fields.append(f"tags_{tag_type_enum.value}")
            fields.append(f"tags_{tag_type_enum.value}_pks")

    def update(self, instance: PostJobVersion, validated_data: dict) -> PostJobVersion:
        for field in self.Meta.fields:
            is_updatable_field = not field.endswith("_pks")
            if is_updatable_field:
                self._m2m_field_update(
                    instance,
                    validated_data=validated_data,
                    field_name=field,
                )
        return super().update(instance, validated_data)

    def _m2m_field_update(
        self,
        instance: PostJobVersion,
        validated_data: dict,
        field_name: str,
    ):
        if field_name in validated_data:
            tags_new = validated_data.pop(field_name)
            tags_field = getattr(instance, field_name)
            tags_field.set(tags_new)
