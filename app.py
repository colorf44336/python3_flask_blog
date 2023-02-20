from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json 
from flask_mail import Mail,Message
from wtforms import Form,StringField,validators
import wtforms.fields as h5fields
import wtforms.widgets  as h5widgets
from werkzeug.utils import secure_filename
import os
import math
with open('config.json','r') as file:
    params=json.load(file)['params']
    
local_server=True
app= Flask(__name__)
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER ='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
    
)
mail=Mail(app)
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else :
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
    
# db=SQLAlchemy(app)
db=SQLAlchemy(app)
# migrate = Migrate(app, db)
app.secret_key='super secret key'
class contactform(Form):
    name=StringField("name",validators=[validators.InputRequired(),validators.Length(min=4,max=150)])
    email=StringField("email",validators=[validators.InputRequired()])
    phone=h5fields.IntegerField("phone",validators=[validators.InputRequired()],widget=h5widgets.NumberInput(min=6000000000,max=10000000000))
    msg=StringField("msg",validators=[validators.InputRequired()])
    
    
class contacts(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20),unique=True,nullable=False)
    phone = db.Column(db.String(12), unique=True, nullable=False)
    message = db.Column(db.String(500),  nullable=False)
    date = db.Column(db.String,  nullable=False)
    
class Posts(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    tagline = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(20),unique=True,nullable=False)
    content = db.Column(db.String(500), unique=True, nullable=False)
    img = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String,  nullable=False)
    
@app.route('/')
def home():
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_post']))
    
    page=request.args.get('page')
    if (not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post'])+int(params['no_of_post'])]
    if (page==1):
        prev="#"
        next="/?page=" +str(page+1)
        
    elif(page==last):
        
        prev="/?page=" +str(page-1)
        next="#"
      
    else:
        prev="/?page=" +str(page-1)
        next="/?page=" +str(page+1)
          
    
    # posts=Posts.query.filter_by().all()[0:params["no_of_post"]]
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)

@app.route('/about')
def about():
    post=Posts.query.filter_by().first()
    return render_template('about.html',params=params,post=post)

@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user']== params['admin_user']:
        posts=Posts.query.filter_by().all()  
        return render_template('dashboard.html',params=params,posts=posts)
    elif request.method=='POST':
        username=request.form.get('uname')
        password=request.form.get('pass')
        if(username==params['admin_user'] and password==params['admin_password']):
            session['user']=username  
            posts=Posts.query.filter_by().all()  
            return render_template('dashboard.html',params=params,posts=posts)
    
    return render_template('login.html',params=params)
        


@app.route('/edit/<string:sr_no>',methods=['GET','POST'])
def post_edit(sr_no):
    
    if 'user' in session and session['user']== params['admin_user']:
        
        if request.method=='POST':
           
            req_title=request.form.get('title')
            req_tagline=request.form.get('tagline')
            req_slug=request.form.get('slug')
            req_img=request.form.get('img_file')
            req_content=request.form.get('content')
            req_date=datetime.now()
            
            # print("ok")
            if sr_no=='0':
               
                post=Posts(title=req_title,tagline=req_tagline,slug=req_slug,content=req_content,img=req_img,date=req_date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sr_no=sr_no).first()
                post.title=req_title
                post.tagline=req_tagline
                post.slug=req_slug
                post.img=req_img
                post.content=req_content
                post.date=req_date
                db.session.commit()
                return redirect('/edit/'+sr_no)

    post=Posts.query.filter_by(sr_no=sr_no).first()
    return render_template('edit.html',params=params,post=post,sr_no=sr_no)

@app.route('/post/<string:post_slug>',methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route('/contact',methods=['GET','POST'])
def contact():
    post=Posts.query.filter_by().first()
    form=contactform(request.form)
    if request.method=='POST' and form.validate():
        if not form.name.data[0].isalpha():
            form.name.errors.append("The name should start with alphbet")
        # elif not form.phone.data.isnum():
        #     form.phone.errors.append("the phone number should be in digit")
        '''add entry to the database'''
        uname=request.form.get('name')
        uemail=request.form.get('email')
        uphone=request.form.get('phone')
        umsg=request.form.get('msg')
        udate=datetime.now()
        
        entry=contacts(name=uname,email=uemail,phone=uphone,message=umsg,date=udate)
        db.session.add(entry)
        db.session.commit()
        
        # msg=Message('new message from website'+ uname,
        #                   sender=uemail,
        #                   recipients=[params['gmail-user']],
        #                   body=f"name={uname}\nemail={uemail}\nphone_number={uphone}\nmessage={umsg}\ndate={udate}"
        #                   )
    
        msg=Message('a messgae from the website',sender=request.form.get('email'),recipients=[params['gmail-user']])
        msg.body=f"name={uname}\nemail={uemail}\nphone_number={uphone}\nmessage={umsg}\ndate={udate}"
        mail.send(msg)
        

    return render_template('contact.html',params=params,form=form,post=post)


@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if request.method=='POST':
        f=request.files['file1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
    return "uploaded successfully "
        
@app.route('/logout',methods=['GET','POST'])
def logout():
    session.pop('user')
    return redirect('/dashboard')
    
      
@app.route("/delete/<string:sr_no>",methods=['GET','POST'])
def delete_d(sr_no):
    print("ok")
    if 'user' in session and session['user']== params['admin_user']:
        print("ok ok ")
        post=Posts.query.filter_by(sr_no=sr_no).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')
    
app.run(debug=True)