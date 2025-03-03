from app import app
from app import impression

def surveillance_impression():
    impression.main()

if __name__ == '__main__':
    app.run(debug=True)
    surveillance_impression()
