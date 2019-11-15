import enum

from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


camera_used_table = Table(
    'camera_used',
    Base.metadata,
    Column('movie_id', String(16), ForeignKey('movie.id'), primary_key=True),
    Column('camera_id', Integer, ForeignKey('camera.id'), primary_key=True)
)


class Movie(Base):
    __tablename__ = 'movie'

    id = Column(String(16), primary_key=True)
    title = Column(String(256), nullable=False)
    english_title = Column(String(256), nullable=False)

    cameras = relationship(
        'Camera',
        secondary=camera_used_table,
        back_populates='movies'
    )

    def __repr__(self):
        return '<Movie(id={}, title={}, english_title={})>'.format(
            self.id,
            self.title,
            self.english_title
        )


class Medium(enum.Enum):
    film = 1
    digital = 2
    unknown = 3


class Camera(Base):
    __tablename__ = 'camera'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True)
    medium = Column(Enum(Medium), nullable=True)

    movies = relationship(
        'Movie',
        secondary=camera_used_table,
        back_populates='cameras'
    )

    def __repr__(self):
        return '<Camera(id={}, name={}, medium={})>'.format(
            self.id,
            self.name,
            self.medium
        )
