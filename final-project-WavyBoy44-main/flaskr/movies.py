from crypt import methods
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import Blueprint, request, render_template
from flaskr.db import get_movies, get_movie
from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator 

DEVELOPER_KEY = 'YOUR_KEY_HERE'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def youtube_search(query_term, max_results, page_token=None):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    
    if page_token:
       search_response = youtube.search().list(
        q = query_term,
        part = 'id,snippet',
        maxResults = max_results,
        pageToken=page_token
        ).execute()
    else:
        search_response = youtube.search().list(
        q = query_term,
        part = 'id,snippet',
        maxResults = max_results,
        ).execute()


    videos = []
    for search_result in search_response['items']:
        if search_result['id']['kind'] == 'youtube#video':
            videos.append(search_result)


    return videos


bp = Blueprint('movies', __name__, url_prefix='/movies')

url = 'https://api.us-east.language-translator.watson.cloud.ibm.com/instances/120e59fa-2289-42ee-ab41-691768866524'
API_KEY = 'nX81NhlM-o05xF4FHB27NTrmlY7dJuIFEu083m4KRv_J'

authenticator = IAMAuthenticator(API_KEY)
language_translator = LanguageTranslatorV3(
    version = '2018-05-01',
    authenticator = authenticator
)
language_translator.set_service_url(url)

def translator(text):
    translate = language_translator.translate(
    text = text,
    model_id='en-zh').get_result()
    data = json.dumps(translate, indent=2, ensure_ascii=False, skipkeys=True)
    json_object = json.loads(data)
    t = json_object.get("translations")
    text = t[0]["translation"]
    return text

# https://werkzeug.palletsprojects.com/en/2.0.x/routing/
# Rules that end with a slash are “branches”, others are “leaves”. 
# If strict_slashes is enabled (the default), 
# visiting a branch URL without a trailing slash will redirect to the URL with a slash appended.
@bp.route('/', methods=['GET'], strict_slashes=False)
def movie_list():
    movies = get_movies()
    return render_template('movies.html', movies=movies)


@bp.route('/translate', methods=['GET'])
def translate():
    id = request.args.get('id')
    movie = get_movie(id)
    title = movie[0]['title']
    translated_title = translator(title)
    overview = movie[0]['overview']
    translated = translator(overview)
    return render_template('translate.html', title=title, overview=overview, 
        movie=movie, translated_title=translated_title, 
        translated=translated)
    

@bp.route('/videos', methods=['GET'])
def videos():
    id = request.args.get('id')
    movie = get_movie(id)
    youtube_url = 'https://www.youtube.com/embed/'
    title = movie[0]['title'] + 'Offical Trailer'
    trailer = youtube_search(title, 1)
    videoId = youtube_url + trailer[0]['id']['videoId']
    return render_template('videos.html', trailer=trailer, url=videoId, movie=movie)
    
