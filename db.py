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

        self.session_maker = sessionmaker(bind=engine)
        self.main_session = self.session_maker()

    def get_session(self):
        return self.session_maker()

    def get_movie_by_id(self, movie_id, session=None):
        """
        queries the Movie table for a movie with the given movie id
        @param movie_id: a string representing the id of the movie to query for
        @param session: an optional session to use for database transactions
        @return: a Movie object if a movie with the given id was found, else None
        """
        # if a specific session isn't provided, use the main one
        if session is None:
            session = self.main_session

        movie = session.query(Movie).filter_by(id=movie_id).first()

        if movie:
            return movie

        return None

    def add_movie_and_cameras(self, movie_id, movie_title, movie_english_title, cameras_used, session=None):
        """
        adds new rows in the database for the given movie and list of cameras used
        @param movie_id: the id of the movie to add
        @param movie_title: the title of the movie to add
        @param movie_english_title: the english title of the movie to add
        @param camaras_used: a list of strings, that are names of cameras used in the given movie
        @param session: an optional session to use for database transactions
        @return: the movie object that has been created and added to the database
        """
        # if a specific session isn't provided, use the main one
        if session is None:
            session = self.main_session

        movie = Movie(id=movie_id, title=movie_title, english_title=movie_english_title)

        try:
            for camera_name in cameras_used:
                camera = session.query(Camera).filter_by(name=camera_name).first()
                if not camera:
                    camera = Camera(name=camera_name)

                movie.cameras.append(camera)

                session.add(camera)

            session.add(movie)

            session.commit()
        except Exception:
            # if there is an error, rollback any changes to the session
            session.rollback()
            raise

        return movie
