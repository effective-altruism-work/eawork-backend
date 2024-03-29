from drf_writable_nested import WritableNestedModelSerializer
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from eawork.models import Company
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostTagType
from eawork.models import JobPostTagTypeEnum
from eawork.models import JobPostVersion
from eawork.models import User
from eawork.models.comment import Comment


class TagTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = JobPostTagType
        fields = [
            "type",
        ]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPostTag
        fields = [
            "pk",
            "name",
            "is_featured",
            "link"
            # "types",
            # "count",
        ]


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "name",
            "id_external_80_000_hours",
            "description",
            "logo_url",
            "url",
            "linkedin_url",
            "facebook_url",
            "career_page_url",
            "created_at",
            "updated_at",
            "author",
        ]


class JobPostSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = JobPost
        fields = [
            "company",
            "id_external_80_000_hours",
        ]


class JobPostVersionSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    post = JobPostSerializer(read_only=True)

    for tag_type_enum in JobPostTagTypeEnum:
        locals()[f"tags_{tag_type_enum.value}"] = TagSerializer(many=True, required=False)
        # for tags editing:
        # locals()[f"tags_{tag_type_enum.value}_pks"] = PrimaryKeyRelatedField(
        #     many=True,
        #     queryset=JobPostTag.objects.filter(types__type=tag_type_enum),
        #     source=f"tags_{tag_type_enum.value}",
        #     required=False,
        # )

    class Meta:
        model = JobPostVersion
        fields = [
            "title",
            "post",
            "description",
            "description_short",
            "url_external",
            "author",
            "closes_at",
            "posted_at",
            "created_at",
            "updated_at",
            "experience_min",
            "experience_avg",
            "salary_min",
            "salary_max",
        ]
        for tag_type_enum in JobPostTagTypeEnum:
            fields.append(f"tags_{tag_type_enum.value}")

    def update(self, instance: JobPostVersion, validated_data: dict) -> JobPostVersion:
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
        instance: JobPostVersion,
        validated_data: dict,
        field_name: str,
    ):
        if field_name in validated_data:
            tags_new = validated_data.pop(field_name)
            tags_field = getattr(instance, field_name)
            tags_field.set(tags_new)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
        ]
        extra_kwargs = {"email": {"validators": []}}

    def create(self, validated_data: dict) -> User:
        user = User.objects.filter(email=validated_data["email"]).last()
        if not user:
            user = User.objects.create(**validated_data)
        return user


class CommentSerializer(WritableNestedModelSerializer):
    children = SerializerMethodField()
    author = UserSerializer()

    class Meta:
        model = Comment
        fields = [
            "pk",
            "parent",
            "post",
            "author",
            "content",
            "children",
            "updated_at",
            "created_at",
        ]

    def get_children(self, comment: Comment) -> dict | None:
        if comment.children.exists():
            return CommentSerializer(comment.children, many=True, read_only=True).data
        return None
