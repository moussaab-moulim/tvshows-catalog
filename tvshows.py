from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Tvshow, Base, Episode, User
import json
import requests

engine = create_engine('sqlite:///tvshows.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
pic = 'https://pbs.twimg.com/profile_images/2671170543/' \
      '18debd694829ed78203a5a36dd364160_400x400.png'
User1 = User(name="jhon doe", email="jhondoe@gmail.com",
             picture=pic)
session.add(User1)
session.commit()
# getting data from public api to populate our database
api_url = 'http://api.tvmaze.com/shows/'

results = []
for i in range(1, 11):
    show = api_url + str(i)

    # get the show with the id=i
    response = requests.get(show)
    if response.status_code == 200:
        results = json.loads(response.content.decode('utf-8'))
        # add the show to database
        print('adding ' + results['name'])
        if results['image'] is None:
            picturet = "https://via.placeholder.com/453x667"
        else:
            picturet = results['image'].values()[1]
            summ = results['summary'].replace('<p>', '').replace('</p>', '')
        tvshow = Tvshow(user_id=2, name=results['name'],
                        summary=summ,
                        rating=results['rating'].values()[0],
                        picture=picturet)
        session.add(tvshow)
        session.commit()
        # after inserting the tvshow we get the episodes of the tv show
        ep_response = requests.get(show + "/episodes")
        if ep_response.status_code == 200:
            ep_results = []
            ep_results = json.loads(ep_response.content.decode('utf-8'))
            print("adding episodes of " + results['name'])
            for episode in ep_results:
                if episode['image'] is None:
                    picture = "https://via.placeholder.com/750x400"
                else:
                    picture = episode['image'].values()[1]
                    summ = results['summary'].replace('<p>', '').replace(
                        '</p>', '')
                tvEpisode = Episode(user_id=2, name=episode['name'],
                                    summary=summ,
                                    number=episode['number'],
                                    season=episode['season'],
                                    picture=picture,
                                    tvshow=tvshow)

                session.add(tvEpisode)
                session.commit()

print "added the tvshows"
