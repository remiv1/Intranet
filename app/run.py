"""Point d'entrée local de l'application Flask."""

from app.application import peraudiere


if __name__ == '__main__':
    peraudiere.run(host="0.0.0.0", port=5000)
