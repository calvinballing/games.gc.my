from app import app, db
from flask import render_template, flash, redirect, jsonify
from flask_oauth2_login import GoogleLogin
from math import floor
from .forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.hanabi import hanabi_games, HanabiGame

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(floor(n/10)%10!=1)*(n%10<4)*n%10::4])
google_login = GoogleLogin(app)
print('starting views...')

@app.errorhandler(404)
def page_not_found(e):
    print(e)
    return render_template('404.html'), 404

@app.errorhandler(401)
def not_authorized(e):
    return redirect('/login')

@app.route("/")
@app.route("/index")
@app.route("/pagecount")
def pagecount():
    messages = [
        'Peanut butter is delicious with oatmeal',
        'Raisins are too',
    ]
    if current_user.is_anonymous:
        message = 'Hello person! You should log in to see the awesome pageview counting facilities of this page!'
    else:
        current_user.pagecount+=1
        db.session.commit()
        messages.append( str(current_user.pagecount**2-1)+' is a cool nuber')
        message = 'You have visited this page {} times!'.format(current_user.pagecount)
    return render_template('pagecount.html', title='Pagecount', message=message,  messages=messages)

@app.route('/hanabisample')
@login_required
def hanabisample():
    return render_template('hanabisample.html', title='Hanabi Sample Board', socketio_namespace='/hanabisample')

@app.route('/hanabi/<player_num>/<gameid>')
@login_required
def hanabi(player_num, gameid):
    print("{} is requesting to join hanabi gameid {}".format(current_user.fullname, gameid))
    gameid = str(gameid)
    # If the game doesn't already exist, create it!
    if not gameid in hanabi_games:
        hanabi_games[gameid] = HanabiGame(int(player_num), gameid)
        print("Created gameid {}".format(gameid))
    # See if we are already in the player list
    game = hanabi_games[gameid]
    if current_user in game.players:
        print("Player is returning")
    # Otherwise, see if it can take more players
    elif (len(game.players) < game.player_count):
        print("Player is new")
        index = len(game.players)
        current_user.tmp[gameid] = {'player_index':index}
        game.players.append(current_user)
    else:
        return "The game {} already has {} players".format(gameid, game.player_count)

    print("Taking {} player index".format(current_user.tmp[gameid]['player_index'])) #Put the user into the game room
    return render_template(
            'hanabi.html', 
            title='Hanabi Board', 
            socketio_namespace='/hanabi',
            player_index=current_user.tmp[gameid]['player_index'],
            player_count=game.player_count,
            hand_size=game.hand_size,
            letters=HanabiGame.letters,
            gameid=gameid,
            )

#########
# Login #
#########
@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect('/index')
    return """<html><a href="{}">Login with Google</a>""".format(google_login.authorization_url())

@google_login.login_success
def login_success(token, profile):
    user = User.query.filter_by(email=profile['email']).first()
    print(user)
    # If there is not an entry for the user, create one
    if user is None:
        user = User(email=profile['email'], fullname=profile['name'])
        db.session.add(user)
        db.session.commit()
        message = 'Created and logged in user {}'.format(profile['name'])
    else:
        message = 'Login successful for {}'.format(profile['name'])
    login_user(user) #TODO add remember me option
    print(message)
    flash(message)
    return redirect('/index')
    #return jsonify(token=token, profile=profile)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/index')