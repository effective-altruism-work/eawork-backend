from typing import Literal, TypedDict, List, Dict
from typing import TypedDict
from pyairtable import Table
from django.conf import settings
from urllib.parse import urlparse
import json
import time
import collections
import re

class Datum(TypedDict):
  link: str # can be blank
  name: str

class DropdownData(TypedDict):
    problem_areas: List[Datum]
    problem_areas_tags: List[Datum]
    problem_areas_filter: List[Datum]
    rationales: List[Datum]
    location_filters: List[Datum]
    top_org_problem_areas: List[Datum]

def import_from_airtable():
    print("\nimport airtable")
    dropdown = get_dropdown_data()
    locations = get_locations_data()

    raw_vacancies = get_raw_vacancy_data()
    raw_organisations = get_raw_organisation_data()

    organisations = transform_organisations_data(
        raw_organisations, 
        dropdown["top_org_problem_areas"], 
        dropdown["problem_areas_tags"] | dropdown["problem_areas"] | dropdown["rationales"] | dropdown["top_org_problem_areas"], 
        locations, 
        dropdown["location_filters"])

    vacancies = transform_vacancies_data(raw_vacancies, dropdown["problem_areas"] | dropdown["problem_areas_filters"], dropdown["rationales"], locations)

    res = {
        "meta": {"retrieved_at": round(time.time() * 1000)},
        "data": {
            "status": 1, 
            "vacancies": vacancies, 
            "organisations": organisations, 
            "rationales": dropdown["rationales"] | dropdown["problem_areas"] | dropdown["problem_areas_filters"]
        },
    }

    with open("output.txt", 'w') as writer:
        writer.write(json.dumps(res, indent=4))

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
    "problem_areas_filters": {},
    "rationales": {},
    "location_filters": {},
    "top_org_problem_areas": {}
  }

  # separate all the data we got in get_raw_dropdown_data into their own nests.
  for record in raw_data:
    properties = {"name": record["fields"]["!Name for front end"].strip(), "link": record.get("!Link for tag") or ""}
    match record['fields']["!Category"]:
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


def get_locations_data():
    table_name = '!Locations'
    params = {
      'fields':['!Location',
      ],
      'max_records': 1000,
      'pageSize': 100
    }

    locations = get_airtable_data(table_name, params)

    if (type(locations) != list): 
      return []
    location_id_to_name_map = {}
    for location in locations:
      location_id_to_name_map[location['id']] = location['fields']['!Location']

    return location_id_to_name_map

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


def transform_vacancies_data(vacancies: List[Dict], problem_area_id_to_name_map: Dict, rationale_id_to_name_map: Dict, location_id_to_name_map: Dict):
    transformed_vacancies = []
     # Go through transforming individual vacancies.
    for prevacancy in vacancies:
      vacancy: dict = prevacancy["fields"]
      # Add the slug we'll use to link to the vacancy on *our* job board.

      # Generate first half of slug based on job title
      job_title_slug: str = vacancy['!Title'][0:40]
      job_title_slug = job_title_slug.strip()
      job_title_slug = job_title_slug.lower()
      job_title_slug = re.sub('/[^a-z0-9\-]/', '-', job_title_slug)
      job_title_slug = job_title_slug.replace('---', '-')
      job_title_slug = job_title_slug.replace('--', '-')
      job_title_slug = re.sub('/-/', '', job_title_slug)

      # Slug will look something like this:
      #   strategic-policy-researcher___rec1A8kYUhb0mcIi7
      slug = job_title_slug + '___' + prevacancy['id']
      vacancy['slug'] = slug

      # Rename some fields
      vacancy["Job title"] = vacancy.pop('!Title')

      vacancy['Closing date'] = vacancy.pop('!Date it closes', None)

      vacancy['Link'] = vacancy.pop('!Vacancy page', "" )

      vacancy['Role type'] = vacancy.pop('!Role type', None )

      vacancy['Hiring organisation ID'] = vacancy.pop('!Org', None )

      vacancy['Date listed'] = vacancy.pop('!Date published', None )

      vacancy['Degree requirements'] = vacancy.pop('!Required degree', None )

      vacancy['Job description'] = vacancy.pop('!Description' "")

      vacancy['Location'] = vacancy.pop('!Location', [] )


      vacancy['is_recommended_org'] = vacancy.pop('!is_recommended_org', False)

      vacancy['ea_forum_link'] = vacancy.pop('!ea_forum_link', "")

      vacancy['MinimumExperienceLevel'] = vacancy.pop('!MinimumExperienceLevel', None)

      vacancy['Salary (display)'] = vacancy.pop('!Salary (display)', None)

      vacancy['Region'] = vacancy.pop('!Region', "")

      vacancy['Problem area (tags)'] = vacancy.pop('!Problem area (tags)', [])

      vacancy['Featured'] = vacancy.pop('!Featured', False)


      # Convert the Featured field to a boolean value instead of an empty string or an array.
      if type(vacancy['Featured']) == list and vacancy['Featured'][0] == 'Yes':
        vacancy['Featured'] = True
      else:
        vacancy['Featured'] = False
      

        #   # "Job description" field is required, even if blank.
        #   if(!isset(vacancy['fields']['Job description'])):
        #     vacancy['fields']['Job description'] = ''
        

        # Get the human-friendly "time ago" string, so we don't have to
        # generate this client side.
        #   date_listed_human_friendly = get_human_friendly_time_ago(strtotime(vacancy['fields']['Date listed']))


        #   # If vacancy was posted just minutes or hours ago, we should say
        #   # "Posted today" instead of showing more accurate info. The reason is
        #   # that we want to cache this API response for up to 24 hours.
        #   if(strpos(date_listed_human_friendly, 'minute') !== false || strpos(date_listed_human_friendly, 'hour') !== false):
        #     date_listed_human_friendly = 'today'
        

        #   vacancy['fields']['Date listed human friendly'] = date_listed_human_friendly

        #   vacancy['Date listed'] = date('Y/m/d H:i', strtotime(vacancy['Date listed']))

      # Add hiring org information to orgs_with_vacancies list.
      hiring_org_name = vacancy['Hiring organisation ID']
      vacancy['Hiring organisation ID'] = hiring_org_name

        # hmm?
        #   orgs_with_vacancies[hiring_org_name] = org_name_to_org_info_map[hiring_org_name]


      # Avoid doing the computation to add tracking params client side.
      # I _think_ this works out ok: GZIP compresison means that the impact
      # on API payload size of adding this property should be less than 5KB.
      vacancy['Link UTM'] = get_link_with_tracking_params(vacancy['Link'])

      vacancy['Role types'] = vacancy['Role type']

      # Response must include three "Role type" fields, even if blank.
      vacancy['Role type 2'] = ''
      vacancy['Role type 3'] = ''

      if not vacancy['Role type']:
        vacancy['Role type'] = []
    #   else:
    #     role_types = vacancy['Role type']
    #     vacancy = convert_array_field_to_string_fields(vacancy, 'Role type', role_types)
      

      # Get "Problem area main" and "Problem area others" record IDs into a single array.
      problem_area_key = "!Problem area (filters)" # transitional

      problem_area_ids = []
      if problem_area_key in vacancy:
        # temporary accommodation of duplicate airtable column type being string instead of array.
        ids = vacancy[problem_area_key]
        if (type(ids) == list):
          problem_area_ids = ids
        else:
          print("PROBLEM AREA TODO")
        
      

      # if(!empty(vacancy['fields']['!Problem area (others)'])):
      #   problem_area_ids = array_merge(problem_area_ids, vacancy['fields']['!Problem area (others)'])
      # 

      # Get problem area names from record IDs
      problem_area_names = []
      for id in problem_area_ids:
        # temporary accommodation of duplicate airtable column type being string instead of array.
        if (type(vacancy[problem_area_key]) == list):
          print(problem_area_key, vacancy[problem_area_key], id, problem_area_id_to_name_map.get(id))
          problem_area_names.append(problem_area_id_to_name_map[id])
        else:
          problem_area_names.append(id)
        
      

      # Add array of problem areas to the vacancy fields
      vacancy['Problem areas'] = problem_area_names

      # Remove the original fields
      vacancy.pop(problem_area_key, None)
      # unset(vacancy['fields']['!Problem area (others)'])

      # Get rationale names from record IDs
      rationale_ids = []
      if vacancy['Problem area (tags)']:
        rationale_ids = vacancy['Problem area (tags)']
      

      rationale_names = []

      # temporary accommodation of duplicate airtable column type being string instead of array.
      if type(rationale_ids)== list:
        for id in rationale_ids:
          rationale_names.append(rationale_id_to_name_map[id])
        
    #   else:
    #     rationale_names = array_map(function (id) {
    #       return preg_replace('/\d+. /','',id)
    #     }, explode(", ", rationale_ids))
      

      vacancy['Problem area (tags)'] = rationale_names


      # # Response must include Vacancy CTA field, even if blank in Airtable.
      # if(empty(vacancy['fields']['Vacancy CTA'])):
      #   vacancy['fields']['Vacancy CTA'] = null
      # 

      # Format the location information for display in vacancy lists
      # and the job board filters.
      #
      # We don't want to do this formatting on the client side.
      vacancy['Locations'] = []
      cities_and_countries = []
      countries = []

      # Transform location fields...
      location_ids = vacancy['Location']
      for idx, id in enumerate(location_ids):
        print(idx)
        # Get location name
        location_name: str = location_id_to_name_map[id]

        # Split and transform
        location_parts = location_name.split(".")
        location_city = location_parts[0]
        location_country = location_parts[1]

        # @TODO 2021-02-09: I guess we can remove these fields once we've
        # removed references to them from job-board.js.
        # Could also remove the "Location" field which only contains Airtable
        # IDs.
        # @TODO -- start block to delete

        # Must always include these fields
        vacancy['Additional Location: City'] = ''
        vacancy['Additional Location: Country'] = ''

        if idx == 0:
          vacancy['Location: City'] = location_city
          vacancy['Location: Country'] = location_country
        elif idx == 1:
          vacancy['Additional Location: City'] = location_city
          vacancy['Additional Location: Country'] = location_country
        # else:
          # We do not support more than 2 locations per vacancy at the moment.
        

        city_and_country = ''
        city_lowercase = location_city.lower()
        country_lowercase = location_country.lower()

        if city_lowercase == 'various countries' and country_lowercase == 'various countries':
          city_and_country = location_city
        elif city_lowercase != 'remote':
          city_and_country = location_city

          if country_lowercase != 'usa':
            city_and_country = city_and_country + ', ' + location_country
          
        elif city_lowercase == 'remote' and country_lowercase != 'remote':
          city_and_country = location_city + ', ' + location_country
        else:
          city_and_country = location_country
        

        city_and_country = city_and_country.split()
        cities_and_countries.append(city_and_country)

        if location_country:
          countries.append(location_country)
        

      

      vacancy['Locations'] = {
        'citiesAndCountries': cities_and_countries,
          'countries': countries,
      }

      # Now that we've extracted the locations, remove the "Location" field
      # which only contains Airtable IDs, and isn't needed by job-board.js
      # in the front end.
      vacancy.pop('Location')

      # Flatten the vacancy data - for parity with SheetDB, we don't want
      # all the field data nested in the "fields" array. The transform
      # looks like this:
      #   vacancy['fields']['xxx'] => vacancy['xxx']
      transformed_vacancies.append(vacancy)

def transform_organisations_data(
    organisations: List[Dict], top_orgs_problem_areas: Dict, all_potential_tags: Dict, location_id_to_name_map: Dict, region_id_to_name_map: Dict
):
    transformed_orgs = []

    for preorg in organisations:
        org: Dict = preorg["fields"]
        # Rename some fields
        org["Name"] = org.pop("!Org")
        org["Domain"] = org.pop("!Home page", "")
        org["Career Page"] = org.pop("!Vacancies page", "")
        org["Company Description"] = org.pop("!Description", "")
        org["Company Logo"] = org.pop("!Logo", "")
        org["text_hover"] = org.pop("!Text_hover", "")
        org["problem_areas"] = org.pop("!Problem area (orgs)", [])
        org["locations"] = org.pop("!Locations (orgs)", [])
        org["internal_links"] = org.pop("!Internal links", "")
        org["external_links"] = org.pop("!External links", "")
        org["org_size"] = org.pop("!Org size", 0)
        org["founded_year"] = org.pop("!Founded year", 0)
        org["glassdoor_link"] = org.pop("!Glassdoor link", "")
        org["social_media_links"] = org.pop("!Social media links", "")
        org["region"] = org.pop("!Region (orgs)", "")
        org["recommended_org"] = org.pop("!Recommended org (star)", False)
        org["forum_link"] = org.pop("!EA Forum link", "")
        org["single_line_description"] = org.pop("!Single line description", "")
        org["tags"] = org.pop("!Tags (orgs)", [])

        # Transform some fields

        # Get problem area names from record IDs
        problem_area_names = []

        # account for null field in problem areas
        if type(org["problem_areas"]) == list:
            problem_area_ids = org["problem_areas"]
            for problem_area_id in problem_area_ids:
                problem_area_names.append(top_orgs_problem_areas[problem_area_id])

        org["problem_areas"] = problem_area_names

        # Get tag names from record IDs
        tag_names = []

        # account for null field in tags
        if type(org["tags"]) == list:
            tag_ids = org["tags"]
            for tag_id in tag_ids:
                tag_names.append(all_potential_tags[tag_id]["name"])
        org["tags"] = tag_names

        # Get location names from record IDs
        location_names = []
        if type(org["locations"]) == list:
            location_ids = org["locations"]
            for location_id in location_ids:
                location_names.append(location_id_to_name_map[location_id])
        org["locations"] = location_names

        # Get region names from record IDs
        region_names = []
        if type(org["region"]) == list:
            region_ids = org["region"]
            for region_id in region_ids:
                region_names.append(region_id_to_name_map.get(region_id))
        org["region"] = region_names

        # "Domain", "Career Page" and "Company Logo" fields can contain:
        # (1) [null] -- array with single element with value null
        # (2) ["string"] -- array with single element of type string
        # (3) "" -- empty string

        # If (1) then implode, and get ""
        # If (2) then implode and get "string"
        # If (3) don't need to transform

        # Transform "Domain" field values from array to string
        if type(org["Domain"]) == list:
            org["Domain"] = org["Domain"].join(", ")

        # Transform "Career Page" field values from array to string
        if type(org["Career Page"]) == list:
            org["Career Page"] = org["Career Page"].join(", ")
            

        if not org["Domain"]:
            # If domain is missing http prefix, add it.
            if "http" not in org["Domain"]:
                org["Domain"] = "https:#" + org["Domain"]

            # Add UTM params to homepage link
            org["Domain"] = get_link_with_tracking_params(
                org["Domain"]
            )

        if not org["Career Page"]:
            # If career page is missing http prefix, add it.
            if "http" not in org["Career Page"]:
                org["Career Page"] = "https:#" + org["Career Page"]

            # Add UTM params to career page link
            org["Career Page"] = get_link_with_tracking_params(
                org["Career Page"]
            )

        # Transform "Company Logo" field values from array to string
        if type(org["Company Logo"]) == list:
            org["Company Logo"] = org["Company Logo"].join(", ")

        # Transform "Company Description" field values from array to string
        # Haven't seen any values for this field being served as an array,
        # but since I (RD) don't really understand why sometimes get arrays back
        # from airtable so transforming it just in case.
        if type(org["Company Logo"])==list:
            org["Company Logo"] = org["Company Logo"].join(", ")

        # 2021-09: Rewrite company logo image url since we no longer use WP Engine's CDN at
        # cdn.80000hours.org, and now just use Cloudflare as a CDN for our images at
        # 80000hours.org
        org["Company Logo"] = org["Company Logo"].replace(
            "https:#cdn.80000hours.org",
            "https:#80000hours.org",
        )

        # Should use thumbnail version of company logo if it exists
        if not org["Company Logo"]:
            if "-150x150" not in org["Company Logo"]:

                # /*
                #   Usually WordPress does not generate a thumbnail if the uploaded
                #   image is already 160x160 or smaller. We have changed the default
                #   behaviour so that thumbnails are always generated.

                #   See lib/wp-admin.php in the WordPress repository.
                # */
                thumbnail_url = org["Company Logo"].replace(".jpg", "-160x160.jpg")
                thumbnail_url = thumbnail_url.replace(".jpeg", "-160x160.jpeg")
                thumbnail_url = thumbnail_url.replace(".png", "-160x160.png")
                thumbnail_url = thumbnail_url.replace(".gif", "-160x160.gif")

                org["Company Logo"] = thumbnail_url

        # simple typecast
        org["recommended_org"] = bool(
            org["recommended_org"]
        )
        
        transformed_orgs.append(org)

    return transformed_orgs


def get_airtable_data(table_name, params: dict):
    table = Table(settings.AIRTABLE["API_KEY"], settings.AIRTABLE["BASE_ID"], table_name)
    data = table.all(
        fields=params["fields"],
        formula=params.get("filterByFormula") or "",
        sort=params.get("sort") or [],
        max_records=params.get("max_records"),
    )
    return data
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

  url = url_parts['scheme'] + ':#' + url_parts['host'] + url_parts['path'] + '?' + url_parts['query']

  if url_parts['fragment']:
    url = url + '#' + url_parts['fragment']

  return url

def http_build_query(data):
    built = data
    print('todo')
    return built


# def convert_array_field_to_string_fields(vacancy: Dict, field_label: str, field_array: List):
#     for i, key in enumerate(field_array):

#       new_field_label = field_label

#       if i > 0:
#         new_field_label = field_label + ' ' + (i + 1)

#       vacancy[new_field_label] = field_array[key]

#     return vacancy