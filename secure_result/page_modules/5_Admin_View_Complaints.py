import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
from model_loader import predict_category, find_similar_complaint, predict_sla
import pandas as pd

def get_category_name(category_value):
    category_mapping = {'0': 'Marks Mismatch', '1': 'Absentee Error', '2': 'Missing Grade', '3': 'Calculation Discrepancy', 'Marks Mismatch': 'Marks Mismatch', 'Absentee Error': 'Absentee Error', 'Missing Grade': 'Missing Grade', 'Calculation Discrepancy': 'Calculation Discrepancy'}
    category_str = str(category_value) if category_value else 'Calculation Discrepancy'
    return category_mapping.get(category_str, 'Calculation Discrepancy')

def get_risk_badge_html(risk_level: str) -> str:
    colors = {'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#28a745'}
    color = colors.get(risk_level, '#6c757d')
    return f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">SLA Risk: {risk_level}</span>'

def render_duplicate_insights(complaint_text: str, complaint_id: int):
    try:
        similar_complaints = find_similar_complaint(complaint_text, top_k=3)
    except Exception as e:
        st.error(f'Error finding similar complaints: {str(e)}')
        similar_complaints = []
    if not similar_complaints:
        st.info('ℹ️ No similar complaints found in historical data.')
        return
    st.subheader('🔍 Duplicate/Near Duplicate Insights')
    for idx, similar in enumerate(similar_complaints, 1):
        similarity_score = similar.get('score', 0.0)
        if similarity_score >= 0.8:
            st.warning(f'**High Similarity ({similarity_score:.1%})** - Potential Duplicate #{idx}')
        elif similarity_score >= 0.6:
            st.info(f'**Moderate Similarity ({similarity_score:.1%})** - Similar Complaint #{idx}')
        else:
            st.caption(f'**Low Similarity ({similarity_score:.1%})** - Related Complaint #{idx}')
        with st.container():
            st.write(f'**Details - Index: {similar.get('index', 'N/A')}**')
            col1, col2 = st.columns(2)
            with col1:
                st.write(f'**Similarity Score:** {similarity_score:.2%}')
                st.write(f'**Category:** {similar.get('complaint_type', 'N/A')}')
            with col2:
                resolution_time = similar.get('resolution_time')
                if resolution_time is not None:
                    st.write(f'**Resolution Time:** {resolution_time} days')
                else:
                    st.write(f'**Resolution Time:** Not available')
            st.write('**Resolution Description:**')
            st.text_area('Resolution', value=similar.get('resolution_desc', 'N/A'), height=80, key=f'resolution_desc_{complaint_id}_{idx}', disabled=True, label_visibility='collapsed')
            st.write('**Original Complaint Text:**')
            st.text_area('Similar Complaint', value=similar.get('complaint_text', 'N/A'), height=100, key=f'similar_text_{complaint_id}_{idx}', disabled=True)
        st.divider()

def render_sla_prediction_panel(complaint: dict):
    st.subheader('⏱️ SLA Breach Prediction')
    complaint_text = complaint.get('text', '')
    student_username = complaint.get('student_username', '')
    student_results = db.get_results_by_student(student_username)
    faculty_department = 'Computer Science'
    student_program = None
    if student_results:
        latest_result = student_results[0] if student_results else None
        if latest_result:
            faculty_department = latest_result.get('faculty_department', faculty_department)
            student_program = latest_result.get('program', None)
    course_code = complaint.get('course_code', '')
    semester = complaint.get('semester', '')
    try:
        sla_input = {'Complaint Type': complaint.get('predicted_category', 'Calculation Discrepancy'), 'Faculty Department': faculty_department or 'Computer Science'}
        sla_result = predict_sla(sla_input)
        median_resolution_time = sla_result.get('predicted_median_days', 5)
        breach_probability = sla_result.get('breach_prob_at_t', 0.5)
        if breach_probability < 0.3:
            risk_level = 'Low'
        elif breach_probability < 0.6:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
    except Exception as e:
        st.error(f'❌ Error in SLA prediction: {str(e)}')
        breach_probability = 0.0
        median_resolution_time = 5
        risk_level = 'Low'
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('🕒 SLA Risk', risk_level)
    with col2:
        st.metric('📉 Breach Probability', f'{breach_probability * 100:.1f}%')
    with col3:
        st.metric('📆 Expected Resolution Time', f'{int(median_resolution_time)} days')
    if risk_level == 'High':
        st.error(f'⚠️ **High SLA Risk** - {breach_probability * 100:.1f}% probability of exceeding 7-day SLA')
    elif risk_level == 'Medium':
        st.warning(f'⚡ **Medium SLA Risk** - {breach_probability * 100:.1f}% probability of exceeding 7-day SLA')
    else:
        st.success(f'✅ **Low SLA Risk** - {breach_probability * 100:.1f}% probability of exceeding 7-day SLA')
    category_display = get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))
    st.write('**SLA Feature Analysis:**')
    st.info(f'Based on **Complaint Type:** {category_display} and **Faculty Department:** {faculty_department}')
    with st.container():
        st.write('**Feature Breakdown:**')
        st.write(f'**Primary Factors:**')
        st.write(f'- Complaint Category: {category_display}')
        st.write(f'- Department: {faculty_department}')
        st.write(f'- Breach Probability: {breach_probability:.1%} (probability of resolution > 7 days)')
        st.write(f'- Median Resolution Time: {int(median_resolution_time)} days')
        if median_resolution_time > 7:
            st.warning('⚠️ Median resolution time exceeds SLA threshold (7 days)')
        elif median_resolution_time > 5:
            st.info('ℹ️ Median resolution time is within acceptable range')
        else:
            st.success('✅ Median resolution time is below SLA threshold')

def render_chat_message(message: dict, is_admin: bool=False):
    sender_role = message.get('sender_role', '')
    sender_username = message.get('sender_username', 'Unknown')
    message_text = message.get('message_text', '')
    created_at = message.get('created_at', '')
    file_paths_json = message.get('file_paths')
    if sender_role == 'system':
        bg_color = '#fff3e0'
        border_color = '#ff9800'
        label = '🤖 System Recommendation'
    elif sender_role == 'admin':
        bg_color = '#e3f2fd'
        border_color = '#2196f3'
        label = f'👤 Admin ({sender_username})'
    else:
        bg_color = '#f1f8e9'
        border_color = '#8bc34a'
        label = f'👤 Student ({sender_username})'
    st.markdown(f'\n        <div style="\n            background-color: {bg_color};\n            border-left: 4px solid {border_color};\n            padding: 12px;\n            margin: 8px 0;\n            border-radius: 4px;\n        ">\n            <div style="font-weight: bold; margin-bottom: 4px; color: #333;">\n                {label}\n            </div>\n            <div style="color: #555; margin-bottom: 4px;">\n                {(message_text if message_text else '<em>No text message</em>')}\n            </div>\n            <div style="font-size: 0.85em; color: #888;">\n                {created_at}\n            </div>\n        </div>\n        ', unsafe_allow_html=True)
    if file_paths_json:
        try:
            file_paths = json.loads(file_paths_json)
            if file_paths:
                for file_path in file_paths:
                    file_full_path = Path(__file__).parent.parent / file_path
                    if file_full_path.exists():
                        with open(file_full_path, 'rb') as f:
                            file_data = f.read()
                            file_name = Path(file_path).name
                            st.download_button(label=f'📎 {file_name}', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'msg_download_{message.get('message_id')}_{file_name}')
        except:
            pass

def run():
    st.header('📋 View & Manage Complaints')
    username = st.session_state.get('username')
    role = st.session_state.get('role')
    if not username or role != 'admin':
        st.error('Admin access required. Please login as an admin.')
        return
    complaints = db.get_all_complaints(limit=1000)
    if not complaints:
        st.info('No complaints in the system yet.')
        return

    def get_category_id(category_name):
        reverse_mapping = {'Marks Mismatch': ['0', 'Marks Mismatch'], 'Absentee Error': ['1', 'Absentee Error'], 'Missing Grade': ['2', 'Missing Grade'], 'Calculation Discrepancy': ['3', 'Calculation Discrepancy']}
        return reverse_mapping.get(category_name, [category_name])
    st.subheader('🔍 Filter & Search Complaints')
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox('Filter by Status', ['All', 'Pending', 'Resolved', 'Rejected'], index=0)
    with col2:
        category_options = ['All', 'Marks Mismatch', 'Absentee Error', 'Missing Grade', 'Calculation Discrepancy']
        category_filter = st.selectbox('Filter by Category', category_options, index=0)
    with col3:
        search_term = st.text_input('Search (Student/Text)', placeholder='Search by student or complaint text...')
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        sla_risk_filter = st.selectbox('Filter by SLA Risk', ['All', 'High', 'Medium', 'Low'], index=0)
    with col5:
        unique_course_codes = sorted(set([c.get('course_code') for c in complaints if c.get('course_code')]))
        course_code_filter = st.selectbox('Filter by Course Code', ['All'] + unique_course_codes, index=0)
    with col6:
        unique_semesters = sorted(set([c.get('semester') for c in complaints if c.get('semester')]))
        semester_filter = st.selectbox('Filter by Semester', ['All'] + unique_semesters, index=0)
    with col7:
        sort_by = st.selectbox('Sort by', ['Newest First', 'Oldest First', 'High Risk First', 'Low Risk First'], index=0)
    filtered_complaints = complaints
    if status_filter != 'All':
        filtered_complaints = [c for c in filtered_complaints if c.get('status') == status_filter]
    if category_filter != 'All':
        category_ids = get_category_id(category_filter)
        filtered_complaints = [c for c in filtered_complaints if str(c.get('predicted_category') or 'Calculation Discrepancy') in category_ids or get_category_name(c.get('predicted_category') or 'Calculation Discrepancy') == category_filter]
    if search_term:
        search_lower = search_term.lower()
        filtered_complaints = [c for c in filtered_complaints if search_lower in str(c.get('student_username', '')).lower() or search_lower in str(c.get('text', '')).lower()]
    for complaint in filtered_complaints:
        if complaint.get('status') not in ['Resolved', 'Rejected']:
            complaint_text = complaint.get('text', '')
            student_username = complaint.get('student_username', '')
            student_results = db.get_results_by_student(student_username)
            faculty_department = 'Computer Science'
            student_program = None
            if student_results:
                latest_result = student_results[0] if student_results else None
                if latest_result:
                    faculty_department = latest_result.get('faculty_department', faculty_department)
                    student_program = latest_result.get('program', None)
            course_code = complaint.get('course_code', '')
            semester = complaint.get('semester', '')
            try:
                sla_input = {'Complaint Type': complaint.get('predicted_category', 'Calculation Discrepancy'), 'Faculty Department': faculty_department or 'Computer Science'}
                sla_result = predict_sla(sla_input)
                breach_prob = sla_result.get('breach_prob_at_t', 0.5)
                median_time = sla_result.get('predicted_median_days', 5)
                if breach_prob < 0.3:
                    risk_lvl = 'Low'
                elif breach_prob < 0.6:
                    risk_lvl = 'Medium'
                else:
                    risk_lvl = 'High'
                complaint['sla_risk_level'] = risk_lvl
                complaint['sla_breach_probability'] = breach_prob
                complaint['sla_median_resolution_time'] = median_time
            except Exception:
                complaint['sla_risk_level'] = 'Low'
                complaint['sla_breach_probability'] = 0.0
                complaint['sla_median_resolution_time'] = 5
        else:
            complaint['sla_risk_level'] = 'Low'
            complaint['sla_breach_probability'] = 0.0
            complaint['sla_median_resolution_time'] = 0.0
    if sla_risk_filter != 'All':
        filtered_complaints = [c for c in filtered_complaints if c.get('sla_risk_level') == sla_risk_filter]
    if course_code_filter != 'All':
        filtered_complaints = [c for c in filtered_complaints if c.get('course_code') == course_code_filter]
    if semester_filter != 'All':
        filtered_complaints = [c for c in filtered_complaints if c.get('semester') == semester_filter]
    if sort_by == 'High Risk First':
        filtered_complaints.sort(key=lambda x: x.get('sla_breach_probability', 0), reverse=True)
    elif sort_by == 'Low Risk First':
        filtered_complaints.sort(key=lambda x: x.get('sla_breach_probability', 0))
    elif sort_by == 'Oldest First':
        for c in filtered_complaints:
            created_at_str = c.get('created_at', '')
            try:
                if isinstance(created_at_str, str):
                    if 'T' in created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                    c['_sort_date'] = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
                else:
                    c['_sort_date'] = datetime.now()
            except:
                c['_sort_date'] = datetime.now()
        filtered_complaints.sort(key=lambda x: x.get('_sort_date', datetime.now()), reverse=True)
    else:
        for c in filtered_complaints:
            created_at_str = c.get('created_at', '')
            try:
                if isinstance(created_at_str, str):
                    if 'T' in created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                    c['_sort_date'] = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
                else:
                    c['_sort_date'] = datetime.now()
            except:
                c['_sort_date'] = datetime.now()
        filtered_complaints.sort(key=lambda x: x.get('_sort_date', datetime.now()))
    st.write(f'Showing {len(filtered_complaints)} of {len(complaints)} complaints')
    st.divider()
    view_mode = st.radio('View Mode', ['Cards', 'Table'], horizontal=True)
    st.divider()
    if view_mode == 'Table':
        for complaint in filtered_complaints:
            complaint_id = complaint.get('complaint_id')
            current_status = complaint.get('status', 'Pending')
            status_options = ['Pending', 'In Progress', 'Resolved', 'Rejected']
            status_index = status_options.index(current_status) if current_status in status_options else 0
            category_display = get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))
            risk_level = complaint.get('sla_risk_level', 'Medium')
            risk_badge = get_risk_badge_html(risk_level)
            st.markdown(risk_badge, unsafe_allow_html=True)
            with st.expander(f'**ID:** {complaint_id} | **Student:** {complaint.get('student_username', 'N/A')} | **Category:** {category_display} | **Status:** {current_status} | **SLA Risk:** {risk_level}', expanded=False):
                st.write('**Complaint Text:**')
                st.write(complaint.get('text', 'No text provided'))
                course_code = complaint.get('course_code')
                semester = complaint.get('semester')
                if course_code or semester:
                    st.write('**Course Information:**')
                    info_cols = st.columns(2)
                    if course_code:
                        info_cols[0].write(f'**Course Code:** {course_code}')
                    if semester:
                        info_cols[1].write(f'**Semester:** {semester}')
                file_path = complaint.get('file_path')
                if file_path:
                    file_full_path = Path(__file__).parent.parent / file_path
                    if file_full_path.exists():
                        with open(file_full_path, 'rb') as f:
                            file_data = f.read()
                            file_name = Path(file_path).name
                            st.download_button(label='📎 Download Supporting Evidence', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'table_download_{complaint_id}')
                    else:
                        st.caption('⚠️ File not found on server')
                st.divider()
                render_duplicate_insights(complaint.get('text', ''), complaint_id)
                st.divider()
                render_sla_prediction_panel(complaint)
                st.divider()
                st.subheader('💬 Communication Thread')
                try:
                    similar_complaints = find_similar_complaint(complaint.get('text', ''), top_k=1)
                except Exception:
                    similar_complaints = []
                messages = db.get_complaint_messages(complaint_id)
                system_messages = []
                if similar_complaints and len(similar_complaints) > 0:
                    similar = similar_complaints[0]
                    similarity_score = similar.get('score', 0.0)
                    if similarity_score > 0.7:
                        similar_text = similar.get('complaint_text', '')[:200] + '...' if len(similar.get('complaint_text', '')) > 200 else similar.get('complaint_text', '')
                        similar_resolution_time = similar.get('resolution_time', 'N/A')
                        similar_category = similar.get('complaint_type', 'Unknown')
                        resolution_desc = similar.get('resolution_desc', '')
                        system_msg_text = f'**Similar Resolved Case Found** (Similarity: {similarity_score:.1%})\n                        \n**Category:** {similar_category}\n**Resolution Time:** {similar_resolution_time} days\n**Previous Complaint Text:** "{similar_text}"\n**Resolution Description:** "{resolution_desc[:200]}{('...' if len(resolution_desc) > 200 else '')}"\n\nThis complaint is similar to a previously resolved case. Review the resolution approach above.'
                        system_messages.append({'message_id': -1, 'sender_role': 'system', 'sender_username': 'System', 'message_text': system_msg_text, 'created_at': 'System Recommendation', 'file_paths': None})
                all_messages = system_messages + messages if messages else system_messages
                if all_messages:
                    st.write('**Message History:**')
                    for message in all_messages:
                        render_chat_message(message, is_admin=True)
                else:
                    st.info('No messages yet. Start the conversation below.')
                st.divider()
                st.write('**Send a Message:**')
                with st.form(key=f'message_form_table_{complaint_id}', clear_on_submit=True):
                    message_text = st.text_area('Your Message', placeholder='Type your message here...', height=100, key=f'message_text_table_{complaint_id}')
                    col_img, col_file = st.columns(2)
                    with col_img:
                        message_images = st.file_uploader('Attach Images (Optional)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f'message_images_table_{complaint_id}')
                    with col_file:
                        message_files = st.file_uploader('Attach Files (Optional)', type=['pdf', 'doc', 'docx', 'txt'], accept_multiple_files=True, key=f'message_files_table_{complaint_id}')
                    submit_message = st.form_submit_button('📤 Send Message', use_container_width=True, type='primary')
                    if submit_message:
                        if not message_text and (not message_images) and (not message_files):
                            st.error('⚠️ Please provide a message, image, or file.')
                        else:
                            try:
                                saved_file_paths = []
                                upload_dir = Path(__file__).parent.parent / 'uploads' / 'complaint_messages'
                                upload_dir.mkdir(parents=True, exist_ok=True)
                                if message_images:
                                    for img in message_images:
                                        file_ext = Path(img.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(img.getbuffer())
                                        saved_file_paths.append(f'uploads/complaint_messages/{safe_filename}')
                                if message_files:
                                    for file in message_files:
                                        file_ext = Path(file.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(file.getbuffer())
                                        saved_file_paths.append(f'uploads/complaint_messages/{safe_filename}')
                                file_paths_json = json.dumps(saved_file_paths) if saved_file_paths else None
                                db.add_complaint_message(complaint_id, username, 'admin', message_text if message_text else None, file_paths_json)
                                st.success('✅ Message sent successfully!')
                                st.rerun()
                            except Exception as e:
                                st.error(f'❌ Error sending message: {str(e)}')
                st.divider()
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    new_status = st.selectbox('Update Status', status_options, index=status_index, key=f'table_status_{complaint_id}')
                with col2:
                    current_category = complaint.get('predicted_category', 'Calculation Discrepancy')
                    current_category_name = get_category_name(current_category)
                    category_options = ['Marks Mismatch', 'Absentee Error', 'Missing Grade', 'Calculation Discrepancy']
                    try:
                        category_index = category_options.index(current_category_name)
                    except ValueError:
                        category_index = 0
                    new_category_name = st.selectbox('Update Category', category_options, index=category_index, key=f'table_category_{complaint_id}')
                    new_category_id = get_category_id(new_category_name)[0]
                with col3:
                    if st.button('Update Status', key=f'table_update_status_{complaint_id}', use_container_width=True, type='primary'):
                        try:
                            db.update_complaint_status(complaint_id, new_status)
                            st.success(f'✅ Status updated to {new_status}')
                            st.rerun()
                        except Exception as e:
                            st.error(f'❌ Error updating status: {str(e)}')
                st.divider()
                if st.button('🗑️ Delete Complaint', key=f'table_delete_{complaint_id}', type='secondary', use_container_width=True):
                    if db.delete_complaint(complaint_id):
                        st.success(f'✅ Complaint #{complaint_id} deleted successfully!')
                        st.rerun()
                    else:
                        st.error(f'❌ Failed to delete complaint #{complaint_id}')
                if new_status == 'Resolved':
                    st.divider()
                    st.write('**📝 Resolution Notes (Required when resolving):**')
                    resolution_note = st.text_area('Resolution Note', placeholder='Describe how this complaint was resolved...', key=f'table_resolution_note_{complaint_id}', height=100)
                    col_img, col_file = st.columns(2)
                    with col_img:
                        resolution_images = st.file_uploader('Upload Resolution Images (Optional)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f'table_resolution_images_{complaint_id}')
                    with col_file:
                        resolution_files = st.file_uploader('Upload Resolution Files (Optional)', type=['pdf', 'doc', 'docx', 'txt'], accept_multiple_files=True, key=f'table_resolution_files_{complaint_id}')
                    if st.button('💾 Save Resolution Notes', key=f'table_save_resolution_{complaint_id}', use_container_width=True, type='primary'):
                        if not resolution_note or len(resolution_note.strip()) < 10:
                            st.error('⚠️ Please provide a resolution note (at least 10 characters) when resolving a complaint.')
                        else:
                            try:
                                saved_file_paths = []
                                upload_dir = Path(__file__).parent.parent / 'uploads' / 'resolution'
                                upload_dir.mkdir(parents=True, exist_ok=True)
                                if resolution_images:
                                    for img in resolution_images:
                                        file_ext = Path(img.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(img.getbuffer())
                                        saved_file_paths.append(f'uploads/resolution/{safe_filename}')
                                if resolution_files:
                                    for file in resolution_files:
                                        file_ext = Path(file.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(file.getbuffer())
                                        saved_file_paths.append(f'uploads/resolution/{safe_filename}')
                                file_paths_json = json.dumps(saved_file_paths) if saved_file_paths else None
                                db.add_resolution_update(complaint_id, username, resolution_note, file_paths_json)
                                st.success('✅ Resolution notes saved successfully!')
                                st.rerun()
                            except Exception as e:
                                st.error(f'❌ Error saving resolution notes: {str(e)}')
                with col4:
                    if st.button('Update Category', key=f'table_update_category_{complaint_id}', use_container_width=True):
                        try:
                            db.update_complaint_category(complaint_id, new_category_id)
                            st.success(f'✅ Category updated to {new_category_name}')
                            st.rerun()
                        except Exception as e:
                            st.error(f'❌ Error updating category: {str(e)}')
    else:
        for complaint in filtered_complaints:
            status = complaint.get('status', 'Pending')
            status_emoji = {'Pending': '🟡', 'Resolved': '🟢', 'In Progress': '🔵', 'Rejected': '🔴'}.get(status, '⚪')
            category_display = get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))
            risk_level = complaint.get('sla_risk_level', 'Medium')
            risk_badge = get_risk_badge_html(risk_level)
            st.markdown(risk_badge, unsafe_allow_html=True)
            complaint_id = complaint.get('complaint_id')
            with st.expander(f'{status_emoji} **ID:** {complaint_id} | **{category_display}** | **{status}** | **SLA Risk:** {risk_level} | {complaint.get('created_at', 'N/A')}', expanded=False):
                st.write('**Complaint Text:**')
                st.write(complaint.get('text', 'No text provided'))
                st.divider()
                col1, col2, col3, col4 = st.columns(4)
                col1.write(f'**Student:** {complaint.get('student_username', 'N/A')}')
                col2.write(f'**Category:** {get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))}')
                if complaint.get('confidence') is not None:
                    col3.write(f'**Confidence:** {complaint.get('confidence', 0):.1%}')
                col4.write(f'**Status:** {status}')
                course_code = complaint.get('course_code')
                semester = complaint.get('semester')
                if course_code or semester:
                    st.write('**Course Information:**')
                    info_cols = st.columns(2)
                    if course_code:
                        info_cols[0].write(f'**Course Code:** {course_code}')
                    if semester:
                        info_cols[1].write(f'**Semester:** {semester}')
                st.caption(f'**Complaint ID:** {complaint_id} | **Created:** {complaint.get('created_at', 'N/A')}')
                file_path = complaint.get('file_path')
                if file_path:
                    file_full_path = Path(__file__).parent.parent / file_path
                    if file_full_path.exists():
                        with open(file_full_path, 'rb') as f:
                            file_data = f.read()
                            file_name = Path(file_path).name
                            st.download_button(label='📎 Download Supporting Evidence', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'admin_download_{complaint_id}')
                    else:
                        st.caption('⚠️ File not found on server')
                st.divider()
                render_duplicate_insights(complaint.get('text', ''), complaint_id)
                st.divider()
                render_sla_prediction_panel(complaint)
                st.divider()
                st.subheader('💬 Communication Thread')
                try:
                    similar_complaints = find_similar_complaint(complaint.get('text', ''), top_k=1)
                except Exception:
                    similar_complaints = []
                messages = db.get_complaint_messages(complaint_id)
                system_messages = []
                if similar_complaints and len(similar_complaints) > 0:
                    similar = similar_complaints[0]
                    similarity_score = similar.get('score', 0.0)
                    if similarity_score > 0.7:
                        similar_text = similar.get('complaint_text', '')[:200] + '...' if len(similar.get('complaint_text', '')) > 200 else similar.get('complaint_text', '')
                        similar_resolution_time = similar.get('resolution_time', 'N/A')
                        similar_category = similar.get('complaint_type', 'Unknown')
                        resolution_desc = similar.get('resolution_desc', '')
                        system_msg_text = f'**Similar Resolved Case Found** (Similarity: {similarity_score:.1%})\n                        \n**Category:** {similar_category}\n**Resolution Time:** {similar_resolution_time} days\n**Previous Complaint Text:** "{similar_text}"\n**Resolution Description:** "{resolution_desc[:200]}{('...' if len(resolution_desc) > 200 else '')}"\n\nThis complaint is similar to a previously resolved case. Review the resolution approach above.'
                        system_messages.append({'message_id': -1, 'sender_role': 'system', 'sender_username': 'System', 'message_text': system_msg_text, 'created_at': 'System Recommendation', 'file_paths': None})
                all_messages = system_messages + messages if messages else system_messages
                if all_messages:
                    st.write('**Message History:**')
                    for message in all_messages:
                        render_chat_message(message, is_admin=True)
                else:
                    st.info('No messages yet. Start the conversation below.')
                st.divider()
                st.write('**Send a Message:**')
                with st.form(key=f'message_form_card_{complaint_id}', clear_on_submit=True):
                    message_text = st.text_area('Your Message', placeholder='Type your message here...', height=100, key=f'message_text_card_{complaint_id}')
                    col_img, col_file = st.columns(2)
                    with col_img:
                        message_images = st.file_uploader('Attach Images (Optional)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f'message_images_card_{complaint_id}')
                    with col_file:
                        message_files = st.file_uploader('Attach Files (Optional)', type=['pdf', 'doc', 'docx', 'txt'], accept_multiple_files=True, key=f'message_files_card_{complaint_id}')
                    submit_message = st.form_submit_button('📤 Send Message', use_container_width=True, type='primary')
                    if submit_message:
                        if not message_text and (not message_images) and (not message_files):
                            st.error('⚠️ Please provide a message, image, or file.')
                        else:
                            try:
                                saved_file_paths = []
                                upload_dir = Path(__file__).parent.parent / 'uploads' / 'complaint_messages'
                                upload_dir.mkdir(parents=True, exist_ok=True)
                                if message_images:
                                    for img in message_images:
                                        file_ext = Path(img.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(img.getbuffer())
                                        saved_file_paths.append(f'uploads/complaint_messages/{safe_filename}')
                                if message_files:
                                    for file in message_files:
                                        file_ext = Path(file.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(file.getbuffer())
                                        saved_file_paths.append(f'uploads/complaint_messages/{safe_filename}')
                                file_paths_json = json.dumps(saved_file_paths) if saved_file_paths else None
                                db.add_complaint_message(complaint_id, username, 'admin', message_text if message_text else None, file_paths_json)
                                st.success('✅ Message sent successfully!')
                                st.rerun()
                            except Exception as e:
                                st.error(f'❌ Error sending message: {str(e)}')
                st.divider()
                st.write('**Update Complaint:**')
                current_status = complaint.get('status', 'Pending')
                status_options = ['Pending', 'In Progress', 'Resolved', 'Rejected']
                status_index = status_options.index(current_status) if current_status in status_options else 0
                action_cols = st.columns([2, 2, 1, 1])
                with action_cols[0]:
                    new_status = st.selectbox('Select Status', status_options, index=status_index, key=f'status_select_{complaint_id}', label_visibility='visible')
                with action_cols[1]:
                    current_category = complaint.get('predicted_category', 'Calculation Discrepancy')
                    current_category_name = get_category_name(current_category)
                    category_options = ['Marks Mismatch', 'Absentee Error', 'Missing Grade', 'Calculation Discrepancy']
                    try:
                        category_index = category_options.index(current_category_name)
                    except ValueError:
                        category_index = 0
                    new_category_name = st.selectbox('Select Category', category_options, index=category_index, key=f'category_select_{complaint_id}', label_visibility='visible')
                    new_category_id = get_category_id(new_category_name)[0]
                with action_cols[2]:
                    if st.button('Update Status', key=f'update_status_{complaint_id}', use_container_width=True, type='primary'):
                        try:
                            db.update_complaint_status(complaint_id, new_status)
                            st.success(f'✅ Status updated to {new_status}')
                            st.rerun()
                        except Exception as e:
                            st.error(f'❌ Error updating status: {str(e)}')
                st.divider()
                if st.button('🗑️ Delete Complaint', key=f'card_delete_{complaint_id}', type='secondary', use_container_width=True):
                    if db.delete_complaint(complaint_id):
                        st.success(f'✅ Complaint #{complaint_id} deleted successfully!')
                        st.rerun()
                    else:
                        st.error(f'❌ Failed to delete complaint #{complaint_id}')
                if new_status == 'Resolved':
                    st.divider()
                    st.write('**📝 Resolution Notes (Required when resolving):**')
                    resolution_note = st.text_area('Resolution Note', placeholder='Describe how this complaint was resolved...', key=f'card_resolution_note_{complaint_id}', height=100)
                    col_img, col_file = st.columns(2)
                    with col_img:
                        resolution_images = st.file_uploader('Upload Resolution Images (Optional)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f'card_resolution_images_{complaint_id}')
                    with col_file:
                        resolution_files = st.file_uploader('Upload Resolution Files (Optional)', type=['pdf', 'doc', 'docx', 'txt'], accept_multiple_files=True, key=f'card_resolution_files_{complaint_id}')
                    if st.button('💾 Save Resolution Notes', key=f'card_save_resolution_{complaint_id}', use_container_width=True, type='primary'):
                        if not resolution_note or len(resolution_note.strip()) < 10:
                            st.error('⚠️ Please provide a resolution note (at least 10 characters) when resolving a complaint.')
                        else:
                            try:
                                saved_file_paths = []
                                upload_dir = Path(__file__).parent.parent / 'uploads' / 'resolution'
                                upload_dir.mkdir(parents=True, exist_ok=True)
                                if resolution_images:
                                    for img in resolution_images:
                                        file_ext = Path(img.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(img.getbuffer())
                                        saved_file_paths.append(f'uploads/resolution/{safe_filename}')
                                if resolution_files:
                                    for file in resolution_files:
                                        file_ext = Path(file.name).suffix.lower()
                                        safe_filename = f'{complaint_id}_{uuid.uuid4().hex[:8]}{file_ext}'
                                        file_path = upload_dir / safe_filename
                                        with open(file_path, 'wb') as f:
                                            f.write(file.getbuffer())
                                        saved_file_paths.append(f'uploads/resolution/{safe_filename}')
                                file_paths_json = json.dumps(saved_file_paths) if saved_file_paths else None
                                db.add_resolution_update(complaint_id, username, resolution_note, file_paths_json)
                                st.success('✅ Resolution notes saved successfully!')
                                st.rerun()
                            except Exception as e:
                                st.error(f'❌ Error saving resolution notes: {str(e)}')
                with action_cols[3]:
                    if st.button('Update Category', key=f'update_category_{complaint_id}', use_container_width=True):
                        try:
                            db.update_complaint_category(complaint_id, new_category_id)
                            st.success(f'✅ Category updated to {new_category_name}')
                            st.rerun()
                        except Exception as e:
                            st.error(f'❌ Error updating category: {str(e)}')
    st.divider()
    st.subheader('📥 Export Complaints')
    all_complaints = db.get_all_complaints(limit=10000)
    if all_complaints:
        export_all_data = []
        for c in all_complaints:
            export_all_data.append({'Complaint ID': c.get('complaint_id'), 'Student': c.get('student_username', ''), 'Course Code': c.get('course_code', ''), 'Semester': c.get('semester', ''), 'Text': c.get('text', ''), 'Category': get_category_name(c.get('predicted_category', 'Calculation Discrepancy')), 'Confidence': c.get('confidence', 0) if c.get('confidence') is not None else '', 'Status': c.get('status', 'Pending'), 'File Path': c.get('file_path', ''), 'Created At': c.get('created_at', '')})
        df_all = pd.DataFrame(export_all_data)
        csv_all = df_all.to_csv(index=False)
        st.download_button(label='📥 Export All Complaints as CSV', data=csv_all, file_name=f'all_complaints_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv', mime='text/csv', use_container_width=True, key='export_all_complaints')
run()