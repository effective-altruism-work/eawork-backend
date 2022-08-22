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
            ["get_tags_generic_formatted", "tags"],
            ["get_tags_affiliation_formatted", "affiliations"],
            ["get_tags_cause_area_formatted", "cause_areas"],
            ["get_tags_exp_required_formatted", "exp_required"],
            ["get_tags_degree_required_formatted", "degree_required"],
            ["get_tags_country_formatted", "countries"],
            ["get_tags_city_formatted", "cities"],
            ["get_tags_role_type_formatted", "role_types"],
        ]
