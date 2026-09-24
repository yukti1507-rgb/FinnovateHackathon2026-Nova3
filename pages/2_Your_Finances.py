import streamlit as st

from calculations.language import show_language_picker, t

from app_model.db import get_connection
from app_model.finances import (
    get_user_profile,
    update_user_profile,
    create_user_profile_record,
    get_income,
    add_income,
    update_income,
    delete_income,
    to_monthly_cents,
    get_expenses,
    add_expense,
    update_expense,
    delete_expense,
    get_loans,
    add_loan,
    update_loan,
    delete_loan,
    get_savings,
    add_or_update_savings,
    get_goals,
    add_goal,
    update_goal,
    delete_goal
)
from app_model.money import to_cents

st.set_page_config(
    page_title="Your Finances",
    page_icon="👤",
    layout="wide"
)

show_language_picker()


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = get_connection()


# ============================================================
# CHECK LOGGED-IN USER
# ============================================================

if not st.session_state.get("Logged_in", False):
    st.error("Please log in to access your finances.")
    st.stop()

user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

if user_id is None:
    st.error("Your user account could not be identified. Please log in again.")
    st.stop()


# ============================================================
# LOAD USER PROFILE
# ============================================================

profile = get_user_profile(conn, user_id)

# Older/existing accounts may not have a profile record yet.
# Create one automatically using the email already stored for
# the account if necessary.

if profile is None:
    try:
        from app_model.users import get_email

        user_email = get_email(conn, username)

        if user_email is None:
            st.error(
                "Your account profile could not be created because "
                "your email address could not be found."
            )
            st.stop()

        create_user_profile_record(
            conn=conn,
            user_id=user_id,
            email=user_email,
            occupation=None,
            financial_experience=None,
            avatar=None,
            background_color=None,
            role="user"
        )

        profile = get_user_profile(conn, user_id)

    except Exception as e:
        st.error(f"Unable to load your profile: {e}")
        st.stop()


# ============================================================
# PAGE TITLE
# ============================================================

st.title(t("Your Finances"))
st.caption(
    t("Edit your details anytime — your dashboard updates automatically.")
)


# ============================================================
# DEFAULT SESSION STATE
# ============================================================

if "current_savings" not in st.session_state:
    st.session_state["current_savings"] = 0.0

if "monthly_savings" not in st.session_state:
    st.session_state["monthly_savings"] = 0.0

if "savings_rate" not in st.session_state:
    st.session_state["savings_rate"] = 3.0

if "goals" not in st.session_state:
    st.session_state["goals"] = []

if "loans" not in st.session_state:
    st.session_state["loans"] = []

if "subscriptions" not in st.session_state:
    st.session_state["subscriptions"] = []

if "variable_expenses" not in st.session_state:
    st.session_state["variable_expenses"] = []

if "other_fixed_expenses" not in st.session_state:
    st.session_state["other_fixed_expenses"] = []

if "other_income" not in st.session_state:
    st.session_state["other_income"] = []


# =========================
# ABOUT YOU
# =========================

st.subheader("👤 About You")
st.caption(
    "Tell us a little about yourself so we can personalise your financial experience."
)

occupation_options = [
    "Student",
    "Employed",
    "Self-employed",
    "Unemployed",
    "Rather not say"
]

financial_experience_options = [
    "Beginner",
    "Some experience",
    "Confident",
    "Rather not say"
]

living_situation_options = [
    "With parents/family",
    "Living alone",
    "With partner/spouse",
    "Other",
    "Rather not say"
]

dependants_options = [
    "No",
    "Yes",
    "Rather not say"
]


# =========================
# LOAD SAVED PROFILE VALUES
# =========================

saved_occupation = profile.get("occupation")

if saved_occupation in occupation_options:
    occupation_index = occupation_options.index(saved_occupation)
else:
    occupation_index = 0


saved_experience = profile.get("financial_experience")

if saved_experience in financial_experience_options:
    experience_index = financial_experience_options.index(
        saved_experience
    )
else:
    experience_index = 0


saved_living_situation = profile.get("living_situation")

if saved_living_situation in living_situation_options:
    living_situation_index = living_situation_options.index(
        saved_living_situation
    )
else:
    living_situation_index = 0


saved_dependants = profile.get("dependants")

if saved_dependants in dependants_options:
    dependants_index = dependants_options.index(
        saved_dependants
    )
else:
    dependants_index = 0


# =========================
# PROFILE FIELDS
# =========================

profile_col1, profile_col2 = st.columns(2)

with profile_col1:

    selected_occupation = st.selectbox(
        "Occupation",
        occupation_options,
        index=occupation_index,
        key="profile_occupation"
    )

    selected_living_situation = st.selectbox(
        "Living situation",
        living_situation_options,
        index=living_situation_index,
        key="profile_living_situation"
    )


with profile_col2:

    selected_experience = st.selectbox(
        "Financial experience",
        financial_experience_options,
        index=experience_index,
        key="profile_financial_experience"
    )

    selected_dependants = st.selectbox(
        "Dependants",
        dependants_options,
        index=dependants_index,
        key="profile_dependants"
    )


# =========================
# AI PERSONALISATION
# =========================

st.subheader("🤖 AI Personalisation")

st.caption(
    "Allow the AI assistant to use your profile information "
    "to provide more personalised financial guidance."
)

saved_personalisation = profile.get(
    "personalisation_enabled",
    False
)

personalisation_enabled = st.toggle(
    "Allow AI to use my profile information",
    value=saved_personalisation,
    key="profile_personalisation"
)

if personalisation_enabled:
    st.info(
        "Your profile information may be used by the AI assistant "
        "to personalise your financial guidance."
    )
else:
    st.info(
        "Your profile information will remain saved, but the AI "
        "assistant will not use it for personalisation."
    )


# =========================
# SAVE PROFILE
# =========================

if st.button("💾 Save Profile", type="primary"):

    st.session_state["pending_profile_save"] = {
        "occupation": selected_occupation,
        "financial_experience": selected_experience,
        "living_situation": selected_living_situation,
        "dependants": selected_dependants,
        "personalisation_enabled": personalisation_enabled
    }

    st.session_state["show_profile_confirmation"] = True


# =========================
# PROFILE SAVE CONFIRMATION
# =========================

if st.session_state.get("show_profile_confirmation", False):

    st.warning("Please confirm your profile changes.")

    pending_profile = st.session_state.get(
        "pending_profile_save",
        {}
    )

    st.write(
        f"**Occupation:** "
        f"{pending_profile.get('occupation', '')}"
    )

    st.write(
        f"**Financial experience:** "
        f"{pending_profile.get('financial_experience', '')}"
    )

    st.write(
        f"**Living situation:** "
        f"{pending_profile.get('living_situation', '')}"
    )

    st.write(
        f"**Dependants:** "
        f"{pending_profile.get('dependants', '')}"
    )

    personalisation_status = (
        "Enabled"
        if pending_profile.get("personalisation_enabled", False)
        else "Disabled"
    )

    st.write(
        f"**AI Personalisation:** "
        f"{personalisation_status}"
    )

    if pending_profile.get("personalisation_enabled", False):

        st.info(
            "The AI assistant will be allowed to use your "
            "profile information to provide personalised "
            "financial guidance."
        )

    else:

        st.info(
            "Your profile information will still be saved, "
            "but the AI assistant will not use it for "
            "personalised guidance."
        )

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:

        if st.button(
            "Cancel",
            use_container_width=True
        ):
            st.session_state.pop(
                "pending_profile_save",
                None
            )

            st.session_state[
                "show_profile_confirmation"
            ] = False

            st.rerun()

    with confirm_col2:

        if st.button(
            "Confirm & Save",
            type="primary",
            use_container_width=True
        ):

            try:

                update_user_profile(
                    conn=conn,
                    user_id=user_id,
                    occupation=pending_profile["occupation"],
                    financial_experience=pending_profile[
                        "financial_experience"
                    ],
                    living_situation=pending_profile[
                        "living_situation"
                    ],
                    dependants=pending_profile[
                        "dependants"
                    ],
                    personalisation_enabled=pending_profile[
                        "personalisation_enabled"
                    ]
                )

                st.session_state.pop(
                    "pending_profile_save",
                    None
                )

                st.session_state[
                    "show_profile_confirmation"
                ] = False

                st.success(
                    "Your profile has been saved successfully."
                )

                # Reload the profile from the database
                profile = get_user_profile(
                    conn,
                    user_id
                )

            except Exception as e:

                st.error(
                    f"Unable to save your profile: {e}"
                )

st.divider()


# =========================
# INCOME
# =========================

st.subheader("💵 Income")

st.caption(
    "Add all the money you regularly receive. "
    "You can enter income as daily, weekly, monthly or yearly."
)


# =========================
# LOAD INCOME INTO SESSION
# =========================

if "income_draft" not in st.session_state:

    income_records = get_income(
        conn,
        user_id
    )

    draft_records = []

    for record in income_records:

        draft_records.append({
            "id": record["id"],
            "source": record["source"],
            "amount": record["amount"],
            "currency": record["currency"],
            "frequency": record["frequency"]
        })

    st.session_state["income_draft"] = draft_records


income_draft = st.session_state["income_draft"]


# =========================
# FREQUENCY OPTIONS
# =========================

frequency_options = [
    "daily",
    "weekly",
    "monthly",
    "yearly"
]


# =========================
# FIND MAIN INCOME
# =========================

main_income_record = None
other_income_records = []

for record in income_draft:

    if record["source"] == "Main income":
        main_income_record = record

    else:
        other_income_records.append(record)


# =========================
# MAIN INCOME
# =========================

st.markdown("### Main income")

if main_income_record is not None:

    main_income_amount = st.number_input(
        "Monthly take-home income",
        min_value=0.0,
        step=100.0,
        value=float(main_income_record["amount"]),
        key="main_income_amount"
    )

else:

    main_income_amount = st.number_input(
        "Monthly take-home income",
        min_value=0.0,
        step=100.0,
        value=0.0,
        key="main_income_amount"
    )


# =========================
# OTHER INCOME
# =========================

st.markdown("### Other sources of income")

st.caption(
    "Examples: freelance work, rental income, "
    "allowance, side business or occasional work."
)


for index, record in enumerate(other_income_records):

    record_id = record["id"]

    # Temporary records receive a string ID.
    # Database records have integer IDs.
    widget_id = str(record_id)

    with st.expander(
        f"{record['source']} — "
        f"Rs {record['amount']:,.2f} / {record['frequency']}"
    ):

        col1, col2 = st.columns([2, 1])

        with col1:

            source = st.text_input(
                "Income source",
                value=record["source"],
                key=f"income_source_{widget_id}"
            )

        with col2:

            amount = st.number_input(
                "Amount (Rs)",
                min_value=0.0,
                step=100.0,
                value=float(record["amount"]),
                key=f"income_amount_{widget_id}"
            )

        frequency = st.selectbox(
            "Frequency",
            frequency_options,
            index=frequency_options.index(
                record["frequency"]
            ),
            key=f"income_frequency_{widget_id}"
        )

        monthly_equivalent = to_monthly_cents(
            amount,
            frequency
        )

        st.caption(
            f"Monthly equivalent: "
            f"Rs {monthly_equivalent:,.2f}"
        )

        if st.button(
            "🗑️ Remove",
            key=f"remove_income_{widget_id}",
            use_container_width=True
        ):

            # Remove from the draft only.
            # Nothing is deleted from SQLite yet.
            st.session_state["income_draft"] = [
                item
                for item in st.session_state["income_draft"]
                if item["id"] != record_id
            ]

            st.rerun()


# =========================
# ADD NEW INCOME
# =========================

with st.expander("➕ Add another income source"):

    new_source = st.text_input(
        "Income source",
        placeholder="e.g. Freelance, Rental, Allowance",
        key="new_income_source"
    )

    col1, col2 = st.columns(2)

    with col1:

        new_amount = st.number_input(
            "Amount (Rs)",
            min_value=0.0,
            step=100.0,
            value=0.0,
            key="new_income_amount"
        )

    with col2:

        new_frequency = st.selectbox(
            "Frequency",
            frequency_options,
            key="new_income_frequency"
        )

    if new_amount > 0:

        new_monthly_equivalent = to_monthly_cents(
            new_amount,
            new_frequency
        )

        st.caption(
            f"Monthly equivalent: "
            f"Rs {new_monthly_equivalent:,.2f}"
        )

    if st.button(
        "Add income source",
        type="secondary",
        use_container_width=True
    ):

        if new_source.strip() == "":
            st.error(
                "Please enter an income source."
            )

        elif new_amount <= 0:
            st.error(
                "Amount must be greater than 0."
            )

        elif new_source.strip().lower() == "main income":
            st.error(
                "Please use the Main income section "
                "for your main income."
            )

        else:

            # Generate a temporary ID.
            # It will only exist in session state until saved.
            temp_id = f"new_{len(st.session_state['income_draft']) + 1}"

            st.session_state["income_draft"].append({
                "id": temp_id,
                "source": new_source.strip(),
                "amount": new_amount,
                "currency": "MUR",
                "frequency": new_frequency
            })

            # Clear the add form.
            st.session_state.pop(
                "new_income_source",
                None
            )

            st.session_state.pop(
                "new_income_amount",
                None
            )

            st.session_state.pop(
                "new_income_frequency",
                None
            )

            st.rerun()


# =========================
# CALCULATE PREVIEW TOTAL
# =========================

monthly_income_total = 0.0


# Main income
monthly_income_total += main_income_amount


# Other income
for index, record in enumerate(other_income_records):

    record_id = record["id"]
    widget_id = str(record_id)

    amount = st.session_state.get(
        f"income_amount_{widget_id}",
        record["amount"]
    )

    frequency = st.session_state.get(
        f"income_frequency_{widget_id}",
        record["frequency"]
    )

    monthly_income_total += to_monthly_cents(
        amount,
        frequency
    )


# =========================
# DISPLAY TOTAL
# =========================

st.divider()

st.markdown("### 📊 Monthly income overview")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Main income",
        f"Rs {main_income_amount:,.2f}"
    )

with col2:

    st.metric(
        "Estimated monthly income",
        f"Rs {monthly_income_total:,.2f}"
    )


st.caption(
    "Daily, weekly and yearly income is converted "
    "to an estimated monthly equivalent."
)


# =========================
# REVIEW CHANGES
# =========================

st.divider()

if st.button(
    "💾 Review & Save Changes",
    type="primary",
    use_container_width=True,
    key="save_income_btn"
):

    # Build a complete snapshot of what the user
    # currently wants to save.

    pending_income = []

    # Main income
    pending_income.append({
        "id": (
            main_income_record["id"]
            if main_income_record is not None
            else None
        ),
        "source": "Main income",
        "amount": main_income_amount,
        "currency": "MUR",
        "frequency": "monthly"
    })


    # Other income
    for record in other_income_records:

        record_id = record["id"]
        widget_id = str(record_id)

        source = st.session_state.get(
            f"income_source_{widget_id}",
            record["source"]
        )

        amount = st.session_state.get(
            f"income_amount_{widget_id}",
            record["amount"]
        )

        frequency = st.session_state.get(
            f"income_frequency_{widget_id}",
            record["frequency"]
        )

        pending_income.append({
            "id": record_id,
            "source": source.strip(),
            "amount": amount,
            "currency": "MUR",
            "frequency": frequency
        })


    # Add newly created draft records.
    for record in income_draft:

        if isinstance(record["id"], str):

            pending_income.append({
                "id": record["id"],
                "source": record["source"],
                "amount": record["amount"],
                "currency": record["currency"],
                "frequency": record["frequency"]
            })


    # Basic validation
    validation_error = None

    if main_income_amount <= 0:
        validation_error = (
            "Main income must be greater than 0."
        )

    else:

        for record in pending_income:

            if record["source"].strip() == "":
                validation_error = (
                    "Every income source must have a name."
                )
                break

            if record["amount"] <= 0:
                validation_error = (
                    "Every income amount must be greater than 0."
                )
                break

    if validation_error:

        st.error(validation_error)

    else:

        st.session_state[
            "pending_income_save"
        ] = pending_income

        st.session_state[
            "show_income_confirmation"
        ] = True

        st.rerun()


# =========================
# CONFIRMATION
# =========================

if st.session_state.get(
    "show_income_confirmation",
    False
):

    pending_income = st.session_state.get(
        "pending_income_save",
        []
    )

    st.warning(
        "Please review your income changes before saving."
    )

    st.markdown("#### Changes to be saved")

    confirmation_total = 0.0

    for record in pending_income:

        monthly_equivalent = to_monthly_cents(
            record["amount"],
            record["frequency"]
        )

        confirmation_total += monthly_equivalent

        if record["source"] == "Main income":

            st.write(
                f"**Main income:** "
                f"Rs {record['amount']:,.2f} / month"
            )

        else:

            st.write(
                f"**{record['source']}** — "
                f"Rs {record['amount']:,.2f} / "
                f"{record['frequency']} "
                f"(≈ Rs {monthly_equivalent:,.2f} / month)"
            )

    st.markdown(
        f"**Estimated monthly income: "
        f"Rs {confirmation_total:,.2f}**"
    )

    st.divider()

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:

        if st.button(
            "Cancel",
            use_container_width=True
        ):

            st.session_state.pop(
                "pending_income_save",
                None
            )

            st.session_state[
                "show_income_confirmation"
            ] = False

            st.rerun()


    with confirm_col2:

        if st.button(
            "✅ Confirm & Save",
            type="primary",
            use_container_width=True
        ):

            try:

                # ---------------------------------
                # Existing database IDs
                # ---------------------------------

                existing_records = get_income(
                    conn,
                    user_id
                )

                existing_ids = {
                    record["id"]
                    for record in existing_records
                }


                # ---------------------------------
                # IDs that should remain
                # ---------------------------------

                pending_existing_ids = {
                    record["id"]
                    for record in pending_income
                    if isinstance(record["id"], int)
                }


                # ---------------------------------
                # Delete removed records
                # ---------------------------------

                for existing_id in existing_ids:

                    if existing_id not in pending_existing_ids:

                        delete_income(
                            conn=conn,
                            income_id=existing_id,
                            user_id=user_id
                        )


                # ---------------------------------
                # Add / update records
                # ---------------------------------

                for record in pending_income:

                    record_id = record["id"]

                    # New income source
                    if not isinstance(record_id, int):

                        add_income(
                            conn=conn,
                            user_id=user_id,
                            source=record["source"],
                            amount=record["amount"],
                            currency=record["currency"],
                            frequency=record["frequency"]
                        )

                    # Existing income source
                    else:

                        update_income(
                            conn=conn,
                            income_id=record_id,
                            user_id=user_id,
                            source=record["source"],
                            amount=record["amount"],
                            currency=record["currency"],
                            frequency=record["frequency"]
                        )


                # ---------------------------------
                # Refresh draft from database
                # ---------------------------------

                st.session_state["income_draft"] = (
                    get_income(
                        conn,
                        user_id
                    )
                )


                st.session_state.pop(
                    "pending_income_save",
                    None
                )

                st.session_state[
                    "show_income_confirmation"
                ] = False


                st.success(
                    "Your income information has been saved successfully."
                )

                st.rerun()


            except Exception as e:

                st.error(
                    f"Unable to save your income information: {e}"
                )


st.divider()

# ============================================================
# EXPENSES
# ============================================================

st.subheader("💸 Expenses")

st.caption(
    "Add everything you regularly spend money on. "
    "You can enter expenses as daily, weekly, monthly or yearly."
)


# ============================================================
# INITIALISE EXPENSE DRAFT
# ============================================================

if "expense_draft" not in st.session_state:

    existing_expenses = get_expenses(
        conn,
        user_id
    )

    draft_expenses = []

    for expense in existing_expenses:

        draft_expenses.append({
            "id": expense["id"],
            "category": expense["category"],
            "name": expense["name"],
            "amount": expense["amount"],
            "currency": expense["currency"],
            "frequency": expense["frequency"],
            "expense_type": expense["expense_type"]
        })

    st.session_state["expense_draft"] = draft_expenses


expense_draft = st.session_state["expense_draft"]


# ============================================================
# OPTIONS
# ============================================================

expense_categories = [
    "Housing",
    "Food",
    "Transport",
    "Utilities",
    "Education",
    "Healthcare",
    "Subscriptions",
    "Entertainment",
    "Shopping",
    "Personal care",
    "Family",
    "Insurance",
    "Debt / Loan",
    "Other"
]

frequency_options = [
    "daily",
    "weekly",
    "monthly",
    "yearly"
]


# ============================================================
# ADD EXPENSE
# ============================================================

st.markdown("### ➕ Add an expense")

st.caption(
    "Don't worry about whether an expense is fixed, variable "
    "or a subscription. Just add it here and choose the "
    "category that best describes it."
)


with st.expander(
    "Add a new expense",
    expanded=True
):

    new_expense_name = st.text_input(
        "Expense name",
        placeholder="e.g. Groceries, Netflix, Bus pass",
        key="new_expense_name"
    )

    new_expense_category = st.selectbox(
        "Category",
        expense_categories,
        key="new_expense_category"
    )

    col1, col2 = st.columns(2)

    with col1:

        new_expense_amount = st.number_input(
            "Amount (Rs)",
            min_value=0.0,
            step=50.0,
            key="new_expense_amount"
        )

    with col2:

        new_expense_frequency = st.selectbox(
            "Frequency",
            frequency_options,
            key="new_expense_frequency"
        )

    new_expense_is_need = st.toggle(
        "Need",
        value=True,
        key="new_expense_need"
    )

    if new_expense_amount > 0:

        new_amount_cents = to_cents(
            new_expense_amount
        )

        new_monthly_cents = to_monthly_cents(
            new_amount_cents,
            new_expense_frequency
        )

        st.caption(
            f"Estimated monthly cost: "
            f"**Rs "
            f"{new_monthly_cents // 100:,}."
            f"{new_monthly_cents % 100:02d}**"
        )

    if st.button(
        "Add expense",
        type="primary",
        use_container_width=True
    ):

        if new_expense_name.strip() == "":

            st.error(
                "Please enter an expense name."
            )

        elif new_expense_amount <= 0:

            st.error(
                "Amount must be greater than 0."
            )

        else:

            temp_id = (
                f"new_"
                f"{len(st.session_state['expense_draft']) + 1}"
            )

            st.session_state["expense_draft"].append({
                "id": temp_id,
                "category": new_expense_category,
                "name": new_expense_name.strip(),
                "amount": new_expense_amount,
                "currency": "MUR",
                "frequency": new_expense_frequency,
                "expense_type": (
                    "Need"
                    if new_expense_is_need
                    else "Want"
                )
            })

            st.session_state.pop(
                "new_expense_name",
                None
            )

            st.session_state.pop(
                "new_expense_amount",
                None
            )

            st.session_state.pop(
                "new_expense_category",
                None
            )

            st.session_state.pop(
                "new_expense_frequency",
                None
            )

            st.session_state.pop(
                "new_expense_need",
                None
            )

            st.rerun()


# ============================================================
# YOUR EXPENSES
# ============================================================

st.markdown("### 🧾 Your expenses")

if len(expense_draft) == 0:

    st.info(
        "You haven't added any expenses yet. "
        "Use the form above to add your first expense."
    )

else:

    st.caption(
        "You can edit or remove expenses here. "
        "Your changes will not be saved until you confirm them."
    )


# ============================================================
# DISPLAY / EDIT EXPENSES
# ============================================================

for record in expense_draft:

    record_id = record["id"]
    widget_id = str(record_id)

    amount_cents = to_cents(
        record["amount"]
    )

    monthly_cents = to_monthly_cents(
        amount_cents,
        record["frequency"]
    )

    with st.expander(
        f"{record['name']} — "
        f"Rs "
        f"{amount_cents // 100:,}."
        f"{amount_cents % 100:02d} "
        f"/ {record['frequency']}"
    ):

        col1, col2 = st.columns([2, 1])

        with col1:

            edited_name = st.text_input(
                "Expense name",
                value=record["name"],
                key=f"expense_name_{widget_id}"
            )

        with col2:

            edited_is_need = st.toggle(
                "Need",
                value=(
                    record["expense_type"] == "Need"
                ),
                key=f"expense_need_{widget_id}"
            )

        edited_category = st.selectbox(
            "Category",
            expense_categories,
            index=(
                expense_categories.index(
                    record["category"]
                )
                if record["category"]
                in expense_categories
                else expense_categories.index("Other")
            ),
            key=f"expense_category_{widget_id}"
        )

        col1, col2 = st.columns(2)

        with col1:

            edited_amount = st.number_input(
                "Amount (Rs)",
                min_value=0.0,
                value=float(record["amount"]),
                step=50.0,
                key=f"expense_amount_{widget_id}"
            )

        with col2:

            edited_frequency = st.selectbox(
                "Frequency",
                frequency_options,
                index=frequency_options.index(
                    record["frequency"]
                ),
                key=f"expense_frequency_{widget_id}"
            )

        if edited_amount > 0:

            edited_amount_cents = to_cents(
                edited_amount
            )

            edited_monthly_cents = to_monthly_cents(
                edited_amount_cents,
                edited_frequency
            )

            st.caption(
                f"Estimated monthly cost: "
                f"**Rs "
                f"{edited_monthly_cents // 100:,}."
                f"{edited_monthly_cents % 100:02d}**"
            )

        if st.button(
            "🗑️ Remove expense",
            key=f"remove_expense_{widget_id}",
            use_container_width=True
        ):

            st.session_state["expense_draft"] = [
                item
                for item in st.session_state["expense_draft"]
                if item["id"] != record_id
            ]

            st.rerun()


# ============================================================
# CALCULATE DRAFT TOTALS
# ============================================================

draft_total_cents = 0
draft_needs_cents = 0
draft_wants_cents = 0


for record in expense_draft:

    record_id = record["id"]
    widget_id = str(record_id)

    amount = st.session_state.get(
        f"expense_amount_{widget_id}",
        record["amount"]
    )

    frequency = st.session_state.get(
        f"expense_frequency_{widget_id}",
        record["frequency"]
    )

    is_need = st.session_state.get(
        f"expense_need_{widget_id}",
        record["expense_type"] == "Need"
    )

    amount_cents = to_cents(
        amount
    )

    monthly_cents = to_monthly_cents(
        amount_cents,
        frequency
    )

    draft_total_cents += monthly_cents

    if is_need:

        draft_needs_cents += monthly_cents

    else:

        draft_wants_cents += monthly_cents


# ============================================================
# MONTHLY EXPENSE OVERVIEW
# ============================================================

st.divider()

st.markdown("### 📊 Monthly expense overview")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Estimated monthly expenses",
        f"Rs "
        f"{draft_total_cents // 100:,}."
        f"{draft_total_cents % 100:02d}"
    )

with col2:

    st.metric(
        "Needs",
        f"Rs "
        f"{draft_needs_cents // 100:,}."
        f"{draft_needs_cents % 100:02d}"
    )

with col3:

    st.metric(
        "Wants",
        f"Rs "
        f"{draft_wants_cents // 100:,}."
        f"{draft_wants_cents % 100:02d}"
    )

st.caption(
    "Daily, weekly and yearly expenses are converted "
    "to estimated monthly equivalents."
)


# ============================================================
# AVAILABLE AFTER EXPENSES
# ============================================================

current_income = st.session_state.get(
    "income",
    0
)

try:

    income_cents = to_cents(
        current_income
    )

except (TypeError, ValueError):

    income_cents = 0


available_cents = (
    income_cents
    - draft_total_cents
)


col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Monthly income",
        f"Rs "
        f"{income_cents // 100:,}."
        f"{income_cents % 100:02d}"
    )

with col2:

    st.metric(
        "Available after expenses",
        f"Rs "
        f"{available_cents // 100:,}."
        f"{available_cents % 100:02d}"
    )


if (
    income_cents > 0
    and draft_total_cents > income_cents
):

    st.warning(
        "⚠️ Your estimated monthly expenses currently "
        "exceed your income."
    )


# ============================================================
# REVIEW & SAVE
# ============================================================

st.divider()

st.caption(
    "Your changes are not saved to your account yet. "
    "Review them before saving."
)


if st.button(
    "💾 Review & Save Changes",
    type="primary",
    use_container_width=True,
    key="save_expenses_btn"
):

    pending_expenses = []

    validation_error = None

    for record in expense_draft:

        record_id = record["id"]
        widget_id = str(record_id)

        edited_name = st.session_state.get(
            f"expense_name_{widget_id}",
            record["name"]
        )

        edited_category = st.session_state.get(
            f"expense_category_{widget_id}",
            record["category"]
        )

        edited_amount = st.session_state.get(
            f"expense_amount_{widget_id}",
            record["amount"]
        )

        edited_frequency = st.session_state.get(
            f"expense_frequency_{widget_id}",
            record["frequency"]
        )

        edited_is_need = st.session_state.get(
            f"expense_need_{widget_id}",
            record["expense_type"] == "Need"
        )

        edited_name = edited_name.strip()

        if edited_name == "":

            validation_error = (
                "Every expense must have a name."
            )

            break

        if edited_amount <= 0:

            validation_error = (
                "Every expense amount must be greater than 0."
            )

            break

        pending_expenses.append({
            "id": record_id,
            "category": edited_category,
            "name": edited_name,
            "amount": edited_amount,
            "currency": record["currency"],
            "frequency": edited_frequency,
            "expense_type": (
                "Need"
                if edited_is_need
                else "Want"
            )
        })

    if validation_error:

        st.error(
            validation_error
        )

    else:

        st.session_state[
            "pending_expense_save"
        ] = pending_expenses

        st.session_state[
            "show_expense_confirmation"
        ] = True

        st.rerun()


# ============================================================
# EXPENSE CONFIRMATION
# ============================================================

if st.session_state.get(
    "show_expense_confirmation",
    False
):

    pending_expenses = st.session_state.get(
        "pending_expense_save",
        []
    )

    st.warning(
        "Please review your expense changes before saving."
    )

    st.markdown(
        "#### Changes to be saved"
    )

    confirmation_total_cents = 0
    confirmation_needs_cents = 0
    confirmation_wants_cents = 0

    if len(pending_expenses) == 0:

        st.info(
            "All expenses will be removed."
        )

    for record in pending_expenses:

        amount_cents = to_cents(
            record["amount"]
        )

        monthly_cents = to_monthly_cents(
            amount_cents,
            record["frequency"]
        )

        confirmation_total_cents += monthly_cents

        if record["expense_type"] == "Need":

            confirmation_needs_cents += monthly_cents

        else:

            confirmation_wants_cents += monthly_cents

        st.write(
            f"**{record['name']}** — "
            f"Rs "
            f"{amount_cents // 100:,}."
            f"{amount_cents % 100:02d} / "
            f"{record['frequency']} — "
            f"{record['category']} — "
            f"{record['expense_type']}"
        )

        if record["frequency"] != "monthly":

            st.caption(
                f"Monthly equivalent: "
                f"Rs "
                f"{monthly_cents // 100:,}."
                f"{monthly_cents % 100:02d}"
            )

    st.divider()

    st.markdown(
        f"**Estimated monthly expenses:** "
        f"Rs "
        f"{confirmation_total_cents // 100:,}."
        f"{confirmation_total_cents % 100:02d}"
    )

    st.markdown(
        f"**Needs:** "
        f"Rs "
        f"{confirmation_needs_cents // 100:,}."
        f"{confirmation_needs_cents % 100:02d}"
    )

    st.markdown(
        f"**Wants:** "
        f"Rs "
        f"{confirmation_wants_cents // 100:,}."
        f"{confirmation_wants_cents % 100:02d}"
    )

    st.divider()

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:

        if st.button(
            "Cancel",
            use_container_width=True
        ):

            st.session_state.pop(
                "pending_expense_save",
                None
            )

            st.session_state[
                "show_expense_confirmation"
            ] = False

            st.rerun()

    with confirm_col2:

        if st.button(
            "✅ Confirm & Save",
            type="primary",
            use_container_width=True
        ):

            try:

                # ------------------------------------------------
                # Get current database records
                # ------------------------------------------------

                existing_expenses = get_expenses(
                    conn,
                    user_id
                )

                existing_ids = {
                    expense["id"]
                    for expense in existing_expenses
                }

                pending_existing_ids = {
                    expense["id"]
                    for expense in pending_expenses
                    if isinstance(
                        expense["id"],
                        int
                    )
                }

                # ------------------------------------------------
                # Delete removed expenses
                # ------------------------------------------------

                for existing_id in existing_ids:

                    if (
                        existing_id
                        not in pending_existing_ids
                    ):

                        delete_expense(
                            conn=conn,
                            expense_id=existing_id,
                            user_id=user_id
                        )

                # ------------------------------------------------
                # Add / update expenses
                # ------------------------------------------------

                for expense in pending_expenses:

                    expense_id = expense["id"]

                    if not isinstance(
                        expense_id,
                        int
                    ):

                        add_expense(
                            conn=conn,
                            user_id=user_id,
                            category=expense["category"],
                            name=expense["name"],
                            amount=expense["amount"],
                            frequency=expense["frequency"],
                            expense_type=expense["expense_type"],
                            currency=expense["currency"]
                        )

                    else:

                        update_expense(
                            conn=conn,
                            expense_id=expense_id,
                            user_id=user_id,
                            category=expense["category"],
                            name=expense["name"],
                            amount=expense["amount"],
                            frequency=expense["frequency"],
                            expense_type=expense["expense_type"],
                            currency=expense["currency"]
                        )

                # ------------------------------------------------
                # Reload saved data
                # ------------------------------------------------

                st.session_state["expense_draft"] = (
                    get_expenses(
                        conn,
                        user_id
                    )
                )

                st.session_state.pop(
                    "pending_expense_save",
                    None
                )

                st.session_state[
                    "show_expense_confirmation"
                ] = False

                st.success(
                    "Your expense information "
                    "has been saved successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to save your expense "
                    f"information: {e}"
                )

st.divider()

# ============================================================
# LOANS
# ============================================================

st.subheader("🏦 Loans")

st.caption(
    "Add each loan you're currently repaying. "
    "You can enter the amount still owed, interest rate "
    "and monthly repayment."
)


# ============================================================
# INITIALISE LOAN DRAFT
# ============================================================

if "loan_draft" not in st.session_state:

    existing_loans = get_loans(
        conn,
        user_id
    )

    draft_loans = []

    for loan in existing_loans:

        draft_loans.append({
            "id": loan["id"],
            "name": loan["name"],
            "principal": loan["principal"],
            "interest_rate": loan["interest_rate"],
            "monthly_payment": loan["monthly_payment"],
            "currency": loan["currency"]
        })

    st.session_state["loan_draft"] = draft_loans


loan_draft = st.session_state["loan_draft"]


# ============================================================
# ADD LOAN
# ============================================================

st.markdown("### ➕ Add a loan")

with st.expander(
    "Add a new loan",
    expanded=True
):

    new_loan_name = st.text_input(
        "Loan name",
        placeholder="e.g. Car Loan, Student Loan",
        key="new_loan_name"
    )

    col1, col2 = st.columns(2)

    with col1:

        new_loan_principal = st.number_input(
            "Amount still owed (Rs)",
            min_value=0.0,
            step=500.0,
            key="new_loan_principal"
        )

    with col2:

        new_loan_rate = st.number_input(
            "Interest rate (%)",
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key="new_loan_rate"
        )

    new_loan_payment = st.number_input(
        "Monthly payment (Rs)",
        min_value=0.0,
        step=50.0,
        key="new_loan_payment"
    )

    if st.button(
        "Add loan",
        type="primary",
        use_container_width=True
    ):

        if new_loan_name.strip() == "":

            st.error(
                "Please enter a loan name."
            )

        elif new_loan_principal <= 0:

            st.error(
                "Amount still owed must be greater than 0."
            )

        elif new_loan_payment <= 0:

            st.error(
                "Monthly payment must be greater than 0."
            )

        else:

            temp_id = (
                f"new_"
                f"{len(st.session_state['loan_draft']) + 1}"
            )

            st.session_state["loan_draft"].append({
                "id": temp_id,
                "name": new_loan_name.strip(),
                "principal": new_loan_principal,
                "interest_rate": new_loan_rate,
                "monthly_payment": new_loan_payment,
                "currency": "MUR"
            })

            st.session_state.pop(
                "new_loan_name",
                None
            )

            st.session_state.pop(
                "new_loan_principal",
                None
            )

            st.session_state.pop(
                "new_loan_rate",
                None
            )

            st.session_state.pop(
                "new_loan_payment",
                None
            )

            st.rerun()


# ============================================================
# YOUR LOANS
# ============================================================

st.markdown("### 🧾 Your loans")

if len(loan_draft) == 0:

    st.info(
        "You haven't added any loans yet. "
        "Use the form above to add your first loan."
    )

else:

    st.caption(
        "You can edit or remove loans here. "
        "Your changes will not be saved until you confirm them."
    )


# ============================================================
# DISPLAY / EDIT LOANS
# ============================================================

for loan in loan_draft:

    loan_id = loan["id"]
    widget_id = str(loan_id)

    with st.expander(
        f"{loan['name']} — "
        f"Rs "
        f"{loan['monthly_payment']:,.2f}/month"
    ):

        edited_name = st.text_input(
            "Loan name",
            value=loan["name"],
            key=f"loan_name_{widget_id}"
        )

        col1, col2 = st.columns(2)

        with col1:

            edited_principal = st.number_input(
                "Amount still owed (Rs)",
                min_value=0.0,
                value=float(loan["principal"]),
                step=500.0,
                key=f"loan_principal_{widget_id}"
            )

        with col2:

            edited_interest_rate = st.number_input(
                "Interest rate (%)",
                min_value=0.0,
                value=float(loan["interest_rate"]),
                step=0.1,
                format="%.2f",
                key=f"loan_rate_{widget_id}"
            )

        edited_payment = st.number_input(
            "Monthly payment (Rs)",
            min_value=0.0,
            value=float(loan["monthly_payment"]),
            step=50.0,
            key=f"loan_payment_{widget_id}"
        )

        if edited_payment <= 0:

            st.warning(
                "Monthly payment must be greater than 0."
            )

        if st.button(
            "🗑️ Remove loan",
            key=f"remove_loan_{widget_id}",
            use_container_width=True
        ):

            st.session_state["loan_draft"] = [
                item
                for item in st.session_state["loan_draft"]
                if item["id"] != loan_id
            ]

            st.rerun()


# ============================================================
# MONTHLY LOAN OVERVIEW
# ============================================================

total_principal_cents = 0
total_payment_cents = 0

for loan in loan_draft:

    loan_id = loan["id"]
    widget_id = str(loan_id)

    principal = st.session_state.get(
        f"loan_principal_{widget_id}",
        loan["principal"]
    )

    payment = st.session_state.get(
        f"loan_payment_{widget_id}",
        loan["monthly_payment"]
    )

    total_principal_cents += to_cents(
        principal
    )

    total_payment_cents += to_cents(
        payment
    )


st.divider()

st.markdown("### 📊 Loan overview")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Total amount still owed",
        f"Rs "
        f"{total_principal_cents // 100:,}."
        f"{total_principal_cents % 100:02d}"
    )

with col2:

    st.metric(
        "Total monthly repayments",
        f"Rs "
        f"{total_payment_cents // 100:,}."
        f"{total_payment_cents % 100:02d}"
    )


# ============================================================
# REVIEW & SAVE
# ============================================================

st.divider()

st.caption(
    "Your loan changes are not saved to your account yet. "
    "Review them before saving."
)


if st.button(
    "💾 Review & Save Changes",
    type="primary",
    use_container_width=True,
    key="save_loans_btn"
):

    pending_loans = []

    validation_error = None

    for loan in loan_draft:

        loan_id = loan["id"]
        widget_id = str(loan_id)

        edited_name = st.session_state.get(
            f"loan_name_{widget_id}",
            loan["name"]
        )

        edited_principal = st.session_state.get(
            f"loan_principal_{widget_id}",
            loan["principal"]
        )

        edited_interest_rate = st.session_state.get(
            f"loan_rate_{widget_id}",
            loan["interest_rate"]
        )

        edited_payment = st.session_state.get(
            f"loan_payment_{widget_id}",
            loan["monthly_payment"]
        )

        edited_name = edited_name.strip()

        if edited_name == "":

            validation_error = (
                "Every loan must have a name."
            )

            break

        if edited_principal <= 0:

            validation_error = (
                "Every loan's amount still owed "
                "must be greater than 0."
            )

            break

        if edited_payment <= 0:

            validation_error = (
                "Every loan's monthly payment "
                "must be greater than 0."
            )

            break

        if edited_interest_rate < 0:

            validation_error = (
                "Interest rate cannot be negative."
            )

            break

        pending_loans.append({
            "id": loan_id,
            "name": edited_name,
            "principal": edited_principal,
            "interest_rate": edited_interest_rate,
            "monthly_payment": edited_payment,
            "currency": loan["currency"]
        })

    if validation_error:

        st.error(
            validation_error
        )

    else:

        st.session_state[
            "pending_loan_save"
        ] = pending_loans

        st.session_state[
            "show_loan_confirmation"
        ] = True

        st.rerun()


# ============================================================
# LOAN CONFIRMATION
# ============================================================

if st.session_state.get(
    "show_loan_confirmation",
    False
):

    pending_loans = st.session_state.get(
        "pending_loan_save",
        []
    )

    st.warning(
        "Please review your loan changes before saving."
    )

    st.markdown(
        "#### Changes to be saved"
    )

    confirmation_principal_cents = 0
    confirmation_payment_cents = 0

    if len(pending_loans) == 0:

        st.info(
            "All loans will be removed."
        )

    for loan in pending_loans:

        principal_cents = to_cents(
            loan["principal"]
        )

        payment_cents = to_cents(
            loan["monthly_payment"]
        )

        confirmation_principal_cents += (
            principal_cents
        )

        confirmation_payment_cents += (
            payment_cents
        )

        st.write(
            f"**{loan['name']}** — "
            f"Rs "
            f"{principal_cents // 100:,}."
            f"{principal_cents % 100:02d} owed — "
            f"{loan['interest_rate']:.2f}% interest — "
            f"Rs "
            f"{payment_cents // 100:,}."
            f"{payment_cents % 100:02d}/month"
        )

    st.divider()

    st.markdown(
        f"**Total amount still owed:** "
        f"Rs "
        f"{confirmation_principal_cents // 100:,}."
        f"{confirmation_principal_cents % 100:02d}"
    )

    st.markdown(
        f"**Total monthly repayments:** "
        f"Rs "
        f"{confirmation_payment_cents // 100:,}."
        f"{confirmation_payment_cents % 100:02d}"
    )

    st.divider()

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:

        if st.button(
            "Cancel",
            use_container_width=True
        ):

            st.session_state.pop(
                "pending_loan_save",
                None
            )

            st.session_state[
                "show_loan_confirmation"
            ] = False

            st.rerun()

    with confirm_col2:

        if st.button(
            "✅ Confirm & Save",
            type="primary",
            use_container_width=True
        ):

            try:

                existing_loans = get_loans(
                    conn,
                    user_id
                )

                existing_ids = {
                    loan["id"]
                    for loan in existing_loans
                }

                pending_existing_ids = {
                    loan["id"]
                    for loan in pending_loans
                    if isinstance(
                        loan["id"],
                        int
                    )
                }

                # --------------------------------------------
                # DELETE REMOVED LOANS
                # --------------------------------------------

                for existing_id in existing_ids:

                    if (
                        existing_id
                        not in pending_existing_ids
                    ):

                        delete_loan(
                            conn=conn,
                            loan_id=existing_id,
                            user_id=user_id
                        )

                # --------------------------------------------
                # ADD / UPDATE LOANS
                # --------------------------------------------

                for loan in pending_loans:

                    loan_id = loan["id"]

                    if not isinstance(
                        loan_id,
                        int
                    ):

                        add_loan(
                            conn=conn,
                            user_id=user_id,
                            name=loan["name"],
                            principal=loan["principal"],
                            interest_rate=loan["interest_rate"],
                            monthly_payment=loan["monthly_payment"],
                            currency=loan["currency"]
                        )

                    else:

                        update_loan(
                            conn=conn,
                            loan_id=loan_id,
                            user_id=user_id,
                            name=loan["name"],
                            principal=loan["principal"],
                            interest_rate=loan["interest_rate"],
                            monthly_payment=loan["monthly_payment"],
                            currency=loan["currency"]
                        )

                # --------------------------------------------
                # RELOAD FROM DATABASE
                # --------------------------------------------

                st.session_state["loan_draft"] = (
                    get_loans(
                        conn,
                        user_id
                    )
                )

                st.session_state.pop(
                    "pending_loan_save",
                    None
                )

                st.session_state[
                    "show_loan_confirmation"
                ] = False

                st.success(
                    "Your loan information "
                    "has been saved successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to save your loan "
                    f"information: {e}"
                )
st.divider()

# ============================================================
# SAVINGS
# ============================================================

st.subheader(t("🏦 Savings"))

st.caption(
    t(
        "Keep track of your overall savings and how much "
        "you plan to save each month."
    )
)


# ============================================================
# INITIALISE SAVINGS DRAFT
# ============================================================

if "savings_draft" not in st.session_state:

    existing_savings = get_savings(
        conn,
        user_id
    )

    if existing_savings is None:

        st.session_state["savings_draft"] = {
            "current_savings": 0.0,
            "monthly_savings": 0.0,
            "savings_rate": 0.0,
            "currency": "MUR"
        }

    else:

        st.session_state["savings_draft"] = {
            "current_savings": existing_savings["current_savings"],
            "monthly_savings": existing_savings["monthly_savings"],
            "savings_rate": existing_savings["savings_rate"],
            "currency": existing_savings["currency"]
        }


savings_draft = st.session_state["savings_draft"]


# ============================================================
# CURRENT SAVINGS
# ============================================================

st.markdown(
    f"### {t('💰 Your current savings')}"
)

edited_current_savings = st.number_input(
    t("How much do you currently have saved?"),
    min_value=0.0,
    value=float(
        savings_draft["current_savings"]
    ),
    step=100.0,
    key="savings_current_amount"
)


# ============================================================
# AVAILABLE AFTER EXPENSES
# ============================================================

current_income = st.session_state.get(
    "income",
    0
)

current_expenses = st.session_state.get(
    "expenses",
    0
)

try:

    income_cents = to_cents(
        current_income
    )

except (TypeError, ValueError):

    income_cents = 0


try:

    expenses_cents = to_cents(
        current_expenses
    )

except (TypeError, ValueError):

    expenses_cents = 0


available_cents = (
    income_cents
    - expenses_cents
)


available = available_cents / 100


# ============================================================
# MONTHLY SAVINGS
# ============================================================

st.markdown(
    f"### {t('📈 Monthly savings')}"
)

st.caption(
    t(
        f"You have about Rs {available:,.2f} "
        "available after your current expenses."
    )
)

edited_monthly_savings = st.number_input(
    t("How much would you like to save each month?"),
    min_value=0.0,
    value=float(
        savings_draft["monthly_savings"]
    ),
    step=100.0,
    key="savings_monthly_amount",
    help=(
        f"You currently have about "
        f"Rs {available:,.2f} available "
        "after expenses."
    )
)


if edited_monthly_savings > available:

    st.warning(
        f"⚠️ You've set your savings target to "
        f"Rs {edited_monthly_savings:,.2f}/month, "
        f"but only Rs {available:,.2f} is currently "
        "available after your expenses."
    )


# ============================================================
# SAVINGS INTEREST RATE
# ============================================================

st.markdown(
    f"### {t('📊 Savings growth')}"
)

edited_savings_rate = st.slider(
    t("Expected annual interest rate on your savings (%)"),
    0.0,
    10.0,
    value=float(
        savings_draft["savings_rate"]
    ),
    step=0.1,
    key="savings_interest_rate"
)


# ============================================================
# SAVINGS OVERVIEW
# ============================================================

st.divider()

st.markdown(
    f"### {t('📊 Savings overview')}"
)

current_savings_cents = to_cents(
    edited_current_savings
)

monthly_savings_cents = to_cents(
    edited_monthly_savings
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        t("Current savings"),
        f"Rs "
        f"{current_savings_cents // 100:,}."
        f"{current_savings_cents % 100:02d}"
    )

with col2:

    st.metric(
        t("Planned monthly savings"),
        f"Rs "
        f"{monthly_savings_cents // 100:,}."
        f"{monthly_savings_cents % 100:02d}"
    )

with col3:

    st.metric(
        t("Expected annual rate"),
        f"{edited_savings_rate:.1f}%"
    )


# ============================================================
# REVIEW & SAVE
# ============================================================

st.divider()

st.caption(
    t(
        "Your savings changes are not saved to your account yet. "
        "Review them before saving."
    )
)


if st.button(
    t("💾 Review & Save Changes"),
    type="primary",
    use_container_width=True,
    key="save_savings_btn"
):

    validation_error = None

    if edited_current_savings < 0:

        validation_error = (
            "Current savings cannot be negative."
        )

    elif edited_monthly_savings < 0:

        validation_error = (
            "Monthly savings cannot be negative."
        )

    elif edited_savings_rate < 0:

        validation_error = (
            "Savings interest rate cannot be negative."
        )

    if validation_error:

        st.error(
            t(validation_error)
        )

    else:

        st.session_state[
            "pending_savings_save"
        ] = {
            "current_savings": edited_current_savings,
            "monthly_savings": edited_monthly_savings,
            "savings_rate": edited_savings_rate,
            "currency": savings_draft["currency"]
        }

        st.session_state[
            "show_savings_confirmation"
        ] = True

        st.rerun()


# ============================================================
# SAVINGS CONFIRMATION
# ============================================================

if st.session_state.get(
    "show_savings_confirmation",
    False
):

    pending_savings = st.session_state.get(
        "pending_savings_save"
    )

    if pending_savings is not None:

        st.warning(
            t(
                "Please review your savings changes "
                "before saving."
            )
        )

        st.markdown(
            f"#### {t('Changes to be saved')}"
        )

        confirmation_current_cents = to_cents(
            pending_savings["current_savings"]
        )

        confirmation_monthly_cents = to_cents(
            pending_savings["monthly_savings"]
        )

        st.write(
            f"**{t('Current savings')}:** "
            f"Rs "
            f"{confirmation_current_cents // 100:,}."
            f"{confirmation_current_cents % 100:02d}"
        )

        st.write(
            f"**{t('Monthly savings')}:** "
            f"Rs "
            f"{confirmation_monthly_cents // 100:,}."
            f"{confirmation_monthly_cents % 100:02d}"
        )

        st.write(
            f"**{t('Expected annual interest rate')}:** "
            f"{pending_savings['savings_rate']:.1f}%"
        )

        st.divider()

        confirm_col1, confirm_col2 = st.columns(2)

        with confirm_col1:

            if st.button(
                t("Cancel"),
                use_container_width=True
            ):

                st.session_state.pop(
                    "pending_savings_save",
                    None
                )

                st.session_state[
                    "show_savings_confirmation"
                ] = False

                st.rerun()

        with confirm_col2:

            if st.button(
                t("✅ Confirm & Save"),
                type="primary",
                use_container_width=True
            ):

                try:

                    add_or_update_savings(
                        conn=conn,
                        user_id=user_id,
                        current_savings=(
                            pending_savings[
                                "current_savings"
                            ]
                        ),
                        monthly_savings=(
                            pending_savings[
                                "monthly_savings"
                            ]
                        ),
                        savings_rate=(
                            pending_savings[
                                "savings_rate"
                            ]
                        ),
                        currency=(
                            pending_savings[
                                "currency"
                            ]
                        )
                    )

                    # Reload directly from database
                    saved_savings = get_savings(
                        conn,
                        user_id
                    )

                    st.session_state[
                        "savings_draft"
                    ] = {
                        "current_savings": (
                            saved_savings[
                                "current_savings"
                            ]
                        ),
                        "monthly_savings": (
                            saved_savings[
                                "monthly_savings"
                            ]
                        ),
                        "savings_rate": (
                            saved_savings[
                                "savings_rate"
                            ]
                        ),
                        "currency": (
                            saved_savings[
                                "currency"
                            ]
                        )
                    }

                    st.session_state.pop(
                        "pending_savings_save",
                        None
                    )

                    st.session_state[
                        "show_savings_confirmation"
                    ] = False

                    st.success(
                        t(
                            "Your savings information "
                            "has been saved successfully."
                        )
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"{t('Unable to save your savings information')}: "
                        f"{e}"
                    )
st.divider()


# ============================================================
# GOALS
# ============================================================

st.subheader(t("🎯 Your Goals"))

st.caption(
    t(
        "Add the financial goals you're working towards. "
        "You can set the amount you need and when you want "
        "to achieve each goal."
    )
)


# ============================================================
# INITIALISE GOAL DRAFT
# ============================================================

if "goal_draft" not in st.session_state:

    existing_goals = get_goals(
        conn,
        user_id
    )

    draft_goals = []

    for goal in existing_goals:

        draft_goals.append({
            "id": goal["id"],
            "goal_name": goal["goal_name"],
            "target_amount": goal["target_amount"],
            "current_amount": goal["current_amount"],
            "target_date": goal["target_date"],
            "priority": goal["priority"],
            "status": goal["status"],
            "currency": goal["currency"]
        })

    st.session_state["goal_draft"] = draft_goals


goal_draft = st.session_state["goal_draft"]


# ============================================================
# ADD GOAL
# ============================================================

st.markdown(
    f"### {t('➕ Add a goal')}"
)

with st.expander(
    t("Add a new goal"),
    expanded=True
):

    new_goal_name = st.text_input(
        t("Goal name"),
        placeholder="e.g. New laptop, Emergency fund, Car",
        key="new_goal_name"
    )

    col1, col2 = st.columns(2)

    with col1:

        new_goal_amount = st.number_input(
            t("Amount needed (Rs)"),
            min_value=0.0,
            step=500.0,
            key="new_goal_amount"
        )

    with col2:

        new_goal_years = st.number_input(
            t("Years to achieve"),
            min_value=1,
            max_value=30,
            step=1,
            key="new_goal_years"
        )

    if st.button(
        t("Add goal"),
        type="primary",
        use_container_width=True
    ):

        if new_goal_name.strip() == "":

            st.error(
                t("Please give your goal a name.")
            )

        elif new_goal_amount <= 0:

            st.error(
                t("Goal amount must be greater than 0.")
            )

        else:

            temp_id = (
                f"new_"
                f"{len(st.session_state['goal_draft']) + 1}"
            )

            st.session_state["goal_draft"].append({
                "id": temp_id,
                "goal_name": new_goal_name.strip(),
                "target_amount": new_goal_amount,
                "current_amount": 0.0,
                "target_date": None,
                "priority": 0,
                "status": "in_progress",
                "currency": "MUR",
                "years": new_goal_years
            })

            st.session_state.pop(
                "new_goal_name",
                None
            )

            st.session_state.pop(
                "new_goal_amount",
                None
            )

            st.session_state.pop(
                "new_goal_years",
                None
            )

            st.rerun()


# ============================================================
# YOUR GOALS
# ============================================================

st.markdown(
    f"### {t('🎯 Your goals')}"
)

if len(goal_draft) == 0:

    st.info(
        t(
            "You haven't added any goals yet. "
            "Use the form above to add your first goal."
        )
    )

else:

    st.caption(
        t(
            "You can edit or remove goals here. "
            "Your changes will not be saved until you confirm them."
        )
    )


# ============================================================
# DISPLAY / EDIT GOALS
# ============================================================

for goal in goal_draft:

    goal_id = goal["id"]
    widget_id = str(goal_id)

    target_amount_cents = to_cents(
        goal["target_amount"]
    )

    with st.expander(
        f"{goal['goal_name']} — "
        f"Rs "
        f"{target_amount_cents // 100:,}."
        f"{target_amount_cents % 100:02d}"
    ):

        edited_name = st.text_input(
            t("Goal name"),
            value=goal["goal_name"],
            key=f"goal_name_{widget_id}"
        )

        edited_amount = st.number_input(
            t("Amount needed (Rs)"),
            min_value=0.0,
            value=float(goal["target_amount"]),
            step=500.0,
            key=f"goal_amount_{widget_id}"
        )

        # Existing goals get their target date converted
        # back into an approximate number of years.
        existing_years = 1

        if goal.get("years") is not None:

            existing_years = int(
                goal["years"]
            )

        elif goal.get("target_date"):

            try:

                target_date = datetime.strptime(
                    goal["target_date"],
                    "%Y-%m-%d"
                ).date()

                today = date.today()

                existing_years = max(
                    1,
                    target_date.year - today.year
                )

            except (
                ValueError,
                TypeError
            ):

                existing_years = 1

        edited_years = st.number_input(
            t("Years to achieve"),
            min_value=1,
            max_value=30,
            value=existing_years,
            step=1,
            key=f"goal_years_{widget_id}"
        )

        if edited_amount <= 0:

            st.warning(
                t(
                    "Amount must be greater than 0."
                )
            )

        if st.button(
            t("🗑️ Remove goal"),
            key=f"remove_goal_{widget_id}",
            use_container_width=True
        ):

            st.session_state["goal_draft"] = [
                item
                for item in st.session_state["goal_draft"]
                if item["id"] != goal_id
            ]

            st.rerun()


# ============================================================
# GOAL OVERVIEW
# ============================================================

total_goal_amount_cents = 0

for goal in goal_draft:

    goal_id = goal["id"]
    widget_id = str(goal_id)

    amount = st.session_state.get(
        f"goal_amount_{widget_id}",
        goal["target_amount"]
    )

    total_goal_amount_cents += to_cents(
        amount
    )


st.divider()

st.markdown(
    f"### {t('📊 Goal overview')}"
)

col1, col2 = st.columns(2)

with col1:

    st.metric(
        t("Number of goals"),
        len(goal_draft)
    )

with col2:

    st.metric(
        t("Total amount needed"),
        f"Rs "
        f"{total_goal_amount_cents // 100:,}."
        f"{total_goal_amount_cents % 100:02d}"
    )


# ============================================================
# REVIEW & SAVE
# ============================================================

st.divider()

st.caption(
    t(
        "Your goal changes are not saved to your account yet. "
        "Review them before saving."
    )
)


if st.button(
    t("💾 Review & Save Changes"),
    type="primary",
    use_container_width=True,
    key="save_goals_btn"
):

    pending_goals = []

    validation_error = None

    for goal in goal_draft:

        goal_id = goal["id"]
        widget_id = str(goal_id)

        edited_name = st.session_state.get(
            f"goal_name_{widget_id}",
            goal["goal_name"]
        )

        edited_amount = st.session_state.get(
            f"goal_amount_{widget_id}",
            goal["target_amount"]
        )

        edited_years = st.session_state.get(
            f"goal_years_{widget_id}",
            1
        )

        edited_name = edited_name.strip()

        if edited_name == "":

            validation_error = (
                "Every goal must have a name."
            )

            break

        if edited_amount <= 0:

            validation_error = (
                "Every goal amount must be greater than 0."
            )

            break

        if edited_years < 1:

            validation_error = (
                "Every goal must have at least "
                "1 year to achieve."
            )

            break

        # Calculate target date from years.
        target_date = (
            date.today().replace(
                year=date.today().year + int(edited_years)
            )
        )

        pending_goals.append({
            "id": goal_id,
            "goal_name": edited_name,
            "target_amount": edited_amount,
            "current_amount": goal.get(
                "current_amount",
                0.0
            ),
            "target_date": target_date.isoformat(),
            "priority": goal.get(
                "priority",
                0
            ),
            "status": goal.get(
                "status",
                "in_progress"
            ),
            "currency": goal["currency"],
            "years": edited_years
        })

    if validation_error:

        st.error(
            t(validation_error)
        )

    else:

        st.session_state[
            "pending_goal_save"
        ] = pending_goals

        st.session_state[
            "show_goal_confirmation"
        ] = True

        st.rerun()


# ============================================================
# GOAL CONFIRMATION
# ============================================================

if st.session_state.get(
    "show_goal_confirmation",
    False
):

    pending_goals = st.session_state.get(
        "pending_goal_save",
        []
    )

    st.warning(
        t(
            "Please review your goal changes before saving."
        )
    )

    st.markdown(
        f"#### {t('Changes to be saved')}"
    )

    confirmation_total_cents = 0

    if len(pending_goals) == 0:

        st.info(
            t("All goals will be removed.")
        )

    for goal in pending_goals:

        amount_cents = to_cents(
            goal["target_amount"]
        )

        confirmation_total_cents += amount_cents

        st.write(
            f"**{goal['goal_name']}** — "
            f"Rs "
            f"{amount_cents // 100:,}."
            f"{amount_cents % 100:02d} — "
            f"{goal['years']} "
            f"{t('years')}"
        )

        st.caption(
            f"{t('Target date')}: "
            f"{goal['target_date']}"
        )

    st.divider()

    st.markdown(
        f"**{t('Total amount needed')}:** "
        f"Rs "
        f"{confirmation_total_cents // 100:,}."
        f"{confirmation_total_cents % 100:02d}"
    )

    st.divider()

    confirm_col1, confirm_col2 = st.columns(2)

    with confirm_col1:

        if st.button(
            t("Cancel"),
            use_container_width=True
        ):

            st.session_state.pop(
                "pending_goal_save",
                None
            )

            st.session_state[
                "show_goal_confirmation"
            ] = False

            st.rerun()

    with confirm_col2:

        if st.button(
            t("✅ Confirm & Save"),
            type="primary",
            use_container_width=True
        ):

            try:

                existing_goals = get_goals(
                    conn,
                    user_id
                )

                existing_ids = {
                    goal["id"]
                    for goal in existing_goals
                }

                pending_existing_ids = {
                    goal["id"]
                    for goal in pending_goals
                    if isinstance(
                        goal["id"],
                        int
                    )
                }

                # --------------------------------------------
                # DELETE REMOVED GOALS
                # --------------------------------------------

                for existing_id in existing_ids:

                    if (
                        existing_id
                        not in pending_existing_ids
                    ):

                        delete_goal(
                            conn=conn,
                            goal_id=existing_id,
                            user_id=user_id
                        )

                # --------------------------------------------
                # ADD / UPDATE GOALS
                # --------------------------------------------

                for goal in pending_goals:

                    goal_id = goal["id"]

                    if not isinstance(
                        goal_id,
                        int
                    ):

                        add_goal(
                            conn=conn,
                            user_id=user_id,
                            goal_name=goal[
                                "goal_name"
                            ],
                            target_amount=goal[
                                "target_amount"
                            ],
                            current_amount=goal[
                                "current_amount"
                            ],
                            target_date=goal[
                                "target_date"
                            ],
                            priority=goal[
                                "priority"
                            ],
                            status=goal[
                                "status"
                            ],
                            currency=goal[
                                "currency"
                            ]
                        )

                    else:

                        update_goal(
                            conn=conn,
                            goal_id=goal_id,
                            user_id=user_id,
                            goal_name=goal[
                                "goal_name"
                            ],
                            target_amount=goal[
                                "target_amount"
                            ],
                            current_amount=goal[
                                "current_amount"
                            ],
                            target_date=goal[
                                "target_date"
                            ],
                            priority=goal[
                                "priority"
                            ],
                            status=goal[
                                "status"
                            ],
                            currency=goal[
                                "currency"
                            ]
                        )

                # --------------------------------------------
                # RELOAD FROM DATABASE
                # --------------------------------------------

                st.session_state["goal_draft"] = (
                    get_goals(
                        conn,
                        user_id
                    )
                )

                st.session_state.pop(
                    "pending_goal_save",
                    None
                )

                st.session_state[
                    "show_goal_confirmation"
                ] = False

                st.success(
                    t(
                        "Your goals have been "
                        "saved successfully."
                    )
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"{t('Unable to save your goals')}: "
                    f"{e}"
                )

st.divider()


# ============================================================
# DASHBOARD
# ============================================================

if st.button(
    t("📊 View my Dashboard"),
    type="primary"
):

    st.switch_page(
        "pages/3_Dashboard.py"
    )