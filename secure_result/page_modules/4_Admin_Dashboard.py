import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
from model_loader import predict_sla, find_similar_complaint
import pandas as pd
import plotly.express as px

def get_category_name(category_value):
    category_mapping = {'0': 'Marks Mismatch', '1': 'Absentee Error', '2': 'Missing Grade', '3': 'Calculation Discrepancy', 'Marks Mismatch': 'Marks Mismatch', 'Absentee Error': 'Absentee Error', 'Missing Grade': 'Missing Grade', 'Calculation Discrepancy': 'Calculation Discrepancy'}
    category_str = str(category_value) if category_value else 'Calculation Discrepancy'
    return category_mapping.get(category_str, 'Calculation Discrepancy')

def run():
    st.header('🛠️ Admin Dashboard')
    username = st.session_state.get('username')
    role = st.session_state.get('role')
    if not username or role != 'admin':
        st.error('Admin access required. Please login as an admin.')
        return
    st.subheader(f'Welcome, {username} — Admin Overview')
    complaints = db.get_all_complaints(limit=1000)
    try:
        import sqlite3
        from pathlib import Path
        DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'db.sqlite3'
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT status, COUNT(*) as cnt FROM results GROUP BY status')
        rows = cur.fetchall()
        results_summary = {r['status']: r['cnt'] for r in rows}
        cur.execute('SELECT course_code, COUNT(*) as cnt FROM results GROUP BY course_code ORDER BY cnt DESC LIMIT 10')
        top_courses = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception:
        results_summary = {}
        top_courses = []
    total_complaints = len(complaints)
    pending = sum((1 for c in complaints if c.get('status') == 'Pending'))
    in_progress = sum((1 for c in complaints if c.get('status') == 'In Progress'))
    resolved = sum((1 for c in complaints if c.get('status') == 'Resolved'))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Total Complaints', total_complaints)
    col2.metric('Pending', pending)
    col3.metric('In Progress', in_progress)
    col4.metric('Resolved', resolved)
    st.divider()
    st.subheader('⏱️ SLA Risk Analytics (ML-Powered)')
    sla_data = []
    duplicate_count = 0
    for complaint in complaints:
        if complaint.get('status') in ['Resolved', 'Rejected']:
            continue
        category_display = get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))
        student_username = complaint.get('student_username', '')
        student_results = db.get_results_by_student(student_username)
        faculty_department = 'Computer Science'
        if student_results:
            latest_result = student_results[0] if student_results else None
            if latest_result:
                faculty_department = latest_result.get('faculty_department', faculty_department)
        course_code = complaint.get('course_code', '')
        semester = complaint.get('semester', '')
        student_program = None
        if student_results:
            latest_result = student_results[0] if student_results else None
            if latest_result:
                student_program = latest_result.get('program', None)
        try:
            sla_input = {'Complaint Type': category_display, 'Faculty Department': faculty_department or 'Computer Science'}
            sla_result = predict_sla(sla_input)
            median_resolution_time = sla_result.get('predicted_median_days', 5)
            breach_probability = sla_result.get('breach_prob_at_t', 0.5)
            if breach_probability < 0.3:
                risk_level = 'Low'
            elif breach_probability < 0.6:
                risk_level = 'Medium'
            else:
                risk_level = 'High'
        except Exception:
            breach_probability = 0.0
            median_resolution_time = 5
            risk_level = 'Low'
        sla_data.append({'risk_level': risk_level, 'breach_probability': breach_probability, 'median_resolution_time': median_resolution_time, 'complaint_id': complaint.get('complaint_id'), 'status': complaint.get('status', 'Pending')})
        if complaint.get('duplicate_reference') is not None:
            duplicate_count += 1
    if sla_data:
        high_risk_count = sum((1 for r in sla_data if r['risk_level'] == 'High'))
        medium_risk_count = sum((1 for r in sla_data if r['risk_level'] == 'Medium'))
        low_risk_count = sum((1 for r in sla_data if r['risk_level'] == 'Low'))
        mean_median_time = sum((r['median_resolution_time'] for r in sla_data)) / len(sla_data) if sla_data else 0
        mean_breach_prob = sum((r['breach_probability'] for r in sla_data)) / len(sla_data) if sla_data else 0
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        risk_col1.metric('High Risk SLA Complaints', high_risk_count, help='Complaints with high SLA breach risk requiring immediate attention')
        risk_col2.metric('Mean Predicted Resolution Time', f'{int(round(mean_median_time))} days', help='Average predicted median resolution time from ML model')
        risk_col3.metric('Duplicate Complaints', duplicate_count, help='Number of complaints marked as duplicates')
        risk_dist = pd.DataFrame({'Risk Level': ['High', 'Medium', 'Low'], 'Count': [high_risk_count, medium_risk_count, low_risk_count]})
        fig_risk = px.bar(risk_dist, x='Risk Level', y='Count', title='SLA Risk Distribution (ML-Powered)', color='Risk Level', color_discrete_map={'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'})
        fig_risk.update_layout(showlegend=False)
        st.plotly_chart(fig_risk, use_container_width=True)
        st.write('**Additional Statistics:**')
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric('Medium Risk', medium_risk_count)
        with stat_col2:
            st.metric('Low Risk', low_risk_count)
        with stat_col3:
            st.metric('Average Breach Probability', f'{mean_breach_prob * 100:.1f}%', help='Average probability of SLA breach (resolution > 7 days)')
        if duplicate_count > 0:
            st.write('**Duplicate Complaint Statistics:**')
            duplicate_complaints = [c for c in complaints if c.get('duplicate_reference') is not None]
            duplicate_by_status = {}
            for dup in duplicate_complaints:
                status = dup.get('status', 'Pending')
                duplicate_by_status[status] = duplicate_by_status.get(status, 0) + 1
            dup_df = pd.DataFrame({'Status': list(duplicate_by_status.keys()), 'Count': list(duplicate_by_status.values())})
            if not dup_df.empty:
                fig_dup = px.pie(dup_df, names='Status', values='Count', title='Duplicate Complaints by Status')
                st.plotly_chart(fig_dup, use_container_width=True)
    else:
        st.info('No unresolved complaints available for SLA risk analysis.')
    st.divider()
    st.subheader('Complaint Categories')
    categories = [get_category_name(c.get('predicted_category') or 'Calculation Discrepancy') for c in complaints]
    if categories:
        df_cat = pd.DataFrame({'category': categories})
        fig_cat = px.pie(df_cat, names='category', title='Predicted Category Distribution')
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info('No complaints available to build category chart.')
    st.subheader('Complaints Over Time')
    dates = [c.get('created_at', '')[:10] for c in complaints if c.get('created_at')]
    if dates:
        df_time = pd.DataFrame({'date': dates})
        df_time = df_time.groupby('date').size().reset_index(name='count')
        df_time = df_time.sort_values('date')
        fig_time = px.bar(df_time, x='date', y='count', title='Complaints by Date')
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info('No timestamped complaints to show timeline.')
    st.divider()
    st.subheader('Results Summary (All Students)')
    rs_cols = st.columns(3)
    rs_cols[0].metric('Passed', results_summary.get('Pass', 0))
    rs_cols[1].metric('Failed', results_summary.get('Fail', 0))
    rs_cols[2].metric('Backlog', results_summary.get('Backlog', 0))
    if top_courses:
        st.markdown('**Top courses by number of uploaded results**')
        tc_df = pd.DataFrame(top_courses)
        st.table(tc_df.rename(columns={'course_code': 'Course', 'cnt': 'Count'}).head(10))
    else:
        st.info('No uploaded results yet to summarize.')
    st.divider()
    st.subheader('🔎 Quick Actions & Recent Complaints')
    qcol1, qcol2 = st.columns([2, 1])
    with qcol1:
        st.markdown('**Recent complaints (latest 10)**')
        for c in complaints[:10]:
            status = c.get('status', 'Pending')
            status_emoji = {'Pending': '🟡', 'Resolved': '🟢', 'In Progress': '🔵', 'Rejected': '🔴'}.get(status, '⚪')
            category_display = get_category_name(c.get('predicted_category', 'Calculation Discrepancy'))
            with st.expander(f'{status_emoji} {category_display} - {status} | {c.get('created_at', 'N/A')}', expanded=False):
                st.write(c.get('text', ''))
                st.write(f'**Student:** {c.get('student_username')}')
                st.write(f'**Complaint ID:** {c.get('complaint_id')}')
                if c.get('confidence') is not None:
                    st.caption(f'Confidence: {c.get('confidence', 0):.2%}')
                cols = st.columns(4)
                if cols[0].button('Mark In Progress', key=f'inprog_{c.get('complaint_id')}'):
                    db.update_complaint_status(c.get('complaint_id'), 'In Progress')
                    st.rerun()
                if cols[1].button('Mark Resolved', key=f'res_{c.get('complaint_id')}'):
                    db.update_complaint_status(c.get('complaint_id'), 'Resolved')
                    st.rerun()
                if cols[2].button('Mark Rejected', key=f'rej_{c.get('complaint_id')}'):
                    db.update_complaint_status(c.get('complaint_id'), 'Rejected')
                    st.rerun()
                if cols[3].button('View Student Results', key=f'vr_{c.get('complaint_id')}'):
                    st.info("Use 'Upload Results' to add results for this student, or ask them to check 'My Results'.")
    with qcol2:
        st.markdown('**Admin Tools**')
        if st.button('Go to View Complaints', use_container_width=True, key='admin_dash_view_complaints_btn'):
            st.info("Use the sidebar navigation to access 'View Complaints' page.")
        if st.button('Upload Results CSV', use_container_width=True, key='admin_dash_upload_results_btn'):
            st.info("Use the sidebar navigation to access 'Upload Results (CSV)' page to upload a CSV file of marks.")
    st.divider()
    st.caption("Tip: Use 'Upload Results (CSV)' to bulk-upload student marks. Use 'View Complaints' to manage and reclassify items.")
run()