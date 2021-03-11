#!/usr/bin/env python

# configuration
S3_BUCKET_NAME = "REPLACE-WITH-YOUR-BUCKET"
SITE_NAME = "EXAMPLE SITE"
AUTHOR_INFO = {'name': 'YOUR NAME HERE', 'email': 'YOUR_EMAIL@EXAMPLE.COM'}
FEED_LANGUAGE = 'en'
SITE_URL = "https://EXAMPLE.COM"

import sys
import os
import pathlib
import datetime

from dateutil.parser import parse
from dateutil.tz import tzutc
from feedgen.feed import FeedGenerator
import jinja2
import yaml


def main():
    allowed_args = ["help", "init", "deploy", "generate", "serve"]
    if len(sys.argv) != 2:
        print(help_message)
        sys.exit(0)
    elif sys.argv[1] not in allowed_args:
        print(help_message)

    command = sys.argv[1]
    if command == "help":
        print(help_message)
    elif command == "init":
        init()
    elif command == "deploy":
        deploy()
    elif command == "generate":
        generate()
    elif command == "serve":
        generate()
        serve()

def init():
    os.system("npm install -D tailwindcss@latest postcss@latest autoprefixer@latest")

    for d in ["static", "static/css", "static/js", "site", "site/posts", "site/feed",
    "posts", "templates"]:
        if not os.path.isdir(d):
            os.mkdir(d)

    if not os.path.isfile("static/css/main.css"):
        with open("static/css/main.css", "w") as f:
            f.write(tailwind_css)
    if not os.path.isfile("tailwind.config.js"):
        with open("tailwind.config.js", "w") as f:
            f.write(tailwind_config)
    if not os.path.isfile("postcss.config.js"):
        with open("postcss.config.js", "w") as f:
            f.write(postcss_config)
    if not os.path.isfile("templates/home.html"):
        with open("templates/home.html", "w") as f:
            f.write(home_template)
    if not os.path.isfile("templates/post.html"):
        with open("templates/post.html", "w") as f:
            f.write(post_template)

def deploy():
    generate(True)
    print("Uploading site...")
    os.system(f"aws s3 sync site s3://{S3_BUCKET_NAME}")

def generate(prod=False):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    post_template = env.get_template('post.html')
    home_template = env.get_template('home.html')

    print("Processing posts...")
    posts = []
    for entry in os.scandir("posts"):
        if entry.is_dir():
            with open(entry.path + '/index.html', 'r') as f:
                data = f.read()

            head, body = data.split("---")
            headers = yaml.load(head, Loader=yaml.FullLoader)

            post_data = {
                'site_title': SITE_NAME,
                'url': entry.path,
                'title': headers['title'],
                'date': headers['date'],
                'body': body
            }
            posts.append(post_data)

            finished_post = post_template.render(post_data)
            os.makedirs("site/" + entry.path, exist_ok=True)
            with open("site/" + entry.path + "/index.html", 'w') as f:
                f.write(finished_post)

    sorted_posts = sorted(posts, key = lambda k: parse(k['date']), reverse=True)

    print("Compiling home page...")
    home_data = {
        'site_title': SITE_NAME,
        'posts': sorted_posts
    }
    finished_homepage = home_template.render(home_data)
    with open("site/index.html", 'w') as f:
        f.write(finished_homepage)

    print("Compiling Atom feed...")
    feed = create_feed(sorted_posts)
    with open("site/feed/index.html", 'w') as f:
        f.write(feed)

    print("Copying static files...")
    os.system('rsync -avr --exclude=css/* static/ site')

    print("Generating CSS...")
    if prod:
        os.system("NODE_ENV=production postcss static/css/main.css -o site/css/main.css")
    else:
        if not os.path.isfile('./site/css/main.css') or aNewerThanB('./static/css/main.css', './site/css/main.css'):
            os.system("postcss static/css/main.css -o site/css/main.css")
        else:
            print("\tNot generating CSS. Generated CSS already up to date")

def create_feed(posts):
    fg = FeedGenerator()
    fg.id(SITE_URL)
    fg.title(SITE_NAME)
    fg.author(AUTHOR_INFO)
    fg.link(href=SITE_URL, rel='alternate')
    fg.link(href=SITE_URL + '/feed/', rel='self')
    fg.language(FEED_LANGUAGE)

    for i in range(min(10, len(posts))):
        post = posts[i]
        fe = fg.add_entry()
        fe.id(fg.id() + '/' + post['url'])
        fe.title(post['title'])
        fe.link(href=fe.id())
        fe.published(parse(post['date']).replace(tzinfo=tzutc()))

    return fg.atom_str(pretty=True).decode('utf-8')

def serve():
    os.system("python -m http.server -d site")

def aNewerThanB(fileA, fileB):
    file_A_fname = pathlib.Path(fileA)
    file_A_mtime = datetime.datetime.fromtimestamp(file_A_fname.stat().st_mtime)
    file_B_fname = pathlib.Path(fileB)
    file_B_mtime = datetime.datetime.fromtimestamp(file_B_fname.stat().st_mtime)
    return file_A_mtime > file_B_mtime

home_template = """
<!doctype html>
<html>
<head>
  <title>{{site_title}}</title>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link href="/css/main.css" rel="stylesheet">
</head>
<body>
<h1>{{site_title}}</h1>
<hr>

<div>
  {% for post in posts %}
  <div>
    <div><a href="/{{post.url}}">{{post.title}}</a></div>
    <div>{{post.date}}</div>
  </div>
  {% endfor %}
</div>

</body>
</html>
"""
post_template = """
<!doctype html>
<html>
<head>
  <title>{{title}} | {{site_title}}</title>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link href="/css/main.css" rel="stylesheet">
</head>
<body>
<h1>{{title}}</h1>
<h2>{{date}}</h2>
{{content}}
</body>
</html>
"""

postcss_config = """
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  }
}
"""

tailwind_config = """
module.exports = {
  purge: [
    './site/**/*.html',
    './site/**/*.js',
  ],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {},
  plugins: [],
}
"""

tailwind_css = """
@tailwind base;
@tailwind components;
@tailwind utilities;
"""

help_message = """s4gen usage:
\ts4gen command

AVAILABLE COMMANDS
\thelp\t\t display this message
\tinit\t\t initialize static site directory
\tdeploy\t\t generate site files and publish site to s3
\tgenerate\t generate site files (without deploying)
\tserve\t\t serve site files locally to preview site
"""

if __name__ == "__main__":
    main()
