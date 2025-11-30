import streamlit as st
import sys
from pathlib import Path
import json
import uuid
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
from model_loader import find_similar_complaint

def get_category_name(category_value):
    category_mapping = {'0': 'Marks Mismatch', '1': 'Absentee Error', '2': 'Missing Grade', '3': 'Calculation Discrepancy', 'Marks Mismatch': 'Marks Mismatch', 'Absentee Error': 'Absentee Error', 'Missing Grade': 'Missing Grade', 'Calculation Discrepancy': 'Calculation Discrepancy'}
    category_str = str(category_value) if category_value else 'Calculation Discrepancy'
    return category_mapping.get(category_str, 'Calculation Discrepancy')

def run():
    st.header('📊 Student Dashboard')
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
    complaints = db.get_complaints_by_student(username)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Total Results', len(results))
    with col2:
        st.metric('Passed Courses', sum((1 for r in results if r.get('status') == 'Pass')))
    with col3:
        st.metric('Failed Courses', sum((1 for r in results if r.get('status') == 'Fail')))
    with col4:
        st.metric('Pending Complaints', sum((1 for c in complaints if c.get('status') == 'Pending')))
    st.divider()
    st.subheader('📝 Recent Results')
    if results:
        for result in results[:5]:
            course_code = result.get('course_code', 'N/A')
            course_name = result.get('course_name', 'N/A')
            with st.expander(f'**{course_code}** - {course_name}', expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f'**Course Code:** {course_code}')
                c2.write(f'**Semester:** {result.get('semester', 'N/A')}')
                c3.write(f'**Marks:** {result.get('marks', 'N/A')}')
                status = result.get('status', 'Pass')
                if status == 'Pass':
                    c4.success(f'**Status:** {status}')
                elif status == 'Fail':
                    c4.error(f'**Status:** {status}')
                else:
                    c4.warning(f'**Status:** {status}')
                st.caption(f'Uploaded: {result.get('uploaded_at', 'N/A')}')
        if len(results) > 5:
            st.info(f"Showing 5 of {len(results)} results. View all in 'My Results' page.")
    else:
        st.info('No results found. Results will appear here once uploaded by an admin.')
    st.divider()
    st.subheader('📋 Recent Complaints')
    if complaints:
        for complaint in complaints[:5]:
            status = complaint.get('status', 'Pending')
            emoji = {'Pending': '🟡', 'Resolved': '🟢', 'In Progress': '🔵', 'Rejected': '🔴'}.get(status, '⚪')
            category_display = get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))
            with st.expander(f'{emoji} {category_display} - {status}', expanded=False):
                st.write(complaint.get('text', 'No text'))
                a, b = st.columns(2)
                a.write(f'**Category:** {category_display}')
                b.write(f'**Status:** {status}')
                st.divider()
                st.subheader('💬 Communication Thread')
                try:
                    similar_complaints = find_similar_complaint(complaint.get('text', ''), top_k=1)
                except Exception:
                    similar_complaints = []
                messages = db.get_complaint_messages(complaint.get('complaint_id'))
                system_messages = []
                if similar_complaints and len(similar_complaints) > 0:
                    similar = similar_complaints[0]
                    similarity_score = similar.get('score', 0.0)
                    if similarity_score > 0.7:
                        similar_text = similar.get('complaint_text', '')[:200] + '...' if len(similar.get('complaint_text', '')) > 200 else similar.get('complaint_text', '')
                        similar_resolution_time = similar.get('resolution_time', 'N/A')
                        similar_category = similar.get('complaint_type', 'Unknown')
                        resolution_desc = similar.get('resolution_desc', '')
                        system_msg_text = f'**Similar Resolved Case Found** (Similarity: {similarity_score:.1%})\n                        \n**Category:** {similar_category}\n**Resolution Time:** {similar_resolution_time} days\n**Previous Complaint Text:** "{similar_text}"\n**Resolution Description:** "{resolution_desc[:200]}{('...' if len(resolution_desc) > 200 else '')}"\n\nThis complaint is similar to a previously resolved case. The admin may use a similar resolution approach.'
                        system_messages.append({'message_id': -1, 'sender_role': 'system', 'sender_username': 'System', 'message_text': system_msg_text, 'created_at': 'System Recommendation', 'file_paths': None})
                all_messages = system_messages + messages if messages else system_messages
                if all_messages:
                    st.write('**Message History:**')
                    for message in all_messages:
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
                        st.markdown(f'\n                            <div style="\n                                background-color: {bg_color};\n                                border-left: 4px solid {border_color};\n                                padding: 12px;\n                                margin: 8px 0;\n                                border-radius: 4px;\n                            ">\n                                <div style="font-weight: bold; margin-bottom: 4px; color: #333;">\n                                    {label}\n                                </div>\n                                <div style="color: #555; margin-bottom: 4px;">\n                                    {(message_text if message_text else '<em>No text message</em>')}\n                                </div>\n                                <div style="font-size: 0.85em; color: #888;">\n                                    {created_at}\n                                </div>\n                            </div>\n                            ', unsafe_allow_html=True)
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
                                                st.download_button(label=f'📎 {file_name}', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'dashboard_msg_download_{message.get('message_id')}_{file_name}')
                            except:
                                pass
                else:
                    st.info('No messages yet. Start the conversation below.')
                st.divider()
                st.write('**Send a Message:**')
                with st.form(key=f'dashboard_message_form_{complaint.get('complaint_id')}', clear_on_submit=True):
                    message_text = st.text_area('Your Message', placeholder='Type your message here...', height=100, key=f'dashboard_message_text_{complaint.get('complaint_id')}')
                    col_img, col_file = st.columns(2)
                    with col_img:
                        message_images = st.file_uploader('Attach Images (Optional)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f'dashboard_message_images_{complaint.get('complaint_id')}')
                    with col_file:
                        message_files = st.file_uploader('Attach Files (Optional)', type=['pdf', 'doc', 'docx', 'txt'], accept_multiple_files=True, key=f'dashboard_message_files_{complaint.get('complaint_id')}')
                    submit_message = st.form_submit_button('📤 Send Message', use_container_width=True, type='primary')
                    if submit_message:
                        if not message_text and (not message_images) and (not message_files):
                            st.error('⚠️ Please provide a message, image, or file.')
                        else:
                            try:
                                saved_file_paths = []
                                upload_dir = Path(__file__).parent.parent / 'uploads' / 'complaint_messages'
                                upload_dir.mkdir(parents=True, exist_ok=True)
                                complaint_id = complaint.get('complaint_id')
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
                                db.add_complaint_message(complaint_id, username, 'student', message_text if message_text else None, file_paths_json)
                                st.success('✅ Message sent successfully!')
                                st.rerun()
                            except Exception as e:
                                st.error(f'❌ Error sending message: {str(e)}')
                st.divider()
                if status == 'Resolved':
                    st.divider()
                    st.subheader('✅ Resolution Details')
                    resolution_updates = db.get_resolution_updates(complaint.get('complaint_id'))
                    if resolution_updates:
                        for update in resolution_updates:
                            st.write(f'**Resolved by:** {update.get('admin_username', 'Admin')}')
                            st.write(f'**Resolved on:** {update.get('created_at', 'N/A')}')
                            if update.get('note_text'):
                                st.write('**Resolution Note:**')
                                st.info(update.get('note_text'))
                            file_paths_json = update.get('file_paths')
                            if file_paths_json:
                                try:
                                    file_paths = json.loads(file_paths_json)
                                    if file_paths:
                                        st.write('**Resolution Attachments:**')
                                        for file_path in file_paths:
                                            file_full_path = Path(__file__).parent.parent / file_path
                                            if file_full_path.exists():
                                                with open(file_full_path, 'rb') as f:
                                                    file_data = f.read()
                                                    file_name = Path(file_path).name
                                                    st.download_button(label=f'📎 Download {file_name}', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'dashboard_resolution_download_{complaint.get('complaint_id')}_{file_name}')
                                            else:
                                                st.caption(f'⚠️ File not found: {file_name}')
                                except:
                                    pass
                    else:
                        st.info('Resolution details are being prepared. Please check back later.')
                st.caption(f'Submitted: {complaint.get('created_at', 'N/A')}')
        if len(complaints) > 5:
            st.info(f'Showing 5 of {len(complaints)} complaints.')
    else:
        st.info("No complaints submitted yet. Use 'Submit Complaint' to file a new complaint.")
run()