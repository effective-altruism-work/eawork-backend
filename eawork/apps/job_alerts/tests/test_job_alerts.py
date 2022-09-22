import datetime
import json
import time

import pytz
from algoliasearch_django import clear_index
from dateutil.relativedelta import relativedelta
from django.core import mail

from eawork.apps.job_alerts.job_alert import check_new_jobs_for_all_alerts
from eawork.models import JobAlert
from eawork.models import JobPost
from eawork.models import JobPostTag
from eawork.models import JobPostVersion
from eawork.services.import_80_000_hours import import_80_000_hours_jobs
from eawork.tests.cases import EAWorkTestCase


class JobCreateTest(EAWorkTestCase):
    algolia_caching_time_s = 6  # 5s isn't enough
    fixtures_posted_at_years_offset = 50

    @classmethod
    def setUpClass(cls):
        clear_index(JobPostVersion)
        clear_index(JobPostTag)
        super().setUpClass()

    def test_job_create(self):
        post_title = "Software Engineer"
        self._create_post_and_publish_it(post_title)
        self.assertEquals(len(mail.outbox), 1)

        JobAlert.objects.create(
            email="victor+git@givemomentum.com",
            query_json={
                "query": post_title,
            },
        )

        check_new_jobs_for_all_alerts()
        self.assertEquals(len(mail.outbox), 1)

        self._create_post_and_publish_it(post_title + "2")

        check_new_jobs_for_all_alerts()

        # 3 including the 2 new post notifications for the admin
        self.assertEquals(len(mail.outbox), 3)
        print(mail.outbox[2].body)

    def test_80_000_hours_double_import(self):
        alert = JobAlert.objects.create(
            email="victor+git@givemomentum.com",
            query_json={
                "query": "",
                "facetFilters": ["tags_role_type:Research"],
            },
        )

        with open("eawork/tests/fixtures/json_to_import.json", "r") as json_to_import:
            json_to_import = json.loads(json_to_import.read())

        import_80_000_hours_jobs(json_to_import)
        time.sleep(self.algolia_caching_time_s)
        check_new_jobs_for_all_alerts()
        self.assertEquals(len(mail.outbox), 1)
        print(mail.outbox[0].body)

        alert.last_checked_at = datetime.datetime.now(pytz.utc) + relativedelta(
            years=self.fixtures_posted_at_years_offset
        )
        alert.save()

        import_80_000_hours_jobs(json_to_import)
        time.sleep(self.algolia_caching_time_s)
        check_new_jobs_for_all_alerts()
        self.assertEquals(len(mail.outbox), 1)

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
        time.sleep(self.algolia_caching_time_s)

        return JobPost.objects.get(version_current=post_version)
