s4gen: AWS S3 Static Site Generator
-----------------------------------

This static site generator is tailored for my use case and I'm not sure how
useful it will be for others. It is essentially a python script that you copy
into the directory you want to generate your static site from. It automatically
creates an ATOM feed for the site as well.

## Prequisites and Assumptions

You must have npm and the aws command line tools installed in order for s4gen to
function. You also need to install the libraries s4gen uses internally. I
recommend doing this with pip in a virtual environment as follows:

    python3 -m venv venv
    source venv/bin/activate
    pip install wheel
    pip install -r requirements.txt

For the aws command line tools your credentials must be configured, and you need
to have the S3 bucket you are going to use for you static site created and
accessible.

s4gen assumes you are using tailwindcss, since this is the css framework I use.
When deploying it automatically minimizes the css (including removing unnused
css rules).

## Commands

- s4gen.py help             show help message listing available commands
- s4gen.py init             initialize site directory (does nothing if already initialized)
- s4gen.py deploy           generate site and deploy to s3
- s4gen.py generate         generate site (without deploying)
- s4gen.py serve            serve site files locally to preview site

## Complementary Libaries

- Footnotes.js. This is a simple library I wrote to make footnotes, sidenotes,
  or endnotes easy to add to static sites.

## Contributing

I do not have the time to work on open source projects at this point in my life,
so I will not be accepting any PRs (except bug fixes) or implementing any
requested features. However, s4gen is in the public domain, so feel free to
modify, fork, or otherwise do whatever you want with this code.
