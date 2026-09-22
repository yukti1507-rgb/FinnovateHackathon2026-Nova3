import streamlit as st
import sqlite3

def display_avatar(conn, username):
    cur = conn.cursor()
    sql = 'SELECT avatar FROM users WHERE username = ?'
    param = (username,)
    cur.execute(sql, param)
    chosen_avatar = cur.fetchone()[0]

    if chosen_avatar:
        st.logo(chosen_avatar, size = 'large')
    else:
        st.logo("👤", size = 'large')
    return chosen_avatar