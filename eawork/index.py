from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register
from django.conf import settings

from eawork.models import JobPostVersion


if settings.IS_ENABLE_ALGOLIA:

    @register(JobPostVersion)
    class JobsIndex(AlgoliaIndex):
        index_name = settings.ALGOLIA["INDEX_NAME_JOBS"]
        should_index = "is_should_submit_to_algolia"

        fields = [
            "title",
            "description",
            "created_at",
            "updated_at",
            "closes_at",
            "posted_at",
            "url_external",
            "experience_min",
            "experience_avg",
            "salary_min",
            "salary_max",
            [
                "get_tags_generic_formatted",
                "tags_generic",
            ],
            [
                "get_tags_area_formatted",
                "tags_area",
            ],
            [
                "get_tags_degree_required_formatted",
                "tags_degree_required",
            ],
            [
                "get_tags_country_formatted",
                "tags_country",
            ],
            [
                "get_tags_city_formatted",
                "tags_city",
            ],
            [
                "get_tags_role_type_formatted",
                "tags_role_type",
            ],
            [
                "get_tags_skill_formatted",
                "tags_skill",
            ],
            [
                "get_tags_location_type_formatted",
                "tags_location_type",
            ],
            [
                "get_tags_location_type_formatted",
                "tags_location_type",
            ],
            [
                "get_tags_workload_formatted",
                "tags_workload",
            ],
            [
                "get_tags_immigration_formatted",
                "tags_immigration",
            ],
        ]
