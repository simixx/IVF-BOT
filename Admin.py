import streamlit as st
import sqlite3
from sqlite3 import Error

def create_connection():
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect('ivf_bot.db')
    except Error as e:
        print(e)
    return conn

def main():
    conn = create_connection()

    st.title("Admin Dashboard")

    if conn:
        st.subheader("User Information")
        users = conn.execute("SELECT * FROM users").fetchall()
        for user in users:
            st.write(f"User ID: {user[0]}")
            st.write(f"Username: {user[1]}")
            st.write(f"Role: {user[3]}")
            st.write(f"Name: {user[4]}")
            st.write(f"Age: {user[5]}")
            st.write(f"Medical History: {user[6]}")
            st.write(f"Progress: {user[7]}")
            st.write("-------")

if __name__ == "__main__":
    main()
