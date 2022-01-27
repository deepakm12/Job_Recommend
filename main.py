import streamlit as st # Make Frontend
import pymongo # Database connection
from pymongo import MongoClient # Access database url
import pandas as pd # Basic dataframe operations
import pdfplumber # Plumb pdf for visual debugging and data extraction including table data
import PyPDF2 # To scan pdf documents
from rake_nltk import Rake # Simple Key extraction
import string # String operations
import io # Convert a binary resume file to decoded file readable by python
import re # Regular expression
import nltk # Natural Language toolkit
nltk.download('stopwords')
nltk.download('punkt')
import lxml # most feature-rich and easy-to-use library for processing XML and HTML

country = st.sidebar.text_input('Country')
# Each element that's passed to st.sidebar is pinned to the left.
# text_input display a single-line text input widget.
uploaded_file = st.file_uploader('Upload your resume')
# file_uploader uploades files are limited to 200MB.
file_text = ''
# To save file data
phrases = []
# takes phrases
# keyphrases function
def keyphrases(file, min_word, max_word, num_phrases):
    text = file
    text = text.lower()
    # lowercase text inputted
    text = ''.join(s for s in text if ord(s) > 31 and ord(s) < 126)
    # ord(s) = 31 is Space
    # ord(s) = 125 is right curly brace
    # using join() function to join text
    text = text
    text = re.sub(' +', ' ', text)
    # Replace multiple space with single space
    text = text.translate(str.maketrans('', '', string.punctuation))
    # maketrans-specify the list of characters that need to be replaced in the whole string
    # translate() method in Python for making many character replacements in strings.
    text = ''.join([i for i in text if not i.isdigit()])
    # join if not a digit
    r = Rake(min_length=min_word, max_length=max_word)
    # extract keywords of size entered to the function
    r.extract_keywords_from_text(text)
    # Extraction given the text.
    phrases = r.get_ranked_phrases()
    # To get keyword phrases ranked highest to lowest.

    if num_phrases < len(phrases):
        phrases = phrases[0:num_phrases]
        # only keep phrases of length specified earlier

    return phrases
    # returns key phrases


# check if file has any data
if uploaded_file is not None:
    uploaded_file.seek(0)
    # Top of pdf file
    file = uploaded_file.read()
    # Read the file data
    pdf = PyPDF2.PdfFileReader(io.BytesIO(file))
    # Convert it into python readable format from binary form
    for page in range(pdf.getNumPages()):
        # getNumPages for calculating the number of pages in this PDF file.
        file_text += (pdf.getPage(page).extractText())
        # getPage for retrieving a page by number from this PDF file.
        # extractText for extracting text

        phrases.extend(keyphrases(file_text, 2, 4, 10))
        # Extend add return value in phrases after function is run


if len(phrases) > 0:
    q_terms = st.multiselect('Select key phrases',options=phrases,default=phrases) #display keywords

#mongo-connection
client = pymongo.MongoClient("mongodb+srv://deepm12:abcd123@cluster0.7pyxk.mongodb.net/Job_Recommender?retryWrites=true&w=majority")

def query(country,keywords):

    result = client['JobRecommender']['Companies'].aggregate([
        {
            '$search': {
                'text': {
                    'path': [
                        'industry'
                    ],
                    'query': [
                        ' %s' % (keywords)
                    ],
                    'fuzzy': {
                        'maxEdits': 2,
                        'prefixLength': 2
                    }
                }
            }
        }, {
            '$project': {
                'Name': '$name',
                'Industry': '$industry',
                'City': '$locality',
                'Country': '$country',
                'score': {
                    '$meta': 'searchScore'
                }
            }
        }, {
            '$match': {
                'Country': '%s' % (country)
            }
        }, {
            '$limit': 10
        }
    ])

    df = pd.DataFrame(result)

    return df

if st.button('Search'):
    df = query(country,phrases)
    st.write(df)