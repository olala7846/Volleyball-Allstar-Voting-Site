# NTU Volley Allstar Voting Site
GAE(Google App Engine) volleyball allstar game voting website

* Langulage: Python
* Web framework: 
 * Flask (Site FE & BE),
 * Google Cloud Endpoint (Admin API BE)
* Database: Google Datastore (ndb)
* CSS framework: Bootstrap 4 (Alpha)
* Javascript framework: AngularJS (1.5)
* Mail service: Sendgrid

## Prerequisites
1. Learn Python, [GAE][GAE]
2. Learn Git, Pypi, [virtualenv][virtualenv], [npm][npm], [Bower][Bower]
3. Learn, [AngularJS][AngularJS], [Bootstrap][Bootstrap], [Flask][Flask]

## Setup
1. Setup [GAE development environment][GAE_PYTHON]
2. Clone this git projcet locally `git clone https://github.com/olala7846/ntuvb-allstar.git`
3. Install python packages (with pypi & virtualenv)
	
	```
	$ virtualenv venv 
	$ source venv/bin/activate
	$ pip install -r packages.txt
	```
4. Install css/js packages

	```
	$ npm install bower #Install bower
	$ bower install #Install packages under ./bower_compoments
	```
5. Launch local server and start coding!
	
	```
	$ sh ./script/launch_dev_server.sh
	$ sh./script/open_chrome  # for local cloud endpoint
	```
6. To send email, create your own `secrets.py`

	```
	# secrets.py
	SENDGRID_ID='YOUR_SENDGRID_ACCOUNT'
	SENDGRID_PASSWORD='YOUR_SENDGRID_PASSWORD`
	```
	**WARNING!! NEVER COMMIT THIS FILE**

## Components
1. Database schema: see `models.py` 	
2. Webserver: see `voting.py`
3. Admin api server: see `voting_backend.py`
4. Main queue: see `queue.yaml`
5. Cron job: see `cron.yaml`


[GAE]: https://cloud.google.com/appengine/docs
[virtualenv]: http://docs.python-guide.org/en/latest/dev/virtualenvs/
[npm]: https://www.npmjs.com/
[Flask]: http://flask.pocoo.org/
[GAE_PYTHON]: https://cloud.google.com/appengine/docs/python/
[Bower]: http://bower.io/
[Bootstrap]: http://getbootstrap.com/
[AngularJS]: https://angularjs.org/