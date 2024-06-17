import sqlite3
import pandas as pd

def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_file)
    return conn

def initialize_database(conn):
    """Initialize the database with tables and constraints."""
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS vendor_data (
                            vendor_type TEXT NOT NULL,
                            vendor_name TEXT PRIMARY KEY,
                            GST_NO INTEGER NOT NULL,
                            Contact_person_name TEXT NOT NULL,
                            address TEXT NOT NULL,
                            city TEXT NOT NULL,
                            pan_no TEXT NOT NULL
                        )''')

        # Add a check constraint for pan_no length
        conn.execute('''CREATE TRIGGER IF NOT EXISTS check_pan_length
                        BEFORE INSERT ON vendor_data
                        FOR EACH ROW
                        WHEN (LENGTH(NEW.pan_no) > 10)
                        BEGIN
                            SELECT RAISE(ABORT, 'Pan number must be 10 characters or less');
                        END;''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS material_data (
                            Part_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            part_no INTEGER NOT NULL,
                            scf TEXT NOT NULL,
                            process_type TEXT NOT NULL,
                            part_od REAL NOT NULL,
                            part_width INTEGER NOT NULL,
                            part_inner_dimension REAL NOT NULL,
                            material_specification TEXT NOT NULL,
                            finish_wt REAL NOT NULL,
                            green_drg_no INTEGER NOT NULL
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS rm_cost_data (
                            grade_type TEXT NOT NULL,
                            usd_cif REAL NOT NULL,
                            rate REAL NOT NULL,
                            final_landed_cost REAL
                        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS supplier_data (
                            input_weight REAL,
                            process_code TEXT,
                            machining_time REAL,
                            inspection_time REAL,
                            process_cost REAL,
                            machining_cost REAL,
                            inspection_cost REAL
                        )''')

def insert_data(conn, table, data):
    """Insert data into SQLite database."""
    try:
        data.to_sql(table, conn, if_exists='append', index=False)
    except sqlite3.IntegrityError as e:
        print(f"IntegrityError: {str(e)}")
        # Log the error or handle it appropriately

def fetch_data(query, conn):
    """Fetch data from SQLite database."""
    return pd.read_sql_query(query, conn)
