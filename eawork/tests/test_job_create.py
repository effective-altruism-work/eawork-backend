import time

from algoliasearch_django import clear_index
from django.core import mail

from eawork.models import JobAlert
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostVersion
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
        post_first: JobPost = self._create_post_and_publish_it(post_title)

        alert = JobAlert.objects.create(
            email="victor+git@givemomentum.com",
            query_json={
                "query": post_title,
            },
            post_pk_seen_last=0,
        )

        check_new_jobs_for_all_alerts()
        self.assertEquals(len(mail.outbox), 1)
        print(mail.outbox[0].body)
        alert.refresh_from_db()
        self.assertEquals(alert.post_pk_seen_last, post_first.pk)

        post_second: JobPost = self._create_post_and_publish_it(post_title + "2")

        check_new_jobs_for_all_alerts()

        self.assertEquals(len(mail.outbox), 2)
        print(mail.outbox[1].body)
        alert.refresh_from_db()
        self.assertEquals(alert.post_pk_seen_last, post_second.pk)

    def _create_post_and_publish_it(self, title: str) -> JobPost:
        tags_skill = ["Django", "Angular", "PostgreSQL"]
        res = self.client.post(
            "/api/jobs/post",
            dict(
                email=self.gen.faker.email(),
                company_name="Company Test Name",
                title=title,
                description_short="<p>Short description.</p><p>Second paragraph.</p>",
                description="<p>Kind of longer description.</p><p>Second paragraph.</p>",
                url_external="https://givemomentum.com/careers",
                tags_area=["Operations"],
                tags_country=["United States"],
                tags_skill=tags_skill,
            ),
        )
        self.assertEquals(res.json(), {"success": True})

        post_version = JobPostVersion.objects.get(title=title)
        post_version.publish()

        # wait for algolia cache to clear
        time.sleep(4)

        return JobPost.objects.get(version_current=post_version)
