import streamlit as st
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
import db
from model_loader import predict_category, find_similar_complaint, predict_sla

def get_category_name(category_value):
    category_mapping = {'0': 'Marks Mismatch', '1': 'Absentee Error', '2': 'Missing Grade', '3': 'Calculation Discrepancy', 'Marks Mismatch': 'Marks Mismatch', 'Absentee Error': 'Absentee Error', 'Missing Grade': 'Missing Grade', 'Calculation Discrepancy': 'Calculation Discrepancy'}
    category_str = str(category_value) if category_value else 'Calculation Discrepancy'
    return category_mapping.get(category_str, 'Calculation Discrepancy')

def run():
    st.header('📝 Submit Complaint')
    username = st.session_state.get('username')
    role = st.session_state.get('role')
    if not username:
        st.error('Not logged in.')
        return
    if role != 'student':
        st.error('❌ Access denied. This page is only available for students.')
        st.info('Please login with a student account to access this page.')
        return
    st.subheader('File a New Complaint')
    with st.form('complaint_form', clear_on_submit=True):
        student_results = db.get_results_by_student(username)
        course_codes = sorted(set([r.get('course_code', '') for r in student_results if r.get('course_code')]))
        col1, col2 = st.columns(2)
        with col1:
            if course_codes:
                course_code = st.selectbox('Course Code', options=[''] + course_codes, help='Select a course code from your past results, or leave blank if not applicable')
            else:
                course_code = st.text_input('Course Code', placeholder='e.g., CS101, MATH201', help='Enter the course code related to your complaint (optional)')
        with col2:
            semester = st.selectbox('Semester', options=['', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], help='Select the semester related to your complaint (optional)')
        complaint_text = st.text_area('Describe your complaint', placeholder='Enter your complaint details here...', height=150)
        uploaded_file = st.file_uploader('Upload Supporting Evidence (Optional)', type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'], help='Upload images (PNG, JPG) or documents (PDF, DOC, DOCX) as supporting evidence for your complaint.')
        file_size_mb = 0
        if uploaded_file:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > 10:
                st.warning(f'⚠️ File size ({file_size_mb:.2f} MB) exceeds 10 MB limit. Please upload a smaller file.')
            else:
                st.info(f'📎 File selected: {uploaded_file.name} ({file_size_mb:.2f} MB)')
        if complaint_text:
            with st.expander('🔮 Model Predictions Preview', expanded=True):
                try:
                    cat_result = predict_category(complaint_text)
                    predicted_cat_name = cat_result.get('prediction', 'Calculation Discrepancy')
                    confidence = cat_result.get('confidence', 0.0)
                    student_results = db.get_results_by_student(username)
                    faculty_department = 'Computer Science'
                    if student_results:
                        latest_result = student_results[0] if student_results else None
                        if latest_result:
                            faculty_department = latest_result.get('faculty_department', faculty_department)
                    sla_input = {'Complaint Type': predicted_cat_name, 'Faculty Department': faculty_department or 'Computer Science'}
                    sla_result = predict_sla(sla_input)
                    median_resolution_time = sla_result.get('predicted_median_days', 5)
                    breach_probability = sla_result.get('breach_prob_at_t', 0.5)
                    if breach_probability < 0.3:
                        risk_level = 'Low'
                    elif breach_probability < 0.6:
                        risk_level = 'Medium'
                    else:
                        risk_level = 'High'
                    similar_complaints = find_similar_complaint(complaint_text, top_k=3)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric('Category', predicted_cat_name)
                    with col2:
                        st.metric('Resolution Time', f'{int(median_resolution_time)} days')
                    with col3:
                        st.metric('Breach Probability', f'{breach_probability * 100:.1f}%')
                    top_keywords = cat_result.get('top_keywords', [])
                    if top_keywords:
                        st.caption(f'**Keywords:** {', '.join(top_keywords[:5])}')
                except Exception as e:
                    st.error(f'❌ Error in prediction: {str(e)}')
                    similar_complaints = []
                if similar_complaints and len(similar_complaints) > 0:
                    similar = similar_complaints[0]
                    similarity_score = similar.get('score', 0.0)
                    if similarity_score >= 0.8:
                        st.warning(f'⚠️ **High similarity ({similarity_score:.1%})** to a previous complaint.')
                    elif similarity_score >= 0.6:
                        st.info(f'ℹ️ **Moderate similarity ({similarity_score:.1%})** to previous complaints.')
                    with st.expander(f'📋 Similar Complaint (Score: {similarity_score:.1%})', expanded=similarity_score >= 0.8):
                        st.write(f'**Category:** {similar.get('complaint_type', 'N/A')}')
                        if similar.get('resolution_time'):
                            st.write(f'**Resolution Time:** {similar.get('resolution_time')} days')
                        st.write(f'**Complaint Text:** {similar.get('complaint_text', 'N/A')}')
                        if similar.get('resolution_desc'):
                            st.write(f'**Resolution:** {similar.get('resolution_desc', 'N/A')}')
        else:
            st.info('Start typing your complaint to see AI analysis preview.')
        submitted = st.form_submit_button('Submit Complaint', use_container_width=True)
        if submitted:
            if not complaint_text or len(complaint_text.strip()) < 10:
                st.error('Please enter a complaint with at least 10 characters.')
            else:
                file_path = None
                if uploaded_file:
                    if file_size_mb > 10:
                        st.error('File size exceeds 10 MB limit. Please upload a smaller file.')
                    else:
                        try:
                            file_ext = Path(uploaded_file.name).suffix.lower()
                            safe_filename = f'{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}'
                            upload_dir = Path(__file__).parent.parent / 'uploads' / 'complaints'
                            upload_dir.mkdir(parents=True, exist_ok=True)
                            file_path = upload_dir / safe_filename
                            with open(file_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            file_path_db = f'uploads/complaints/{safe_filename}'
                            file_path = file_path_db
                            st.success(f'📎 File uploaded successfully: {uploaded_file.name}')
                        except Exception as e:
                            st.error(f'❌ Error uploading file: {str(e)}')
                            file_path = None
                try:
                    cat_result = predict_category(complaint_text)
                    predicted_category_name = cat_result.get('prediction', 'Calculation Discrepancy')
                    predicted_category = predicted_category_name
                    confidence = cat_result.get('confidence', 0.0)
                    similar_complaints = find_similar_complaint(complaint_text, top_k=1)
                    duplicate_reference = None
                    if similar_complaints and len(similar_complaints) > 0:
                        similar = similar_complaints[0]
                        similarity_score = similar.get('score', 0.0)
                        if similarity_score >= 0.8:
                            duplicate_reference = similar.get('index')
                    student_results = db.get_results_by_student(username)
                    faculty_department = 'Computer Science'
                    if student_results:
                        latest_result = student_results[0] if student_results else None
                        if latest_result:
                            faculty_department = latest_result.get('faculty_department', faculty_department)
                    sla_input = {'Complaint Type': predicted_category_name, 'Faculty Department': faculty_department}
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
                    st.error(f'❌ Error in AI prediction: {str(e)}')
                    predicted_category = 'Calculation Discrepancy'
                    predicted_category_name = 'Calculation Discrepancy'
                    confidence = 0.0
                    duplicate_reference = None
                    similar_complaints = []
                    median_resolution_time = 5
                    breach_probability = 0.0
                    risk_level = 'Low'
                complaint_id = db.add_complaint(student_username=username, text=complaint_text.strip(), predicted_category=predicted_category, confidence=confidence, file_path=file_path, course_code=course_code if course_code else None, semester=semester if semester else None, duplicate_reference=duplicate_reference)
                if complaint_id:
                    st.success(f'✅ Complaint submitted successfully! (ID: {complaint_id})')
                    st.info('📊 **Model Predictions:**')
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric('Category', predicted_category_name)
                    with col2:
                        st.metric('Resolution Time', f'{int(median_resolution_time)} days')
                    with col3:
                        st.metric('Breach Probability', f'{breach_probability * 100:.1f}%')
                    if duplicate_reference:
                        st.warning(f'⚠️ **Potential Duplicate Detected:** This complaint is very similar to complaint ID {duplicate_reference}. Please check if your issue has already been reported.')
                        if similar_complaints:
                            similar = similar_complaints[0]
                            similarity_score = similar.get('score', 0.0)
                            st.write(f'**Similar Complaint** (Score: {similarity_score:.1%})')
                            st.write(f'**Category:** {similar.get('complaint_type', 'N/A')}')
                            if similar.get('resolution_time'):
                                st.write(f'**Resolution Time:** {similar.get('resolution_time')} days')
                            st.write(f'**Text:** {similar.get('complaint_text', 'N/A')}')
                            if similar.get('resolution_desc'):
                                st.write(f'**Resolution:** {similar.get('resolution_desc', 'N/A')}')
                    else:
                        st.success('✅ No similar complaints found. This appears to be a new issue.')
                    st.balloons()
                else:
                    st.error('Failed to submit complaint. Please try again.')
    st.divider()
    st.subheader('📋 Your Previous Complaints')
    complaints = db.get_complaints_by_student(username)
    if complaints:
        for complaint in complaints:
            status = complaint.get('status', 'Pending')
            emoji = {'Pending': '🟡', 'Resolved': '🟢', 'In Progress': '🔵', 'Rejected': '🔴'}.get(status, '⚪')
            category_display = get_category_name(complaint.get('predicted_category', 'Calculation Discrepancy'))
            complaint_id = complaint.get('complaint_id')
            with st.expander(f'{emoji} {category_display} - {status} | {complaint.get('created_at', 'N/A')}', expanded=False):
                st.write(complaint.get('text', 'No text'))
                c1, c2, c3 = st.columns(3)
                c1.write(f'**Complaint ID:** {complaint_id}')
                c2.write(f'**Category:** {category_display}')
                c3.write(f'**Status:** {status}')
                st.divider()
                if st.button('🗑️ Delete', key=f'delete_complaint_{complaint_id}', type='secondary', use_container_width=True):
                    if db.delete_complaint(complaint_id):
                        st.success(f'✅ Complaint #{complaint_id} deleted successfully!')
                        st.rerun()
                    else:
                        st.error(f'❌ Failed to delete complaint #{complaint_id}')
                st.divider()
                st.subheader('💬 Communication Thread')
                similar_complaints = find_similar_complaint(complaint.get('text', ''), top_k=1)
                messages = db.get_complaint_messages(complaint.get('complaint_id'))
                system_messages = []
                if similar_complaints and len(similar_complaints) > 0:
                    similar = similar_complaints[0]
                    similarity_score = similar.get('score', 0.0)
                    if similarity_score > 0.7:
                        similar_text = similar.get('complaint_text', '')
                        similar_resolution_time = similar.get('resolution_time', 'N/A')
                        similar_category = similar.get('complaint_type', 'Unknown')
                        resolution_desc = similar.get('resolution_desc', '')
                        system_msg_text = f'**Similar Resolved Case** (Score: {similarity_score:.1%})\n                        \n**Category:** {similar_category}\n**Resolution Time:** {similar_resolution_time} days\n**Complaint:** "{similar_text}"\n**Resolution:** "{resolution_desc}" '
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
                                                st.download_button(label=f'📎 {file_name}', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'msg_download_{message.get('message_id')}_{file_name}')
                            except:
                                pass
                else:
                    st.info('No messages yet. Start the conversation below.')
                st.divider()
                st.write('**Send a Message:**')
                with st.form(key=f'message_form_{complaint.get('complaint_id')}', clear_on_submit=True):
                    message_text = st.text_area('Your Message', placeholder='Type your message here...', height=100, key=f'message_text_{complaint.get('complaint_id')}')
                    col_img, col_file = st.columns(2)
                    with col_img:
                        message_images = st.file_uploader('Attach Images (Optional)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f'message_images_{complaint.get('complaint_id')}')
                    with col_file:
                        message_files = st.file_uploader('Attach Files (Optional)', type=['pdf', 'doc', 'docx', 'txt'], accept_multiple_files=True, key=f'message_files_{complaint.get('complaint_id')}')
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
                file_path = complaint.get('file_path')
                if file_path:
                    file_full_path = Path(__file__).parent.parent / file_path
                    if file_full_path.exists():
                        with open(file_full_path, 'rb') as f:
                            file_data = f.read()
                            file_name = Path(file_path).name
                            st.download_button(label='📎 Download Original Supporting Evidence', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'download_{complaint.get('complaint_id')}')
                    else:
                        st.caption('⚠️ File not found on server')
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
                                                    st.download_button(label=f'📎 Download {file_name}', data=file_data, file_name=file_name, mime='application/octet-stream', key=f'resolution_download_{complaint.get('complaint_id')}_{file_name}')
                                            else:
                                                st.caption(f'⚠️ File not found: {file_name}')
                                except:
                                    pass
                    else:
                        st.info('Resolution details are being prepared. Please check back later.')
                st.caption(f'Submitted: {complaint.get('created_at', 'N/A')}')
    else:
        st.info('No complaints submitted yet. Use the form above to file your first complaint.')
run()