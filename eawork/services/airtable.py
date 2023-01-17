from typing import Literal, TypedDict, List
from typing import TypedDict
from pyairtable import Table
from django.conf import settings
from urllib.parse import urlparse
import json
import time
import collections

class Datum(TypedDict):
  link: str # can be blank
  name: str

class DropdownData(TypedDict):
    problem_areas: List[Datum]
    problem_area_tags: List[Datum]
    problem_area_filter: List[Datum]
    rationales: List[Datum]
    location_filters: List[Datum]
    top_org_problem_areas: List[Datum]

def import_from_airtable():
    print("\nimport airtable")
    dropdown = get_dropdown_data()
    print(json.dumps(dropdown, indent=4))

    raw_vacancies = get_raw_vacancy_data()
    raw_organisations = get_raw_organisation_data()
    # raw_tags = get_raw_tag_data()

    res = {
        "meta": {"retrieved_at": round(time.time() * 1000)},
        "data": {"status": "???", "vacancies": [], "organisations": [], "rationales": []},
    }

    print(json.dumps(res, indent=4))
    raise Exception("not yet")


def get_raw_dropdown_data():
    formula = "case '!Location filters (orgs tab)'"
    formula = """OR(
      {!Category} = '!Problem area', 
      {!Category} = '!Problem area (tags)',
      {!Category} = '!Problem areas (filters)', 
      {!Category} = '!Rationale', 
      {!Category} = '!Location filters (orgs tab)',
      {!Category} = '!Top orgs (problem area)')"""

    table_name = "!Dropdowns"
    params = {
        "fields": [
            "!Name for front end",
            "!Link for tag",  # maybe only some?
            "!Category",  # crucial! We're pulling lots of different kinds of data, and we are going to need to separate them
        ],
        "filterByFormula": formula,
        "maxRecords": 1000,
    }

    dropdown_data = get_airtable_data(table_name, params)

    return dropdown_data

def get_dropdown_data() -> DropdownData:
  raw_data = get_raw_dropdown_data()
  
  map: DropdownData = {
    "problem_areas": {},
    "problem_areas_tags": {},
    "problem_area_filters": {},
    "rationales": {},
    "location_filters": {},
    "top_org_problem_areas": {}
  }

  # separate all the data we got in get_raw_dropdown_data into their own nests.
  for record in raw_data:
    print(record['fields'])
    properties = {"name": record["fields"]["!Name for front end"].strip(), "link": record["fields"].get("!Link for tag") or ""}
    match record["fields"]["!Category"]:
      case "!Problem area":
        map["problem_areas"][record["id"]] = properties
      case '!Problem area (tags)':
        map["problem_areas_tags"][record["id"]] = properties
      case '!Problem areas (filters)':
        map["problem_areas_filters"][record["id"]] = properties
      case '!Rationale':
        map["rationales"][record["id"]] = properties
      case '!Location filters (orgs tab)':
        map["location_filters"][record["id"]] = properties
      case '!Top orgs (problem area)':
        map["top_org_problem_areas"][record["id"]] = properties

  return map



def get_raw_vacancy_data():
    table_name = "!Vacancies"

    # note that airtable has a weird thing where 21 seems to be a hard limit for reqs.
    fields = [
        "!Title",
        "!Org",
        "!Date it closes",
        # '!Tier',
        "!Date published",
        # '!Problem area (main)',
        "!Problem area (filters)",
        # '!Problem area (others)',
        "!Description",
        "!Vacancy page",
        "!Role type",
        "!Required degree",
        # '!Required experience',
        "!Location",
        # '!CTA code',
        "!is_recommended_org",
        "!ea_forum_link",
        "!MinimumExperienceLevel",
        "!Salary (display)",
        "!Region",
        # '!Rationale',
        "!Problem area (tags)",
        "!Featured",
    ]

    filter = "AND( {!Publication (is it live?)} = '!yes', IS_AFTER({!Date it closes}, DATEADD(TODAY(),-1,'days')), IS_BEFORE({!Date published}, NOW()) )"

    params = {
        "fields": fields,
        "filterByFormula": filter,
        "sort": [
            "-!Date published",  # '-' in column name descends it
            "!Org",
        ],
        "max_records": 10000,
    }

    vacancies = get_airtable_data(table_name, params)

    return vacancies


def get_raw_organisation_data():
    table_name = "!Orgs"
    fields = (
        [
            "!Org",
            "!Home page",
            "!Vacancies page",
            "!Description",
            "!Logo",
            "!Text_hover",
            "!Problem area (orgs)",
            "!Locations (orgs)",
            "!Internal links",
            "!External links",
            "!Org size",
            "!Founded year",
            "!Glassdoor link",
            "!Social media links",
            "!Region (orgs)",
            "!EA Forum link",
            "!Recommended org (star)",
            "!Single line description",
            "!Tags (orgs)",
        ],
    )

    params = {"fields": fields, "max_records": 10000}

    organisations = get_airtable_data(table_name, params)

    return organisations


def transform_organisations_data(
    organisations: list[dict], top_orgs_problem_areas=[], all_potential_tags=[]
):

    top_org_problem_area_id_to_name_map = {}
    for problem_area in top_orgs_problem_areas:
        top_org_problem_area_id_to_name_map[problem_area["id"]] = problem_area["fields"]["!Name for front end"].strip()

    all_potential_tags_id_to_name_map = {}
    for tag in all_potential_tags:
        all_potential_tags_id_to_name_map[tag["id"]] = tag["fields"]["!Name for front end"].strip()

    transformed_orgs = []

    for org in organisations:
        # Rename some fields
        org["Name"] = org.pop("!org")
        org["Domain"] = org.pop("!Home page")
        org["Career Page"] = org.pop("!Vacancies page")
        org["Company Description"] = org.pop("!Description")
        org["Company Logo"] = org.pop("!Logo")
        org["text_hover"] = org.pop("!Text_hover")
        org["problem_areas"] = org.pop("!Problem area (orgs)")
        org["locations"] = org.pop("!Locations (orgs)")
        org["internal_links"] = org.pop("!Internal links")
        org["external_links"] = org.pop("!External links")
        org["org_size"] = org.pop("!Org size")
        org["founded_year"] = org.pop("!Founded year")
        org["glassdoor_link"] = org.pop("!Glassdoor link")
        org["social_media_links"] = org.pop("!Social media links")
        org["region"] = org.pop("!Region (orgs)")
        org["recommended_org"] = org.pop("!Recommended org (star)")
        org["forum_link"] = org.pop("!EA Forum link")
        org["single_line_description"] = org.pop("!Single line description")
        org["tags"] = org.pop("!Tags (orgs)")

        # Transform some fields

        # Get problem area names from record IDs
        problem_area_ids = []
        problem_area_names = []

        # account for null field in problem areas
        if type(org["fields"]["problem_areas"]) == list:
            problem_area_ids = org["fields"]["problem_areas"]
            for problem_area_id in problem_area_ids:
                problem_area_names = top_org_problem_area_id_to_name_map[problem_area_id]

        org["fields"]["problem_areas"] = problem_area_names

        # Get tag names from record IDs
        tag_names = []

        # account for null field in tags
        if type(org["fields"]["tags"]) == list:
            tag_ids = org["fields"]["tags"]
            for tag_id in tag_ids:
                print("todo") # # something something do the mapping
                # tag_names[] = all_potential_tags_id_to_name_map[tag_id]
        org["fields"]["tags"] = tag_names

        # Get location names from record IDs
        location_ids = []
        location_names = []
        if type(org["fields"]["locations"]) == list:
            location_ids = org["fields"]["locations"]
            for location_id in location_ids:
                print("todo")
                # location_names[] = location_id_to_name_map[location_id]
        org["fields"]["locations"] = location_names

        region_ids = []
        region_names = []
        if type(org["fields"]["region"]) == list:
            region_ids = org["fields"]["region"]
            for region_id in region_ids:
                print("todo")
                # region_names[] = region_id_to_name_map[region_id]
        org["fields"]["region"] = region_names

        # "Domain", "Career Page" and "Company Logo" fields can contain:
        # (1) [null] -- array with single element with value null
        # (2) ["string"] -- array with single element of type string
        # (3) "" -- empty string

        # If (1) then implode, and get ""
        # If (2) then implode and get "string"
        # If (3) don't need to transform

        # Transform "Domain" field values from array to string
        if type(org["fields"]["Domain"]) == list:
            org["fields"]["Domain"] =     org["fields"]["Domain"].join(", ")

        # Transform "Career Page" field values from array to string
        if type(org["fields"]["Career Page"]) == list:
            org["fields"]["Career Page"] =     org["fields"]["Career Page"].join(", ")
            

        if not org["fields"]["Domain"]:
            # If domain is missing http prefix, add it.
            if "http" not in org["fields"]["Domain"]:
                org["fields"]["Domain"] = "https:#".org["fields"]["Domain"]

            # Add UTM params to homepage link
            org["fields"]["Domain"] = get_link_with_tracking_params(
                org["fields"]["Domain"]
            )

        if not org["fields"]["Career Page"]:
            # If career page is missing http prefix, add it.
            if "http" not in org["fields"]["Career Page"]:
                org["fields"]["Career Page"] = "https:#".org["fields"]["Career Page"]

            # Add UTM params to career page link
            org["fields"]["Career Page"] = get_link_with_tracking_params(
                org["fields"]["Career Page"]
            )

        # Transform "Company Logo" field values from array to string
        if type(org["fields"]["Company Logo"]) == list:
            org["fields"]["Company Logo"] = org["fields"]["Company Logo"].join(", ")

        # Transform "Company Description" field values from array to string
        # Haven't seen any values for this field being served as an array,
        # but since I (RD) don't really understand why sometimes get arrays back
        # from airtable so transforming it just in case.
        if type(org["fields"]["Company Logo"])==list:
            org["fields"]["Company Logo"] = org["fields"]["Company Logo"].join(", ")

        # 2021-09: Rewrite company logo image url since we no longer use WP Engine's CDN at
        # cdn.80000hours.org, and now just use Cloudflare as a CDN for our images at
        # 80000hours.org
        org["fields"]["Company Logo"] = org["fields"]["Company Logo"].replace(
            "https:#cdn.80000hours.org",
            "https:#80000hours.org",
        )

        # Should use thumbnail version of company logo if it exists
        if not org["fields"]["Company Logo"]:
            if "-150x150" not in org["fields"]["Company Logo"]:

                # /*
                #   Usually WordPress does not generate a thumbnail if the uploaded
                #   image is already 160x160 or smaller. We have changed the default
                #   behaviour so that thumbnails are always generated.

                #   See lib/wp-admin.php in the WordPress repository.
                # */
                thumbnail_url = org["fields"]["Company Logo"].replace(".jpg", "-160x160.jpg")
                thumbnail_url = thumbnail_url.replace(".jpeg", "-160x160.jpeg")
                thumbnail_url = thumbnail_url.replace(".png", "-160x160.png")
                thumbnail_url = thumbnail_url.replace(".gif", "-160x160.gif")

                org["fields"]["Company Logo"] = thumbnail_url

        # simple typecast
        org["fields"]["recommended_org"] = bool(
            org["fields"]["recommended_org"]
        )
        
        transformed_orgs.append(org)

    return transformed_orgs



def get_raw_tag_data():
    filter = "case '!Rationale'"

    table_name = "!Dropdowns"
    params = {
        "fields": ["!Name for front end", "!Link for tag"],
        "filterByFormula": filter,
        "maxRecords": 1000,
        "pageSize": 100,
    }

    tags = get_airtable_data(table_name, params)

    return tags


def get_airtable_data(table_name, params: dict):
    table = Table(settings.AIRTABLE["API_KEY"], settings.AIRTABLE["BASE_ID"], table_name)
    todo = table.all(
        fields=params["fields"],
        formula=params.get("filterByFormula") or "",
        sort=params.get("sort") or [],
        max_records=params.get("max_records"),
    )
    return todo
    # For testing, we may wish to use sample Airtable API responses.
    # Get live data from Airtable.
    # request = this.airtable.getContent(table_name,params)

    # while request = response.next():
    #   response = request.getResponse()

    #   if(isset(response.error)):
    #     header('HTTP/1.0 500 Internal Server Error')
    #     exit(var_dump(response.error))
    #   else:
    #     airtable_data = array_merge(airtable_data, response['records'])
    #   endif

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
    #   endif

    #   airtable_data = json_decode(result, true)

def get_link_with_tracking_params(url: str):
    # Should not add tracking params if domain is 80000hours.org.
    # Tracking params break a few hiring org websites.
    domains_to_exclude = [
      '80000hours.org',
      'jobs.cam.ac.uk',
      'my.corehr.com'
    ]


    domain_match = True
    for domain in domains_to_exclude:

      if url.replace(domain, '') != url:
        domain_match = False
        break

    if not domain_match:
      params = {
        'utm_campaign': '80000 Hours Job Board',
        'utm_source': '80000 Hours Job Board',
      }

      url = append_query_params_to_url(url, params)

    return url


def append_query_params_to_url(url: str, params_to_append: dict):
  url_parts = urlparse(url)
  
  if 'query' in url_parts:
    params = urlparse(url_parts['query'])
  else:
    params = []

  params = params + params_to_append

  # Note that this will url_encode all values
  url_parts['query'] = http_build_query(params)

  url = url_parts['scheme'] + '://' + url_parts['host'] + url_parts['path'] + '?' + url_parts['query']

  if url_parts['fragment']:
    url = url + '#' + url_parts['fragment']

  return url

def http_build_query(data):
    built = data
    print('todo')
    return built