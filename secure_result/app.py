import streamlit as st
import warnings
import os
import sys
import io
from contextlib import redirect_stderr
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_LOGGING_VERBOSITY'] = '3'
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.ERROR)
logging.getLogger('torch').setLevel(logging.ERROR)

class StderrFilter:

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.suppress_patterns = ['oneDNN custom operations', 'MessageFactory', 'GetPrototype', 'torch.classes', 'AttributeError', 'Tried to instantiate class']

    def write(self, text):
        if text and (not any((pattern in text for pattern in self.suppress_patterns))):
            self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()
_original_stderr = sys.stderr
sys.stderr = StderrFilter(_original_stderr)
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', message='.*Trying to unpickle.*')
warnings.filterwarnings('ignore', message='.*InconsistentVersionWarning.*')
warnings.filterwarnings('ignore', message='.*does not have valid feature names.*')
warnings.filterwarnings('ignore', message='.*AttributeError.*')
warnings.filterwarnings('ignore', message='.*MessageFactory.*')
warnings.filterwarnings('ignore', message='.*torch.classes.*')
try:
    from sklearn.utils._warnings import InconsistentVersionWarning
    warnings.filterwarnings('ignore', category=InconsistentVersionWarning)
except ImportError:
    pass
_stderr_suppress = io.StringIO()
with redirect_stderr(_stderr_suppress):
    pass
st.set_option('client.showErrorDetails', True)
import db

def show_header():
    st.markdown('\n\n\n\n        ')

def require_login():
    return 'username' in st.session_state and st.session_state.get('username')

def do_logout():
    for k in ['username', 'role']:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

def show_login_page():
    st.markdown('\n\n\n    Welcome! Please login or create an account to continue.\n\n    ')
    st.divider()
    tab1, tab2 = st.tabs(['🔑 Login', '📝 Sign Up'])
    with tab1:
        st.subheader('Login to Your Account')
        with st.form('login_form', clear_on_submit=False):
            username = st.text_input('Username', placeholder='Enter your username', key='login_username')
            password = st.text_input('Password', type='password', placeholder='Enter your password', key='login_password')
            submitted = st.form_submit_button('Login', use_container_width=True, type='primary')
            if submitted:
                if not username or not password:
                    st.error('Please enter both username and password.')
                elif db.verify_user(username, password):
                    user = db.get_user_by_username(username)
                    st.session_state['username'] = username
                    st.session_state['role'] = user['role']
                    st.success(f'✅ Successfully logged in as **{username}** ({user['role']})')
                    st.balloons()
                    st.rerun()
                else:
                    st.error('❌ Invalid credentials or user does not exist. Please try again.')
    with tab2:
        st.subheader('Create New Account')
        with st.form('signup_form', clear_on_submit=True):
            username = st.text_input('Choose Username', placeholder='Enter a unique username', key='su_username', help='Username must be unique')
            password = st.text_input('Choose Password', type='password', placeholder='Enter a secure password', key='su_password', help='Use a strong password')
            confirm_password = st.text_input('Confirm Password', type='password', placeholder='Re-enter your password', key='su_confirm_password')
            role = st.selectbox('Account Type', ['student', 'admin'], index=0, help='Select your role: Student or Admin')
            submitted = st.form_submit_button('Create Account', use_container_width=True, type='primary')
            if submitted:
                if not username or not password:
                    st.error('Please fill in all required fields.')
                elif password != confirm_password:
                    st.error('❌ Passwords do not match. Please try again.')
                elif len(password) < 6:
                    st.warning('⚠️ Password should be at least 6 characters long.')
                else:
                    ok = db.create_user(username, password, role=role)
                    if ok:
                        st.success(f'✅ Account created successfully! Username: **{username}** (Role: {role})')
                        st.info('You can now login using your credentials.')
                        st.balloons()
                    else:
                        st.error('❌ Username already exists. Please choose a different username.')

def show_logout_button():
    if require_login():
        st.sidebar.divider()
        st.sidebar.markdown('### 👤 User Info')
        username = st.session_state.get('username')
        role = st.session_state.get('role')
        st.sidebar.markdown(f'**Username:** `{username}`')
        st.sidebar.markdown(f'**Role:** `{role}`')
        st.sidebar.divider()
        if st.sidebar.button('🚪 Logout', use_container_width=True, type='secondary'):
            do_logout()

def main():
    st.set_page_config(page_title='Secure Result', layout='wide')
    if not require_login():
        show_login_page()
        st.stop()
    username = st.session_state['username']
    role = st.session_state['role']
    show_logout_button()
    if role == 'student':
        pages = [st.Page('page_modules/1_Student_Dashboard.py', title='Student Dashboard', icon='📊'), st.Page('page_modules/2_Submit_Complaint.py', title='Submit Complaint', icon='📝'), st.Page('page_modules/3_My_Results.py', title='My Results', icon='📋')]
    elif role == 'admin':
        pages = [st.Page('page_modules/4_Admin_Dashboard.py', title='Admin Dashboard', icon='🛠️'), st.Page('page_modules/5_Admin_View_Complaints.py', title='View Complaints', icon='📋'), st.Page('page_modules/6_Admin_Upload_Results.py', title='Upload Results (CSV)', icon='📤'), st.Page('page_modules/7_Admin_Model_Insights.py', title='Model Insights', icon='🤖')]
    else:
        st.error('Unknown role. Contact the developer.')
        st.stop()
    selected_page = st.navigation(pages, position='sidebar')
    show_header()
    selected_page.run()
if __name__ == '__main__':
    try:
        db.init_db()
    except Exception:
        st.warning('Database initialization failed or already done.')
    main()