import streamlit as st

def display_avatar(conn, username):
    cur = conn.cursor()
    sql = '''
        SELECT p.avatar
        FROM user_profile p
        JOIN users_login u ON p.user_id = u.id
        WHERE u.username = ?
    '''
    param = (username,)
    cur.execute(sql, param)
    result = cur.fetchone()
    chosen_avatar = result[0] if result else None

    if chosen_avatar:
        st.logo(chosen_avatar, size = 'large')
    else:
        st.logo("👤", size = 'large')
    return chosen_avatar