# ==============================================================================
# Heroku / Render / Railway Processfile
# Specifies the command executed to run the web application
# Single worker with 2 threads is chosen to optimize memory usage for PyTorch
# ==============================================================================
web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 180 --workers 1 --threads 2
