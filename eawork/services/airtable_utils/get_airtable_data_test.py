from typing import Literal, TypedDict, List, Dict
from typing import TypedDict
from pyairtable import Table
from django.conf import settings
from urllib.parse import urlparse, urlencode, quote_plus
import time
import re

def get_airtable_data_test(table_name: str, params):
    table = Table(settings.AIRTABLE["API_KEY"], settings.AIRTABLE["BASE_ID"], table_name)
    data = table.all(
        fields=params["fields"],
        formula=params.get("filterByFormula", ""),
        sort=params.get("sort", []),
        max_records=params.get("max_records", 1000),
    )
    return data # For testing, we may wish to use sample Airtable API responses.
    # Get live data from Airtable.
    # request = this.airtable.getContent(table_name,params)

    # while request = response.next():
    #   response = request.getResponse()

    #   if(isset(response.error)):
    #     header('HTTP/1.0 500 Internal Server Error')
    #     exit(var_dump(response.error))
    #   else:
    #     airtable_data = array_merge(airtable_data, response['records'])
    #   

    # # Convert Airtable response object to array.
    # airtable_data = json_decode(json_encode(airtable_data), true)

    # else:
    #   # Get test data from local sample file.
    #   sample = this.get_sample_param()
    #   domain = EightyKAPI::get_current_domain()
    #   sample_url = domain . '/samples/airtable/job-board/vacancies/index.php?sample=' . sample

    #   ch = curl_init()
    #   curl_setopt(ch, CURLOPT_SSL_VERIFYPEER, false)
    #   curl_setopt(ch, CURLOPT_RETURNTRANSFER, true)
    #   curl_setopt(ch, CURLOPT_URL, sample_url)
    #   result = curl_exec(ch)
    #   response_info = curl_getinfo(ch)
    #   curl_close(ch)

    #   if(response_info['http_code'] !== 200):
    #     header('HTTP/1.0 500 Internal Server Error')
    #     exit(result)
    #   

    #   airtable_data = json_decode(result, true)
