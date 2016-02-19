# GAE-template
This is a quick start projcet for Python / GAE website
Target to use

* Flask/Jinja - framework, template
* Google Datastore - database
* Bower - static files (CSS, Javascript)
* Python pip - Pypi + virtualenv

## Prerequisits
The following tools mush have been installed first
1. python pip
2. python virtualenv
3. Bower


## Initialization steps:
1. clone project
2. start virtualenv
  `virtualenv venv`
3. activate virtualenv
  `source ./venv/bin/activate`
4. install python packages( Flask, Jinja)
  `pip install packages.txt`

## Vendor files
1. Python pip packages are keep under ./venv/lib/python2.7/site-packages/
2. Other python packages can be put under /lib
3. Bower components are keep under ./bower_components/ and can be link
   under /bower
4. Other static files are keep under ./static and link as /static

