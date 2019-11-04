from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'email': self.email,
            'id': self.id,
            'picture': self.picture,
        }


class Tvshow(Base):
    __tablename__ = 'tvshow'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    summary = Column(String(250))
    rating = Column(String(3))
    picture = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'summary': self.summary,
            'rating': self.rating,
            'picture': self.picture,
        }


class Episode(Base):
    __tablename__ = 'episode'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    summary = Column(String(250))
    number = Column(Integer)
    season = Column(Integer)
    picture = Column(String(250))
    tvshow_id = Column(Integer, ForeignKey('tvshow.id'))
    tvshow = relationship(Tvshow)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'show': self.tvshow.name,
            'name': self.name,
            'summary': self.summary,

            'season': self.season,
            'number': self.number,
            'picture': self.picture,
        }


engine = create_engine('sqlite:///tvshows.db')

Base.metadata.create_all(engine)
