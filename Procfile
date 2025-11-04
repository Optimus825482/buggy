web: flask db upgrade && gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:$PORT --timeout 120 --keep-alive 5 --log-level info wsgi:app
