import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
import pandas as pd

def run():
    st.header('📤 Upload Results (CSV)')
    username = st.session_state.get('username')
    role = st.session_state.get('role')
    if not username or role != 'admin':
        st.error('Admin access required. Please login as an admin.')
        return
    st.subheader('Bulk Upload Student Results')
    st.info('\n\n    **CSV Format Requirements:**\n\n    - **Required columns:** `student_username`, `course_code`\n\n    - **Optional columns:** `course_name`, `semester`, `marks`, `status` (defaults to "Pass")\n\n    - **Status values:** "Pass", "Fail", or "Backlog"\n\n    **Important:** The `student_username` must match the student\'s login username (roll number). \n    Commas will be automatically removed from roll numbers (e.g., "12,213,003" becomes "12213003").\n\n    **Example CSV:**\n\n    ```csv\n\n    student_username,course_code,course_name,semester,marks,status\n\n    12213003,CS101,Introduction to Computer Science,2024-1,85,Pass\n\n    12213004,CS101,Introduction to Computer Science,2024-1,45,Fail\n\n    12213003,MATH201,Calculus II,2024-1,92,Pass\n\n    ```\n\n    ')
    st.divider()
    st.subheader('📁 Upload CSV File')
    uploaded_file = st.file_uploader('Choose a CSV file', type=['csv'], help='Upload a CSV file with student results')
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if 'student_username' in df.columns:
                df['student_username'] = df['student_username'].astype(str).str.replace(',', '', regex=False).str.strip()
            st.success(f'✅ File loaded successfully! ({len(df)} rows)')
            st.divider()
            st.subheader('📋 Data Preview')
            st.dataframe(df.head(10), use_container_width=True)
            if len(df) > 10:
                st.caption(f'Showing first 10 of {len(df)} rows')
            st.divider()
            st.subheader('✅ Validation')
            required_cols = {'student_username', 'course_code'}
            optional_cols = {'course_name', 'semester', 'marks', 'status'}
            all_expected = required_cols | optional_cols
            df_cols = set(df.columns)
            missing_required = required_cols - df_cols
            if missing_required:
                st.error(f'❌ Missing required columns: {', '.join(missing_required)}')
                st.stop()
            else:
                st.success('✅ All required columns present')
                unexpected = df_cols - all_expected
                if unexpected:
                    st.warning(f'⚠️ Unexpected columns (will be ignored): {', '.join(unexpected)}')
                col1, col2 = st.columns(2)
                with col1:
                    st.write('**Required columns:**')
                    for col in required_cols:
                        status = '✅' if col in df_cols else '❌'
                        st.write(f'{status} {col}')
                with col2:
                    st.write('**Optional columns:**')
                    for col in optional_cols:
                        status = '✅' if col in df_cols else '⚪'
                        st.write(f'{status} {col}')
            st.divider()
            st.subheader('📊 Data Statistics')
            col1, col2, col3 = st.columns(3)
            unique_students = df['student_username'].nunique() if 'student_username' in df.columns else 0
            unique_courses = df['course_code'].nunique() if 'course_code' in df.columns else 0
            col1.metric('Total Records', len(df))
            col2.metric('Unique Students', unique_students)
            col3.metric('Unique Courses', unique_courses)
            if 'status' in df.columns:
                status_counts = df['status'].value_counts().to_dict()
                st.write('**Status Distribution:**')
                status_cols = st.columns(len(status_counts))
                for idx, (status, count) in enumerate(status_counts.items()):
                    status_cols[idx].metric(status, count)
            st.divider()
            st.subheader('🚀 Import Results')
            if st.button('Import All Results to Database', type='primary', use_container_width=True):
                try:
                    with st.spinner('Importing results...'):
                        result = db.import_results_from_dataframe(df)
                        inserted = result.get('inserted', 0)
                        errors = result.get('errors', 0)
                        if inserted > 0:
                            st.success(f'✅ Successfully imported {inserted} results!')
                            if errors > 0:
                                st.warning(f'⚠️ {errors} row(s) had errors and were skipped.')
                            st.balloons()
                        else:
                            st.error(f'❌ No results were imported! Check the CSV format and try again.')
                            if errors > 0:
                                st.error(f'Found {errors} error(s) during import. Please check your CSV data.')
                        import sqlite3
                        from pathlib import Path
                        DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'db.sqlite3'
                        conn = sqlite3.connect(str(DB_PATH))
                        conn.row_factory = sqlite3.Row
                        cur = conn.cursor()
                        unique_usernames = df['student_username'].unique().tolist()
                        existing_users = []
                        missing_users = []
                        for username in unique_usernames:
                            cur.execute('SELECT username FROM users WHERE username = ?', (username,))
                            if cur.fetchone():
                                existing_users.append(username)
                            else:
                                missing_users.append(username)
                        conn.close()
                        st.info(f'\n\n                        **Import Summary:**\n\n                        - Records imported: {inserted}\n\n                        - Students affected: {unique_students}\n\n                        - Courses added: {unique_courses}\n\n                        ')
                        if missing_users:
                            st.warning(f"\n                            ⚠️ **Warning:** {len(missing_users)} student username(s) in the CSV do not have user accounts:\n                            \n                            These students won't be able to login to view their results. \n                            Make sure students create accounts with usernames matching their roll numbers.\n                            \n                            Missing usernames: {', '.join(missing_users[:10])}{('...' if len(missing_users) > 10 else '')}\n                            ")
                        else:
                            st.success(f'✅ All {len(existing_users)} student username(s) have user accounts and can login to view results.')
                except Exception as e:
                    st.error(f'❌ Error importing results: {str(e)}')
                    st.exception(e)
        except Exception as e:
            st.error(f'❌ Error reading CSV file: {str(e)}')
            st.exception(e)
    else:
        st.info('👆 Please upload a CSV file to begin')
    st.divider()
    st.subheader('✏️ Manual Entry (Alternative)')
    with st.expander('Add Single Result Manually', expanded=False):
        with st.form('manual_entry_form', clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                student_username = st.text_input('Student Username *', help='Required')
                course_code = st.text_input('Course Code *', help='Required')
                course_name = st.text_input('Course Name', help='Optional')
            with col2:
                semester = st.text_input('Semester', help='Optional (e.g., 2024-1)')
                marks = st.text_input('Marks', help='Optional')
                status = st.selectbox('Status', ['Pass', 'Fail', 'Backlog'], index=0)
            submitted = st.form_submit_button('Add Result', use_container_width=True)
            if submitted:
                if not student_username or not course_code:
                    st.error('Student username and course code are required!')
                else:
                    try:
                        cleaned_username = student_username.replace(',', '').strip()
                        db.add_result(student_username=cleaned_username, course_code=course_code, course_name=course_name if course_name else None, semester=semester if semester else None, marks=marks if marks else '', status=status)
                        st.success(f'✅ Result added for {student_username} - {course_code}')
                        st.rerun()
                    except Exception as e:
                        st.error(f'❌ Error adding result: {str(e)}')
    st.divider()
    st.subheader('📊 Recent Uploads Summary')
    try:
        import sqlite3
        from pathlib import Path
        DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'db.sqlite3'
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('\n\n            SELECT COUNT(*) as total, \n\n                   COUNT(DISTINCT student_username) as students,\n\n                   COUNT(DISTINCT course_code) as courses\n\n            FROM results\n\n        ')
        stats = cur.fetchone()
        cur.execute('\n\n            SELECT course_code, COUNT(*) as count \n\n            FROM results \n\n            GROUP BY course_code \n\n            ORDER BY count DESC \n\n            LIMIT 10\n\n        ')
        top_courses = [dict(r) for r in cur.fetchall()]
        conn.close()
        col1, col2, col3 = st.columns(3)
        col1.metric('Total Results', stats['total'])
        col2.metric('Total Students', stats['students'])
        col3.metric('Total Courses', stats['courses'])
        if top_courses:
            st.write('**Top Courses by Result Count:**')
            tc_df = pd.DataFrame(top_courses)
            st.dataframe(tc_df.rename(columns={'course_code': 'Course', 'count': 'Count'}), use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f'Could not fetch statistics: {e}')
run()