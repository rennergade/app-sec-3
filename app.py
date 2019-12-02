import subprocess
from flask import Flask, render_template, request, redirect, session, url_for, escape
import hashlib
import bleach
import os
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from dbsetup import User, Log, Spell
from datetime import datetime



def create_app(config=None):
    app = Flask(__name__)
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spell.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.secret_key = os.urandom(16)

    db = SQLAlchemy(app)

    # using flask_wtf for csrf protection
    csrf = CSRFProtect(app)

    DICTFILE = "wordlist.txt"


    # app functions

    # hashing our passwords!
    def hashit(key):
        m = hashlib.sha256()
        m.update(key.encode())
        return m.digest()

    # and checking them too!
    def checkit(hash2compare, key):
        return hash2compare == hashit(key)

    def validate_login(username, password, auth):

        user = db.session.query(User).filter_by(username=username).first()

        # check if user exists
        if not user: return 1

        # differentiate via password and 2fa failure
        if not checkit(user.password, password): return 1

        if not checkit(user.twofa, auth): return 2

        return 0


    def register_login(username, password, auth):
        
        #check for user in db, 
        user = db.session.query(User).filter_by(username=username).first() 
        if user: 
            return 1


        # create new user with hashed passwords and auth
        newuser = User(username=username, password=hashit(password), twofa=hashit(auth))
        db.session.add(newuser)
        db.session.commit()    

        return 0

    def db_login(username):
        user = db.session.query(User).filter_by(username=username).first()
        
        if not user: 
            print("User not found")
            return -1

        newlog = Log(username=user.username, user_id=user.id)

        db.session.add(newlog)
        db.session.commit()   

        return 0

    def db_logout(username):
        user = db.session.query(User).filter_by(username=username).first()
        
        if not user: 
            print("User not found")
            return -1

        lastuserlog = db.session.query(Log).filter_by(username=username).order_by(Log.id.desc()).first()

        lastuserlog.logouttime = datetime.utcnow()

        db.session.commit()   

        return 0

    def db_spell(username, textout, misspelled):
        print(username)
        user = db.session.query(User).filter_by(username=username).first()
        
        if not user: 
            print("User not found")
            return -1

        newspell = Spell(username=user.username, subtext=textout, restext=misspelled, user_id=user.id)

        db.session.add(newspell)
        db.session.commit()   

        return 0
    
    # create and add admin
    def create_admin():
        username = "admin"
        password = "Administrator@1"
        auth = "12345678901"

        user = db.session.query(User).filter_by(username=username).first()

        # check if admin exists
        if user: return 1

        newuser = User(username=username, password=hashit(password), twofa=hashit(auth))
        db.session.add(newuser)
        db.session.commit()

    create_admin()


    # app routes

    @app.route("/")
    def home():
        loggedin = False
        username = ""
        if 'username' in session: 
            loggedin = True
            username = session['username']
        return render_template('home.html', loggedin=loggedin, username=username)

    @app.route("/register", methods=['POST', 'GET'])
    def register():
        success = None
        loggedin = False
        if 'username' in session: loggedin = True
        if request.method == 'POST':
            bleached_uname = bleach.clean(request.form['username'])
            bleached_pass = bleach.clean(request.form['password'])
            bleached_auth = bleach.clean(request.form['auth'])
        
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
        username = ""
        if 'username' in session: loggedin = True

        if request.method == 'POST':
            # bleach all input fileds to mediate XSS
            bleached_uname = bleach.clean(request.form['username'])
            bleached_pass = bleach.clean(request.form['password'])
            bleached_auth = bleach.clean(request.form['auth'])

            status = validate_login(bleached_uname, bleached_pass, bleached_auth)
            if status == 0:
                result = 'Success'
                session['username'] = bleached_uname
                username = bleached_uname
                app.logger.info('%s logged in successfully', bleached_uname)
                db_login(bleached_uname)
                loggedin = True
            elif status == 1:
                app.logger.error('%s log in failed', bleached_uname)
                result = 'Invalid username/password'
            elif status == 2:
                result = '2fa'
            else:
                result = 'System Error'

        return render_template('login.html', id=result, loggedin=loggedin, username=username)


    @app.route("/spell_check" , methods=['POST', 'GET'])
    def spell_check():
        loggedin=False
        # using flask 'session' for session hijacking
        if 'username' in session:
            loggedin = True
            textout = None
            misspelled = None
            username = session['username']

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

                db_spell(username, textout, str(misspelled))

                f.close()
                os.remove(textfile)
            
                return render_template('spell_check.html', textout=textout, misspelled=misspelled, loggedin=loggedin, username=username)
            
            
            return render_template('spell_check.html', loggedin=loggedin, username=username)


        return redirect('/login')

    @app.route('/<username>/history' , methods=['POST', 'GET'])
    def query_history(username):
        loggedin=False
        admin=False
        # using flask 'session' for session hijacking
        if username == session['username']:
            loggedin = True
            
            if session['username'] == 'admin':
                admin=True
                if request.method == 'POST':
                    # bleach all input fileds to mediate XSS
                    bleached_query = bleach.clean(request.form['userquery'])
                    history = db.session.query(Spell).filter_by(username=bleached_query).all()

                else: history = db.session.query(Spell).all()
                numqueries = len(history)
                return render_template('history.html', history=history, numqueries=numqueries, loggedin=loggedin, username=session['username'], admin=admin)

            history = db.session.query(Spell).filter_by(username=username).all()
            numqueries = len(history)


            return render_template('history.html', history=history, numqueries=numqueries, loggedin=loggedin, username=session['username'], admin=admin)
        
        return redirect('/login')




    @app.route('/<username>/login_history' , methods=['POST', 'GET'])
    def login_history(username):
        loggedin=False
        admin=False
        # using flask 'session' for session hijacking
        if session['username'] == 'admin':
            loggedin = True 
            admin=True
            if request.method == 'POST':
                # bleach all input fileds to mediate XSS
                bleached_query = bleach.clean(request.form['userid'])
                logins = db.session.query(Log).filter_by(username=bleached_query).all()

            else: logins = db.session.query(Log).all()
            return render_template('login_history.html', logins=logins, loggedin=loggedin, username=session['username'], admin=admin)


        return redirect('/login')



    @app.route('/<username>/history/query<int:id>')
    def query(username, id):
        loggedin=False
        # using flask 'session' for session hijacking
        if session['username'] == username or session['username'] == 'admin':
            loggedin = True

            query = db.session.query(Spell).filter_by(username=username, id=id).first()

            return render_template('query.html', query=query, loggedin=loggedin, username=session['username'])

        return redirect('/login')



            
    @app.route('/logout')
    def logout():
        username = session.pop('username', None)
        app.logger.info('user logged out')
        db_logout(username)

        return render_template('home.html')


    return app
    
if __name__ == "__main__":
    app.create_app()