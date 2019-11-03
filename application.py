from functools import wraps
from flask import Flask, render_template, request, \
    redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Tvshow, Episode, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///tvshows.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')

    return decorated_function

# JSON APIs to view tv shows Information
@app.route('/tvshows/<int:tvshow_id>/episodes/JSON')
def tvsowEpisodeJSON(tvshow_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshow = session.query(Tvshow).filter_by(id=tvshow_id).one()
    episodes = session.query(Episode).filter_by(tvshow_id=tvshow_id).all()
    return jsonify(Episode=[i.serialize for i in episodes])


@app.route('/tvshows/<int:tvshow_id>/episodes/<int:episode_id>/JSON')
def episodeJSON(tvshow_id, episode_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    episode = session.query(Episode).filter_by(id=episode_id).one()
    return jsonify(episode=episode.serialize)


@app.route('/tvshows/JSON')
def tvshowJSON():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshows = session.query(Tvshow).all()
    return jsonify(tvshows=[r.serialize for r in tvshows])


# JSON APIs to view users Information
@app.route('/users/JSON')
def usersJSON():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    users = session.query(User).all()
    return jsonify(users=[r.serialize for r in users])


@app.route('/users/<int:user_id>/JSON')
def userJSON(user_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    user = session.query(User).filter_by(id=user_id).one()
    return jsonify(user=user.serialize)


# Show all tvshows
@app.route('/')
@app.route('/tvshows/')
def showTvshows():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshows = session.query(Tvshow).order_by(asc(Tvshow.name))
    if 'username' not in login_session:
        return render_template('publictvshows.html', tvshows=tvshows)
    else:
        return render_template('tvshows.html', tvshows=tvshows)


# Create a new tvshow
@app.route('/tvshows/new/', methods=['GET', 'POST'])
@login_required
def newTvshow():

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if request.method == 'POST':
        newTvshow = Tvshow(name=request.form['name'],
                           rating=request.form['rating'],
                           picture=request.form['picture'],
                           user_id=login_session['user_id'])
        session.add(newTvshow)
        flash('New Tvshow %s Successfully Created ' % newTvshow.name)
        session.commit()
        return redirect(url_for('showTvshows'))
    else:
        return render_template('newtvshow.html')


# Edit a tvshows
@app.route('/tvshows/<int:tvshow_id>/edit/', methods=['GET', 'POST'])
@login_required
def editTvshow(tvshow_id):

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedTvshow = session.query(Tvshow).filter_by(id=tvshow_id).one()
    if editedTvshow.user_id != login_session['user_id']:
        return "<script>function myFunction(){alert('You are not authorized " \
               "to edit this tvhshow. Please create your own tvshow in order" \
               " to edit.');}</script><body onload='myFunction()''> "
    if request.method == 'POST':
        if request.form['name'] or request.form['summary'] or \
                request.form['rating'] or request.form['picture']:
            if request.form['name']:
                editedTvshow.name = request.form['name']
            if request.form['summary']:
                editedTvshow.summary = request.form['summary']
            if request.form['rating']:
                editedTvshow.rating = request.form['rating']
            if request.form['picture']:
                editedTvshow.picture = request.form['picture']
            session.commit()
            flash('Tvshow Successfully Edited %s' % editedTvshow.name)
            return redirect(url_for('showEpisodes', tvshow_id=tvshow_id))
    else:
        return render_template('edittvshow.html', tvshow=editedTvshow)


# Delete a tvshow
@app.route('/tvshows/<int:tvshow_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteTvshow(tvshow_id):

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshowToDelete = session.query(Tvshow).filter_by(id=tvshow_id).one()
    if tvshowToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized " \
               "to delete this tvshow. Please create " \
               "your own tvshow in order to delete.');}</script>" \
               "<body onload='myFunction()''> "
    if request.method == 'POST':
        session.delete(tvshowToDelete)
        flash('%s Successfully Deleted' % tvshowToDelete.name)
        session.commit()
        return redirect(url_for('showTvshows', tvshow_id=tvshow_id))
    else:
        return render_template('deletetvshow.html', tvshow=tvshowToDelete)


# Show a tvshow episodes
@app.route('/tvshows/<int:tvshow_id>/')
@app.route('/tvshows/<int:tvshow_id>/episodes/')
def showEpisodes(tvshow_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshow = session.query(Tvshow).filter_by(id=tvshow_id).one()
    creator = getUserInfo(tvshow.user_id)
    episodes = session.query(Episode).filter_by(tvshow_id=tvshow_id).all()
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:

        return render_template('publicepisodes.html', episodes=episodes,
                               tvshow=tvshow, creator=creator)
    else:
        return render_template('episodes.html', episodes=episodes,
                               tvshow=tvshow, creator=creator)


# Create a new episode
@app.route('/tvshows/<int:tvshow_id>/episodes/new/', methods=['GET', 'POST'])
@login_required
def newEpisode(tvshow_id):

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshow = session.query(Tvshow).filter_by(id=tvshow_id).one()
    if login_session['user_id'] != tvshow.user_id:
        return "<script>function myFunction() {alert('You are not authorized" \
               " to add episodes to this tvshow. Please " \
               "create your own tvshow in order to add episodes.');}" \
               "</script><body onload='myFunction()''> "
    if request.method == 'POST':
        episode = Episode(name=request.form['name'],
                          summary=request.form['summary'],
                          number=request.form['number'],
                          season=request.form['season'],
                          picture=request.form['picture'],
                          tvshow_id=tvshow_id, user_id=tvshow.user_id)
        session.add(episode)
        session.commit()
        flash('New Episode %s Successfully Created' % (episode.name))
        return redirect(url_for('showEpisodes', tvshow_id=tvshow_id))
    else:
        return render_template('newepisode.html', tvshow_id=tvshow_id)


# Edit an Episode
@app.route('/tvshows/<int:tvshow_id>/episodes/<int:episode_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editEpisode(tvshow_id, episode_id):

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    editedEpisode = session.query(Episode).filter_by(id=episode_id).one()
    tvshow = session.query(Tvshow).filter_by(id=tvshow_id).one()
    if login_session['user_id'] != tvshow.user_id:
        return "<script>function myFunction() {alert('You are not authorized" \
               " to edit episodes of this tvshow. Please " \
               "create your own tvshow in order to edit " \
               "episodes.');}</script><body onload='myFunction()''> "
    if request.method == 'POST':
        if request.form['name']:
            editedEpisode.name = request.form['name']
        if request.form['summary']:
            editedEpisode.description = request.form['summary']
        if request.form['season']:
            editedEpisode.price = request.form['season']
        if request.form['number']:
            editedEpisode.course = request.form['number']
        if request.form['picture']:
            editedEpisode.course = request.form['picture']
        session.commit()
        flash('episode Successfully Edited')
        return redirect(url_for('showEpisodes', tvshow_id=tvshow_id))
    else:
        return render_template('editepisode.html', tvshow_id=tvshow_id,
                               episode_id=episode_id, episode=editedEpisode)


# Delete an episode
@app.route('/tvshow/<int:tvshow_id>/episodes/<int:episode_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteEpisode(tvshow_id, episode_id):

    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    tvshow = session.query(Tvshow).filter_by(id=tvshow_id).one()
    episodeToDelete = session.query(Episode).filter_by(id=episode_id).one()
    if login_session['user_id'] != tvshow.user_id:
        return "<script>function myFunction() {alert('You are not authorized" \
               " to delete episodes from this tvshow. " \
               "Please create your own tvshow in order to delete " \
               "episodes.');}</script><body onload='myFunction()''> "
    if request.method == 'POST':
        session.delete(episodeToDelete)
        session.commit()
        flash('episode Successfully Deleted')
        return redirect(url_for('showEpisodes', tvshow_id=tvshow_id))
    else:
        return render_template('deleteepisode.html', episode=episodeToDelete)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: ' \
              '150px;-webkit-border-radius: ' \
              '150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=' \
          'fb_exchange_token&client_id=%s&client_secret=%s' \
          '&fb_exchange_token=%s' % (
              app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v4.0/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v4.0/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v4.0/me/picture?access_token=' \
          '%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius:' \
              ' 150px;-webkit-border-radius: ' \
              '150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
          % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]

    return "you have been logged out"


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showTvshows'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showTvshows'))


def verifyUser():
    if 'username' not in login_session:
        return redirect('/login')





def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    print(str(user_id))
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        print (e.args)
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
