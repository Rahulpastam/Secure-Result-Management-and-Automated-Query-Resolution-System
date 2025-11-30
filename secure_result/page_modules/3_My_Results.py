import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
import pandas as pd

def run():
    st.header('📊 My Results')
    username = st.session_state.get('username')
    role = st.session_state.get('role')
    if not username:
        st.error('Not logged in.')
        return
    if role != 'student':
        st.error('❌ Access denied. This page is only available for students.')
        st.info('Please login with a student account to access this page.')
        return
    results = db.get_results_by_student(username)
    if not results:
        import sqlite3
        from pathlib import Path
        DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'db.sqlite3'
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) as total FROM results')
            total_results = cur.fetchone()['total']
            cur.execute('SELECT DISTINCT student_username FROM results LIMIT 20')
            all_usernames = [dict(r)['student_username'] for r in cur.fetchall()]
            cleaned_login = str(username).replace(',', '').strip()
            if total_results == 0:
                st.warning('⚠️ **No results found in database.**')
                st.info("The admin needs to upload results using the 'Upload Results (CSV)' page.")
            elif all_usernames:
                matches = [u for u in all_usernames if str(u).replace(',', '').strip() == cleaned_login]
                if matches:
                    st.warning(f'⚠️ Found matching username in database but query returned no results.')
                    st.info(f"**Your username:** '{username}' (cleaned: '{cleaned_login}')")
                    st.info(f'**Found in DB:** {matches[0]}')
                    st.info("💡 **Solution:** Ask an admin to run the 'Fix Student Username Format' tool.")
                else:
                    st.info(f"No results found for username '{username}'.")
                    st.caption(f"**Your username:** '{username}' (cleaned: '{cleaned_login}')")
                    st.caption(f'**Available usernames in database:** {', '.join([str(u) for u in all_usernames[:10]])}')
            else:
                st.info(f"No results found for username '{username}'. Results will appear here once uploaded by an admin.")
            conn.close()
        except Exception as e:
            st.info(f"No results found for username '{username}'. Results will appear here once uploaded by an admin.")
            st.caption(f'Error checking database: {str(e)}')
        return
    st.subheader('📈 Summary Statistics')
    col1, col2, col3, col4 = st.columns(4)
    total_courses = len(results)
    passed = sum((1 for r in results if r.get('status') == 'Pass'))
    failed = sum((1 for r in results if r.get('status') == 'Fail'))
    backlog = sum((1 for r in results if r.get('status') == 'Backlog'))
    pass_rate = passed / total_courses * 100 if total_courses > 0 else 0
    col1.metric('Total Courses', total_courses)
    col2.metric('Passed', passed, delta=f'{pass_rate:.1f}%')
    col3.metric('Failed', failed)
    col4.metric('Backlog', backlog)
    st.divider()
    st.subheader('🔍 Filter Results')
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox('Filter by Status', ['All', 'Pass', 'Fail', 'Backlog'], index=0)
    with col2:
        semester_filter = st.selectbox('Filter by Semester', ['All'] + sorted(set((r.get('semester') for r in results if r.get('semester')))), index=0)
    with col3:
        search_term = st.text_input('Search Course', placeholder='Course code or name...')
    filtered_results = results
    if status_filter != 'All':
        filtered_results = [r for r in filtered_results if r.get('status') == status_filter]
    if semester_filter != 'All':
        filtered_results = [r for r in filtered_results if r.get('semester') == semester_filter]
    if search_term:
        search_lower = search_term.lower()
        filtered_results = [r for r in filtered_results if search_lower in str(r.get('course_code', '')).lower() or search_lower in str(r.get('course_name', '')).lower()]
    st.write(f'Showing {len(filtered_results)} of {len(results)} results')
    st.divider()
    if filtered_results:
        view_mode = st.radio('View Mode', ['Cards', 'Table'], horizontal=True)
        if view_mode == 'Table':
            df_data = []
            for r in filtered_results:
                df_data.append({'Course Code': r.get('course_code', 'N/A'), 'Course Name': r.get('course_name', 'N/A'), 'Semester': r.get('semester', 'N/A'), 'Marks': r.get('marks', 'N/A'), 'Status': r.get('status', 'Pass'), 'Uploaded': r.get('uploaded_at', 'N/A')})
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            for result in filtered_results:
                status = result.get('status', 'Pass')
                status_color = {'Pass': '🟢', 'Fail': '🔴', 'Backlog': '🟡'}.get(status, '⚪')
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        course_code = result.get('course_code', 'N/A')
                        course_name = result.get('course_name', 'N/A')
                        st.write(f'**Course Code:** {course_code}')
                        st.write(f'**Course Name:** {course_name}')
                        if result.get('semester'):
                            st.caption(f'Semester: {result.get('semester')}')
                    with col2:
                        st.write(f'**Marks:** {result.get('marks', 'N/A')}')
                        st.caption(f'Uploaded: {result.get('uploaded_at', 'N/A')}')
                    with col3:
                        if status == 'Pass':
                            st.success(f'{status_color} {status}')
                        elif status == 'Fail':
                            st.error(f'{status_color} {status}')
                        else:
                            st.warning(f'{status_color} {status}')
                    st.divider()
    else:
        st.info('No results match the selected filters.')
    if results:
        st.divider()
        st.subheader('📥 Export Results')
        csv_data = []
        for r in results:
            csv_data.append({'Course Code': r.get('course_code', ''), 'Course Name': r.get('course_name', ''), 'Semester': r.get('semester', ''), 'Marks': r.get('marks', ''), 'Status': r.get('status', ''), 'Uploaded At': r.get('uploaded_at', '')})
        df_export = pd.DataFrame(csv_data)
        csv = df_export.to_csv(index=False)
        st.download_button(label='📥 Download Results as CSV', data=csv, file_name=f'{username}_results.csv', mime='text/csv', use_container_width=True)
run()