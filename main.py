import os
from flask import Flask
from db import db
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    # Create Flask app
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the database
    db.init_app(app)

    # Import and register blueprints/routes
    from app import init_app
    init_app(app)

    # Create tables
    with app.app_context():
        try:
            from models import CleaningJob
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")

    return app

# Create the app
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
# Main app update: 2025-04-17 20:28:36

# Main app update: 2025-04-17 20:28:37

# Main app update: 2025-04-17 20:28:38

# Main app update: 2025-04-17 20:28:40

# Main app update: 2025-04-17 20:28:45

# Main app update: 2025-04-17 20:28:46

# Main app update: 2025-04-17 20:28:47

# Main app update: 2025-04-17 20:28:48

# Main app update: 2025-04-17 20:28:51

# Main app update: 2025-04-17 20:28:52

# Main app update: 2025-04-17 20:28:53

# Main app update: 2025-04-17 20:28:54

# Main app update: 2025-04-17 20:28:57

# Main app update: 2025-04-17 20:28:57

# Main app update: 2025-04-17 20:28:59

# Main app update: 2025-04-17 20:29:03

# Main app update: 2025-04-17 20:29:05

# Main app update: 2025-04-17 20:29:05

# Main app update: 2025-04-17 20:29:06

# Main app update: 2025-04-17 20:29:10

# Main app update: 2025-04-17 20:29:11

# Main app update: 2025-04-17 20:29:16

# Main app update: 2025-04-17 20:29:17

# Main app update: 2025-04-17 20:29:18

# Main app update: 2025-04-17 20:29:20

# Main app update: 2025-04-17 20:29:21

# Main app update: 2025-04-17 20:29:23

# Main app update: 2025-04-17 20:29:26

# Main app update: 2025-04-17 20:29:27

# Main app update: 2025-04-17 20:29:28

# Main app update: 2025-04-17 20:29:30

# Main app update: 2025-04-17 20:30:17

# Main app update: 2025-04-17 20:30:18

# Main app update: 2025-04-17 20:30:19

# Main app update: 2025-04-17 20:30:19

# Main app update: 2025-04-17 20:30:19

# Main app update: 2025-04-17 20:30:20

# Main app update: 2025-04-17 20:30:21

# Main app update: 2025-04-17 20:30:22

# Main app update: 2025-04-17 20:30:22

# Main app update: 2025-04-17 20:30:24

# Main app update: 2025-04-17 20:30:25

# Main app update: 2025-04-17 20:30:26

# Main app update: 2025-04-17 20:30:27

# Main app update: 2025-04-17 20:30:31

# Main app update: 2025-04-17 20:30:33

# Main app update: 2025-04-17 20:30:35

# Main app update: 2025-04-17 20:30:35

# Main app update: 2025-04-17 20:30:37

# Main app update: 2025-04-17 20:30:39

# Main app update: 2025-04-17 20:30:40

# Main app update: 2025-04-17 20:30:40

# Main app update: 2025-04-17 20:30:42

# Main app update: 2025-04-17 20:30:45

# Main app update: 2025-04-17 20:30:49

# Main app update: 2025-04-17 20:30:50

# Main app update: 2025-04-17 20:30:52

# Main app update: 2025-04-17 20:30:53

# Main app update: 2025-04-17 20:30:54

# Main app update: 2025-04-17 20:30:55

# Main app update: 2025-04-17 20:30:56

# Main app update: 2025-04-17 20:30:57

# Main app update: 2025-04-17 20:30:58

# Main app update: 2025-04-17 20:31:00

# Main app update: 2025-04-17 20:31:02

# Main app update: 2025-04-17 20:31:03

# Main app update: 2025-04-17 20:31:05

# Main app update: 2025-04-17 20:31:06

# Main app update: 2025-04-17 20:31:08

# Main app update: 2025-04-17 20:31:11

# Main app update: 2025-04-17 20:31:13

# Main app update: 2025-04-17 20:31:14

# Main app update: 2025-04-17 20:31:16

# Main app update: 2025-04-17 20:31:18

# Main app update: 2025-04-17 20:31:22

# Main app update: 2025-04-17 20:31:26

# Main app update: 2025-04-17 20:31:29

# Main app update: 2025-04-17 20:31:30

# Main app update: 2025-04-17 20:31:32

# Main app update: 2025-04-17 20:31:37

# Main app update: 2025-04-17 20:31:41

# Main app update: 2025-04-17 20:31:42

# Main app update: 2025-04-17 20:31:44

# Main app update: 2025-04-17 20:31:46

# Main app update: 2025-04-17 20:31:47

# Main app update: 2025-04-17 20:31:49

# Main app update: 2025-04-17 20:31:50

# Main app update: 2025-04-17 20:31:51

# Main app update: 2025-04-17 20:31:53

# Main app update: 2025-04-17 20:31:54

# Main app update: 2025-04-17 20:31:54

# Main app update: 2025-04-17 20:31:55

# Main app update: 2025-04-17 20:31:58

# Main app update: 2025-04-17 20:31:58

# Main app update: 2025-04-17 20:32:03

# Main app update: 2025-04-17 20:32:05

# Main app update: 2025-04-17 20:32:05

# Main app update: 2025-04-17 20:32:06

# Main app update: 2025-04-17 20:32:08

# Main app update: 2025-04-17 20:32:12

# Main app update: 2025-04-17 20:32:13

# Main app update: 2025-04-17 20:32:13

# Main app update: 2025-04-17 20:32:15

# Main app update: 2025-04-17 20:32:17

# Main app update: 2025-04-17 20:32:17

# Main app update: 2025-04-17 20:32:18

# Main app update: 2025-04-17 20:32:19

# Main app update: 2025-04-17 20:32:20

# Main app update: 2025-04-17 20:32:21

# Main app update: 2025-04-17 20:32:22

# Main app update: 2025-04-17 20:32:24

# Main app update: 2025-04-17 20:32:26

# Main app update: 2025-04-17 20:32:27

# Main app update: 2025-04-17 20:32:27

# Main app update: 2025-04-17 20:32:28

# Main app update: 2025-04-17 20:32:29

# Main app update: 2025-04-17 20:32:29

# Main app update: 2025-04-17 20:32:31

# Main app update: 2025-04-17 20:32:35

# Main app update: 2025-04-17 20:57:11

# Main app update: 2025-04-17 20:57:12

# Main app update: 2025-04-17 20:57:13

# Main app update: 2025-04-17 20:57:14

# Main app update: 2025-04-17 20:57:15

# Main app update: 2025-04-17 20:57:16

# Main app update: 2025-04-17 20:57:19

# Main app update: 2025-04-17 20:57:22

# Main app update: 2025-04-17 20:57:23

# Main app update: 2025-04-17 20:57:24

# Main app update: 2025-04-17 20:57:24

# Main app update: 2025-04-17 20:57:27

# Main app update: 2025-04-17 20:57:28

# Main app update: 2025-04-17 20:57:29

# Main app update: 2025-04-17 20:57:29

# Main app update: 2025-04-17 20:57:32

# Main app update: 2025-04-17 20:57:34

# Main app update: 2025-04-17 20:57:35

# Main app update: 2025-04-17 20:57:35

# Main app update: 2025-04-17 20:57:40

# Main app update: 2025-04-17 20:57:41

# Main app update: 2025-04-17 20:57:44

# Main app update: 2025-04-17 20:57:44

# Main app update: 2025-04-17 20:57:45

# Main app update: 2025-04-17 20:57:47

# Main app update: 2025-04-17 20:57:47

# Main app update: 2025-04-17 20:57:50

# Main app update: 2025-04-17 20:57:51

# Main app update: 2025-04-17 20:57:53

# Main app update: 2025-04-17 20:57:55

# Main app update: 2025-04-17 20:58:05

# Main app update: 2025-04-17 20:58:06

# Main app update: 2025-04-17 20:58:06

# Main app update: 2025-04-17 20:58:08

# Main app update: 2025-04-17 20:58:08

# Main app update: 2025-04-17 20:58:09

# Main app update: 2025-04-17 20:58:10

# Main app update: 2025-04-17 20:58:10

# Main app update: 2025-04-17 20:58:11

# Main app update: 2025-04-17 20:58:12

# Main app update: 2025-04-17 20:58:13

# Main app update: 2025-04-17 20:58:16

# Main app update: 2025-04-17 20:58:17

# Main app update: 2025-04-17 20:58:20

# Main app update: 2025-04-17 20:58:21

# Main app update: 2025-04-17 20:58:21

# Main app update: 2025-04-17 20:58:22

# Main app update: 2025-04-17 20:58:27

# Main app update: 2025-04-17 20:58:28

# Main app update: 2025-04-17 20:58:31

# Main app update: 2025-04-17 20:58:31

# Main app update: 2025-04-17 20:58:32

# Main app update: 2025-04-17 20:58:32

# Main app update: 2025-04-17 20:58:38

# Main app update: 2025-04-17 20:58:38

# Main app update: 2025-04-17 20:58:40

# Main app update: 2025-04-17 20:58:42

# Main app update: 2025-04-17 20:58:43

# Main app update: 2025-04-17 20:58:44

# Main app update: 2025-04-17 20:58:45

# Main app update: 2025-04-17 20:58:47

# Main app update: 2025-04-17 20:58:49

# Main app update: 2025-04-17 20:58:50

# Main app update: 2025-04-17 20:58:52

# Main app update: 2025-04-17 20:58:52

# Main app update: 2025-04-17 20:58:54

# Main app update: 2025-04-17 20:58:57

# Main app update: 2025-04-17 20:58:58

# Main app update: 2025-04-17 20:58:58

# Main app update: 2025-04-17 20:59:00

# Main app update: 2025-04-17 20:59:03

# Main app update: 2025-04-17 20:59:04

# Main app update: 2025-04-17 20:59:05

# Main app update: 2025-04-17 20:59:05

# Main app update: 2025-04-17 20:59:06

# Main app update: 2025-04-17 20:59:08

# Main app update: 2025-04-17 20:59:09

# Main app update: 2025-04-17 20:59:10

# Main app update: 2025-04-17 20:59:10

# Main app update: 2025-04-17 20:59:11

# Main app update: 2025-04-17 20:59:12

# Main app update: 2025-04-17 20:59:13

# Main app update: 2025-04-17 20:59:13

# Main app update: 2025-04-17 20:59:17

# Main app update: 2025-04-17 20:59:17

# Main app update: 2025-04-17 20:59:20

# Main app update: 2025-04-17 20:59:22

# Main app update: 2025-04-17 20:59:22

# Main app update: 2025-04-17 20:59:22

# Main app update: 2025-04-17 20:59:24

# Main app update: 2025-04-17 20:59:25

# Main app update: 2025-04-17 20:59:25

# Main app update: 2025-04-17 20:59:25
