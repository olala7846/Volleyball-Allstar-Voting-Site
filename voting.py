# voting app
from flask import Flask, render_template, request
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production


@app.route("/voting/")
def all_votings():
    votings = ['voting1', 'voting2']
    content = {'votings': votings}
    return render_template('all_votings.html', content=content)


@app.route("/voting/<voting_id>")
def voting_index(voting_id):
    return 'voting id : %s' % voting_id


@app.errorhandler(404)
def page_not_found(error):
    logger.error('404 not found %s', request)
    msg = 'voting: 404 not found %s' % request
    return msg

if __name__ == "__main__":
    app.run()
