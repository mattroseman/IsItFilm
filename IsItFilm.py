import logging
import gzip
from datetime import datetime
import os
import csv
import re
import threading
from queue import Queue

import requests
from bs4 import BeautifulSoup

from db import DatabaseConnection


# set up logging
LOGGER = logging.getLogger('isitfilm')
logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)-5s] %(asctime)s [%(threadName)-10s](%(filename)s:%(lineno)d): %(message)s'
)
logging.getLogger('isitfilm').setLevel(logging.INFO)

db = DatabaseConnection(
    user=os.environ.get('DB_USER', 'user'),
    password=os.environ.get('DB_PASSWORD', 'password'),
    db=os.environ.get('DB_NAME', 'isitfilm'),
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432')
)

movie_queue = Queue()
total_movie_count = 0
movies_processed = 0


def main():
    global movie_queue, total_movie_count

    LOGGER.info('getting list of movies')
    movies = get_list_of_movies()
    total_movie_count = len(movies)

    # create a queue of movies
    for movie in movies:
        movie_queue.put(movie)

    LOGGER.info('getting cameras used in each movie')
    # create threads to process movies off this queue
    threads = []
    for i in range(int(os.environ.get('NUM_THREADS', '1'))):
        thread = threading.Thread(name='Thread-{}'.format(i), target=process_movie, daemon=True)
        thread.start()
        threads.append(thread)

    # wait for all the threads to finish
    for thread in threads:
        thread.join()


def process_movie():
    """
    process_movie keeps reading movies off the movie_queue and gets the cameras used in it, then adds it to the database
    """
    global movie_queue, total_movies_count, movies_processed

    while not movie_queue.empty():
        movies_processed += 1

        movie = movie_queue.get()
        # if this movie is already in the database, skip it
        if db.get_movie_by_id(movie['id']):
            LOGGER.info('ALREADY PROCESSED {}/{} movie: {}'.format(
                movies_processed, total_movie_count, movie['title']
            ))
            continue

        cameras_used = get_cameras_used(movie['id'])

        # add a row into a PostgreSQL database with the movie name, id, and camera names used
        db.add_movie_and_cameras(movie['id'], movie['title'], movie['english_title'], cameras_used)

        LOGGER.info('{}/{} movie: {}, cameras: {}'.format(
            movies_processed, total_movie_count, movie['title'], cameras_used
        ))


def get_list_of_movies():
    """
    queries IMDb to get a list of all movies (which will be updated with new releases on each call)
    @return: a list of dicts containing movies titles, and IMDb id's
    """
    movies_file_path = 'data/{}{}{}_title.basics.tsv'.format(datetime.now().year, datetime.now().month, datetime.now().day)

    # if the movies file doesn't exist, download and uncompress it
    if not os.path.exists(movies_file_path):
        # TODO delete any previous tsv files, since they will be overwritten
        LOGGER.debug('downloading IMDb title basics tsv file')
        movies_file_compressed = requests.get('https://datasets.imdbws.com/title.basics.tsv.gz').content
        LOGGER.debug('decompressing the title basics tsv file')
        movies_file = gzip.decompress(movies_file_compressed)
        with open(movies_file_path, 'wb') as f:
            f.write(movies_file)

    with open(movies_file_path, 'r') as f:
        movies_tsv = csv.reader(f, delimiter='\t')

        # filter out only movies, and get movie titles and IMDb id's
        LOGGER.debug('filtering out non movies, and extracting relevant movie info')

        # in order to avoid duplicate movies, track ids encountered, and skip any duplicate ids
        movie_ids = set()

        movies = []

        for movie in movies_tsv:
            # skip any non movies
            if movie[1] != 'movie':
                continue

            # skip any movies who's ids have already been added
            if movie[0] in movie_ids:
                continue
            movie_ids.add(movie[0])

            movies.append({'id': movie[0], 'english_title': movie[2], 'title': movie[3]})

    return movies


def get_cameras_used(movie_id):
    """
    given a movie id queries IMDb to get a list of the cameras used in the making of the movie.
    @param movie_id: a string representing the IMDb id for a movie
    @return: a list of strings representing the cameras used in the making of the movie with the given name
    """
    LOGGER.debug('{}: getting IMDb HTML for technical info for movie'.format(movie_id))
    movie_technical_url = 'https://www.imdb.com/title/{}/technical'.format(movie_id)
    movie_technical_response = requests.get(movie_technical_url)
    if movie_technical_response.status_code != 200:
        LOGGER.exception('IMDb didn\'t respond with a 200, got a {} instead.\nResponse: {}'.format(
            movie_technical_response.status_code,
            movie_technical_response.text
        ))
        raise Exception('IMDb didn\'t respond with a 200')
    movie_technical_html = movie_technical_response.text

    # parse the list of cameras out of the HTML for the IMDb technical page
    movie_technical_soup = BeautifulSoup(movie_technical_html, 'html.parser')
    movie_technical_camera_label = movie_technical_soup.find('td', class_='label', string=re.compile('^\s*camera\s*$', re.IGNORECASE))

    # if the Camera table row isn't in the HTML, IMDb doesn't have info on what camera was used
    if movie_technical_camera_label is None:
        LOGGER.debug('{}: no camera info found for this movie'.format(movie_id))
        return []

    LOGGER.debug('{}: parsing camera names used for this movie'.format(movie_id))
    movie_technical_cameras_text = movie_technical_camera_label.next_sibling.next_sibling.get_text()
    movie_cameras = []
    for line in movie_technical_cameras_text.split('\n'):
        # only grab info on the camera name, not the lenses used
        movie_camera = line.split(',')[0].strip()
        if movie_camera:
            movie_cameras.append(movie_camera)

    return movie_cameras


if __name__ == '__main__':
    main()
