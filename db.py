import logging

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from models import Movie, Camera, Base


LOGGER = logging.getLogger('isitfilm')


class DatabaseConnection:
    def __init__(self, user, password, db, host='localhost', port='5432'):
        LOGGER.debug('connecting to database')
        url = 'postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, db)

        engine = sqlalchemy.create_engine(url, client_encoding='utf8')

        Base.metadata.create_all(engine)

        # TODO the session object in db is not thread safe
        # there should be a new session for each thread (find out how to do this)
        self.session = sessionmaker(bind=engine)()

    def get_movie_by_id(self, movie_id):
        """
        queries the Movie table for a movie with the given movie id
        @param movie_id: a string representing the id of the movie to query for
        @return: a Movie object if a movie with the given id was found, else None
        """
        movie = self.session.query(Movie).filter_by(id=movie_id).first()
        if movie:
            return movie

        return None

    def add_movie_and_cameras(self, movie_id, movie_title, movie_english_title, cameras_used):
        """
        adds new rows in the database for the given movie and list of cameras used
        @param movie_id: the id of the movie to add
        @param movie_title: the title of the movie to add
        @param movie_english_title: the english title of the movie to add
        @param camaras_used: a list of strings, that are names of cameras used in the given movie
        @return: the movie object that has been created and added to the database
        """
        movie = Movie(id=movie_id, title=movie_title, english_title=movie_english_title)

        for camera_name in cameras_used:
            camera = Camera(name=camera_name)
            movie.cameras.append(camera)

            self.session.add(camera)

        self.session.add(movie)

        self.session.commit()

        return movie
