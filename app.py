import logging
import os
import sys
from flask import Flask

# Logging konfigurieren
logging_level = os.environ.get('LOG_LEVEL', 'INFO')
level = getattr(logging, logging_level.upper(), logging.INFO)

logging.basicConfig(level=level, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger('ical-proxy')

# Kalender-Routes importieren
from cal_utils.calendar_routes import calendar_routes

def create_app():
    app = Flask(__name__)
    
    # Routes registrieren
    app.register_blueprint(calendar_routes)
    
    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8098))
    app.run(host="0.0.0.0", port=port)
