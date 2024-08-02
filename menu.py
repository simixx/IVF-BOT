import streamlit as st

def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link(r"C:\Users\simran kohi\ivf-bot\app.py", label="Switch accounts")
    
    if st.session_state.role == "admin":
        st.sidebar.page_link(r"C:\Users\simran kohi\ivf-bot\pages\admin.py", label="Manage users")
    
    # Removed the clinician and user options

def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link(r"C:\Users\simran kohi\ivf-bot\app.py", label="Log in")

def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "role" not in st.session_state or st.session_state.role is None:
        unauthenticated_menu()
    else:
        authenticated_menu()

def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "role" not in st.session_state or st.session_state.role is None:
        st.experimental_rerun()  # Redirect to the main page
    else:
        menu()

# Call the menu_with_redirect function to handle navigation
menu_with_redirect()
