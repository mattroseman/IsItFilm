import gzip
from datetime import datetime
import os
import csv
import re

import requests
from bs4 import BeautifulSoup


def main():
    movies = get_list_of_movies()

    for movie in movies:
        # TODO if this movie is already in the database, skip it
        cameras_used = get_cameras_used(movie['id'])

        if cameras_used:
            # TODO add a row into a PostgreSQL database with the movie name, id, and camera names used
            print('\n{}\n{}'.format(movie['title'], cameras_used))


def get_list_of_movies():
    """
    queries IMDb to get a list of all movies (which will be updated with new releases on each call)
    @return: a list of dicts containing movies titles, and IMDb id's
    """
    movies_file_path = 'data/{}{}{}_title.basics.tsv'.format(datetime.now().year, datetime.now().month, datetime.now().day)

    # if the movies file doesn't exist, download and uncompress it
    if not os.path.exists(movies_file_path):
        movies_file_compressed = requests.get('https://datasets.imdbws.com/title.basics.tsv.gz').content
        movies_file = gzip.decompress(movies_file_compressed)
        with open(movies_file_path, 'wb') as f:
            f.write(movies_file)

    with open(movies_file_path, 'r') as f:
        movies_tsv = csv.reader(f, delimiter='\t')

        # filter out only movies, and get movie titles and IMDb id's
        movies = [{'id': movie[0], 'english_title': movie[2], 'title': movie[3]} for movie in movies_tsv if movie[1] == 'movie']

    return movies


def get_cameras_used(movie_id):
    """
    given a movie id queries IMDb to get a list of the cameras used in the making of the movie.
    @param movie_id: a string representing the IMDb id for a movie
    @return: a list of strings representing the cameras used in the making of the movie with the given name
    """
    movie_technical_url = 'https://www.imdb.com/title/{}/technical'.format(movie_id)
    movie_technical_html = requests.get(movie_technical_url).text

    # parse the list of cameras out of the HTML for the IMDb technical page
    movie_technical_soup = BeautifulSoup(movie_technical_html, 'html.parser')
    movie_technical_camera_label = movie_technical_soup.find('td', class_='label', string=re.compile('^\s*camera\s*$', re.IGNORECASE))

    # if the Camera table row isn't in the HTML, IMDb doesn't have info on what camera was used
    if movie_technical_camera_label is None:
        return None

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
