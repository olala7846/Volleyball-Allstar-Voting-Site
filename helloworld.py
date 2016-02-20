# hello app
from flask import Flask, render_template, request
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production


@app.route("/hello")
def hello():
    print 'Handled by hello'
    return render_template('helloworld.html', content={})


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found %s', request)
    msg = 'hello: 404 not found %s' % request
    return msg

if __name__ == "__main__":
    app.run()
