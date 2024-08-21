from flask import Flask, render_template, jsonify
import psycopg2

app = Flask(__name__)

# Konfigurace připojení k databázi
dbname = 'DP_pokus'
user = 'postgres'
password = 'kapli4ky'
host = 'localhost'
port = '5432'

def get_db_connection():
    connection = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    return connection

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # SQL dotaz pro načtení dat
        cursor.execute("SELECT zkratka, ST_AsGeoJSON(geom) as geom FROM metadata_dat")
        results = cursor.fetchall()

        data = [{'zkratka': row[0], 'geometry': row[1]} for row in results]

        cursor.close()
        connection.close()

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
