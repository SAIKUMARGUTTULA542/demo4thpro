from flask import Flask, render_template, request,flash, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, dept, students
import random, string
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from flask import make_response

app = Flask(__name__)
CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
APPLICATION_NAME = "Dept"
engine = create_engine('sqlite:///deptmenu.db',connect_args={'check_same_thread':False},echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()



#creating login session
@app.route('/login')
def showlogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',STATE=state)
    #return "the current session state is %s"%login_session['state']

#creating gconnect
@app.route('/gconnect',methods=['POST'])
def gconnect():
        if request.args.get('state') != login_session['state']:
            response = make_response(json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return responseh
    
        code = request.data
        try:
            ''' Upgrade the authorization code into a credentials object'''
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(
                json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        ''' Check that the access token is valid.'''
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        ''' If there was an error in the access token info, abort.'''
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'
            return response

        ''' Verify that the access token is used for the intended user.'''
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        ''' Verify that the access token is valid for this app.'''
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps("Token's client ID does not match app's."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        stored_access_token = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')
        if stored_access_token is not None and gplus_id == stored_gplus_id:
            response = make_response(json.dumps('Current user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response
            print "done!"
        ''' Store the access token in the session for later use.'''
        login_session['access_token'] = credentials.access_token
        login_session['gplus_id'] = gplus_id
        ''' Get user info'''
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)
        data = json.loads(answer.text)
        #data = answer.json()

        login_session['username'] = data['name']
        #login_session['picture'] = data['picture']
        login_session['email'] = data['email']
        # see if user exit,if not create new user
        user_id = getUserID(login_session['email'])
        if not user_id:
            user_id = createUser(login_session)
        login_session['user_id'] = user_id
        output = ''
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        flash("you are now logged in as %s" % login_session['username'])
        print "done!"
        return output
#creating new user
def createUser(login_session):
    newUser = User(name=login_session['username'],email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

#getting user info
def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

# getting user ID
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None




@app.route('/dept/<int:dept_id>/JSON')
def deptJSON(dept_id):
    dept = session.query(dept).filter_by(id=dept_id).one()
    students = session.query(students).filter_by(
        dept_id=dept_id).all()
    return jsonify(students=[i.serialize for i in students])


@app.route('/dept/<int:dept_id>/students/<int:stdid>/JSON')
def studentsJSON(dept_id, stdid):
    students = session.query(students).filter_by(id=stdid).one()
    return jsonify(students=students.serialize)

 
@app.route('/dept/JSON')
def deptsJSON():
    dept = session.query(dept).all()
    return jsonify(dept=[d.serialize for d in dept])


# Show all depts2
@app.route('/')

@app.route('/dept/')
def showdept():
    d = session.query(dept)
    return render_template('dept.html', dept=d)


# Create a new dept
@app.route('/dept/new/', methods=['GET', 'POST'])
def newdept():
    if request.method == 'POST':
        newdept = dept(Deptname=request.form['name'])
        print (newdept)
        session.add(newdept)
        session.commit()
        return redirect(url_for('showdept'))
    else:
        return render_template('newdept.html')
    # return "This page will be for making a new dept"

# Edit a dept


@app.route('/dept/<int:dept_id>/edit/', methods=['GET', 'POST'])
def editdept(dept_id):
    editeddept = session.query(
        dept).filter_by(dept_id=dept_id).one()
   # edit = session.query(
       # dept).filter_by(dept_id=dept_id).one()
    

    if request.method == 'POST':
        if request.form['name']:
            editeddept.Deptname = request.form['name']
            return redirect(url_for('showdept'))
    else:
        return render_template(
            'editdept.html', dept=editeddept)

    # return 'This page will be for editing dept %s' % dept_id

# Delete a dept


@app.route('/dept/<int:dept_id>/delete/', methods=['GET', 'POST'])
def deletedept(dept_id):
    deptToDelete = session.query(
        dept).filter_by(dept_id=dept_id).one()
    if request.method == 'POST':
        session.delete(deptToDelete)
        session.commit()
        return redirect(url_for('showdept'))
    else:
        return render_template(
            'deldept.html', d=deptToDelete)
    # return 'This page will be for deleting restaurant %s' % restaurant_id


# Show a deppt students
@app.route('/dept/<int:dept_id>/')
@app.route('/dept/<int:dept_id>/students/')
def showstudents(dept_id):
    depts = session.query(dept).filter_by(dept_id=dept_id).one()
    student = session.query(students).filter_by(
        dept_id=dept_id).all()
    return render_template('students.html', s=student, d=depts)
    # return 'This page is the students for dept %s' % dept_id

# Create a new menu item


@app.route(
    '/dept/<int:dept_id>/students/new/', methods=['GET', 'POST'])
def newstudents(dept_id):
    if request.method == 'POST':
        newstudents = students(name=request.form['name'], dept_id=dept_id)
        session.add(newstudents)
        session.commit()

        return redirect(url_for('showstudents', dept_id=dept_id))
    else:
        return render_template('newstudents.html', dept_id=dept_id)

    
   


@app.route('/dept/<int:dept_id>/<int:stdid>/edit',
           methods=['GET', 'POST'])
def editstudent(dept_id, stdid):
    editedstudent = session.query(students).filter_by(stdid=stdid).one()
    if request.method == 'POST':
        if request.form['name']:
            editedstudent.name = request.form['name']
      
        session.add(editedstudent)
        session.commit()
        return redirect(url_for('showstudents', dept_id=dept_id))
    else:

        return render_template(
            'editstudents.html', dept_id=dept_id, s=stdid, student=editedstudent)

  


@app.route('/dept/<int:dept_id>/students/<int:stdid>/delete',
           methods=['GET', 'POST'])
def deletestudent(dept_id, stdid):
    studentToDelete = session.query(students).filter_by(stdid=stdid).one()
    if request.method == 'POST':
        session.delete(studentToDelete)
        session.commit()
        return redirect(url_for('showstudents', dept_id=dept_id))
    else:
        return render_template('delstudents.html',s=stdid,st=studentToDelete)
  

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host='localhost', port=5050)
