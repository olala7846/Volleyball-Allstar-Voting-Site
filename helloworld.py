from flask import Flask, render_template

app = Flask(__name__)
app.config['DEBUG'] = True  # turn to false on production


@app.route("/")
def hello():
    return render_template('helloworld.html', content={})

if __name__ == "__main__":
    app.run()
