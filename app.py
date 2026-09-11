import streamlit as st

from database import (
    init_database,
    admin_exists,
    create_user,
    get_user_by_username,
    get_user_by_email,
)

from validator import (
    hash_password,
    register_user,
    login_user,
    request_password_recovery,
    reset_password_with_token,
)

from dashboard import (
    # Member pages
    show_welcome,
    show_profile,
    show_contact_admin,
    show_members,
    show_messages,
    show_finances,
    show_login_issue,

    # Admin pages
    show_admin_home,
    show_user_management,
    show_admin_finances,
    show_admin_login_issues,
    show_password_reset,
    show_admin_announcements,
    show_admin_messages,
    show_admin_member_messages,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ROCKVILLE LEAGUE OF FRIENDS CLUB",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_database()


# =========================================================
# CREATE DEFAULT ADMIN
# =========================================================

if not admin_exists():

    create_user(
        username="admin",
        full_name="Rockville Club Administrator",
        email="admin@rockvilleclub.local",
        password_hash=hash_password("Admin@123"),
        role="admin",
        status="active",
    )


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "home"

if "message_to" not in st.session_state:
    st.session_state.message_to = None

if "selected_member" not in st.session_state:
    st.session_state.selected_member = None


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def logout():
    """
    Log the current user out.
    """

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "home"
    st.session_state.message_to = None
    st.session_state.selected_member = None

    st.rerun()


def go_to(page):
    """
    Change the current page.
    """

    st.session_state.page = page
    st.rerun()


def require_login():
    """
    Prevent unauthenticated users from opening
    protected pages.
    """

    if not st.session_state.logged_in:

        st.session_state.page = "login"
        st.rerun()


def require_admin():
    """
    Prevent non-admin users from accessing
    administrator pages.
    """

    require_login()

    if st.session_state.user["role"] != "admin":

        st.error(
            "You do not have permission to access this page."
        )

        st.stop()


def require_member():
    """
    Prevent admins from accessing member-only pages.
    """

    require_login()

    if st.session_state.user["role"] != "member":

        st.error(
            "This page is available to club members."
        )

        st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        # 🤝 ROCKVILLE
        ### LEAGUE OF FRIENDS CLUB
        """
    )

    st.divider()

    # -----------------------------------------------------
    # LOGGED IN
    # -----------------------------------------------------

    if st.session_state.logged_in:

        user = st.session_state.user

        st.success(
            f"Welcome, {user['full_name']}"
        )

        st.caption(
            f"Username: {user['username']}"
        )

        st.caption(
            f"Account: {user['role'].title()}"
        )

        st.divider()

        # =================================================
        # ADMIN NAVIGATION
        # =================================================

        if user["role"] == "admin":

            st.subheader("🛡️ Administration")

            if st.button(
                "📊 Dashboard",
                use_container_width=True,
            ):
                go_to("admin_home")

            if st.button(
                "👥 User Management",
                use_container_width=True,
            ):
                go_to("admin_users")

            if st.button(
                "💰 Financial Records",
                use_container_width=True,
            ):
                go_to("admin_finances")

            if st.button(
                "✉️ Message Member",
                use_container_width=True,
            ):
                go_to("admin_member_messages")

            if st.button(
                "💬 Member Messages",
                use_container_width=True,
            ):
                go_to("admin_messages")

            if st.button(
                "🔐 Login Issues",
                use_container_width=True,
            ):
                go_to("admin_login")

            if st.button(
                "🔑 Reset Password",
                use_container_width=True,
            ):
                go_to("admin_password")

            if st.button(
                "📰 News & Announcements",
                use_container_width=True,
            ):
                go_to("admin_news")

        # =================================================
        # MEMBER NAVIGATION
        # =================================================

        else:

            st.subheader("👤 Member Area")

            if st.button(
                "🏠 Club Home",
                use_container_width=True,
            ):
                go_to("welcome")

            if st.button(
                "👤 My Profile",
                use_container_width=True,
            ):
                go_to("profile")

            if st.button(
                "💰 My Financial Records",
                use_container_width=True,
            ):
                go_to("finances")

            if st.button(
                "👥 Club Members",
                use_container_width=True,
            ):
                go_to("members")

            if st.button(
                "✉️ My Messages",
                use_container_width=True,
            ):
                go_to("messages")

            if st.button(
                "💬 Contact Admin",
                use_container_width=True,
            ):
                go_to("contact_admin")

            if st.button(
                "🔐 Report Login Problem",
                use_container_width=True,
            ):
                go_to("login_issue")

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            logout()

    # -----------------------------------------------------
    # NOT LOGGED IN
    # -----------------------------------------------------

    else:

        st.subheader("Member Access")

        if st.button(
            "🏠 Home",
            use_container_width=True,
        ):
            go_to("home")

        if st.button(
            "📝 Register",
            use_container_width=True,
        ):
            go_to("register")

        if st.button(
            "🔐 Login",
            use_container_width=True,
        ):
            go_to("login")

        if st.button(
            "🔑 Forgot Password",
            use_container_width=True,
        ):
            go_to("forgot_password")


# =========================================================
# HOME PAGE
# =========================================================

if st.session_state.page == "home":

    st.markdown(
            """
            <div style="
                padding: 50px;
                border-radius: 20px;
                background:linear-gradient(135deg,#12372A,#436850);
                color: white;
                text-align: center;
            ">
    
                
                    🤝 ROCKVILLE LEAGUE OF FRIENDS CLUB
                
    
               
    
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.subheader("🤝 Friendship")

        st.write(
            "Building lasting friendships and "
            "supporting one another."
        )

    with col2:

        st.subheader("💰 Financial Unity")

        st.write(
            "Manage your club contributions, "
            "dues, savings, levies and other records."
        )

    with col3:

        st.subheader("👥 Community")

        st.write(
            "Connect with fellow members and "
            "stay informed about club activities."
        )

    st.divider()

    st.info(
        "New membership registrations must be "
        "approved by the club administrator."
    )


# =========================================================
# REGISTRATION
# =========================================================

elif st.session_state.page == "register":

    st.title(
        "📝 Register for ROCKVILLE LEAGUE OF FRIENDS CLUB"
    )

    st.write(
        "Create your membership account below."
    )

    st.info(
        "Your account will remain pending until "
        "the administrator approves your registration."
    )

    with st.form("registration_form"):

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
        )

        username = st.text_input(
            "Username",
            placeholder="Choose a username",
        )

        email = st.text_input(
            "Email Address",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
        )

        register = st.form_submit_button(
            "Create Membership Account",
            use_container_width=True,
        )

    if register:

        success, message = register_user(
            full_name,
            username,
            email,
            password,
            confirm_password,
        )

        if success:

            st.success(
                "Registration submitted successfully!"
            )

            st.info(
                "Your registration is now waiting for "
                "administrator approval."
            )

        else:

            st.error(message)


# =========================================================
# LOGIN
# =========================================================

elif st.session_state.page == "login":

    st.title("🔐 Member Login")

    st.write(
        "Login to the ROCKVILLE LEAGUE OF FRIENDS CLUB portal."
    )

    with st.form("login_form"):

        username = st.text_input(
            "Username",
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        login = st.form_submit_button(
            "Login",
            use_container_width=True,
        )

    if login:

        user, message = login_user(
            username,
            password,
        )

        if user:

            st.session_state.logged_in = True

            st.session_state.user = user

            if user["role"] == "admin":

                st.session_state.page = "admin_home"

            else:

                st.session_state.page = "welcome"

            st.rerun()

        else:

            st.error(message)

    st.divider()

    if st.button(
        "🔑 Forgot Password?",
        use_container_width=True,
    ):

        go_to("forgot_password")

    if st.button(
        "🔐 Having trouble logging in?",
        use_container_width=True,
    ):

        go_to("login_issue_public")


# =========================================================
# PASSWORD RECOVERY
# =========================================================

elif st.session_state.page == "forgot_password":

    st.title("🔑 Password Recovery")

    st.write(
        "Enter the email address associated with your "
        "club membership account."
    )

    with st.form("password_recovery_request"):

        email = st.text_input(
            "Email Address"
        )

        submit = st.form_submit_button(
            "Request Recovery",
            use_container_width=True,
        )

    if submit:

        success, message, token = request_password_recovery(
            email
        )

        if success:

            st.success(
                "A password recovery request has been created."
            )

            # Development mode:
            # The token is displayed here so the system can
            # be tested before email delivery is configured.
            if token:

                st.warning(
                    "DEVELOPMENT MODE: Your recovery token is:"
                )

                st.code(token)

                st.info(
                    "In production, this token should be "
                    "sent to the member's registered email."
                )

                if st.button(
                    "Continue to Reset Password",
                    use_container_width=True,
                ):

                    st.session_state.recovery_token = token
                    go_to("reset_password")

        else:

            # Do not reveal whether an email exists.
            st.success(
                "If that email belongs to a club member, "
                "recovery instructions have been generated."
            )


# =========================================================
# RESET PASSWORD
# =========================================================

elif st.session_state.page == "reset_password":

    st.title("🔐 Create New Password")

    token = st.session_state.get(
        "recovery_token",
        "",
    )

    if not token:

        token = st.text_input(
            "Recovery Token"
        )

    with st.form("reset_password_form"):

        new_password = st.text_input(
            "New Password",
            type="password",
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
        )

        submit = st.form_submit_button(
            "Reset Password",
            use_container_width=True,
        )

    if submit:

        success, message = reset_password_with_token(
            token,
            new_password,
            confirm_password,
        )

        if success:

            st.success(message)

            st.session_state.pop(
                "recovery_token",
                None,
            )

            st.session_state.page = "login"

            st.info(
                "You can now log in with your new password."
            )

        else:

            st.error(message)


# =========================================================
# PUBLIC LOGIN ISSUE
# =========================================================

elif st.session_state.page == "login_issue_public":

    st.title("🔐 Login Assistance")

    st.write(
        "If you are unable to log in, please provide "
        "your username and describe the problem."
    )

    with st.form("public_login_issue"):

        username = st.text_input(
            "Username"
        )

        issue = st.text_area(
            "Describe the problem",
            height=180,
        )

        submit = st.form_submit_button(
            "Submit Login Issue",
            use_container_width=True,
        )

    if submit:

        if not username.strip():

            st.error(
                "Please enter your username."
            )

        elif not issue.strip():

            st.error(
                "Please describe the problem."
            )

        else:

            from database import create_login_issue

            user = get_user_by_username(
                username.strip()
            )

            user_id = (
                user["id"]
                if user
                else None
            )

            create_login_issue(
                user_id,
                username.strip(),
                issue.strip(),
            )

            st.success(
                "Your login issue has been submitted "
                "to the club administrator."
            )


# =========================================================
# MEMBER: WELCOME
# =========================================================

elif st.session_state.page == "welcome":

    require_member()

    show_welcome(
        st.session_state.user
    )


# =========================================================
# MEMBER: PROFILE
# =========================================================

elif st.session_state.page == "profile":

    require_member()

    show_profile(
        st.session_state.user
    )


# =========================================================
# MEMBER: FINANCES
# =========================================================

elif st.session_state.page == "finances":

    require_member()

    show_finances(
        st.session_state.user
    )


# =========================================================
# MEMBER: MEMBERS
# =========================================================

elif st.session_state.page == "members":

    require_member()

    show_members(
        st.session_state.user
    )


# =========================================================
# MEMBER: MESSAGES
# =========================================================

elif st.session_state.page == "messages":

    require_member()

    show_messages(
        st.session_state.user
    )


# =========================================================
# MEMBER: CONTACT ADMIN
# =========================================================

elif st.session_state.page == "contact_admin":

    require_member()

    show_contact_admin(
        st.session_state.user
    )


# =========================================================
# MEMBER: LOGIN ISSUE
# =========================================================

elif st.session_state.page == "login_issue":

    require_member()

    show_login_issue(
        st.session_state.user
    )


# =========================================================
# ADMIN: HOME
# =========================================================

elif st.session_state.page == "admin_home":

    require_admin()

    show_admin_home()


# =========================================================
# ADMIN: USER MANAGEMENT
# =========================================================

elif st.session_state.page == "admin_users":

    require_admin()

    show_user_management()


# =========================================================
# ADMIN: FINANCES
# =========================================================

elif st.session_state.page == "admin_finances":

    require_admin()

    show_admin_finances()


# =========================================================
# ADMIN: MESSAGE INDIVIDUAL MEMBER
# =========================================================

elif st.session_state.page == "admin_member_messages":

    require_admin()

    show_admin_member_messages(
        st.session_state.user
    )


# =========================================================
# ADMIN: MEMBER MESSAGE CENTER
# =========================================================

elif st.session_state.page == "admin_messages":

    require_admin()

    show_admin_messages()


# =========================================================
# ADMIN: LOGIN ISSUES
# =========================================================

elif st.session_state.page == "admin_login":

    require_admin()

    show_admin_login_issues()


# =========================================================
# ADMIN: PASSWORD RESET
# =========================================================

elif st.session_state.page == "admin_password":

    require_admin()

    show_password_reset()


# =========================================================
# ADMIN: NEWS
# =========================================================

elif st.session_state.page == "admin_news":

    require_admin()

    show_admin_announcements(
        st.session_state.user
    )


# =========================================================
# UNKNOWN PAGE
# =========================================================

else:

    st.error(
        "The requested page could not be found."
    )

    if st.button(
        "Return Home",
        use_container_width=True,
    ):

        go_to("home")
