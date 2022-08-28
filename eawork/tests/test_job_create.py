from algoliasearch_django import clear_index
from django.core import mail

from eawork.models import JobAlert
from eawork.models import JobPostTag
from eawork.models import JobPostVersion
from eawork.models import PostStatus
from eawork.services.job_alert import check_new_jobs_for_all_alerts
from eawork.tests.cases import EAWorkTestCase


class JobCreateTest(EAWorkTestCase):
    @classmethod
    def setUpClass(cls):
        clear_index(JobPostVersion)
        clear_index(JobPostTag)
        super().setUpClass()

    def test_job_create(self):
        post_title = "Software Engineer"
        tags_skill = ["Django", "Angular", "PostgreSQL"]
        res = self.client.post(
            "/api/jobs/post",
            dict(
                email=self.gen.faker.email(),
                company_name="Company Test Name",
                title="Software Engineer",
                description_short="<p>Short description.</p><p>Second paragraph.</p>",
                description="<p>Kind of longer description.</p><p>Second paragraph.</p>",
                url_external="https://givemomentum.com/careers",
                tags_area=["Operations"],
                tags_country=["United States"],
                tags_skill=tags_skill,
            ),
        )
        self.assertEquals(res.json(), {"success": True})

        post_version = JobPostVersion.objects.get(title=post_title)
        post_version.status = PostStatus.PUBLISHED
        post_version.save()

        JobAlert.objects.create(
            email="victor+git@givemomentum.com",
            query_json={
                "query": post_title,
            },
            post_pk_seen_last=0,
        )
        check_new_jobs_for_all_alerts()

        self.assertEquals(len(mail.outbox), 1)
        print(mail.outbox[0].body)
