from algoliasearch_django import AlgoliaIndex
from algoliasearch_django.decorators import register
from django.conf import settings

from eawork.models import JobPostTag
from eawork.models import JobPostVersion


if settings.IS_ENABLE_ALGOLIA:

    @register(JobPostVersion)
    class JobsIndex(AlgoliaIndex):
        index_name = settings.ALGOLIA["INDEX_NAME_JOBS"]
        should_index = "is_should_submit_to_algolia"
        custom_objectID = "get_post_pk"

        fields = [
            ["get_post_pk", "post_pk"],
            "title",
            "description",
            "description_short",
            ["get_description_for_search", "description_for_search"],
            ["get_id_external_80_000_hours", "id_external_80_000_hours"],
            "created_at",
            "updated_at",
            "closes_at",
            "posted_at",
            "url_external",
            "experience_min",
            "experience_avg",
            "salary_min",
            "salary_max",
            ["get_combined_org_data", "org_data"],
            ["get_company_name", "company_name"],
            ["get_company_url", "company_url"],
            ["get_company_logo_url", "company_logo_url"],
            ["get_company_career_page_url", "company_career_page_url"],
            ["get_company_ea_forum_url", "company_ea_forum_url"],
            ["get_company_is_top_recommended_org", "company_is_recommended_org"],
            ["get_company_description", "company_description"],
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
                "get_tags_exp_required_formatted",
                "tags_exp_required",
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
                "get_tags_location_80k_formatted",
                "tags_location_80k",
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

    @register(JobPostTag)
    class JobPostTagIndex(AlgoliaIndex):
        index_name = settings.ALGOLIA["INDEX_NAME_TAGS"]
        fields = [
            "name",
            "description",
            "synonyms",
            ["get_types_formatted", "types"],
            "created_at",
            "status",
            "is_featured",
            "count",
        ]
