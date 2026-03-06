import os
import time
import psycopg2

host = os.getenv("DB_HOST", "postgres")
port = int(os.getenv("DB_PORT", "5432"))
name = os.getenv("DB_NAME", "bigdata")
user = os.getenv("DB_USER", "bigdata")
password = os.getenv("DB_PASSWORD", "bigdata")

max_retries = 20
retry_delay = 3

for attempt in range(1, max_retries + 1):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
        )
        break
    except Exception as exc:
        print(f"Intento {attempt}/{max_retries} - PostgreSQL no disponible: {exc}")
        if attempt == max_retries:
            raise
        time.sleep(retry_delay)

with conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                cliente TEXT NOT NULL,
                importe NUMERIC(10, 2) NOT NULL,
                fecha_carga TIMESTAMP DEFAULT NOW()
            )
            """
        )
        cur.execute(
            """
            INSERT INTO ventas (cliente, importe)
            VALUES
                ('ACME', 1200.50),
                ('Globex', 980.10),
                ('Initech', 1430.00)
            """
        )
        cur.execute("SELECT id, cliente, importe, fecha_carga FROM ventas ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()

print("Últimos registros en ventas:")
for row in rows:
    print(row)

conn.close()
print("Carga completada correctamente.")
