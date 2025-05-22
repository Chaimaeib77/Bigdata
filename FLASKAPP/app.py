from flask import Flask
from utils.routes import bp as routes_blueprint

app = Flask(__name__)
app.register_blueprint(routes_blueprint)  # ⬅️ ceci est essentiel !

if __name__ == "__main__":
    app.run(debug=True)
