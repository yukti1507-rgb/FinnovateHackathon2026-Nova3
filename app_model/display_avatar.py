import streamlit as st
import sqlite3


def display_avatar(conn, username):
    if not username:
        st.logo("👤", size='large')
        return None

    cur = conn.cursor()
    sql = '''
        SELECT p.avatar
        FROM user_profile p
        JOIN users_login u ON p.user_id = u.id
        WHERE u.username = ?
    '''
    cur.execute(sql, (username,))
    row = cur.fetchone()
    chosen_avatar = row[0] if row and row[0] else None

    if chosen_avatar:
        st.logo(chosen_avatar, size='large')
    else:
        st.logo("👤", size='large')
    return chosen_avatar