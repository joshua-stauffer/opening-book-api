import os
from app import create_app, db
from app.models import User, Move
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print('Unable to load environmental variables')

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.cli.command()
def test():
    """Run all tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db, User=User, Move=Move
    )