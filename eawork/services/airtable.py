from typing import TypedDict, List, Dict
from typing import TypedDict
from pyairtable import Table
from django.conf import settings
from urllib.parse import urlencode, quote_plus
import time
import re
from eawork.services.airtable_utils.title_to_slug import title_to_slug

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

    # get related records that we'll use in vacancies, orgs, and rationales
    dropdown = get_dropdown_data()
    locations = get_locations_data()

    raw_vacancies = get_raw_vacancy_data()
    vacancies = transform_vacancies_data(raw_vacancies, dropdown["problem_areas"] | dropdown["problem_areas_filters"], locations) # `|` does dictionary merge

    raw_organisations = get_raw_organisation_data()
    organisations = transform_organisations_data(
        raw_organisations, 
        dropdown["top_org_problem_areas"], 
        dropdown["problem_areas_tags"] | dropdown["problem_areas"] | dropdown["rationales"] | dropdown["top_org_problem_areas"], # `|` does dictionary merge
        locations, 
        dropdown["location_filters"])

    res = {
        "meta": {"retrieved_at": round(time.time() * 1000)},
        "data": {
            "status": 1, 
            "vacancies": vacancies, 
            "organisations": organisations, 
            "rationales": dropdown["rationales"] | dropdown["problem_areas"] | dropdown["problem_areas_filters"]
        },
    }

    # with open("output.txt", 'w') as writer:
    #     writer.write(json.dumps(res, indent=4))

    return res


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

  # separate all the data we got in get_raw_dropdown_data into their own maps.
  for record in raw_data:
    properties = {"name": record["fields"].get("!Name for front end", "").strip(), "link": record["fields"].get("!Link for tag", "")}
    key = ""
    match record['fields']["!Category"]:
      case "!Problem area":
        key = 'problem_areas'
      case '!Problem area (tags)':
        key = 'problem_areas_tags'
      case '!Problem areas (filters)':
        key = 'problem_areas_filters'
      case '!Rationale':
        key='rationales'
      case '!Location filters (orgs tab)':
        key='location_filters'
      case '!Top orgs (problem area)':
        key='top_org_problem_areas'
      
    map[key][record["id"]] = properties
  return map

# these categories are used across vacancies, orgs, and rationales. We call all of them here to reduce the amount of calls to Airtable.
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
    params: Param = {
        "fields": [
            "!Name for front end",
            "!Link for tag",  # maybe only some?
            "!Category",  # crucial! We're pulling lots of different kinds of data, and we are going to need to separate them
        ],
        "filterByFormula": formula,
        "max_records": 1000,
    }

    dropdown_data = get_airtable_data(table_name, params)

    return dropdown_data


def get_locations_data():
    table_name = '!Locations'
    params: Param = {
      'fields':['!Location',
      ],
      'max_records': 1000,
      'pageSize': 100
    }

    locations = get_airtable_data(table_name, params)

    if (type(locations) != list): 
      return {}
    location_id_to_name_map = {}
    for location in locations:
      location_id_to_name_map[location['id']] = location['fields']['!Location']

    return location_id_to_name_map

def get_raw_vacancy_data():
    table_name = "!Vacancies"

    # note that airtable has a weird thing where 21 seems to be a hard limit for number of fields requested.
    fields = [
        "!Title",
        "!Org",
        "!Date it closes",
        "!Date published",
        "!Problem area (filters)",
        "!Description",
        "!Vacancy page",
        "!Role type",
        "!Required degree",
        "!Location",
        "!is_recommended_org",
        "!ea_forum_link",
        "!MinimumExperienceLevel",
        "!Salary (display)",
        "!Region",
        "!Problem area (tags)",
        "!Featured",
        "!Visa sponsorship",
        "!Evergreen"
    ]

    filter = "AND( {!Publication (is it live?)} = '!yes', IS_AFTER({!Date it closes}, DATEADD(TODAY(),-1,'days')), IS_BEFORE({!Date published}, NOW()) )"

    params: Param = {
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
            "!Additional commentary"
        ],
    )

    params = {"fields": fields, "max_records": 10000}

    organisations = get_airtable_data(table_name, params)

    return organisations


def transform_vacancies_data(vacancies: List[Dict], problem_area_id_to_name_map: Dict, location_id_to_name_map: Dict):
    transformed_vacancies = []
     # Go through transforming individual vacancies.
    for vacancy_container in vacancies:
      vacancy: dict = vacancy_container["fields"]
      vacancy['id'] = vacancy_container['id']
      vacancy['createdTime'] = vacancy_container['createdTime']
      vacancy['slug'] = title_to_slug(vacancy['!Title'], vacancy['id'])

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
      vacancy['visa'] = vacancy.pop('!Visa sponsorship', False)
      vacancy['evergreen'] = vacancy.pop('!Evergreen', False)


      # Convert the Featured field to a boolean value instead of an empty string or an array.
      if type(vacancy['Featured']) == list and vacancy['Featured'][0] == 'Yes':
        vacancy['Featured'] = True
      else:
        vacancy['Featured'] = False
      
      if type(vacancy['Problem area (tags)']) == str:
        vacancy['Problem area (tags)'] = vacancy['Problem area (tags)'].split(", ")
    

      vacancy['Role types'] = vacancy.pop('Role type', '')

      # Response must include three "Role type" fields, even if blank.
      vacancy['Role type 2'] = ''
      vacancy['Role type 3'] = ''

      # Get problem areas from record IDs

      problem_area_key = "!Problem area (filters)" 
      problem_area_ids = []
      if problem_area_key in vacancy:
        # temporary accommodation of duplicate airtable column type being string instead of array.
        ids = vacancy[problem_area_key]
        if (type(ids) == list):
          problem_area_ids = ids
      
      problem_area_names = []
      for id in problem_area_ids:
        # temporary accommodation of duplicate airtable column type being string instead of array.
        if (type(vacancy[problem_area_key]) == list):
          problem_area_names.append(problem_area_id_to_name_map[id]["name"])
        else:
          problem_area_names.append(id)
        
      
      # Add array of problem areas to the vacancy fields
      vacancy['Problem areas'] = problem_area_names

      # Remove the original fields
      vacancy.pop(problem_area_key, None)

      # Locations!
      cities_and_countries = []
      countries = []

      # Transform location fields...
      location_ids = vacancy['Location']
      for idx, id in enumerate(location_ids):
        # Get location name
        location_name: str = location_id_to_name_map[id]

        # Split and transform
        location_parts = location_name.split(".")
        location_city = location_parts[0]
        location_country = location_parts[1]

        # Must always include these fields (???)
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
        

        cities_and_countries.append(city_and_country)

        if location_country:
          countries.append(location_country)
        
      vacancy['Locations'] = {
        'citiesAndCountries': cities_and_countries,
          'countries': countries,
      }

      # Now that we've extracted the locations, remove the "Location" field
      # which only contains Airtable IDs, and isn't needed anymore
      vacancy.pop('Location')

      transformed_vacancies.append(vacancy)
    
    return transformed_vacancies

def transform_organisations_data(
    organisations: List[Dict], top_orgs_problem_areas: Dict, all_potential_tags: Dict, location_id_to_name_map: Dict, region_id_to_name_map: Dict
):
    transformed_orgs = {}

    for org_container in organisations:
        org: Dict = org_container["fields"]
        # Rename  fields
        org["name"] = org.pop("!Org")
        org["homepage"] = org.pop("!Home page", "")
        org["career_page"] = org.pop("!Vacancies page", "")
        org["description"] = org.pop("!Description", "")
        org["logo"] = org.pop("!Logo", "")
        org["text_hover"] = org.pop("!Text_hover", "")
        org["problem_areas"] = org.pop("!Problem area (orgs)", [])
        org["locations"] = org.pop("!Locations (orgs)", [])
        org["internal_links"] = org.pop("!Internal links", "")
        org["external_links"] = org.pop("!External links", "")
        org["org_size"] = org.pop("!Org size", "")
        org["founded_year"] = org.pop("!Founded year", "")
        org["glassdoor_link"] = org.pop("!Glassdoor link", "")
        org["social_media_links"] = org.pop("!Social media links", "")
        org["region"] = org.pop("!Region (orgs)", "")
        org["recommended_org"] = org.pop("!Recommended org (star)", False)
        org["forum_link"] = org.pop("!EA Forum link", "")
        org["single_line_description"] = org.pop("!Single line description", "")
        org["tags"] = org.pop("!Tags (orgs)", [])
        org["additional_commentary"] = org.pop("!Additional commentary", '')

        # Transform fields

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
                region_dict = region_id_to_name_map.get(region_id)
                if region_dict:
                  region_names.append(region_dict.get("name"))
        org["region"] = region_names

        # "Domain", "Career Page" and "Company Logo" fields can contain:
        # (1) [null] -- array with single element with value null
        # (2) ["string"] -- array with single element of type string
        # (3) "" -- empty string

        # If (1) then implode, and get ""
        # If (2) then implode and get "string"
        # If (3) don't need to transform

        # Transform "Domain" field values from array to string
        if type(org["homepage"]) == list:
            org["homepage"] = org["homepage"].join(", ")

        # Transform "Career Page" field values from array to string
        if type(org["career_page"]) == list:
            org["career_page"] = org["career_page"].join(", ")
            

            # If domain is missing http prefix, add it.
        if "http" not in org["homepage"]:
            org["homepage"] = "https://" + org["homepage"]

            # Add UTM params to homepage link
        org["homepage"] = append_url_params(
                org["homepage"]
        )

            # If career page is missing http prefix, add it.
        if "http" not in org["career_page"]:
            org["career_page"] = "https://" + org["career_page"]

            # Add UTM params to career page link
        org["career_page"] = append_url_params(
            org["career_page"]
        )

        # Transform "Company Logo" field values from array to string
        if type(org["logo"]) == list:
            org["logo"] = org["logo"].join(", ")

     
        if type(org["logo"])==list:
            org["logo"] = org["logo"].join(", ")

     
        org["logo"] = org["logo"].replace(
            "https:#cdn.80000hours.org",
            "https:#80000hours.org",
        )

        # Should use thumbnail version of company logo if it exists
        if "-150x150" not in org["logo"]:
            thumbnail_url = org["logo"].replace(".jpg", "-160x160.jpg")
            thumbnail_url = thumbnail_url.replace(".jpeg", "-160x160.jpeg")
            thumbnail_url = thumbnail_url.replace(".png", "-160x160.png")
            thumbnail_url = thumbnail_url.replace(".gif", "-160x160.gif")

            org["logo"] = thumbnail_url

        # simple typecast
        org["recommended_org"] = bool(
            org["recommended_org"]
        )
        
        transformed_orgs[org["name"]] = org

    return transformed_orgs



class Param(TypedDict):
  fields: List[str]
  filterByFormula: str
  max_records: int
  sort: List[str]

def get_airtable_data(table_name: str, params: Param) -> List[dict]:
    table = Table(settings.AIRTABLE["API_KEY"], settings.AIRTABLE["BASE_ID"], table_name)
    data = table.all(
        fields=params["fields"],
        formula=params.get("filterByFormula", ""),
        sort=params.get("sort", []),
        max_records=params.get("max_records", 1000),
    )
    return data
   
def append_url_params(url: str):
    # Should not add tracking params if domain is 80000hours.org, or these other sites that get broken by tracking params
    domains_to_exclude = [
      '80000hours.org',
      'jobs.cam.ac.uk',
      'my.corehr.com'
    ]

    domain_match = False
    for domain in domains_to_exclude:

      if url.replace(domain, '') != url:
        domain_match = True
        break

    if not domain_match:
      params = {
        'utm_campaign': '80000 Hours Job Board',
        'utm_source': '80000 Hours Job Board',
      }

      querystring = urlencode(params, quote_via=quote_plus)
      if ("?" in url):
        return url + "&" + querystring
      else:
        return url + "?" + querystring

    return url

