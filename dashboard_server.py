import os
from dashboard.app import app

server = app.server

port = int(os.environ.get("PORT", 8050))
app.run(host="0.0.0.0", port=port, debug=False)