from app_model.money import (
    encrypt_amount,
    decrypt_amount_decimal
)


# ============================================================
# INCOME
# ============================================================

def add_income(conn, user_id, source, amount, currency="MUR",
               frequency="monthly"):
    """
    Adds an income source for a user.

    The amount is converted to cents and encrypted
    before being stored in the database.
    """

    cur = conn.cursor()

    encrypted_amount = encrypt_amount(amount)

    cur.execute(
        """
        INSERT INTO income (
            user_id,
            source,
            currency,
            amount_encrypted,
            frequency
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            source,
            currency,
            encrypted_amount,
            frequency
        )
    )

    conn.commit()

    return cur.lastrowid


def get_income(conn, user_id):
    """
    Retrieves all income sources belonging to a user.

    Returns decrypted monetary values.
    """

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            source,
            currency,
            amount_encrypted,
            frequency
        FROM income
        WHERE user_id = ?
        ORDER BY id
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    income = []

    for row in rows:
        income.append({
            "id": row[0],
            "source": row[1],
            "currency": row[2],
            "amount": decrypt_amount_decimal(row[3]),
            "frequency": row[4]
        })

    return income


def update_income(conn, income_id, user_id, source, amount,
                   currency="MUR", frequency="monthly"):
    """
    Updates an existing income record.

    user_id is included to ensure that a user can only
    update their own financial record.
    """

    encrypted_amount = encrypt_amount(amount)

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE income
        SET
            source = ?,
            currency = ?,
            amount_encrypted = ?,
            frequency = ?
        WHERE id = ?
        AND user_id = ?
        """,
        (
            source,
            currency,
            encrypted_amount,
            frequency,
            income_id,
            user_id
        )
    )

    conn.commit()

    return cur.rowcount > 0


def delete_income(conn, income_id, user_id):
    """
    Deletes an income record belonging to the user.
    """

    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM income
        WHERE id = ?
        AND user_id = ?
        """,
        (income_id, user_id)
    )

    conn.commit()

    return cur.rowcount > 0

def to_monthly_cents(amount_cents, frequency):
    """
    Converts an amount stored as integer cents
    into an estimated monthly amount in integer cents.

    All calculations remain in integer cents.
    """

    if frequency == "daily":
        return (amount_cents * 365 + 6) // 12

    elif frequency == "weekly":
        return (amount_cents * 52 + 6) // 12

    elif frequency == "monthly":
        return amount_cents

    elif frequency == "yearly":
        return (amount_cents + 6) // 12

    else:
        raise ValueError(
            f"Unsupported frequency: {frequency}"
        )

# ============================================================
# EXPENSES
# ============================================================

def add_expense(
    conn,
    user_id,
    category,
    name,
    amount,
    frequency="monthly",
    expense_type="Need",
    currency="MUR"
):
    """
    Adds an expense for a user.

    expense_type should be:
        Need
        Want
    """

    if expense_type not in ("Need", "Want"):
        raise ValueError(
            "expense_type must be either 'Need' or 'Want'."
        )

    encrypted_amount = encrypt_amount(amount)

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO expenses (
            user_id,
            category,
            name,
            currency,
            amount_encrypted,
            frequency,
            expense_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category,
            name,
            currency,
            encrypted_amount,
            frequency,
            expense_type
        )
    )

    conn.commit()

    return cur.lastrowid


def get_expenses(conn, user_id):
    """
    Retrieves all expenses belonging to a user.

    Monetary values are decrypted before being returned.
    """

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            category,
            name,
            currency,
            amount_encrypted,
            frequency,
            expense_type
        FROM expenses
        WHERE user_id = ?
        ORDER BY id
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    expenses = []

    for row in rows:
        expenses.append({
            "id": row[0],
            "category": row[1],
            "name": row[2],
            "currency": row[3],
            "amount": decrypt_amount_decimal(row[4]),
            "frequency": row[5],
            "expense_type": row[6]
        })

    return expenses


def update_expense(
    conn,
    expense_id,
    user_id,
    category,
    name,
    amount,
    frequency="monthly",
    expense_type="Need",
    currency="MUR"
):
    """
    Updates an existing expense belonging to the user.
    """

    if expense_type not in ("Need", "Want"):
        raise ValueError(
            "expense_type must be either 'Need' or 'Want'."
        )

    encrypted_amount = encrypt_amount(amount)

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE expenses
        SET
            category = ?,
            name = ?,
            currency = ?,
            amount_encrypted = ?,
            frequency = ?,
            expense_type = ?
        WHERE id = ?
        AND user_id = ?
        """,
        (
            category,
            name,
            currency,
            encrypted_amount,
            frequency,
            expense_type,
            expense_id,
            user_id
        )
    )

    conn.commit()

    return cur.rowcount > 0


def delete_expense(conn, expense_id, user_id):
    """
    Deletes an expense belonging to the user.
    """

    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM expenses
        WHERE id = ?
        AND user_id = ?
        """,
        (expense_id, user_id)
    )

    conn.commit()

    return cur.rowcount > 0


# ============================================================
# SAVINGS
# ============================================================

def add_or_update_savings(
    conn,
    user_id,
    current_savings,
    monthly_savings,
    savings_rate,
    currency="MUR"
):
    """
    Creates or updates the user's savings record.

    Each user can have only one savings record.
    """

    current_encrypted = encrypt_amount(current_savings)
    monthly_encrypted = encrypt_amount(monthly_savings)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM savings
        WHERE user_id = ?
        """,
        (user_id,)
    )

    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE savings
            SET
                current_savings_encrypted = ?,
                monthly_savings_encrypted = ?,
                savings_rate = ?,
                currency = ?
            WHERE user_id = ?
            """,
            (
                current_encrypted,
                monthly_encrypted,
                savings_rate,
                currency,
                user_id
            )
        )
    else:
        cur.execute(
            """
            INSERT INTO savings (
                user_id,
                current_savings_encrypted,
                monthly_savings_encrypted,
                savings_rate,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                current_encrypted,
                monthly_encrypted,
                savings_rate,
                currency
            )
        )

    conn.commit()

    return True


def get_savings(conn, user_id):
    """
    Retrieves the user's savings information.
    """

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            current_savings_encrypted,
            monthly_savings_encrypted,
            savings_rate,
            currency
        FROM savings
        WHERE user_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "current_savings": decrypt_amount_decimal(row[1]),
        "monthly_savings": decrypt_amount_decimal(row[2]),
        "savings_rate": row[3],
        "currency": row[4]
    }


# ============================================================
# LOANS
# ============================================================

def add_loan(
    conn,
    user_id,
    name,
    principal,
    interest_rate,
    monthly_payment,
    currency="MUR"
):
    """
    Adds a loan for a user.

    Principal and monthly payment are encrypted.
    Interest rate is not monetary, so it remains a REAL value.
    """

    principal_encrypted = encrypt_amount(principal)
    payment_encrypted = encrypt_amount(monthly_payment)

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO loans (
            user_id,
            name,
            currency,
            principal_encrypted,
            interest_rate,
            monthly_payment_encrypted
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            currency,
            principal_encrypted,
            interest_rate,
            payment_encrypted
        )
    )

    conn.commit()

    return cur.lastrowid


def get_loans(conn, user_id):
    """
    Retrieves all loans belonging to a user.
    """

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            name,
            currency,
            principal_encrypted,
            interest_rate,
            monthly_payment_encrypted
        FROM loans
        WHERE user_id = ?
        ORDER BY id
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    loans = []

    for row in rows:
        loans.append({
            "id": row[0],
            "name": row[1],
            "currency": row[2],
            "principal": decrypt_amount_decimal(row[3]),
            "interest_rate": row[4],
            "monthly_payment": decrypt_amount_decimal(row[5])
        })

    return loans


def update_loan(
    conn,
    loan_id,
    user_id,
    name,
    principal,
    interest_rate,
    monthly_payment,
    currency="MUR"
):
    """
    Updates a loan belonging to the user.
    """

    principal_encrypted = encrypt_amount(principal)
    payment_encrypted = encrypt_amount(monthly_payment)

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE loans
        SET
            name = ?,
            currency = ?,
            principal_encrypted = ?,
            interest_rate = ?,
            monthly_payment_encrypted = ?
        WHERE id = ?
        AND user_id = ?
        """,
        (
            name,
            currency,
            principal_encrypted,
            interest_rate,
            payment_encrypted,
            loan_id,
            user_id
        )
    )

    conn.commit()

    return cur.rowcount > 0


def delete_loan(conn, loan_id, user_id):
    """
    Deletes a loan belonging to the user.
    """

    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM loans
        WHERE id = ?
        AND user_id = ?
        """,
        (loan_id, user_id)
    )

    conn.commit()

    return cur.rowcount > 0


# ============================================================
# FINANCIAL GOALS
# ============================================================

# ============================================================
# GOALS
# ============================================================

def add_goal(
    conn,
    user_id,
    goal_name,
    target_amount,
    current_amount=0,
    target_date=None,
    priority=0,
    status="in_progress",
    currency="MUR"
):
    """
    Adds a financial goal for a user.

    Monetary values are encrypted before being stored.
    """

    if status not in (
        "in_progress",
        "achieved",
        "postponed"
    ):
        raise ValueError(
            "Invalid goal status."
        )

    target_encrypted = encrypt_amount(
        target_amount
    )

    current_encrypted = encrypt_amount(
        current_amount
    )

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO financial_goals (
            user_id,
            goal_name,
            currency,
            target_amount_encrypted,
            current_amount_encrypted,
            target_date,
            priority,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            goal_name,
            currency,
            target_encrypted,
            current_encrypted,
            target_date,
            priority,
            status
        )
    )

    conn.commit()

    return cur.lastrowid


def get_goals(conn, user_id):
    """
    Retrieves all financial goals belonging to a user.
    """

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            goal_name,
            currency,
            target_amount_encrypted,
            current_amount_encrypted,
            target_date,
            priority,
            status
        FROM financial_goals
        WHERE user_id = ?
        ORDER BY priority DESC, id
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    goals = []

    for row in rows:

        goals.append({
            "id": row[0],
            "goal_name": row[1],
            "currency": row[2],
            "target_amount": decrypt_amount_decimal(
                row[3]
            ),
            "current_amount": decrypt_amount_decimal(
                row[4]
            ),
            "target_date": row[5],
            "priority": row[6],
            "status": row[7]
        })

    return goals


def update_goal(
    conn,
    goal_id,
    user_id,
    goal_name,
    target_amount,
    current_amount=0,
    target_date=None,
    priority=0,
    status="in_progress",
    currency="MUR"
):
    """
    Updates a financial goal belonging to the user.
    """

    if status not in (
        "in_progress",
        "achieved",
        "postponed"
    ):
        raise ValueError(
            "Invalid goal status."
        )

    target_encrypted = encrypt_amount(
        target_amount
    )

    current_encrypted = encrypt_amount(
        current_amount
    )

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE financial_goals
        SET
            goal_name = ?,
            currency = ?,
            target_amount_encrypted = ?,
            current_amount_encrypted = ?,
            target_date = ?,
            priority = ?,
            status = ?
        WHERE id = ?
        AND user_id = ?
        """,
        (
            goal_name,
            currency,
            target_encrypted,
            current_encrypted,
            target_date,
            priority,
            status,
            goal_id,
            user_id
        )
    )

    conn.commit()

    return cur.rowcount > 0


def delete_goal(conn, goal_id, user_id):
    """
    Deletes a financial goal belonging to the user.
    """

    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM financial_goals
        WHERE id = ?
        AND user_id = ?
        """,
        (goal_id, user_id)
    )

    conn.commit()

    return cur.rowcount > 0

# ============================================================
# USER PROFILE
# ============================================================

def get_user_profile(conn, user_id):
    """
    Retrieves the profile information for a user.
    """

    cur = conn.cursor()

    cur.execute("""
        SELECT
            user_id,
            email,
            avatar,
            background_color,
            role,
            occupation,
            financial_experience,
            living_situation,
            dependants,
            personalisation_enabled
        FROM user_profile
        WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()

    if row is None:
        return None

    return {
        "user_id": row[0],
        "email": row[1],
        "avatar": row[2],
        "background_color": row[3],
        "role": row[4],
        "occupation": row[5],
        "financial_experience": row[6],
        "living_situation": row[7],
        "dependants": row[8],
        "personalisation_enabled": bool(row[9])
    }


def update_user_profile(
    conn,
    user_id,
    occupation=None,
    financial_experience=None,
    email=None,
    avatar=None,
    background_color=None,
    living_situation=None,
    dependants=None,
    personalisation_enabled=None
):
    """
    Updates the user's profile information.

    Only the supplied values are changed.
    Existing values are preserved when an argument is None.
    """

    current_profile = get_user_profile(conn, user_id)

    if current_profile is None:
        raise ValueError(
            "User profile does not exist."
        )

    if occupation is None:
        occupation = current_profile["occupation"]

    if financial_experience is None:
        financial_experience = current_profile["financial_experience"]

    if email is None:
        email = current_profile["email"]

    if avatar is None:
        avatar = current_profile["avatar"]

    if background_color is None:
        background_color = current_profile["background_color"]

    if living_situation is None:
        living_situation = current_profile["living_situation"]

    if dependants is None:
        dependants = current_profile["dependants"]

    if personalisation_enabled is None:
        personalisation_enabled = current_profile["personalisation_enabled"]

    cur = conn.cursor()

    cur.execute("""
        UPDATE user_profile
        SET
            email = ?,
            avatar = ?,
            background_color = ?,
            occupation = ?,
            financial_experience = ?,
            living_situation = ?,
            dependants = ?,
            personalisation_enabled = ?
        WHERE user_id = ?
    """, (
        email,
        avatar,
        background_color,
        occupation,
        financial_experience,
        living_situation,
        dependants,
        int(personalisation_enabled),
        user_id
    ))

    conn.commit()

    return cur.rowcount > 0


def create_user_profile_record(
    conn,
    user_id,
    email,
    occupation=None,
    financial_experience=None,
    avatar=None,
    background_color=None,
    living_situation=None,
    dependants=None,
    personalisation_enabled=False,
    role="user"
):
    """
    Creates a profile record for a user.

    This is useful when a user has been created in users_login
    but does not yet have a corresponding profile.
    """

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_profile (
            user_id,
            email,
            avatar,
            background_color,
            role,
            occupation,
            financial_experience,
            living_situation,
            dependants,
            personalisation_enabled
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        email,
        avatar,
        background_color,
        role,
        occupation,
        financial_experience,
        living_situation,
        dependants,
        int(personalisation_enabled)
    ))

    conn.commit()

    return cur.lastrowid


def delete_user_profile(conn, user_id):
    """
    Deletes a user's profile record.
    """

    cur = conn.cursor()

    cur.execute("""
        DELETE FROM user_profile
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()

    return cur.rowcount > 0