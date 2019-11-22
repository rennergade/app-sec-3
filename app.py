import subprocess
from flask import Flask, render_template, request, redirect, session, url_for, escape
import hashlib
import bleach
import os
from flask_wtf.csrf import CSRFProtect

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dbsetup import Base, User, Log, Spell


def create_app(config=None):
    app = Flask(__name__)
    app.debug = True

    app.secret_key = os.urandom(16)

    engine = create_engine('sqlite:///spell.db')
    Base.metadata.bind = engine

    DBSession = scoped_session(sessionmaker(bind=engine))
    sqlsession = DBSession()

    # using flask_wtf for csrf protection
    csrf = CSRFProtect(app)

    DICTFILE = "wordlist.txt"



    # hashing our passwords!
    def hashit(key):
        m = hashlib.sha256()
        m.update(key.encode())
        return m.digest()

    # and checking them too!
    def checkit(hash2compare, key):
        return hash2compare == hashit(key)


    def validate_login(username, password, auth):

        user = sqlsession.query(User).filter_by(username=username).first()

        # check if user exists
        if not user: return 1

        # differentiate via password and 2fa failure
        if not checkit(user.password, password): return 1

        if not checkit(user.twofa, auth): return 2

        return 0


    def register_login(username, password, auth):
        
        #check for user in db, 
        user = sqlsession.query(User).filter_by(username=username).first() 
        if user: 
            return 1


        # create new user with hashed passwords and auth
        newuser = User(username=username, password=hashit(password), twofa=hashit(auth))
        sqlsession.add(newuser)
        sqlsession.commit()    

        return 0

    def db_login(username, logtype):
        user = sqlsession.query(User).filter_by(username=username).first()
        
        if not user: 
            print("User not found")
            return -1

        newlog = Log(username=user.username, logtype=logtype, user_id=user.id)

        sqlsession.add(newlog)
        sqlsession.commit()   

        return 0

    def db_spell(username, textout, misspelled):
        print(username)
        user = sqlsession.query(User).filter_by(username=username).first()
        
        if not user: 
            print("User not found")
            return -1

        newspell = Spell(username=user.username, subtext=textout, restext=misspelled, user_id=user.id)

        sqlsession.add(newspell)
        sqlsession.commit()   

        return 0
            



    @app.route("/")
    def home():
        print("home")
        loggedin = False
        if 'username' in session: loggedin = True
        return render_template('home.html', loggedin=loggedin)

    @app.route("/register", methods=['POST', 'GET'])
    def register():
        success = None
        loggedin = False
        if 'username' in session: loggedin = True
        if request.method == 'POST':
            bleached_uname = bleach.clean(request.form['username'])
            bleached_pass = bleach.clean(request.form['password'])
            bleached_auth = bleach.clean(request.form['username'])
        
            status = register_login(bleached_uname, bleached_pass, bleached_auth)
            if status == 0:
                app.logger.info('%s registered successfully', bleached_uname)
                success = 'Registration Success'
            elif status == 1:
                app.logger.error('%s registration failed', bleached_uname)
                success = 'Error Invalid Registration'
            else:
                success = 'System Error'
        
        return render_template('register.html', id=success, loggedin=loggedin)

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        result = None
        loggedin = False
        if 'username' in session: loggedin = True

        if request.method == 'POST':
            # bleach all input fileds to mediate XSS
            bleached_uname = bleach.clean(request.form['username'])
            bleached_pass = bleach.clean(request.form['password'])
            bleached_auth = bleach.clean(request.form['username'])

            status = validate_login(bleached_uname, bleached_pass, bleached_auth)
            if status == 0:
                result = 'Success'
                session['username'] = bleached_uname
                app.logger.info('%s logged in successfully', bleached_uname)
                db_login(bleached_uname, "in")
                loggedin = True
            elif status == 1:
                app.logger.error('%s log in failed', bleached_uname)
                result = 'Invalid username/password'
            elif status == 2:
                result = '2fa'
            else:
                result = 'System Error'

        return render_template('login.html', id=result, loggedin=loggedin)


    @app.route("/spell_check" , methods=['POST', 'GET'])
    def spell_check():
        loggedin=False
        # using flask 'session' for session hijacking
        if 'username' in session:
            loggedin = True
            textout = None
            misspelled = None

            if request.method == 'POST':
                textout = bleach.clean(request.form['inputtext'])
    
                # we've got to write the text to a file for the checker to work (takes file input)
                app.logger.info('attempting to spell check %s ', textout)

                textfile = 'textout.txt'
                with open(textfile, 'w+') as f:
                    f.write(textout)

                # this subprocess call is mostly from the assignment one autograder
                progout = subprocess.Popen(["./a.out", textfile, DICTFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                misspelled = progout.stdout.read().decode().strip().split('\n')

                db_spell(session['username'], textout, str(misspelled))

                f.close()
                os.remove(textfile)
            
                return render_template('spell_check.html', textout=textout, misspelled=misspelled, loggedin=loggedin)
            
            
            return render_template('spell_check.html', loggedin=loggedin)


        return redirect('/login')

            
    @app.route('/logout')
    def logout():
        username = session.pop('username', None)
        app.logger.info('user logged out')
        db_login(username, "out")

        return render_template('home.html')


    return app
    
if __name__ == "__main__":
    app.create_app()