s2gen: Static Site Generator
-----------------------------------

This static site generator is tailored for my use case and I'm not sure how
useful it will be for others. It is essentially a python script that you copy
into the directory you want to generate your static site from. It automatically
creates an Atom feed for the site as well.

## Prequisites and Assumptions

You must have npm installed in order for s2gen to function. You also need to
install the libraries s2gen uses internally. I recommend doing this with pip in
a virtual environment as follows:

    python3 -m venv venv
    source venv/bin/activate
    pip install wheel
    pip install -r requirements.txt

s2gen assumes you are using tailwindcss, since this is the css framework I use.
When generating the release version it automatically minimizes the css
(including removing unnused css rules).

## Commands

- `s2gen.py help`             show help message listing available commands
- `s2gen.py init`             initialize site directory (does nothing if already initialized)
- `s2gen.py release`          generate release version of site
- `s2gen.py generate`         generate site
- `s2gen.py serve`            serve site files locally to preview site

## Complementary Libaries

- [Footnotes.js](https://github.com/jeffreyrogers/Footnotes.js). This is a simple library
  I wrote to make footnotes and sidenotes easy to add to static sites.

## Contributing

I do not have the time to work on open source projects at this point in my life,
so I will not be accepting any PRs (except bug fixes) or implementing any
requested features. However, s2gen is in the public domain, so feel free to
modify, fork, or otherwise do whatever you want with this code.

