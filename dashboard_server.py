import os
from dashboard.app import app
from flask import redirect

server = app.server

@server.route("/")
def index():
    return redirect("/dashboard/")

port = int(os.environ.get("PORT", 8050))
app.run(host="0.0.0.0", port=port, debug=False)