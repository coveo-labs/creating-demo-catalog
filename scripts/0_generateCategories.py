from pathlib import Path
import pandas as pd

excel_file_path = Path('../Barca - Brand Detail.xlsx')
df = pd.read_excel(excel_file_path, sheet_name='Barca Sports Taxonomy', na_filter=False)

#
# Set up categories from Excel file
#
categories = df.to_dict(orient='records')


def createCategoryFolderForImages(parts):
  cur_path = Path('../images')
  for p in parts:
    if p:
      cur_path = cur_path / p.replace('/', '_')
      if not cur_path.exists():
        print(cur_path)
        cur_path.mkdir()


print(categories)

level1 = ''
level2 = ''
level3 = ''
for row in categories:
  if row['Category Level 1']:
    level1 = ''
    level2 = ''
    level3 = ''

  level1 = (row['Category Level 1'] or level1).strip()
  level2 = (row['Category Level 2'] or level2).strip()
  level3 = (row['Category Level 3'] or '').strip()

  # print(level1, ',', level2)
  row['Category Level 1'] = level1
  row['Category Level 2'] = level2
  row['Category Level 3'] = level3

  createCategoryFolderForImages([level1, level2, level3])

categories_csv_file = Path('../outputs/categories.csv')
pd.DataFrame(data=categories).to_csv(categories_csv_file, index=False)
