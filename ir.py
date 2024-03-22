# -*- coding: utf-8 -*-
"""IR

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mp8yYUn4BH8VCdInEWPYLqJ-6FLbhOvB
"""

import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import pickle
import re

df = pd.read_csv("/content/A2_Data.csv")
df.rename(columns={'Unnamed: 0': 'product id'}, inplace=True)

df

pattern = r"'(https?://[^']*)'"

def extract_urls(string):
    urls = re.findall(pattern, string)
    return urls

# Apply the function to extract URLs and replace the 'Image' column
df['Image'] = df['Image'].apply(extract_urls)

# Print the DataFrame with the updated 'Image' column

df = df.explode('Image')
df.reset_index(drop=True, inplace=True)

df['Image'].shape
df.loc[1,'Image']

import pandas as pd
import requests
from io import BytesIO
from PIL import Image

# Function to download image from URL and return bytes
def download_image(url):
    response = requests.get(url)
    img_bytes = BytesIO(response.content)
    return img_bytes

# Function to load image from URL and return PIL Image object
def load_image(url):
  try:
      img_bytes = download_image(url)
      img = Image.open(img_bytes)
      return img
  except Exception as e:
        print(f"Error loading image from URL {url}: {e}")
        return None

# Function to load images from list of URLs
def load_images_from_urls(url_list):
    return load_image(url_list)
    #return [load_image(url) for url in url_list]

# Apply the function to load images and create a new column in the DataFrame
df['Loaded_Images'] = df['Image'].apply(load_images_from_urls)

# Print the DataFrame with the loaded images column
print(df)
with open('/content/images.pkl', 'wb') as f:
    pickle.dump(df['Loaded_Images'], f)

with open('/content/images.pkl', 'rb') as f:
    data = pickle.load(f)
    df['Loaded_Images'] = data

from PIL import ImageEnhance
# preprocess images
def preprocess_image(img):
  preprocessed_images = []
  if img is not None:
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)
    img = img.resize((100, 100))
    # Convert image to grayscale
    #img = img.convert('L')
    preprocessed_images.append(img)
  return preprocessed_images

df['Loaded_Images'] = df['Loaded_Images'].apply(preprocess_image)

df.loc[0,'Loaded_Images']

for i in range(1,100):
  print(df.loc[i,"Loaded_Images"])

from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.preprocessing import image
import numpy as np

# Ensure the VGG16 model is loaded before calling the function
vgg_model = VGG16(weights='imagenet', include_top=False)

# Function to extract features using VGG16 model
def extract_features_vgg(images):
    features_list = []
    for img in images:
        if img is not None:
            print(img)
            img = img.resize((100, 100))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            # Preprocess the image using VGG16 preprocessing function
            x = preprocess_input(x)
            features = vgg_model.predict(x)
            # Normalize features
            features_normalized = features / np.linalg.norm(features)
            features_list.append(features_normalized.flatten())
    return features_list

# Apply the function to extract features using VGG16 and create a new column in the DataFrame
df['VGG16_Features'] = df['Loaded_Images'].apply(extract_features_vgg)

# Print the DataFrame with the extracted VGG16 features column
print(df)

import pickle
with open('/content/extracted_features.pkl', 'wb') as f:
    pickle.dump(df['VGG16_Features'], f)

with open('/content/extracted_features.pkl', 'rb') as f:
    data = pickle.load(f)
    df['VGG16_Features'] = data

input_url = input("Enter the image url: ")
image = load_image(input_url)
image = preprocess_image(image)
image
# https://images-na.ssl-images-amazon.com/images/I/61Yuwnt9eoL._SY88.jpg

from keras.preprocessing.image import img_to_array


image = image[0].resize((100, 100))  # Resize image to VGG16 input size
x = img_to_array(image)
x = np.expand_dims(x, axis=0)
x = preprocess_input(x)
features = vgg_model.predict(x)
features_normalized = features / np.linalg.norm(features)

# reviews pre process - from assi 1
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
import pickle
nltk.download('punkt')
nltk.download('stopwords')

def preprocess_text(content):
    if isinstance(content, str):
        content = content.lower()
        tokens = word_tokenize(content)
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
        tokens = [token for token in tokens if token.strip() != '']
        text = ' '.join(tokens)
        text = text.translate(str.maketrans('', '', string.punctuation))

        return text
    else:
        print(content)
        return ''

# Apply text pre-processing
df['Processed Review'] = df['Review Text'].apply(preprocess_text)

# TF - IDF scores
from collections import Counter
import math

def calculate_term_frequency(review):
    term_freq = {}
    if review is None:
        return None

    count_words = len(review)
    word_frequency = Counter(review)

    for word, freq in word_frequency.items():
        term_freq[word] = freq / count_words

    return term_freq

def calculate_inverse_document_frequency(corpus):
    total_documents = len(corpus)
    inverse_doc_freq = {}
    word_doc_freq = {}

    for document in corpus:
        if document is None:
            continue

        unique_words = set(document)

        for word in unique_words:
            word_doc_freq[word] = word_doc_freq.get(word, 0) + 1

    for word, freq in word_doc_freq.items():
        inverse_doc_freq[word] = math.log(total_documents / freq)

    return inverse_doc_freq

def calculate_tfidf(term_freq_dict, inverse_doc_freq_dict):
    if not term_freq_dict:
        return {}

    tfidf_scores = {}

    for word, tf in term_freq_dict.items():
        tfidf_scores[word] = tf * inverse_doc_freq_dict.get(word, 0)

    return tfidf_scores

df['TF'] = df['Processed Review'].apply(calculate_term_frequency)
c = df['Processed Review'].tolist()
idf = calculate_inverse_document_frequency(c)
def calculate_tfidf_for_row(tf_row, idf_dict):
    return calculate_tfidf(tf_row, idf_dict)
df['TF-IDF'] = df['TF'].apply(calculate_tfidf_for_row, idf_dict=idf)

with open('/content/tf-idf.pkl', 'wb') as f:
    pickle.dump(df['TF-IDF'], f)

from sklearn.metrics.pairwise import cosine_similarity


flat_input_features = features_normalized.flatten()

# Calculate cosine similarity between input features and each array in the DataFrame column
cos_similarities = []

# Store product IDs of images already considered

for index, row in df.iterrows():
    # Exclude images with the same product ID as the input image
    # if row['product id'] == input_row.iloc[0]['product id']:
    #     continue

    resized_array = np.resize(row['VGG16_Features'], features_normalized.shape)
    flat_array = resized_array.flatten()
    cos_sim = cosine_similarity(flat_input_features.reshape(1, -1), flat_array.reshape(1, -1))
    cos_similarities.append((index, cos_sim[0][0]))

    # Add the product ID to the set of considered IDs

# Sort similarity scores in descending order
cos_similarities.sort(key=lambda x: x[1], reverse=True)

# Retrieve top three most similar images
top_three_similar_images = cos_similarities[:3]
top_three_similar_images

input_row = df[df['Image'] == input_url]

if not input_row.empty:
    product_id = input_row.iloc[0]['product id']
    product_review = input_row.iloc[0]['Processed Review']
    tfidf = input_row.iloc[0]['TF-IDF']
    print("Product ID:", product_id)
else:
    print("Image link not found in DataFrame.")

cosine_similarities_reviews = []
for index, cosine_sim in top_three_similar_images:
    tf_idf = df.loc[index, 'TF-IDF']
    tf_idf_input = input_row.iloc[0]['TF-IDF']

    vocabulary = set(tf_idf.keys()) | set(tf_idf_input.keys())

    tfidf_vector1 = np.array([tf_idf.get(word, 0) for word in vocabulary])
    tfidf_vector2 = np.array([tf_idf_input.get(word, 0) for word in vocabulary])

    cosine_sim_result = cosine_similarity([tfidf_vector1], [tfidf_vector2])  # Changed variable name here
    cosine_similarities_reviews.append((index, cosine_sim_result[0][0]))  # Changed variable name here

i = 0
for index, cosine_simalirity in top_three_similar_images:
  print("Product Id:",df.loc[index,"product id"])
  print("Image Link:",df.loc[index,"Image"] )
  print("Product Review:",df.loc[index,"Review Text"] )
  print("Cosine Sim of Image:",cosine_simalirity )
  print("Cosine Sim of Review:",cosine_similarities_reviews[i][1])
  print("Composite Score:", (cosine_simalirity+cosine_similarities_reviews[i][1])/2)
  i+=1

# input images review pre process , cosine sim of input image review and other reviews
input_review = input("enter review: ")
preprocessed_input_review = preprocess_text(input_review)
row = df[df['Processed Review'].apply(lambda i: i == preprocessed_input_review)]

if row.empty:
  print("Image review not found in DataFrame.")
else:
  id = row.iloc[0]['product id']
  url = row.iloc[0]['Image']
  tfidf = row.iloc[0]['TF-IDF']
  input_features = row.iloc[0]['VGG16_Features']

# We use these for everything from our acoustic bass down to our ukuleles. I know there is a smaller model available for ukes, violins, etc.; we haven't yet ordered those, but these will work on smaller instruments if one doesn't extend the feet to their maximum width. They're gentle on the instruments, and the grippy material keeps them secure.  The greatest benefit has been when writing music at the computer and needing to set a guitar down to use the keyboard/mouse - just easier for me than a hanging stand.  We have several and gave one to a friend for Christmas as well. I've used mine on stage, and it folds up small enough to fit right in my gig bag.

from sklearn.metrics.pairwise import cosine_similarity

cos_similarities = []

# Store product IDs of images already considered
considered_ids = set()
considered_ids.add(id)

for index, row in df.iterrows():
    # Exclude images with the same product ID as the input image
    if row['product id'] in considered_ids:
        continue

    considered_ids.add(row['product id'])

    tfidf_dict1 = tfidf
    tfidf_dict2 = row['TF-IDF']
    vocabulary = set(tfidf_dict1.keys()) | set(tfidf_dict2.keys())

    tfidf_vector1 = np.array([tfidf_dict1.get(word, 0) for word in vocabulary])
    tfidf_vector2 = np.array([tfidf_dict2.get(word, 0) for word in vocabulary])

    cosine_sim = cosine_similarity([tfidf_vector1], [tfidf_vector2])
    cos_similarities.append((index, cosine_sim[0][0]))

# Sort similarity scores in descending order
cos_similarities.sort(key=lambda x: x[1], reverse=True)

# Print top three similar reviews
top_three_similar_reviews = cos_similarities[:3]
print(top_three_similar_reviews)

cosine_similarities_images = []
input_features = np.array(input_features)
input_features = input_features.flatten()
print(input_features)
for index, cos_sim in top_three_similar_reviews:
  resized_array = np.resize(df.loc[index,'VGG16_Features'], input_features.shape)
  flat_array = resized_array.flatten()
  cos_sim = cosine_similarity(input_features.reshape(1, -1), flat_array.reshape(1, -1))
  cosine_similarities_images.append((index, cos_sim[0][0]))

print(flat_array)
print(cosine_similarities_images)

i = 0
for index, cosine_simalirity in top_three_similar_reviews:
  print("Product Id:",df.loc[index,"product id"])
  print("Image Link:",df.loc[index,"Image"] )
  print("Product Review:",df.loc[index,"Review Text"] )
  print("Cosine Sim of Review:",cosine_simalirity )
  print("Cosine Sim of Image:",cosine_similarities_images[i][1])
  print("Composite Score:", (cosine_simalirity+cosine_similarities_images[i][1])/2)
  i+=1

# a. Present the top-ranked (image, review) pairs along with the cosine similarity scores
print("Top-ranked (image, review) pairs along with cosine similarity scores:")
for index, similarity_score in top_three_similar_reviews:
    print(f"Image ID: {df.loc[index, 'Image']}, Review: {df.loc[index, 'Review Text']}")
    print(f"Cosine Similarity Score: {similarity_score}")
    print()