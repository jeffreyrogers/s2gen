#!/usr/bin/env python

# configuration
SITE_NAME = "EXAMPLE SITE"
AUTHOR_INFO = {'name': 'YOUR NAME HERE', 'email': 'YOUR_EMAIL@EXAMPLE.COM'}
FEED_LANGUAGE = 'en'
SITE_URL = "https://EXAMPLE.COM"
IMG_URL = "https://EXAMPLE.COM/favicon.ico"

import sys
import os
import pathlib
import datetime

from bs4 import BeautifulSoup
from dateutil.parser import parse
from dateutil.tz import tzutc
from feedgen.feed import FeedGenerator
import jinja2
import yaml


def main():
    allowed_args = ["help", "init", "release", "generate", "serve", "newpost"]
    if len(sys.argv) < 2:
        print(help_message)
        sys.exit(0)
    elif sys.argv[1] not in allowed_args:
        print(help_message)

    command = sys.argv[1]
    if command == "help":
        print(help_message)
    elif command == "init":
        init()
    elif command == "release":
        init()
        generate(True)
    elif command == "generate":
        generate()
    elif command == "serve":
        generate()
        serve()
    elif command == "newpost":
        if len(sys.argv) != 3:
            print(help_message)
        else:
            newPost(sys.argv[2])
    else:
        print(help_message)

def init():
    os.system("npm install -D tailwindcss@latest postcss@latest postcss-cli autoprefixer@latest")

    for d in ["static", "static/css", "static/js", "site", "site/posts", "posts", "templates"]:
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

            parsed_date = parse(headers['date'])
            if 'draft' in headers:
                draft = headers['draft']
            else:
                draft = False
            if 'footnotes' in headers:
                footnotes = headers['footnotes']
            else:
                footnotes = False

            # skip draft posts when building production version of site
            if prod and draft:
                continue

            post_data = {
                'site_title': SITE_NAME,
                'url': entry.path,
                'title': headers['title'],
                'formatted_date': parsed_date.strftime('%b %d, %Y'),
                'date': parsed_date,
                'content': body,
                'draft': draft,
                'footnotes': footnotes
            }
            posts.append(post_data)

            finished_post = post_template.render(post_data)
            os.makedirs("site/" + entry.path, exist_ok=True)
            with open("site/" + entry.path + "/index.html", 'w') as f:
                f.write(finished_post)

    sorted_posts = sorted(posts, key = lambda k: k['date'], reverse=True)

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
    with open("site/feed.atom", 'w') as f:
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
    fg.link(href=SITE_URL + '/feed.atom', rel='self')
    fg.language(FEED_LANGUAGE)
    fg.image(url=IMG_URL)

    for i in range(min(10, len(posts))):
        post = posts[i]
        content = makeAtomContent(post['content'])
        fe = fg.add_entry()
        fe.id(fg.id() + '/' + post['url'])
        fe.title(post['title'])
        fe.link(href=fe.id())
        fe.published(post['date'].replace(tzinfo=tzutc()))
        fe.content(content, type="CDATA")

    return fg.atom_str(pretty=True).decode('utf-8')

def serve():
    os.system("python -m http.server -d site")

def aNewerThanB(fileA, fileB):
    file_A_fname = pathlib.Path(fileA)
    file_A_mtime = datetime.datetime.fromtimestamp(file_A_fname.stat().st_mtime)
    file_B_fname = pathlib.Path(fileB)
    file_B_mtime = datetime.datetime.fromtimestamp(file_B_fname.stat().st_mtime)
    return file_A_mtime > file_B_mtime

def newPost(url):
    os.mkdir('posts/' + url)
    with open('posts/' + url + "/index.html", 'w') as f:
        f.write('title: ' + url + '\n')
        f.write('date: ' + datetime.datetime.now().strftime('%b %d, %Y') + '\n')
        f.write('draft: true\n')
        f.write('---\n')

# In the Atom feed we do not want the footnotes to be dynamic, the way they are for
# the web and mobile versions. Instead, we want the footnotes to be displayed in brackets
# (e.g. [1], [2], etc.) and then to be collected in a section at the end of the piece.
def makeAtomContent(content):
    soup = BeautifulSoup(content, "html.parser")
    footnotes = []
    fn_num = 1

    try:
        while soup.find("span", class_="footnote"):
            fn = soup.find("span", class_="footnote")
            fn.insert_before("[" + str(fn_num) + "]")
            fn = soup.find("span", class_="footnote").extract()
            fn.name = "p"
            del fn['class']
            fn.insert(0, "[" + str(fn_num) + "]: ")
            fn_num += 1
            footnotes.append(fn)
    except Exception as e:
        pass

    if len(footnotes) > 0:
        h2 = soup.new_tag("h2")
        h2.string = "Footnotes"
        soup.append(h2)
        for fn in footnotes:
            soup.append(fn)

    return str(soup)

home_template = """<!doctype html>
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

post_template = """<!doctype html>
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

help_message = """s2gen usage:
\ts2gen command

AVAILABLE COMMANDS
\thelp\t\t display this message
\tinit\t\t initialize static site directory
\trelease\t\t generate release version of site
\tgenerate\t generate site files (without deploying)
\tserve\t\t serve site files locally to preview site
\tnewpost url\t create a new draft post located at /posts/<url>
"""

if __name__ == "__main__":
    main()
