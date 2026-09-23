import streamlit as st
import pandas as pd

from app_model.db import get_connection
from app_model.users import (
    get_user,
    search_usernames,
    get_user_security_info,
    lock_user,
    unlock_user,
    get_audit_logs
)

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

conn = get_connection()


# --------------------------------------------------
# ADMIN ACCESS CHECK
# --------------------------------------------------

if not st.session_state.get("Admin", False):
    st.error("Access denied.")
    st.stop()


# --------------------------------------------------
# PAGE
# --------------------------------------------------

st.title("Admin Dashboard")

tab1, tab2 = st.tabs([
    "User Management",
    "Audit Log"
])


# ==================================================
# TAB 1 — USER MANAGEMENT
# ==================================================

with tab1:

    st.header("User Management")

    # --------------------------------------------------
    # USER SEARCH
    # --------------------------------------------------

    username_search = st.text_input(
        "Search username",
        placeholder="Enter a username...",
        key="user_management_search"
    )

    selected_user = None

    if username_search:

        matching_users = search_usernames(
            conn,
            username_search
        )

        if matching_users:

            # HACKATHON search_usernames() returns:
            # (id, username)

            user_options = [
                user[1]
                for user in matching_users
            ]

            selected_username = st.selectbox(
                "Matching users",
                user_options,
                key="user_management_suggestions"
            )

            selected_user = next(
                user
                for user in matching_users
                if user[1] == selected_username
            )

        else:

            st.info("No matching users found.")

    # --------------------------------------------------
    # SELECTED USER DETAILS
    # --------------------------------------------------

    if selected_user:

        # search_usernames() returns:
        # (id, username)

        user_id = selected_user[0]

        user_details = get_user_security_info(
            conn,
            user_id
        )

        if user_details:

            # get_user_security_info() returns:
            #
            # id
            # username
            # email
            # role
            # failed_attempts
            # locked
            # lockout_count
            # last_login_time

            (
                user_id,
                username,
                email,
                role,
                failed_attempts,
                locked,
                lockout_count,
                last_login_time
            ) = user_details

            st.divider()

            st.subheader(
                f"User Details: {username}"
            )

            st.write(
                f"**User ID:** {user_id}"
            )

            st.write(
                f"**Email:** {email}"
            )

            st.write(
                f"**Role:** {role}"
            )

            st.write(
                f"**Failed login attempts:** {failed_attempts}"
            )

            st.write(
                f"**Lockout count:** {lockout_count}"
            )

            st.write(
                f"**Account locked:** "
                f"{'Yes' if locked else 'No'}"
            )

            st.write(
                f"**Last login:** "
                f"{last_login_time or 'Never'}"
            )

            # --------------------------------------------------
            # ACCOUNT ACTIONS
            # --------------------------------------------------

            st.subheader("Account Actions")

            # Find the currently logged-in administrator.
            admin = get_user(
                conn,
                st.session_state["username"]
            )

            if admin is None:

                st.error(
                    "Could not identify the administrator."
                )

            else:

                # HACKATHON get_user() returns:
                #
                # id
                # username
                # password_hash
                # failed_attempts
                # locked

                admin_id = admin[0]

                # --------------------------------------------------
                # UNLOCK
                # --------------------------------------------------

                if locked:

                    if st.button(
                        "Unlock Account",
                        key=f"unlock_user_{user_id}"
                    ):

                        success, message = unlock_user(
                            conn,
                            user_id,
                            admin_id
                        )

                        if success:

                            st.success(message)

                            st.rerun()

                        else:

                            st.error(message)

                # --------------------------------------------------
                # LOCK
                # --------------------------------------------------

                else:

                    if st.button(
                        "Lock Account",
                        key=f"lock_user_{user_id}"
                    ):

                        success, message = lock_user(
                            conn,
                            user_id,
                            admin_id
                        )

                        if success:

                            st.success(message)

                            st.rerun()

                        else:

                            st.error(message)


# ==================================================
# TAB 2 — AUDIT LOG
# ==================================================

with tab2:

    st.header("Security Monitoring")

    # --------------------------------------------------
    # TIME PERIOD
    # --------------------------------------------------

    period_options = [
        "Today",
        "Last 7 Days",
        "Last 30 Days",
        "All"
    ]

    selected_period = st.selectbox(
        "Select time period",
        period_options,
        key="audit_period_filter"
    )

    if selected_period == "Today":

        logs = get_audit_logs(
            conn,
            days=1
        )

    elif selected_period == "Last 7 Days":

        logs = get_audit_logs(
            conn,
            days=7
        )

    elif selected_period == "Last 30 Days":

        logs = get_audit_logs(
            conn,
            days=30
        )

    else:

        logs = get_audit_logs(conn)

    # --------------------------------------------------
    # AUDIT LOG DATA
    # --------------------------------------------------

    if logs:

        # get_audit_logs() returns:
        #
        # id
        # user_id
        # admin_id
        # action
        # description
        # timestamp
        # affected_user
        # administrator

        logs_df = pd.DataFrame(
            logs,
            columns=[
                "Log ID",
                "User ID",
                "Admin ID",
                "Action",
                "Description",
                "Timestamp",
                "Affected User",
                "Administrator"
            ]
        )

        # --------------------------------------------------
        # FILTERS
        # --------------------------------------------------

        st.subheader("Filter Logs")

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:

            audit_username_search = st.text_input(
                "Search affected username",
                placeholder="Enter a username...",
                key="audit_username_search"
            )

        with filter_col2:

            actions = [
                "All"
            ] + sorted(
                logs_df["Action"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_action = st.selectbox(
                "Filter by action",
                actions,
                key="audit_action_filter"
            )

        # --------------------------------------------------
        # APPLY FILTERS
        # --------------------------------------------------

        filtered_logs_df = logs_df.copy()

        if audit_username_search:

            filtered_logs_df = filtered_logs_df[
                filtered_logs_df["Affected User"]
                .fillna("")
                .str.contains(
                    audit_username_search,
                    case=False,
                    na=False,
                    regex=False
                )
            ]

        if selected_action != "All":

            filtered_logs_df = filtered_logs_df[
                filtered_logs_df["Action"]
                == selected_action
            ]

        # --------------------------------------------------
        # SECURITY METRICS
        # --------------------------------------------------

        st.subheader("Security Metrics")

        total_logs = len(filtered_logs_df)

        failed_logins = len(
            filtered_logs_df[
                filtered_logs_df["Action"]
                == "LOGIN_FAILED"
            ]
        )

        successful_logins = len(
            filtered_logs_df[
                filtered_logs_df["Action"]
                == "LOGIN_SUCCESS"
            ]
        )

        locked_accounts = len(
            filtered_logs_df[
                filtered_logs_df["Action"]
                == "ACCOUNT_LOCKED"
            ]
        )

        unlocked_accounts = len(
            filtered_logs_df[
                filtered_logs_df["Action"]
                == "ACCOUNT_UNLOCKED"
            ]
        )

        blocked_logins = len(
            filtered_logs_df[
                filtered_logs_df["Action"]
                == "LOGIN_BLOCKED"
            ]
        )

        # --------------------------------------------------
        # METRIC DISPLAY
        # --------------------------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Events",
            total_logs
        )

        col2.metric(
            "Failed Logins",
            failed_logins
        )

        col3.metric(
            "Successful Logins",
            successful_logins
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Account Locks",
            locked_accounts
        )

        col5.metric(
            "Account Unlocks",
            unlocked_accounts
        )

        col6.metric(
            "Blocked Logins",
            blocked_logins
        )

        # --------------------------------------------------
        # AUDIT TABLE
        # --------------------------------------------------

        st.subheader("Audit Log Records")

        st.dataframe(
            filtered_logs_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Showing {len(filtered_logs_df)} "
            f"of {len(logs_df)} records."
        )

    else:

        st.info(
            "No audit logs found for this period."
        )