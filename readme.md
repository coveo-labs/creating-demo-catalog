# Building an E Commerce demo

How to build an E Commerce demo from scratch.

# Setup

Our taxonomy for the catalog is defined in `Barca - Brand Detail.xlsx`.

We then follow the following steps to produce the final products.

1. Using the script `1_generateAllVariationsAndDallE.py` we create all the possible variations of the taxonomy, we create the Dall-E queries we need in the next step.
2. Using the script `2_generateDallEImages.py` we call OpenAI Dall-E to generate the images and save them locally.
3. Using the script `3_generateSports.py` we create the actual product catalog. We call OpenAI to create product names, descriptions and reviews.

# Authors

Wim Nijmeijer
