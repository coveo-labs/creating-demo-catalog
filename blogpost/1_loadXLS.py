import pandas as pd
from pathlib import Path
import itertools

df = pd.read_excel(Path('..', 'Barca - Brand Detail.xlsx'), sheet_name='Barca Sports Taxonomy', na_filter=False)

def readCSV():
  global ALL_PARTS
  ALL_PARTS = df.to_dict(orient='records')
  level1 = ''
  level2 = ''
  level3 = ''
  dalle = ''
  id = ''
  # Fix the parts, because level1, level2, level3 might not be there
  for part in ALL_PARTS:
    # print (part)
    # part['DallE name'] = part['Category Level 1']
    if part['DallE name'] == '':
      part['DallE name'] = dalle
    else:
      dalle = part['DallE name'].strip()
    if part['ID']:
      id = float(part['ID'])
    part['ID'] = id
    part['Category Level 1'] = part['Category Level 1']
    if part['Category Level 1'] == '':
      part['Category Level 1'] = level1
    else:
      level1 = part['Category Level 1'].strip()
    if part['Category Level 2'] == '':
      part['Category Level 2'] = level2
    else:
      if level2 != part['Category Level 2'].strip():
        level3 = ''
      level2 = part['Category Level 2'].strip()
    if part['Category Level 3'] == '':
      part['Category Level 3'] = level3
    else:
      level3 = part['Category Level 3'].strip()
    # clean field 'Power (EcPowerOutput)'
    field = part['Fields'].strip()
    # #regex = r"(.* \()"
    # result = re.sub(regex, "", field, 0, re.MULTILINE).replace(")","")
    # #print (result)
    # if (result.startswith('Ec') and not result.startswith('Ec_')):
    #    result = result.replace("Ec","Ec_")
    part['Fields'] = field  # .lower()

    if field == 'ec_Price':
      part['Values'] = float(part['Values'])


def cleanUp(text):
  text = text.replace('<|endoftext|>', '')
  text = text.replace('\n', '').replace('* * *', '').strip()
  return text


def removeUnfinishedSentence(text):
  # text bla. bla bla --> remove the last part
  if (not text.endswith('.')):
    if ('.' in text):
      text = '.'.join(text.split('.')[:-1])

  return text


def executeOpenAI(prompt, temp, length, stop=[]):
  if len(stop) == 0:
    stop = None
  results = openai.Completion.create(
      engine=P_ENGINE,
      prompt=prompt,
      temperature=temp,
      max_tokens=length,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stop=stop
  )
  return results["choices"][0]["text"].strip(' \n').replace('\n', '<BR>')


def executeOpenAIv2(prompt, temp, length, mayfail, stop=[]):
  try:
    if len(stop) == 0:
      stop = None
    results = openai.Completion.create(
        engine=P_ENGINE,
        prompt=prompt,
        temperature=temp,
        max_tokens=length,
        top_p=1,
        frequency_penalty=0.4,
        presence_penalty=0.7,
        stop=stop
    )
    return results["choices"][0]["text"].strip(' \n').replace('\n', '<BR>')
  except:
    if mayfail:
      # saveLibs()
      time.sleep(60)
      return executeOpenAIv2(prompt, temp, length, False, stop=[])


def saveLibs():
  print("Saving names/descr")
  if (len(DESC_MAP) > 5):
    utils.json_dump(DESC_MAP, Path('..', 'outputs', 'descriptions.json'), sort_keys=True)
  if (len(NAME_MAP) > 5):
    utils.json_dump(NAME_MAP, Path('..', 'outputs', 'names.json'), sort_keys=True)


def createBigPartsList():
  global PARTS
  PARTS = []
  currentPart = {}
  for part in ALL_PARTS:
    # print (part)
    if (part['Fields'] == 'ec_Price'):
      # this is the last record
      currentPart[part['Fields']] = part['Values']
      currentPart['DallE name'] = part['DallE name'].strip()
      currentPart['ID'] = float(part['ID'])
      currentPart['Category Level 1'] = part['Category Level 1'].strip()
      currentPart['Category Level 2'] = part['Category Level 2'].strip()
      currentPart['Category Level 3'] = part['Category Level 3'].strip()
      # currentPart.append(part)
      PARTS.append(json.dumps(currentPart))
      currentPart = {}
    else:
      currentPart[part['Fields']] = part['Values']  # .strip()


# create all the possible values for the record


def createTextv2(product, keyword, boat, version, sentence, temp, length):
  sentence = sentence.replace('[PRODUCT]', product)
  sentence = sentence.replace('[KEYWORD]', keyword)
  sentence = sentence.replace('[BOAT]', boat)
  sentence = sentence.replace('[VERSION]', version)
  counter = 0
  line = ''
  while len(line) == 0 or len(line) > length:
    counter += 1
    if (counter > 10):
      break
    line = executeOpenAIv2(sentence,
                           temp,
                           length,
                           True
                           )

  return line


def getAllValues(record, variant_fields):
  random.seed(record['DallE name'])
  new_record = {}
  # record = addVariants(record, variant_fields)
  keys = record.keys()

  for key in keys:
    if (isinstance(record[key], str) and ';' in record[key]):
        # multiple values
      values = []
      curvalues = record[key].split(';')
      for val in curvalues:
        if (val.strip() != ''):
          values.append((val,))
      new_record[key] = values
      print(new_record[key])
    else:
      if isinstance(record[key], str):
        new_record[key] = (record[key],)
      else:
        new_record[key] = (str(record[key]),)
      print(new_record[key])
  keys = new_record.keys()
  values = (new_record[key] for key in keys)
  # print ("GetAllValues")
  # print (new_record)
  combinations = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
  # clean up the combinations
  records = []
  for combi in combinations:
    rnd = random.randint(0, 50)
    # print(rnd)
    processit = rnd <= 45
    if processit:
      new_record = {}
      for key in combi.keys():
        if isinstance(combi[key], tuple):
          new_record[key] = ''.join(combi[key])
        else:
          new_record[key] = combi[key]
        if (isinstance(new_record[key], str)):
          if (new_record[key].upper() == 'YES'):
            new_record[key] = True
          else:
            if (new_record[key].upper() == 'NO'):
              new_record[key] = False

      records.append(new_record)
  # print (records)
  return records
  # combinations= generate_combinations(new_record)
  # print(combinations)


def removeSpecialFieldsFromKey(metadata):
  # Remove ec_boat, ec_version from the metadata
  meta = copy.deepcopy(metadata)
  # del meta['ec_boat']
  # del meta['ec_version']
  del meta['ec_brand']
  return meta


def createVariantKey(metadata, variant_fields):
  variant_key = ''
  meta = removeSpecialFieldsFromKey(metadata)
  for key in meta.keys():
    if key not in variant_fields:
      variant_key += str(meta[key])
    else:
      # 7variant_key+="1"
      pass

  return variant_key


def doWeHaveVariants(metadata, variant_fields):
  variants = False
  meta = removeSpecialFieldsFromKey(metadata)
  for key in meta.keys():
    if key in variant_fields:
      if (meta[key] != ''):
        variants = True

  return variants


def createGroupKey(metadata, grouping_fields, thename):
  variant_key = thename
  meta = removeSpecialFieldsFromKey(metadata)

  for key in meta.keys():
    if key not in grouping_fields:
      variant_key += str(meta[key])
    else:
      # 7variant_key+="1"
      pass

  return variant_key


def getGroupId(rec, grouping_fields, thename):
  group = False
  groupid = ''
  meta = removeSpecialFieldsFromKey(rec)
  for key in meta.keys():
    if key in grouping_fields:
      if (meta[key] != ''):
        group = True

  if group:
    # Grouping is here
    groupid = createGroupKey(rec, grouping_fields, thename)

  return groupid


def getProductId(rec, thename):
  productid = ''
  meta = removeSpecialFieldsFromKey(rec)
  for key in meta.keys():
    if (meta[key] != ''):
      productid += str(meta[key])
  return productid


def getNextPartRecord():
  global PARTS_POINTER
  global PARTS
  record = json.loads(PARTS[PARTS_POINTER])
  PARTS_POINTER += 1
  if (PARTS_POINTER >= len(PARTS)):
    PARTS_POINTER = 0

  return record


def myround(x, base=5):
  return base * round(x/base)


def getPrice(price, groupid):
  random.seed(groupid)
  min_price = int(price-(price/3))
  round_by = int(price/10)
  max_price = int(price+(price/5))
  # print("Min")
  # print(min_price)
  # print ("Max")
  # print (max_price)
  new_price = myround(random.randint(min_price, max_price), round_by)
  return new_price


def createPrice(record, groupid):
  # update price
  discount = random.randint(0, 10) <= 3
  print(record['ec_Price'])
  try:
    price = int(float(record['ec_Price']))
    price = getPrice(price, groupid)
    record['ec_Price'] = price
    record['ec_promo_price'] = price
    # print (price)
    if discount:
      if (price > 10):
        disc = random.randint(int(price/20), int(price/10))
        # print("Discount: "+str(disc))
        disc = myround(disc, int(price/10))
        # print("Discount: "+str(disc))
        record['ec_promo_price'] = price-disc
      else:
        disc = random.randint(int(price/10), int(price/5))
        # print("Discount: "+str(disc))
        disc = myround(disc, int(price/10))
        # print("Discount: "+str(disc))
        record['ec_promo_price'] = price-disc
  except Exception as e:
    print(e)
    print("Bad price")

  return record

# get the product name


def getProductName(key, sentence, all_names, temp):
  global NAME_MAP
  regex = r"^([\d.)\- ]+)"
  name = createTextv2('', '', '', '', sentence, temp, 70)
  name = name.strip()
  print("Product name: "+name)
  # check if we have newlines or numbers
  names = name.split('<BR>')
  thename = ''
  for name in names:
    name = re.sub(regex, '', name, 0, re.MULTILINE).strip()
    print("One of the names: "+name)

    getNewName = False
    if (len(name) > 70 or len(name) < 5):
      print("Invalid length")
    else:
      # name = name+' '+partname
      if name in all_names:
        print("Already got this one")
      else:
        NAME_MAP[key] = name
        print("New name, use it")
        all_names.append(name)
        thename = name
        break
  print("-------")
  if (thename == ''):
    getNewName = True
  else:
    getNewName = False

  return thename, getNewName, all_names


def getImage(parts):
  global ALL_IMAGES
  global ALL_IMAGES_DIR
  filename = ''
  cur_path = Path('..', 'images')
  for p in parts:
    if p:
      cur_path = cur_path / p.replace('/', '_')

  files = []
  if cur_path in ALL_IMAGES_DIR:
    files = ALL_IMAGES_DIR[cur_path]
  else:
    for file in os.listdir(cur_path):
      files.append(str(cur_path)+'\\'+file)
    ALL_IMAGES_DIR[cur_path] = files

  try:
    print('--getImage::cur_path = ' + str(cur_path))
    print(files)
    for file in files:
      if file in ALL_IMAGES:
        pass
      else:
        filename = file
        ALL_IMAGES.append(filename)
        break
  except Exception as e:
    print('getImage::E = ' + str(e))
    filename = ''

  return filename


def getRating():
  # generate a rating from the digits of the product id.
  n = random.randint(0, 50)
  # make sure it's not too low
  if n < 10:
    n = 50
  return n/10.0

def createReview(description):
  sentence = "Create a positive product feedback for a product with this description: :\n"+description.strip()
  reviewText = createTextv2('', '', '', '', sentence, 0.8, 250)
  reviewText = reviewText.strip().replace(';',' ')
  return reviewText

def createCategoryFolderForImages(parts):
  cur_path = Path('..', 'images')
  for p in parts:
    if p:
      cur_path = cur_path / p.replace('/', '_')
      if not cur_path.exists():
        print(cur_path)
        cur_path.mkdir()


def createCategoriesSlug(categories):
  slug = []
  catpath = ''
  for cat in categories:
    cat = cat.lower().replace('&', '').replace('  ', ' ').replace(' ', '-')
    if catpath == '':
      catpath = cat  # man
      slug.append(catpath)
    else:
      catpath = catpath+'/'+cat
      slug.append(catpath)

  # slug = list(set(catpaths))

  return slug


def createListing(record):
  ec_listing = '/' + record['ec_category'][-1].strip().replace('|', '/')
  ec_listing = ec_listing.replace(' ', '_').replace('&', '_').replace('+', '_')  # make it URL-safe by changing spaces and & to underscores (_)
  ec_listing = re.sub(r'__+', '_', ec_listing)  # remove multiple underscores with only one.

  ec_listing = [ec_listing]

  # # if ec_listing has 2 levels, adds the 2nd level for the menu section to be a workable link
  # parts = ec_listing[0].split('/')
  # if len(parts) > 3:
  #   ec_listing.append('/'.join(parts[0:3]))

  if ec_listing[0] in LISTINGS_PROMO:
    ec_listing.append('/Promotions/Surf_With_Us_This_Year')

  return ec_listing


def checkCategoryOverrides(categories):
  categoryPath = '|'.join(filter(lambda x: x, categories))
  if categoryPath in CATEGORIES_OVERRIDES:
    return CATEGORIES_OVERRIDES[categoryPath].split('|')
  return categories


def createRecord(mainrec, therecord, recid,  variant_fields, groupid, parentid, we_have_variants, all_names, all_fields, productIdKey, variantIdKey):
  # record=[]
  global BASE_DALLE
  global DESC_MAP
  global NAME_MAP
  global KEY_RENAME
  global PRODUCT_IDS_MAP
  global VARIANT_IDS_MAP
  global LISTINGS_PROMO
  global REVIEW_MAP
  doNotAdd = False
  product_text = """Generate names by inventing a new word inspired by the keywords.
Keywords: veterinary schedule
Names:
1. Vetify
2. Vetplanner
3. Animalcal
4. Catgenda
5. Pawsome
Keywords: blue video editor
Names:
1. Scenic Blue
2. Blue Filmagic
3. Blue Playcut
4. Blue Editopia
5. Blue Lenso
Keywords: product roadmap
Names:
1. Visboard
2. Roadahead
3. Prodchart
4. Planned
5. Productracker
Keywords: [KEYS]
Names:
1."""
  record = copy.deepcopy(therecord)

  # WIM: ProductIdKey is the key for PRODUCT_IDS_MAP and VARIANT_IDS_MAP
  #   PRODUCT_IDS_MAP[ProductIdKey]=theidto use

  record['ObjectType'] = 'Product'
  record = createPrice(record, groupid)
  # print(record)
  mainRecord = True
  if parentid == 0:
    # this is a main product
    # product id = groupid+productid
    # First check if we have the productIdKey in PRODUCT_IDS_MAP
    productid = ''
    if (productIdKey in PRODUCT_IDS_MAP):
      productid = PRODUCT_IDS_MAP[productIdKey]
    else:
      # we need to create a new one
      productid = getNewProductKey(PRODUCT_IDS_MAP, groupid)
      PRODUCT_IDS_MAP[productIdKey] = productid
    mainRecord = True
    parentid = productid
    record['ec_productid'] = productid
    record['ec_parent_id'] = parentid
    record['ec_parent'] = parentid

    record['DocumentId'] = 'https://sports.barca.group/pdp/'+str(productid)
    print(record['DocumentId'])
    if 'ec_Sizes' in record:
      record['cat_available_sizes'] = mainrec['ec_Sizes']

    # remove the variant_fields from this record
    for field in variant_fields:
      if field in record:
        del record[field]
    # record['Variation Parent (StockKeepingUnit)'] = ''
    # if we_have_variants:
    #   # pass
    #   record['ObjectType'] = 'Variant'
  else:
    # This means a variant
    mainRecord = False
    # remove the main keys
    for field in record.copy():
      if field not in variant_fields and ('ec_' in field or 'cat_' in field):
        del record[field]
    # First set the parent productid
    record['ec_productid'] = str(parentid)
    # this will not be indexed, but used for reference later on
    record['ec_parent'] = parentid

    productid = ''
    if (productIdKey in VARIANT_IDS_MAP):
      productid = VARIANT_IDS_MAP[productIdKey]
    else:
      # we need to create a new one
      productid = getNewProductKey(VARIANT_IDS_MAP, parentid)
      VARIANT_IDS_MAP[productIdKey] = productid
    # Add the record id to the SKU
    # productid = str(parentid)+'_'+f'{recid:05}'
    # Now set the variant fields
    record['ObjectType'] = 'Variant'
    record['DocumentId'] = 'https://sports.barca.group/pdp/'+str(productid)
    print(record['DocumentId'])
    record['ec_sku'] = productid

    # variantKeys = getVariantKeys(record, variant_fields)
    # record['Variation Parent (StockKeepingUnit)'] = groupid
    # for index, elem in enumerate(variantKeys):
    #   record['Variation Attribute Name '+str(index+1)] = elem['field']
    #   record['Variation Attribute Value '+str(index+1)] = elem['value']

  record['permanentid'] = productid
  thename = ''
  # print(record)
  id = str(int(float(record['ID'])))
  # print (record)
  thename = record['DallE name']
  # fix the [COLOR] to [COLORS]
  thename = thename.replace('[COLOR]', '[COLORS]')
  # replace possible occurences inside thename [COLOR] [TYPE]
  data = ''
  cleanname = thename
  for field in record:
    # fieldname = '['+field.upper()+']'
    if field.lower() not in all_fields:
      all_fields.append(field.lower())
    fieldname = '['+field+']'
    # print (fieldname)
    if fieldname in thename:
      thename = thename.replace(fieldname, record[field])
      cleanname = cleanname.replace(fieldname, record[field])
      id += '_'+record[field]
      # print(thename)
  getNewName = True
  cleanname = cleanname.replace('  ', ' ').replace(',', '')
  name = ''
  if cleanname in NAME_MAP:
    name = NAME_MAP[cleanname]
    print("Product name FROM NAMES: "+name+" ==> Key: "+cleanname)
    getNewName = False
  else:
    if not mainRecord:
      # This only happens with variants, variants may have the same name
      getNewName = False
    if getNewName:
      product_text = product_text.replace('[KEYS]', cleanname)
      name, getNewName, all_names = getProductName(cleanname, product_text, all_names, 0.8)
      print("FIXED Product name, 1: "+name)
      if getNewName:
        print("Second attempt for name")
        name, getNewName, all_names = getProductName(cleanname, product_text, all_names, 1.2)
        if getNewName:
          NAME_MAP[cleanname] = name
          print("FIXED Product name, 2: "+name)
  if name == '':
    name = thename

  record["language"] = "English"
  record['ID'] = id.replace(' ', '_')
  # print (record)
  record['ec_item_group_id'] = groupid
  if 'ec_Colors' in record:
    record['cat_color'] = record['ec_Colors']
  if 'ec_Sizes' in record:
    record['cat_size'] = record['ec_Sizes']
    # record['cat_available_sizes'] = mainrec['ec_Sizes']

  if mainRecord:
    PATH_SEP = '\\'
    record['dalle'] = BASE_DALLE.replace('[TITLE]', thename)

    dir = [record['Category Level 1'], record['Category Level 2']]
    cat3 = record.get('Category Level 3', '').strip()
    if cat3:
      dir.append(cat3)

    record['ec_name'] = name
    # record['ec_name'] = (record['Category Level 2'] + ' ' + record['Category Level 1']).strip() #+ ' from ' + record['ec_brand']).strip()
    dir.append(record['ID'])
    record['dir'] = PATH_SEP.join([p.strip() for p in dir])
    createCategoryFolderForImages(dir)

    categories = checkCategoryOverrides([record['Category Level 1'], record['Category Level 2'], cat3])
    record['ec_category'] = utils.build_hierarchy(categories)

    record['ec_listing'] = createListing(record)

    record['Category'] = record['ec_category'][-1].replace('|', '/')
    record["ec_category_slug"] = ';'.join(createCategoriesSlug(record["Category"].split('/')))
    record["cat_slug"] = createCategoriesSlug(record["Category"].split('/'))
    record['ec_partnumber'] = str(productid).replace('SP', 'B')+' '+str(productid)[-3:]
    record['ec_partnumber_oem'] = str(productid)[-3:]+str(productid).replace('SP', '-')
    record['ec_rating'] = getRating()
    # Using ec_rating as based value for ec_cogs for predictability
    # (using a random() would affects subsequent runs)
    record['ec_cogs'] = round(record['ec_rating'] * 90/5.0) / 100.0
    searchfor = 'a '+thename
    keyd = searchfor
    # key = keyd+'main_'+str(main_record)+'_'+record['ec_brand']  # createVariantKey(record,variant_fields)
    descr = ''
    # name = ''
    # getNewName = False
    # type = ''
    # skip = False
    # if 'prttype' in record:
    #   type = record['prttype']

    # partname = record['Category Level 3']
    # if type:
    #   partname = type

    if keyd in DESC_MAP:
      descr = DESC_MAP[keyd]
    else:
      print("OpenAI: Create a description for product: "+searchfor+".")
      descr = createTextv2('', '', '', '', 'Create a description for product: '+searchfor+".", 0.8, 300)
      print("Product descr: "+descr)
      print("-------")
      DESC_MAP[keyd] = descr
    # if not mainRecord:
    #   name = parent_name
    #   print("Product name FROM PARENT: "+name+" ==> Key: "+key)
    # else:
    #   if key in NAME_MAP:
    #     name = NAME_MAP[key]
    #     print("Product name FROM NAMES: "+name+" ==> Key: "+key)
    #   else:
    #     if name == '':
    #       name = findOtherRecord(keyd, all_names)
    #       print(keyd)
    #       print("Product name FROM using MAIN: "+name+" ==> Key: "+str(main_record))
    #       if not name == '':
    #         all_names.append(name)
    #         skip = True
    #     if skip:
    #       print("Product name FROM NAMES with groupid: "+name)
    #     else:
    #       if name in all_names or name == '':
    #         getNewName = True
    #         print("Already have this name ("+key+") or empty... getting a new one")
    #       else:
    #         getNewName = False
    #         all_names.append(name)
    #   # getNewName=False
    #   if not mainRecord:
    #     # This only happens with variants, variants may have the same name
    #     getNewName = False
    #   if getNewName:
    #     if record['Category Level 3'] == '':
    #       keys = record['Category Level 1']+', '+record['Category Level 2']+', '+record['ec_brand']
    #     else:
    #       keys = record['Category Level 1']+', '+record['Category Level 2']+', '+record['Category Level 3']+', '+record['ec_brand']
    #     if type:
    #       keys = keys + ', '+type
    #     product_text = product_text.replace('[KEYS]', keys)
    #     name, getNewName, all_names = getProductName(key, product_text, all_names, 0.8, partname)
    #     if getNewName:
    #       print("Second attempt for name")
    #       newname = thename.strip()
    #       print(newname)
    #       name, getNewName, all_names = getProductName(key, 'Create a different product name for: '+newname+'.', all_names, 1.0, partname)
    #       if getNewName:
    #         name = newname
    #         NAME_MAP[key] = name
    #         print("FIXED Product name: "+name)
    # if name.count(partname) > 1:
    #   name = name.replace(partname, '').strip()
    #   name += ', '+partname
    #   name = name.replace('. ', ', ')
    # if name == ', '+partname:
    #   name = ''
    # #NAME_MAP[key] = name
    # #NAME_MAP[key] = name
    # # key2 = keyd+'main_'+str(main_record)+'_'+record['ec_brand']#createVariantKey(record,variant_fields)
    # #NAME2_MAP[key2] = name
    # if name == '':
    #   name = thename

    # name = getCleanCsvValue(name)
    # #NAME_MAP[key] = name
    # if not name == '':
    #   record['ec_name'] = name
    # record['ec_name'] = record['ec_name'].replace('<BR>', ' ').strip()
    # PRT_NAME[groupid] = name
    descr = descr.replace('<BR>', ' ')
    # print ("Description:")
    # print (descr)
    # descr = cleanDescr(descr, brands, record['ec_brand'], name)
    # #print (descr)

    # descr = getCleanCsvValue(descr)
    record['ec_description'] = descr
    # # record['ec_brand']=''
    record['title'] = record['ec_name']
    # Create the ec_reviews if not there yet
    review = ''
    if keyd in REVIEW_MAP:
      review = REVIEW_MAP[keyd]
    else:
      review = createReview(descr)
      print("Review for: "+descr)
      print(review)
      REVIEW_MAP[keyd] = review
    record['ec_reviews'] = review.replace('"','')
  # # record['ec_price']=''
  # record['ec_shortdesc'] = descr.split('.')[0] + '.'
  # record['ec_in_stock'] = 'TRUE'
  image = ''
  if mainRecord:
    image = getImage(dir)
    if (image == ''):
      doNotAdd = True
      print("No more images... skipping")
    record['orig_image'] = image.replace('/', '\\')
    image = image.replace('\\', '/').replace('../images/', 'https://s3.amazonaws.com/images.barca.group/Sports/')
    image = urllib.parse.quote(image, safe=':/')
    print("Image: ", image)

    # cat3 = record['Category Level 3']
    # price = record['ec_price']
    # cat = record['Category']

    # record = fixFields(record,not mainRecord)
    # Fields which needs to be at Variant and Product level

    record['ec_images'] = [image]
    # record['ec_images_media'] = record['ec_images']
    # record['ec_images_media_listing'] = record['ec_images']
    # record['ec_images_media_alt_text'] = cat3
    # record['ec_images_thumb'] = record['ec_images']
    # record['ec_price'] = price
    # record['Category'] = cat
    # record['ObjectType'] = 'Product'
    record['ec_in_stock'] = 'TRUE'
    # add all metadata into the data property
    record['FileExtension'] = 'html'
    data = f"""<html>
<head>
<style>
  dl {{ display: grid; grid-template-columns: max-content auto; }}
  dt {{ grid-column-start: 1; }}
  dd {{ grid-column-start: 2; }}
</style>
</head>
<body>
  <h1>{record['title']}</h1>
  <code>{record['permanentid']}</code>
  <div>{record['ec_description']}</div>
  <div><img src="{image}" width="300" height="300" /></div>
  <dl>
    <dt>permanentid</dt><dd>{record['permanentid']}</dd>
    <dt>ec_item_group_id</dt><dd>{record['ec_item_group_id']}</dd>
    <dt>ec_productid</dt><dd>{record['ec_productid']}</dd>

    <dt>ec_price</dt><dd>{record['ec_Price']}</dd>
    <dt>ec_promo_price</dt><dd>{record['ec_promo_price']}</dd>

    <dt>ec_brand</dt><dd>{record['ec_brand']}</dd>
    <dt>ec_colors</dt><dd>{record.get('ec_Colors','')}</dd>

    <dt>ec_rating</dt><dd>{record['ec_rating']}</dd>
    <dt>ec_cogs</dt><dd>{record['ec_cogs']}</dd>
  </dl>
  <dl>
    <dt>ec_category</dt><dd>{record['ec_category']}</dd>
    <dt>ec_listing</dt><dd>{record['ec_listing']}</dd>
    <dt>cat_slug</dt><dd>{record['cat_slug']}</dd>
  </dl>
</body>
</html>"""
    record['data'] = data
  # if 'Category Level 1' in record:
  #   del record['Category Level 1']

  # if 'Category Level 2' in record:
  #   del record['Category Level 2']

  # if 'Category Level 3' in record:
  #   del record['Category Level 3']

  # if 'wifi' in (name + ' ' + descr).lower():
  #   record['eng_wifi'] = True

  # rename_part = {}
  # sfid = getIdFromSFDC(productid)
  # if not sfid == '':
  #   rename_part = addFields(record, not mainRecord)
  #   rename_part['Id'] = sfid
  #   rename_part['Name'] = name
  #   rename_part['Description'] = descr
  #   rename_part['EcShortdesc__c'] = descr

  #   RENAME_PARTS.append(rename_part)
  # record['ec_height']=''
  # record['ec_width']=''
  # record['ec_depth']=''
  # print (record)
  # print("************************")
  # name='none'
  return record, all_names, thename, all_fields, doNotAdd


def createBrand(record, brands, groupid):
  #random.seed(groupid)
  thekey = random.randint(0, len(brands)-1)
  #record['ec_brand'] = brands[thekey]
  brand = brands[thekey]
  return brand


def doWeHaveThisGroupIdAlready(key):
  if key in GROUP_IDS_MAP:
    return GROUP_IDS_MAP[key]
  return None


def getNewGroupKey(keys):
  last_value = ''
  for i in sorted(keys):
    last_value = keys[i]
  if last_value == '':
    last_value = f'SP{1:05}'
  # remove the prefix SP
  last_value = int(last_value.replace('SP', ''))
  # last_value +=1
  # print(last_value)
  while f'SP{last_value:05}' in keys.values():
    last_value += 1
  print('getNewGroupKey-last_value: ', last_value)
  return f'SP{last_value:05}'


def getNewProductKey(keys, group):
  last_value = ''
  for i in sorted(keys):
    if group in keys[i]:
      last_value = keys[i]
  if last_value == '':
    last_value = f'{group}_{1:05}'
  # remove the group prefix
  last_value = int(last_value.replace(group+'_', ''))
  # last_value +=1
  while f'{group}_{last_value:05}' in keys.values():
    last_value += 1
  return f'{group}_{last_value:05}'


def process(filename):
  global GROUP_IDS_MAP

  # Get All files
  random.seed(10)
  settings, config = loadConfiguration(filename)
  readCSV()
  # readCSVSKU()
  createBigPartsList()
  utils.json_dump(ALL_PARTS, Path('..', 'outputs', 'Barca - Brand Detail.json'), sort_keys=True)

  total = 0
  total_variants = 0
  total_main_groups = 0
  total_main_groups_sub = 0
  current_total = 0
  versions = ['1', '1 beta', '2', '2 beta', '3 beta', '3', '1', '1 beta', '2', '2 beta', '3 beta', '3', '1', '1 beta', '2', '2 beta', '3 beta', '3']
  # boats=['Mercury','Yamaha','Honda','Evinrude','Suzuki','Johnson','Tohatsu','OMC','Chrysler','Force','Mariner','Mercruiser','Mercury','Nissan','Sears']
  # versions=['1']
  brands = ['Barca Sports', 'Air Head', 'Aqua Marina', 'Anahola', 'HO Sports', 'Connelly', 'Hyperlite']
  variant_fields = ['cat_Diameter', 'cat_Length', 'cat_Thickness', 'ec_Sizes']
  grouping_fields = ['ec_Colors']
  grouping_fields_key = ['']
  all_parts = []
  all_queries = []
  all_fields = []
  all_parts_and_variants = {}
  all_main = {}
  all_main_with_parts = {}
  all_names = []
  total_main_added = 0
  total_variant_added = 0
  total_main_groups_added = 0
  file_counter_parts = 1
  main_record = 1
  html = '<html><body><table border=1>'
  print("No of ALL parts:")
  print(len(ALL_PARTS))
  print("No of parts:")
  print(len(PARTS))
  # First process all the parts, for each part get all the possible values (all_records)
  # Then create Records for each brand
  variant_keys = {}
  parent_keys = {}
  variant_numbers = {}
  for part in PARTS:
    print('\n----new part---')
    # for every part for every key create records
    record = getNextPartRecord()
    # check if there are colors in the record
    colors = ["none"]
    new_record = copy.deepcopy(record)
    # We do not want to use ec_brand in all possible combinations
    del new_record['ec_brand']
    if 'ec_Colors' in record:
      colors = record['ec_Colors'].split(';')
      new_record['ec_Colors'] = ''
    all_records = []
    all_records = getAllValues(new_record, variant_fields)

    first = True
    this_is_main = True
    groupid = 0
    doNotAdd = False
    brand = ''
    groupid = 0
    parentid = 0
    version = ''
    # special case for brands, if we use them they will screw up the variants
    brand_counter = 0
    no_of_brands = 0
    # brands = []
    current_brand = ''
    # saveLibs()
    for color in colors:
      doNotAdd = False
      brand = ''
      groupid = 0
      parentid = 0
      first = True
      for rec in all_records:
        groupid = 0
        parentid = 0
        #   if rec['ec_brand'] in brands:
        #     pass
        #   else:
        #     brands.append(rec['ec_brand'])
        #     no_of_brands += 1
        # for brand in brands:
        # processit = random.randint(0, len(all_records)) <= (len(all_records)-(len(all_records)/5))
        # print("length records: "+str(len(all_records)))
        processit =True
        # if len(all_records) < 10:
        #   processit = True
        if processit:
          doNotAdd = False
          parent_name = ''
          print("Color: "+color)
          if color != 'none':
            rec['ec_Colors'] = color
          # for rec in all_records:
          # print (rec)
          # if rec['ec_brand'] == brand:
          #all_brands = brands
          all_brands = record['ec_brand'].split(';')
          rec['ec_brand'] = 'empty'
          # if (first):
          #   brand = createBrand(rec, all_brands, rec['ID'])

          #   rec['ec_brand'] = brand
          #   first = False
          #   doNotAdd = False
          # else:
          #   rec['ec_brand'] = brand

          total += 1
          current_total += 1
          recid = total+1000
          # if (current_total > MAXPARTS):
          #   current_total = 0
          #   #writeCSV(all_parts, file_counter_parts)
          #   file_counter_parts += 1
          #   all_parts = []
          print('total: ', total)
          # print(rec)

          variant_key = createVariantKey(rec, variant_fields)
          we_have_variants = doWeHaveVariants(rec, variant_fields)
          print(rec)
          thename = rec['DallE name']
          for field in rec:
            fieldname = '['+field+']'
            # print (fieldname)
            if fieldname in thename:
              if (fieldname != '[ec_Colors]'):
                thename = thename.replace(fieldname, rec[field])
          print('theName: ', thename, grouping_fields)
          # if productIdKey in GROUP_IDS_MAP:
          #   groupidKey = GROUP_IDS_MAP[productIdKey]
          # else:
          groupidKey = getGroupId(rec, grouping_fields,  thename)
          productIdKey = getProductId(rec, thename)
          if not groupidKey:
            groupidKey = productIdKey
          newGroup = False
          print("GroupIdKey: ", groupidKey)
          print("ProductIdKey: ", productIdKey)
          if groupidKey != '':
            if groupidKey in all_main:
              print("Existing GROUP item, "+str(groupidKey))
              groupid = all_main[groupidKey]
              total_main_groups_sub += 1
            else:
              print("New GROUP item, "+str(groupidKey))
              newGroup = True
              already = doWeHaveThisGroupIdAlready(groupidKey)
              if (already == None):
                print("New GROUP item, GET NEW KEY, "+str(groupidKey))
                groupid = getNewGroupKey(GROUP_IDS_MAP)
                GROUP_IDS_MAP[groupidKey] = groupid
              else:
                print("New GROUP item, EXISTING KEY, "+str(groupidKey))
                groupid = GROUP_IDS_MAP[groupidKey]
              all_main[groupidKey] = groupid
              total_main_groups += 1
          else:
            groupid = getNewGroupKey(GROUP_IDS_MAP)
            print('New groupid = ', groupid)
            GROUP_IDS_MAP[productIdKey] = groupid
            total_main_groups += 1
          # if the variant_key is already in the variant_keys, then we need to set the groupid
          # if variant_key == '':
            # no variant info so normal product
            # groupid = 0
          

          if we_have_variants and variant_key in variant_keys and variant_key != '':  # and groupid!=0:
            # already got
            this_is_main = False
            doNotAdd = False
            # groupid = variant_keys[variant_key]
            parentid = variant_keys[variant_key]
            print(variant_key+" ==> Already got, this is a variant, using parentid="+str(parentid))
            total_variants += 1
            rec['ec_brand'] = brand
            # pass
          else:
            # we do not have it
            brand = createBrand(rec, all_brands, groupid)
            rec['ec_brand']=brand
            this_is_main = True
            print(variant_key+" ==> Main product")
            parentid = 0
            main_record += 1

          print('brand: ', rec['ec_brand'])
          print("Variants: "+str(we_have_variants))
          # this is the main record
          if not doNotAdd:
            rec_added, all_names, parent_name, all_fields, doNotAdd = createRecord(
                new_record, rec, recid, variant_fields, groupid, parentid, we_have_variants, all_names, all_fields, productIdKey, variant_key)
            parentid = rec_added['ec_parent']

            if (variant_key != '') and we_have_variants:
              variant_keys[variant_key] = parentid
            print("Parentid: "+str(parentid)+", doNotAdd:"+str(doNotAdd)+", ID:"+str(recid))
            groupid = rec_added['ec_item_group_id']
            if not doNotAdd:
              if rec_added['ObjectType'] == 'Product':
                parent_keys[parentid] = "yes"
                total_main_added += 1
              else:
                # remove the keys we do not need
                del rec_added['ec_item_group_id']
                # del rec_added['ec_parent_id']

                # if (variant_key!=''):
                #   if variant_key in variant_numbers:
                #     variant_numbers[variant_key]=variant_numbers[variant_key]+1
                #   else:
                #     variant_numbers[variant_key]=1
                # processvar = random.randint(0,10)<=7
                # if variant_numbers[variant_key]<=14:
                #   processvar=True
                # if processvar:
                total_variant_added += 1
                # else:
                #   doNotAdd = True
              if groupid in parentid and newGroup:
                total_main_groups_added += 1

            # if not doNotAdd:
            #   html+="<tr><td>"+rec_added['title']+'</td><td>'+rec_added['ObjectType']+'</td><td><img src="'+rec_added['orig_image']+'"></td><td>'+str(parentid)+'</td><td>'+str(groupid)+'</td><td>'+str(rec_added)+'</td></tr>'
            # else:
            #   html+="<tr style='color:red'><td>"+rec_added['title']+'</td><td>'+rec_added['ObjectType']+'</td><td><img src="'+rec_added['orig_image']+'"></td><td>'+str(parentid)+'</td><td>'+str(groupid)+'</td><td>'+str(rec_added)+'</td></tr>'
            # if this_is_main:
            #   all_queries.append({'name':parent_name,'dalle':rec_added['dalle'],'id':rec_added['ID'],'dir':rec_added['dir']})

            # Change Column names
            # print(rec_added)
            # rec_added = changeAllColumns(rec_added)
            # print(rec_added)
            # if parentid in all_parts_and_variants:
            #   # This is a variant record
            #   all_parts_and_variants[parentid]=rec_added['ObjectType']
            # else:
            #   # this is the main record
            #   #thekey = random.randint(0, len(brands)-1)
            #   #rec_added['Product EcBrand__c'] = brands[thekey]
            #   all_parts_and_variants[parentid] = [rec_added]
            if not doNotAdd:
              all_parts.append(rec_added)
              if parentid not in all_main_with_parts and rec_added['ObjectType'] == 'Product':
                all_parts_and_variants[parentid] = copy.deepcopy(rec_added)
                all_main_with_parts[parentid] = "yes"
              if parentid in all_main_with_parts and rec_added['ObjectType'] == 'Variant':
                del all_parts_and_variants[parentid]
                del all_main_with_parts[parentid]

              if (not we_have_variants):
                # force at least 1 variant
                rec_added_variant = copy.deepcopy(rec_added)
                rec_added_variant['ObjectType'] = 'Variant'
                for field in rec_added_variant.copy():
                  if field not in variant_fields and ('ec_' in field or 'cat_' in field):
                    del rec_added_variant[field]
                newid = str(parentid)+'_00001'
                if 'ec_Sizes' in rec_added_variant:
                  rec_added_variant['cat_size'] = rec_added_variant['ec_Sizes']
                # Now set the variant fields
                # rec_added_variant['ec_item_group_id'] = rec_added['ec_item_group_id']
                rec_added_variant['ec_parent'] = rec_added['ec_parent']
                rec_added_variant['ec_productid'] = rec_added['ec_productid']
                rec_added_variant['DocumentId'] = 'https://sports.barca.group/pdp/'+str(newid)
                rec_added_variant['ec_sku'] = newid
                rec_added_variant['permanentid'] = newid
                all_parts.append(rec_added_variant)
            # else:
            #   pass
          else:
            print(" Not Adding: because no more images are available...")
            print(rec)
            # break

          first = False
      # break

    # break
  # We need to fix the missing variants
  # for rec in all_parts_and_variants:
  #   rec_added_variant = copy.deepcopy(all_parts_and_variants[rec])
  #   rec_added_variant['ObjectType']='Variant'
  #   newid = rec_added_variant['ec_parent_id']+'_NOV_'+f'{recid:05}'
  #   recid+=1
  #   total_variant_added +=1
  #   #Now set the variant fields
  #   rec_added_variant['DocumentId'] = 'https://sports.barca.group/pdp/'+str(newid)
  #   rec_added_variant['ec_sku'] = newid
  #   rec_added_variant['permanentid'] = newid
  #   all_parts.append(rec_added_variant)

  # fix all parts for those variants which do not have a product
  for part in all_parts.copy():
    if (part['ec_parent'] not in parent_keys and part['ObjectType'] == 'Variant'):
      all_parts.remove(part)
      total_variant_added -= 1
      print("Removing variant because no product was there "+str(part['ec_parent'])+", ID:"+str(part['DocumentId']))


  print("Fixing bad parents without childs :)")
  
  for prod in all_parts.copy():
    if prod['ObjectType']=='Product':
      #check if Variant is there
      found=False
      for var in all_parts:
        if var['ec_parent']==prod['ec_parent'] and var['ObjectType']=='Variant':
          #we have it
          #no issue
          #print("Variant found on: "+str(prod['ec_parent']))
          found=True
          break
      if not found:
        all_parts.remove(prod)
        print("No Variant found on: "+str(prod['ec_parent']))
  # html += '</table></body></html>'
  # nows = str(datetime.now()).replace(':', '_').replace('.', '_')
  # with open(Path('..', 'outputs', 'SPORTS_'+str(nows)+'.html'), 'w', encoding='utf-8') as f:
  #   f.write(html)

  utils.json_dump(all_parts, Path('..', 'outputs', 'products.json'), sort_keys=False)
  utils.json_dump([*all_parts[:20], *all_parts[100:110], *all_parts[1000:1010]], Path('..', 'outputs', 'products_SAMPLE.json'), sort_keys=True)
  utils.json_dump(all_main, Path('..', 'outputs', 'productgroups.json'), sort_keys=False)
  utils.json_dump(PRODUCT_IDS_MAP, Path('..', 'outputs', 'product_ids.json'), sort_keys=False)
  utils.json_dump(GROUP_IDS_MAP, Path('..', 'outputs', 'group_ids.json'), sort_keys=False)
  utils.json_dump(VARIANT_IDS_MAP, Path('..', 'outputs', 'variant_ids.json'), sort_keys=False)
  utils.json_dump(REVIEW_MAP, Path('..', 'outputs', 'reviews.json'), sort_keys=False)
  utils.json_dump(variant_keys, Path('..', 'outputs', 'variant_keys.json'), sort_keys=False)

  categories = filter(lambda x: 'ec_category' in x, all_parts)
  categories = map(lambda x: x.get('ec_category')[-1], categories)
  categories = list(sorted(set(categories)))
  utils.json_dump(categories, Path('..', 'outputs', 'ec_category.json'), sort_keys=False)

  saveLibs()
  with open(Path('../outputs/key_rename.csv'), 'w', encoding='utf-8') as f:
    for keys in KEY_RENAME:
      f.write(keys['old']+','+keys['new']+'\n')

  if PUSHIT:
    push = CoveoPush.Push(settings['push_source'], settings['push_org'], settings['push_key'], p_Mode=CoveoConstants.Constants.Mode.Stream)
    push.Start(False, False)
    for rec in all_parts:
      push.AddJson(rec)
    push.End(False, False)
  # print(all_parts_and_variants)
  # writeCSV(all_parts, file_counter_parts)
  # print("Now writing the CSV files")
  # all_parts = []
  # all_parts_vars = []
  # current_total = 0
  # current_vars = 0
  # total = 0
  # total_variants = 0
  # total_skipped = 0
  # file_counter_parts = 1
  # brand = ''
  # first = True
  # for part in all_parts_and_variants.keys():
  #   first = True
  #   current_vars = 0
  #   for variant in all_parts_and_variants[part]:
  #     if first:
  #       if (current_total > MAXPARTS):
  #         current_total = 0
  #         writeCSV(all_parts, file_counter_parts)
  #         #writeCSVVars(all_parts_vars, file_counter_parts)
  #         file_counter_parts += 1
  #         all_parts = []
  #         all_parts_vars = []
  #       #brand = variant['Product EcBrand__c']
  #       # fix the record['Variation AttributeSet']='WithVariants'
  #       # if (len(all_parts_and_variants[part])==1):
  #       #   variant['Variation AttributeSet']=''
  #       # else:
  #       #   variant['Variation AttributeSet']='WithVariants'

  #       first = False
  #       #del variant['Variation Parent (StockKeepingUnit)']
  #       #del variant['Variation AttributeSet']
  #       all_parts.append(variant)
  #       current_total += 1
  #       total += 1
  #     else:
  #       #variant['Product EcBrand__c']=brand
  #       #del variant['Variation AttributeSet']
  #       print("Fixing Brand = "+brand)
  #       # if (len(all_parts_vars)<40):
  #       # all_parts_vars.append(variant)
  #       current_vars += 1
  #       total_variants += 1
  #       if current_vars < MAXVARS:
  #         all_parts.append(variant)
  #         total_variants += 1
  #       else:
  #         print("Skipping variant, to many")
  #         total_skipped += 1
  #       current_total += 1

  # writeCSV(all_parts, file_counter_parts)
  # writeCSV(RENAME_PARTS, 1000)
  # writeCSVVars(all_parts_vars, file_counter_parts)
  # Create Batch file for uploads
  # upload_counter = 1
  # upload_file_counter = 1
  # upload_max = 50
  # buffer = ''
  # for x in range(1, file_counter_parts+1):
  #   buffer += 'echo Processing: C:/test/outputParts_'+str(x)+'.csv >> output'+str(upload_file_counter)+'.txt\n'
  #   buffer += 'call sfdx commerce:products:import -u vbernard@barca.com -v vbernard@barca.com -c C:/test/outputParts_' + \
  #       str(x)+'.csv -n "'+CATALOG+'" >>output'+str(upload_file_counter)+'.txt\n'
  #   upload_counter += 1
  #   if (upload_counter > upload_max):
  #     writeUpload(upload_file_counter, buffer)
  #     upload_file_counter += 1
  #     upload_counter = 1
  #     buffer = ''

  # writeUpload(upload_file_counter, buffer)

  print("We are done!\n")
  print("Copy all CSV to C:/Test and run Upload.cmd")
  # print("Processed: "+str(total+total_variants+total_skipped)+" records")
  print("All products        : " + str(total))
  print("Main products       : " + str(main_record))
  print("Main Groups products (with same color): " + str(total_main_groups))
  print("Sub Groups products (with same color): " + str(total_main_groups_sub))
  print("Variants        :  "+str(total_variants))
  print("ADDED, All               : " + str(total_main_added+total_variant_added))
  print("ADDED, Main products     : " + str(total_main_added))
  print("ADDED, Variant products  : " + str(total_variant_added))
  print("ADDED, Main Groups       : " + str(total_main_groups_added))
  # print("Skipped Variants:  "+str(total_skipped))
  # utils.json_dump(DESC_MAP, Path('../outputs/descriptions.json'), sort_keys=True)
  # utils.json_dump(NAME_MAP, Path('../outputs/names.json'), sort_keys=True)
  # utils.json_dump(PRT_NAME, Path('../outputs/PRT_NAME.json'), sort_keys=True)
  # utils.json_dump(NAME2_MAP, Path('../outputs/names2.json'), sort_keys=True)


try:
  # fileconfig = sys.argv[1]
  # process(fileconfig)
  process('')
except Exception as e:
  print(e)
  traceback.print_exception(*sys.exc_info())
  # print ("Specify configuration json (like config.json) on startup")
