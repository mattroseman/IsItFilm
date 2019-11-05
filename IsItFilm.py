import gzip
from datetime import datetime
import os
import csv

import requests


def main():
    movies = get_list_of_movies()

    print(movies)
    return

    for movie in movies:
        cameras_used = get_cameras_used(movie)

        print('\n{}\n{}'.format(movie, cameras_used))


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


def get_cameras_used(movie_name):
    """
    given a movie name queries IMDb to get a list of the cameras used in the making of the movie.
    @param movie_name: a string representing the name of the movie
    @return: a list of strings representing the cameras used in the making of the movie with the given name
    """
    pass


if __name__ == '__main__':
    main()
