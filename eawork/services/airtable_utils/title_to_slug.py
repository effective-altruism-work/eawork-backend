import re

def title_to_slug(title: str, id)-> str:
      pre_slug: str = title[0:40]
      pre_slug = pre_slug.strip()
      pre_slug = pre_slug.lower()
      pre_slug = re.sub('[^a-z0-9\-]', '-', pre_slug)
      pre_slug = pre_slug.replace('---', '-')
      pre_slug = pre_slug.replace('--', '-')
      pre_slug = re.sub('\-$', '', pre_slug)

      # Slug will look something like this:
      #   strategic-policy-researcher___rec1A8kYUhb0mcIi7
      slug = pre_slug + '___' + id

      return slug
