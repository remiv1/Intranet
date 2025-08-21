from waitress import serve
from application import peraudiere

if __name__ == '__main__':
    serve(peraudiere, host="0.0.0.0", port=5000)
