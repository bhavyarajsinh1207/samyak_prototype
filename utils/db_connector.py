# utils/db_connector.py
import sqlalchemy
import pandas as pd
import streamlit as st

def get_db_connection(db_config):
    """
    Establishes a database connection using SQLAlchemy.
    """
    db_type = db_config["type"].lower()
    host = db_config["host"]
    port = db_config["port"]
    db_name = db_config["name"]
    user = db_config["user"]
    password = db_config["password"]

    connection_string = ""
    try:
        if db_type == "postgresql":
            connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
        elif db_type == "mysql":
            connection_string = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}"
        elif db_type == "sql server":
            connection_string = f"mssql+pyodbc://{user}:{password}@{host}:{port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == "sqlite":
            connection_string = f"sqlite:///{db_name}"
        else:
            st.error(f"Unsupported database type: {db_type}")
            return None

        engine = sqlalchemy.create_engine(connection_string)
        conn = engine.connect()
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

def fetch_data_from_db(connection, table_name, query_limit=1000):
    """
    Fetches data from a specified table in the database.
    """
    try:
        # Basic sanitization
        if not all(c.isalnum() or c in ['_'] for c in table_name):
            raise ValueError("Invalid table name.")

        query = f"SELECT * FROM {table_name} LIMIT {query_limit}"
        df = pd.read_sql(query, connection)
        return df
    except Exception as e:
        st.error(f"Error fetching data from table '{table_name}': {str(e)}")
        return pd.DataFrame()