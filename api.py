from flask import Flask, jsonify, send_file
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()  # This is to load your environment variables from .env file

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    return conn

def create_temperature_plot():
    # Establish database connection and fetch data
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT period, temperature
        FROM weather_forecasts
        WHERE scraped_at >= current_date - INTERVAL '7 days'
        ORDER BY scraped_at;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()

    # Convert the data into a DataFrame for easier plotting
    df = pd.DataFrame(data, columns=['period', 'temperature'])

    # Clean and prepare the data
    df['temperature'] = df['temperature'].str.extract('(\d+)').astype(int)  # Extract temperature value and convert to integer

    # Create a plot
    fig, ax = plt.subplots()
    ax.plot(df['period'], df['temperature'], marker='o', linestyle='-', color='b')
    ax.set(title='Weekly Temperature Trends', xlabel='Period', ylabel='Temperature (°F)')
    ax.grid(True)
    ax.set_xticklabels(df['period'], rotation=45)  # Rotate period labels for better visibility

    return fig

@app.route('/temperature_trends')
def temperature_trends():
    fig = create_temperature_plot()
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)  # Close the plot to free up memory
    buf.seek(0)

    # Send the buffer as a response
    return send_file(buf, mimetype='image/png')

@app.route('/weather', methods=['GET'])
def get_weather():
    conn = get_db_connection()
    cur = conn.cursor()
    # Assuming 'scraped_at' is storing the datetime of when the data was scraped
    cur.execute("""
        SELECT id, period, short_desc, temperature, scraped_at
        FROM weather_forecasts
        WHERE scraped_at >= current_date - INTERVAL '1 week'
        ORDER BY scraped_at DESC;
    """)
    weather_data = cur.fetchall()
    cur.close()
    conn.close()

    # Prepare the data for JSON response
    columns = ['id', 'period', 'short_desc', 'temperature', 'scraped_at']
    result = [dict(zip(columns, row)) for row in weather_data]

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)