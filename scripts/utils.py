import json
import os
import pandas as pd


def build_hierarchy(path):
  #
  # transform [
  #   "Computers & Electronics",
  #   "Software",
  #   "Computer Utilities",
  #   "Database Software"
  # ]
  # into [
  #   "Computers & Electronics",
  #   "Computers & Electronics|Software",
  #   "Computers & Electronics|Software|Computer Utilities",
  #   "Computers & Electronics|Software|Computer Utilities|Database Software"
  # ]

  h = []
  cur = []
  for p in path:
    p = p.strip()
    if p:
      a = [*cur, p]
      h.append('|'.join(a))
      cur.append(p)

  return h


def json_dump(data, file_name, indent=2, sort_keys=False):
  with open(file_name, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=indent, sort_keys=sort_keys, check_circular=False)


def json_load(file_name):
  data = {}
  try:
    with open(file_name, 'r', encoding='utf-8') as f:
      data = json.load(f)
  except:
    pass
  return data


def unique_list(list):
  # using list(set(list)) will return the list in random order
  _set = set()
  _list = filter(lambda x: x, list)  # remove empty values
  unique_list = [x for x in _list if x not in _set and (_set.add(x) or True)]
  return unique_list


def get_categories():
  excel_file_path = os.path.join('..', '..', 'Brand Detail.xlsx')
  df = pd.read_excel(excel_file_path, sheet_name='Engineering Tax - Fields', na_filter=False)

  categories = df.to_dict(orient='records')
  ALL_CATEGORIES = []

  level1 = ''
  level2 = ''
  level3 = ''
  for row in categories:
    if row['Category level 1']:
      # new category, reset
      level1 = ''
      level2 = ''
      level3 = ''

    level1 = (row['Category level 1'] or level1).strip()
    level2 = (row['Category level 2'] or level2).strip()
    level3 = (row['Category level 3'] or level3).strip()

    row['Category level 1'] = level1
    row['Category level 2'] = level2
    row['Category level 3'] = level3

    ALL_CATEGORIES.append(','.join([level1, level2, level3]))

  return unique_list(ALL_CATEGORIES)
