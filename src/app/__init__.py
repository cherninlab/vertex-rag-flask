﻿import logging
from flask import Flask
from config.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enhanced logging configuration
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    app.logger.setLevel(logging.INFO)

    # Initialize routes
    from app.routes import main, api
    app.register_blueprint(main.bp)
    app.register_blueprint(api.bp)

    return app
