
from flask import Flask, request, redirect, session, render_template_string, send_from_directory
import sqlite3, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

DB = "blog.db"
UPLOAD_FOLDER = "uploads"
PROFILE_FOLDER = "profile_pics"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS posts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    image TEXT,
    author TEXT,
    created TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS comments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    user TEXT,
    comment TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS likes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    user TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS follow(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower TEXT,
    following TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS profile(
    username TEXT PRIMARY KEY,
    photo TEXT,
    description TEXT,
    school TEXT,
    college TEXT,
    degree TEXT,
    dob TEXT,
    address TEXT)""")

    conn.commit()
    conn.close()

init_db()

# ---------------- CSS ----------------

STYLE = """
<style>
body{
margin:0;
font-family:Arial;
background:linear-gradient(135deg,#667eea,#764ba2);
color:white;
animation:fade 0.6s;
}
@keyframes fade{
from{opacity:0}
to{opacity:1}
}
.container{width:80%;margin:auto;padding:30px;}
.card{
background:white;color:black;border-radius:12px;
padding:20px;margin:20px 0;
box-shadow:0 8px 20px rgba(0,0,0,0.3);
transition:0.3s;}
.card:hover{transform:scale(1.03);}
button{
background:linear-gradient(45deg,#ff6a00,#ee0979);
border:none;padding:10px 20px;color:white;
border-radius:8px;font-weight:bold;cursor:pointer;
transition:0.3s;}
button:hover{
transform:scale(1.1);
background:linear-gradient(45deg,#36d1dc,#5b86e5);}
input,textarea{
width:100%;padding:10px;margin:10px 0;border-radius:8px;border:none;}
.nav{
background:linear-gradient(90deg,#ff6a00,#ee0979);
padding:15px;}
.nav a{
color:white;margin-right:15px;font-weight:bold;text-decoration:none;}
.blog-img{width:100%;border-radius:10px;margin-top:10px;}
</style>
"""

# ---------------- NAVBAR ----------------

NAV = """
<div class='nav'>
<a href='/'>Home</a>

{% if session.get('user') %}
<a href='/dashboard'>Dashboard</a>
<a href='/create'>Create Blog</a>
<a href='/profile'>Profile</a>
<a href='/logout'>Logout</a>
{% else %}
<a href='/login'>Login</a>
<a href='/register'>Register</a>
{% endif %}
</div>
"""

# ---------------- HOME ----------------

@app.route("/",methods=["GET","POST"])
def home():

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    search=request.form.get("search")

    if search:
        c.execute("SELECT * FROM posts WHERE title LIKE ?",('%'+search+'%',))
    else:
        c.execute("SELECT * FROM posts ORDER BY id DESC")

    posts=c.fetchall()
    conn.close()

    return render_template_string(STYLE+NAV+"""

<div class='container'>

<h1>Blog Platform</h1>

<form method='post'>
<input name='search' placeholder='Search blog'>
<button>Search</button>
</form>

{% for p in posts %}

<div class='card'>

<h2>{{p[1]}}</h2>

{% if p[3] %}
<img src="/uploads/{{p[3]}}" class="blog-img">
{% endif %}

<p>{{p[2][:200]}}</p>

<a href='/post/{{p[0]}}'><button>Read</button></a>

</div>

{% endfor %}

</div>
""",posts=posts)

# ---------------- REGISTER ----------------

@app.route("/register",methods=["GET","POST"])
def register():

    if request.method=="POST":
        user=request.form["username"]
        pw=generate_password_hash(request.form["password"])

        conn=sqlite3.connect(DB)
        c=conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?)",(user,pw))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template_string(STYLE+NAV+"""
<div class='container'>
<h2>Register</h2>
<form method='post'>
<input name='username'>
<input type='password' name='password'>
<button>Register</button>
</form>
</div>
""")

# ---------------- LOGIN ----------------

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        user=request.form["username"]
        pw=request.form["password"]

        conn=sqlite3.connect(DB)
        c=conn.cursor()

        c.execute("SELECT password FROM users WHERE username=?",(user,))
        data=c.fetchone()

        conn.close()

        if data and check_password_hash(data[0],pw):
            session["user"]=user
            return redirect("/")

    return render_template_string(STYLE+NAV+"""
<div class='container'>
<h2>Login</h2>
<form method='post'>
<input name='username'>
<input type='password' name='password'>
<button>Login</button>
</form>
</div>
""")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute("SELECT * FROM posts WHERE author=?", (session["user"],))
    posts=c.fetchall()

    conn.close()

    return render_template_string(STYLE+NAV+"""

<div class='container'>

<h2>Dashboard</h2>

<a href="/create"><button>Create Blog</button></a>

{% for p in posts %}

<div class='card'>

<h3>{{p[1]}}</h3>

{% if p[3] %}
<img src="/uploads/{{p[3]}}" class="blog-img">
{% endif %}

<p>{{p[2][:150]}}</p>

<a href="/post/{{p[0]}}"><button>View</button></a>

</div>

{% endfor %}

</div>
""",posts=posts)

# ---------------- CREATE BLOG ----------------

@app.route("/create",methods=["GET","POST"])
def create():

    if "user" not in session:
        return redirect("/login")

    if request.method=="POST":

        title=request.form["title"]
        desc=request.form["description"]

        file=request.files["image"]
        filename=secure_filename(file.filename)

        if filename:
            file.save(os.path.join(UPLOAD_FOLDER,filename))

        conn=sqlite3.connect(DB)
        c=conn.cursor()

        c.execute("""INSERT INTO posts
        (title,description,image,author,created)
        VALUES (?,?,?,?,?)""",
        (title,desc,filename,session["user"],datetime.now()))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template_string(STYLE+NAV+"""
<div class='container'>
<h2>Create Blog</h2>
<form method='post' enctype='multipart/form-data'>
<input name='title' placeholder='Title'>
<textarea name='description' placeholder='Description'></textarea>
<input type='file' name='image'>
<button>Publish</button>
</form>
</div>
""")

# ---------------- VIEW POST ----------------

@app.route("/post/<int:id>",methods=["GET","POST"])
def post(id):

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    if request.method=="POST":

        comment=request.form["comment"]

        if "user" in session:
            c.execute("INSERT INTO comments(post_id,user,comment) VALUES (?,?,?)",
            (id,session["user"],comment))
            conn.commit()

    c.execute("SELECT * FROM posts WHERE id=?", (id,))
    post=c.fetchone()

    c.execute("SELECT * FROM comments WHERE post_id=?", (id,))
    comments=c.fetchall()

    conn.close()

    return render_template_string(STYLE+NAV+"""

<div class='container'>

<div class='card'>

<h2>{{post[1]}}</h2>

{% if post[3] %}
<img src="/uploads/{{post[3]}}" class="blog-img">
{% endif %}

<p>{{post[2]}}</p>

<a href="/like/{{post[0]}}"><button>❤️ Like</button></a>
<a href="/follow/{{post[4]}}"><button>Follow {{post[4]}}</button></a>

</div>

<h3>Comments</h3>

{% for c in comments %}

<div class='card'>
<b>{{c[2]}}</b>
<p>{{c[3]}}</p>
</div>

{% endfor %}

{% if session.get('user') %}

<form method='post'>
<textarea name='comment'></textarea>
<button>Add Comment</button>
</form>

{% endif %}

</div>
""",post=post,comments=comments)

# ---------------- LIKE ----------------

@app.route("/like/<int:id>")
def like(id):

    if "user" not in session:
        return redirect("/login")

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute("INSERT INTO likes(post_id,user) VALUES (?,?)",(id,session["user"]))
    conn.commit()
    conn.close()

    return redirect("/post/"+str(id))

# ---------------- FOLLOW ----------------

@app.route("/follow/<author>")
def follow(author):

    if "user" not in session:
        return redirect("/login")

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute("INSERT INTO follow(follower,following) VALUES (?,?)",
    (session["user"],author))

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- PROFILE ----------------

@app.route("/profile",methods=["GET","POST"])
def profile():

    if "user" not in session:
        return redirect("/login")

    conn=sqlite3.connect(DB)
    c=conn.cursor()

    if request.method=="POST":

        desc=request.form["desc"]
        school=request.form["school"]
        college=request.form["college"]
        degree=request.form["degree"]
        dob=request.form["dob"]
        address=request.form["address"]

        photo=request.files["photo"]
        filename=secure_filename(photo.filename)

        if filename:
            photo.save(os.path.join(PROFILE_FOLDER,filename))

        c.execute("""INSERT OR REPLACE INTO profile
        VALUES (?,?,?,?,?,?,?,?)""",
        (session["user"],filename,desc,school,college,degree,dob,address))

        conn.commit()

    c.execute("SELECT * FROM profile WHERE username=?", (session["user"],))
    data=c.fetchone()

    conn.close()

    return render_template_string(STYLE+NAV+"""

<div class='container'>

<h2>Profile</h2>

{% if data %}
<div class='card'>
{% if data[1] %}
<img src="/profile_pic/{{data[1]}}" width="120">
{% endif %}
<p>{{data[2]}}</p>
<p>{{data[3]}}</p>
<p>{{data[4]}}</p>
<p>{{data[5]}}</p>
<p>{{data[6]}}</p>
<p>{{data[7]}}</p>
</div>
{% endif %}

<form method='post' enctype='multipart/form-data'>

<input type='file' name='photo'>
<textarea name='desc' placeholder='Description'></textarea>
<input name='school' placeholder='School'>
<input name='college' placeholder='College'>
<input name='degree' placeholder='Degree'>
<input type='date' name='dob'>
<input name='address' placeholder='Address'>

<button>Save Profile</button>

</form>

</div>
""",data=data)

# ---------------- IMAGE ROUTES ----------------

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/profile_pic/<filename>')
def profile_pic(filename):
    return send_from_directory(PROFILE_FOLDER, filename)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

import os

if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )