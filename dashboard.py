import streamlit as st
from datetime import date

from database import (
    FINANCIAL_CATEGORIES,

    get_all_users,
    get_active_members,
    get_pending_users,
    get_user_by_id,
    update_user_profile,
    update_user_status,
    delete_user,

    add_financial_record,
    get_user_financial_records,
    get_all_financial_records,
    get_member_financial_summary,
    update_financial_record,
    delete_financial_record,

    send_message,
    get_user_messages,
    get_conversation,
    get_message_contacts,
    mark_conversation_read,
    get_unread_count,

    create_admin_message,
    get_admin_messages,
    resolve_admin_message,

    create_login_issue,
    get_login_issues,
    resolve_login_issue,

    create_announcement,
    get_announcements,
    get_all_announcements,
    update_announcement,
    delete_announcement
)

from validator import reset_user_password


# =========================================================
# MEMBER WELCOME
# =========================================================

def show_welcome(user):
    

    st.title(
        f"🤝 Welcome, {user['full_name']}!"
    )

    st.success(
        "Welcome to ROCKVILLE LEAGUE OF FRIENDS CLUB."
    )

    st.markdown("""
    ## ROCKVILLE LEAGUE OF FRIENDS CLUB

    This platform helps members stay connected,
    communicate with one another, keep their contact
    information up to date and view their personal
    financial records.

    We value friendship, unity, accountability and
    mutual support among all members.
    """)

    st.divider()

    st.subheader("📰 Latest News & Announcements")

    announcements = get_announcements()

    if not announcements:

        st.info(
            "There are currently no announcements."
        )

    for announcement in announcements:

        with st.container(border=True):

            st.subheader(
                announcement["title"]
            )

            st.write(
                announcement["content"]
            )

            st.caption(
                f"Posted by {announcement['author_name']} "
                f"on {announcement['created_at']}"
            )


# =========================================================
# MEMBER PROFILE
# =========================================================

def show_profile(user):

    st.title("👤 My Profile")

    with st.form("profile_form"):

        full_name = st.text_input(
            "Full Name",
            value=user["full_name"]
        )

        email = st.text_input(
            "Email",
            value=user["email"]
        )

        phone = st.text_input(
            "Phone",
            value=user["phone"] or ""
        )

        address = st.text_area(
            "Address",
            value=user["address"] or ""
        )

        emergency = st.text_input(
            "Emergency Contact",
            value=user["emergency_contact"] or ""
        )

        submit = st.form_submit_button(
            "Save Profile",
            use_container_width=True
        )

    if submit:

        success, message = update_user_profile(
            user["id"],
            full_name,
            email,
            phone,
            address,
            emergency
        )

        if success:

            user["full_name"] = full_name
            user["email"] = email
            user["phone"] = phone
            user["address"] = address
            user["emergency_contact"] = emergency

            st.success(message)

        else:

            st.error(message)


# =========================================================
# MEMBER CONTACT ADMIN
# =========================================================

def show_contact_admin(user):

    st.title("💬 Contact Administrator")

    with st.form("contact_admin_form"):

        subject = st.text_input(
            "Subject"
        )

        message = st.text_area(
            "Message",
            height=180
        )

        submit = st.form_submit_button(
            "Send to Administrator",
            use_container_width=True
        )

    if submit:

        if not subject.strip() or not message.strip():

            st.error(
                "Subject and message are required."
            )

        else:

            create_admin_message(
                user["id"],
                subject.strip(),
                message.strip()
            )

            st.success(
                "Your message has been sent to the administrator."
            )


# =========================================================
# MEMBER LIST / MESSAGE
# =========================================================

def show_members(user):

    st.title("👥 Members")

    members = [
        member
        for member in get_active_members()
        if member["id"] != user["id"]
    ]

    if not members:

        st.info(
            "There are no other active members."
        )
        return

    st.write(
        "Select a member to start a private conversation."
    )

    for member in members:

        with st.container(border=True):

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.markdown(
                    f"### {member['full_name']}"
                )

                st.caption(
                    f"@{member['username']}"
                )

            with col2:

                if st.button(
                    "💬 Message",
                    key=f"open_member_{member['id']}",
                    use_container_width=True
                ):

                    st.session_state.selected_contact = \
                        member["id"]

                    st.rerun()

    # -----------------------------------------------------
    # Prominent message area
    # -----------------------------------------------------

    if "selected_contact" in st.session_state:

        receiver = get_user_by_id(
            st.session_state.selected_contact
        )

        if receiver:

            st.divider()

            st.markdown(
                f"""
                <div style="
                    background-color:#e8f0fe;
                    border:3px solid #1f4e79;
                    border-radius:15px;
                    padding:20px;
                    margin-top:10px;
                ">
                    <h2 style="color:#1f4e79;">
                        💬 Message {receiver['full_name']}
                    </h2>
                    <p>
                        Your message will be private.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.form(
                "prominent_member_message"
            ):

                message = st.text_area(
                    "Write your message",
                    height=180,
                    placeholder="Type your message here..."
                )

                col1, col2 = st.columns(2)

                with col1:

                    send = st.form_submit_button(
                        "📨 SEND MESSAGE",
                        use_container_width=True
                    )

                with col2:

                    cancel = st.form_submit_button(
                        "Cancel",
                        use_container_width=True
                    )

            if send:

                if not message.strip():

                    st.error(
                        "Message cannot be empty."
                    )

                else:

                    send_message(
                        user["id"],
                        receiver["id"],
                        message.strip()
                    )

                    st.success(
                        f"Message sent to {receiver['full_name']}."
                    )

                    del st.session_state.selected_contact

                    st.rerun()

            if cancel:

                del st.session_state.selected_contact
                st.rerun()


# =========================================================
# MESSAGES / INBOX
# =========================================================

def show_messages(user):

    unread = get_unread_count(
        user["id"]
    )

    st.title("✉️ My Messages")

    if unread:

        st.warning(
            f"You have {unread} unread message(s)."
        )

    contacts = get_message_contacts(
        user["id"]
    )

    if not contacts:

        st.info(
            "You don't have any conversations yet."
        )

        return

    st.subheader("Conversations")

    for contact in contacts:

        if st.button(
            f"💬 {contact['full_name']} "
            f"(@{contact['username']})",
            key=f"conversation_{contact['id']}",
            use_container_width=True
        ):

            st.session_state.selected_contact = \
                contact["id"]

            st.rerun()

    if "selected_contact" not in st.session_state:

        return

    contact = get_user_by_id(
        st.session_state.selected_contact
    )

    if not contact:

        return

    mark_conversation_read(
        user["id"],
        contact["id"]
    )

    st.divider()

    st.markdown(
        f"""
        <div style="
            background:#1f4e79;
            color:white;
            padding:15px;
            border-radius:10px;
        ">
            <h2>💬 {contact['full_name']}</h2>
            <p>@{contact['username']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    conversation = get_conversation(
        user["id"],
        contact["id"]
    )

    for message in conversation:

        if message["sender_id"] == user["id"]:

            st.markdown(
                f"""
                <div style="
                    background:#dcf8c6;
                    padding:12px;
                    border-radius:12px;
                    margin:8px 0;
                    margin-left:20%;
                ">
                    <b>You</b><br>
                    {message['message']}
                    <br>
                    <small>{message['created_at']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div style="
                    background:#f1f1f1;
                    padding:12px;
                    border-radius:12px;
                    margin:8px 20% 8px 0;
                ">
                    <b>{message['sender_name']}</b><br>
                    {message['message']}
                    <br>
                    <small>{message['created_at']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("### ✍️ Reply")

    with st.form("conversation_reply"):

        message = st.text_area(
            "Message",
            height=120
        )

        send = st.form_submit_button(
            "📨 Send",
            use_container_width=True
        )

    if send:

        if message.strip():

            send_message(
                user["id"],
                contact["id"],
                message.strip()
            )

            st.rerun()

        else:

            st.error(
                "Message cannot be empty."
            )


# =========================================================
# MEMBER FINANCES
# =========================================================

def show_finances(user):

    st.title("💰 My Financial Records")

    year = st.selectbox(
        "Financial Year",
        list(
            range(
                date.today().year,
                date.today().year - 10,
                -1
            )
        )
    )

    summary = get_member_financial_summary(
        user["id"],
        year
    )

    st.subheader(
        f"Financial Summary — {year}"
    )

    cols = st.columns(4)

    for index, category in enumerate(
        FINANCIAL_CATEGORIES
    ):

        with cols[index % 4]:

            st.metric(
                category,
                f"₦{summary[category]:,.2f}"
            )

    st.divider()

    records = get_user_financial_records(
        user["id"],
        year
    )

    if not records:

        st.info(
            f"No records found for {year}."
        )

        return

    for record in records:

        with st.container(border=True):

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.subheader(
                    record["category"]
                )

                st.write(
                    record["description"]
                )

                st.caption(
                    record["record_date"]
                )

            with col2:

                st.metric(
                    "Amount",
                    f"₦{record['amount']:,.2f}"
                )


# =========================================================
# LOGIN ISSUE
# =========================================================

def show_login_issue(user):

    st.title("🔐 Login Support")

    with st.form("login_issue_form"):

        issue = st.text_area(
            "Describe your login problem",
            height=180
        )

        submit = st.form_submit_button(
            "Submit",
            use_container_width=True
        )

    if submit:

        if not issue.strip():

            st.error(
                "Please describe your problem."
            )

        else:

            create_login_issue(
                user["id"],
                user["username"],
                issue.strip()
            )

            st.success(
                "Your issue has been sent to the administrator."
            )


# =========================================================
# ADMIN HOME
# =========================================================

def show_admin_home():

    st.title(
        "🛡️ ROCKVILLE LEAGUE OF FRIENDS CLUB"
    )

    st.subheader(
        "Administrator Dashboard"
    )

    users = get_all_users()

    active = [
        u for u in users
        if u["status"] == "active"
        and u["role"] == "member"
    ]

    pending = [
        u for u in users
        if u["status"] == "pending"
    ]

    suspended = [
        u for u in users
        if u["status"] == "suspended"
    ]

    unread_issues = [
        i for i in get_login_issues()
        if i["status"] == "open"
    ]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Active Members",
            len(active)
        )

    with col2:
        st.metric(
            "Pending",
            len(pending)
        )

    with col3:
        st.metric(
            "Suspended",
            len(suspended)
        )

    with col4:
        st.metric(
            "Login Issues",
            len(unread_issues)
        )

    st.divider()

    st.markdown("""
    ### Welcome to the Administration Area

    From here you can manage members, financial records,
    private messages, announcements, login problems and
    account access.
    """)


# =========================================================
# ADMIN USER MANAGEMENT
# =========================================================

def show_user_management():

    st.title("👥 User Management")

    pending = get_pending_users()

    st.subheader(
        f"Pending Registrations ({len(pending)})"
    )

    if not pending:

        st.info(
            "There are no pending registrations."
        )

    for user in pending:

        with st.container(border=True):

            st.markdown(
                f"### {user['full_name']}"
            )

            st.write(
                f"Username: **{user['username']}**"
            )

            st.write(
                f"Email: **{user['email']}**"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                if st.button(
                    "✅ Accept",
                    key=f"accept_{user['id']}"
                ):

                    update_user_status(
                        user["id"],
                        "active"
                    )

                    st.success(
                        "Registration accepted."
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "❌ Reject",
                    key=f"reject_{user['id']}"
                ):

                    update_user_status(
                        user["id"],
                        "rejected"
                    )

                    st.warning(
                        "Registration rejected."
                    )

                    st.rerun()

            with col3:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_pending_{user['id']}"
                ):

                    delete_user(
                        user["id"]
                    )

                    st.success(
                        "Registration deleted."
                    )

                    st.rerun()

    st.divider()

    st.subheader("All Members")

    users = get_all_users()

    for user in users:

        if user["role"] == "admin":
            continue

        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [4, 2, 1]
            )

            with col1:

                st.markdown(
                    f"### {user['full_name']}"
                )

                st.caption(
                    f"@{user['username']} | "
                    f"{user['email']}"
                )

            with col2:

                st.write(
                    f"Status: **{user['status']}**"
                )

            with col3:

                if st.button(
                    "✏️ Open",
                    key=f"open_user_{user['id']}",
                    use_container_width=True
                ):

                    st.session_state.edit_user_id = \
                        user["id"]

                    st.rerun()

    # -----------------------------------------------------
    # Direct member modification
    # -----------------------------------------------------

    if "edit_user_id" not in st.session_state:

        return

    user = get_user_by_id(
        st.session_state.edit_user_id
    )

    if not user:

        return

    st.divider()

    st.markdown(
        f"""
        <div style="
            background:#1f4e79;
            color:white;
            padding:18px;
            border-radius:12px;
        ">
            <h2>✏️ Modify {user['full_name']}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("admin_edit_user"):

        full_name = st.text_input(
            "Full Name",
            value=user["full_name"]
        )

        email = st.text_input(
            "Email",
            value=user["email"]
        )

        phone = st.text_input(
            "Phone",
            value=user["phone"] or ""
        )

        address = st.text_area(
            "Address",
            value=user["address"] or ""
        )

        emergency = st.text_input(
            "Emergency Contact",
            value=user["emergency_contact"] or ""
        )

        status_options = [
            "active",
            "suspended",
            "pending",
            "rejected"
        ]

        status = st.selectbox(
            "Account Status",
            status_options,
            index=status_options.index(
                user["status"]
            )
        )

        save = st.form_submit_button(
            "Save Member",
            use_container_width=True
        )

    if save:

        success, message = update_user_profile(
            user["id"],
            full_name,
            email,
            phone,
            address,
            emergency
        )

        if success:

            update_user_status(
                user["id"],
                status
            )

            st.success(
                "Member information updated."
            )

            st.rerun()

        else:

            st.error(message)

    col1, col2 = st.columns(2)

    with col1:

        if user["status"] == "suspended":

            if st.button(
                "▶️ Reactivate Account",
                use_container_width=True
            ):

                update_user_status(
                    user["id"],
                    "active"
                )

                st.success(
                    "Account reactivated."
                )

                st.rerun()

        else:

            if st.button(
                "⛔ Suspend Account",
                use_container_width=True
            ):

                update_user_status(
                    user["id"],
                    "suspended"
                )

                st.warning(
                    "Account suspended."
                )

                st.rerun()

    with col2:

        if st.button(
            "🗑️ Permanently Delete",
            use_container_width=True
        ):

            delete_user(
                user["id"]
            )

            del st.session_state.edit_user_id

            st.success(
                "Member deleted."
            )

            st.rerun()


# =========================================================
# ADMIN FINANCES
# =========================================================

def show_admin_finances():

    st.title("💰 Financial Management")

    users = [
        user
        for user in get_all_users()
        if user["role"] == "member"
        and user["status"] != "rejected"
    ]

    if not users:

        st.info(
            "No members are available."
        )

        return

    year = st.selectbox(
        "Year",
        list(
            range(
                date.today().year,
                date.today().year - 10,
                -1
            )
        )
    )

    # -----------------------------------------------------
    # MEMBER FINANCIAL SUMMARY
    # -----------------------------------------------------

    st.subheader(
        "Member Financial Summary"
    )

    for user in users:

        summary = get_member_financial_summary(
            user["id"],
            year
        )

        with st.container(border=True):

            st.markdown(
                f"### {user['full_name']}"
            )

            cols = st.columns(4)

            for index, category in enumerate(
                FINANCIAL_CATEGORIES
            ):

                with cols[index % 4]:

                    st.metric(
                        category,
                        f"₦{summary[category]:,.2f}"
                    )

    st.divider()

    # -----------------------------------------------------
    # ADD RECORD
    # -----------------------------------------------------

    st.subheader(
        "➕ Add Financial Record"
    )

    user_options = {
        f"{user['full_name']} (@{user['username']})":
            user["id"]
        for user in users
    }

    with st.form("add_financial_record"):

        selected_user = st.selectbox(
            "Member",
            list(user_options.keys())
        )

        category = st.selectbox(
            "Category",
            FINANCIAL_CATEGORIES
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            step=100.0
        )

        description = st.text_area(
            "Description"
        )

        record_date = st.date_input(
            "Date",
            value=date.today()
        )

        save = st.form_submit_button(
            "Add Record",
            use_container_width=True
        )

    if save:

        if amount <= 0:

            st.error(
                "Amount must be greater than zero."
            )

        else:

            add_financial_record(
                user_options[selected_user],
                category,
                amount,
                description,
                record_date.isoformat()
            )

            st.success(
                "Financial record added."
            )

            st.rerun()

    # -----------------------------------------------------
    # EXISTING RECORDS
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "Existing Financial Records"
    )

    records = get_all_financial_records()

    for record in records:

        with st.container(border=True):

            st.markdown(
                f"**{record['full_name']}** — "
                f"{record['category']}"
            )

            st.write(
                f"₦{record['amount']:,.2f}"
            )

            st.caption(
                f"{record['record_date']} | "
                f"{record['description']}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✏️ Edit",
                    key=f"edit_fin_{record['id']}"
                ):

                    st.session_state.edit_financial = \
                        record["id"]

                    st.rerun()

            with col2:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_fin_{record['id']}"
                ):

                    delete_financial_record(
                        record["id"]
                    )

                    st.rerun()

    if "edit_financial" in st.session_state:

        record = next(
            (
                r for r in records
                if r["id"] ==
                st.session_state.edit_financial
            ),
            None
        )

        if record:

            st.divider()

            st.subheader(
                "✏️ Edit Financial Record"
            )

            with st.form("edit_financial"):

                category = st.selectbox(
                    "Category",
                    FINANCIAL_CATEGORIES,
                    index=FINANCIAL_CATEGORIES.index(
                        record["category"]
                    )
                )

                amount = st.number_input(
                    "Amount",
                    value=float(record["amount"]),
                    min_value=0.0
                )

                description = st.text_area(
                    "Description",
                    value=record["description"] or ""
                )

                record_date = st.date_input(
                    "Date",
                    value=date.fromisoformat(
                        record["record_date"]
                    )
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

            if save:

                update_financial_record(
                    record["id"],
                    category,
                    amount,
                    description,
                    record_date.isoformat()
                )

                del st.session_state.edit_financial

                st.success(
                    "Financial record updated."
                )

                st.rerun()


# =========================================================
# ADMIN MESSAGE INDIVIDUAL MEMBER
# =========================================================

def show_admin_member_messages(admin):

    st.title("✉️ Message Individual Member")

    members = get_active_members()

    if not members:

        st.info(
            "There are no active members."
        )

        return

    options = {
        f"{member['full_name']} (@{member['username']})":
            member["id"]
        for member in members
    }

    selected = st.selectbox(
        "Select Member",
        list(options.keys())
    )

    member_id = options[selected]

    member = get_user_by_id(
        member_id
    )

    st.markdown(
        f"""
        <div style="
            background:#e8f0fe;
            border:3px solid #1f4e79;
            border-radius:15px;
            padding:20px;
        ">
            <h2>💬 {member['full_name']}</h2>
            <p>Private message from the administrator</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    conversation = get_conversation(
        admin["id"],
        member_id
    )

    if conversation:

        st.markdown("### Conversation")

        for message in conversation:

            if message["sender_id"] == admin["id"]:

                st.success(
                    f"**You:** {message['message']}"
                )

            else:

                st.info(
                    f"**{member['full_name']}:** "
                    f"{message['message']}"
                )

    st.markdown("### ✍️ Send Message")

    with st.form("admin_private_message"):

        message = st.text_area(
            "Message",
            height=180
        )

        send = st.form_submit_button(
            "📨 SEND TO MEMBER",
            use_container_width=True
        )

    if send:

        if not message.strip():

            st.error(
                "Message cannot be empty."
            )

        else:

            send_message(
                admin["id"],
                member_id,
                message.strip()
            )

            st.success(
                f"Message sent to {member['full_name']}."
            )

            st.rerun()


# =========================================================
# ADMIN CONTACT MESSAGES
# =========================================================

def show_admin_messages():

    st.title("💬 Member Contact Requests")

    messages = get_admin_messages()

    if not messages:

        st.info(
            "There are no messages."
        )

        return

    for message in messages:

        with st.container(border=True):

            st.subheader(
                message["subject"]
            )

            st.caption(
                f"From {message['full_name']} "
                f"(@{message['username']})"
            )

            st.write(
                message["message"]
            )

            if message["admin_response"]:

                st.success(
                    f"Response: {message['admin_response']}"
                )

            if message["status"] == "open":

                response = st.text_area(
                    "Response",
                    key=f"response_{message['id']}"
                )

                if st.button(
                    "Resolve",
                    key=f"resolve_{message['id']}"
                ):

                    resolve_admin_message(
                        message["id"],
                        response
                    )

                    st.rerun()


# =========================================================
# ADMIN LOGIN ISSUES
# =========================================================

def show_admin_login_issues():

    st.title("🔐 Login Issues")

    issues = get_login_issues()

    if not issues:

        st.info(
            "There are no reported login issues."
        )

        return

    for issue in issues:

        with st.container(border=True):

            st.subheader(
                issue["full_name"]
                or issue["username"]
            )

            st.caption(
                f"Status: {issue['status']}"
            )

            st.write(
                issue["issue"]
            )

            if issue["status"] == "open":

                response = st.text_area(
                    "Response",
                    key=f"login_response_{issue['id']}"
                )

                if st.button(
                    "Resolve",
                    key=f"resolve_login_{issue['id']}"
                ):

                    resolve_login_issue(
                        issue["id"],
                        response
                    )

                    st.rerun()


# =========================================================
# ADMIN PASSWORD RESET
# =========================================================

def show_password_reset():

    st.title("🔑 Reset Member Password")

    members = [
        user
        for user in get_all_users()
        if user["role"] == "member"
    ]

    if not members:

        st.info(
            "No members found."
        )

        return

    options = {
        f"{user['full_name']} (@{user['username']})":
            user["id"]
        for user in members
    }

    selected = st.selectbox(
        "Member",
        list(options.keys())
    )

    with st.form("admin_password_reset"):

        password = st.text_input(
            "New Password",
            type="password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password"
        )

        submit = st.form_submit_button(
            "Reset Password",
            use_container_width=True
        )

    if submit:

        success, message = reset_user_password(
            options[selected],
            password,
            confirm
        )

        if success:

            st.success(message)

        else:

            st.error(message)


# =========================================================
# ADMIN ANNOUNCEMENTS
# =========================================================

def show_admin_announcements(admin):

    st.title(
        "📰 News & Announcements"
    )

    with st.form("new_announcement"):

        title = st.text_input(
            "Title"
        )

        content = st.text_area(
            "Announcement",
            height=180
        )

        publish = st.checkbox(
            "Publish",
            value=True
        )

        submit = st.form_submit_button(
            "Publish Announcement",
            use_container_width=True
        )

    if submit:

        if not title.strip() or not content.strip():

            st.error(
                "Title and content are required."
            )

        else:

            create_announcement(
                title,
                content,
                admin["id"]
            )

            st.success(
                "Announcement published."
            )

            st.rerun()

    st.divider()

    announcements = get_all_announcements()

    for announcement in announcements:

        with st.container(border=True):

            st.subheader(
                announcement["title"]
            )

            st.write(
                announcement["content"]
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✏️ Edit",
                    key=f"edit_news_{announcement['id']}"
                ):

                    st.session_state.edit_news = \
                        announcement["id"]

                    st.rerun()

            with col2:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_news_{announcement['id']}"
                ):

                    delete_announcement(
                        announcement["id"]
                    )

                    st.rerun()

    if "edit_news" in st.session_state:

        announcement = next(
            (
                a for a in announcements
                if a["id"] ==
                st.session_state.edit_news
            ),
            None
        )

        if announcement:

            st.divider()

            with st.form("edit_news_form"):

                title = st.text_input(
                    "Title",
                    value=announcement["title"]
                )

                content = st.text_area(
                    "Content",
                    value=announcement["content"]
                )

                published = st.checkbox(
                    "Published",
                    value=bool(
                        announcement["published"]
                    )
                )

                save = st.form_submit_button(
                    "Save",
                    use_container_width=True
                )

            if save:

                update_announcement(
                    announcement["id"],
                    title,
                    content,
                    int(published)
                )

                del st.session_state.edit_news

                st.rerun()