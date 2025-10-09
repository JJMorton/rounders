# Load environment variables
from dotenv import load_dotenv
import os
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from rounders import app

if __name__ == "__main__":

	# Tell Flask it is behind a proxy
	from werkzeug.middleware.proxy_fix import ProxyFix
	app.wsgi_app = ProxyFix(
		app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
	)

	app.run()

