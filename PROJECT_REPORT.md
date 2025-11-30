# Secure Result Management System
## Comprehensive Project Report

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Tech Stack and Overview](#tech-stack-and-overview)
3. [System Architecture](#system-architecture)
4. [Database Schema](#database-schema)
5. [Machine Learning Models](#machine-learning-models)
6. [User Interface Design](#user-interface-design)
7. [Backend Implementation](#backend-implementation)
8. [Page-by-Page Feature Documentation](#page-by-page-feature-documentation)
9. [Integration and Testing](#integration-and-testing)
10. [Conclusion](#conclusion)

---

## Executive Summary

The **Secure Result Management System** is a comprehensive web application designed to streamline academic result management and complaint handling in educational institutions. The system leverages modern web technologies, machine learning algorithms, and a robust database architecture to provide an intelligent, user-friendly platform for both students and administrators.

### Key Features:
- **Automated Complaint Categorization** using machine learning
- **SLA (Service Level Agreement) Risk Prediction** for complaint resolution
- **Duplicate Complaint Detection** using semantic similarity
- **Real-time Communication Thread** between students and admins
- **Bulk Result Upload** via CSV files
- **Comprehensive Analytics Dashboard** with visualizations
- **Role-based Access Control** (Student and Admin roles)

---

## Tech Stack and Overview

### Frontend Framework

#### **Streamlit**
- **Purpose**: Primary web framework for building the user interface
- **Why Streamlit**: 
  - Rapid development of interactive web applications
  - Built-in components for data visualization, forms, and file uploads
  - Python-native, allowing seamless integration with ML models
  - Automatic UI updates and reactive programming model
- **Usage in Project**:
  - All user-facing pages are built using Streamlit components
  - Navigation system using `st.navigation()` for multi-page applications
  - Form handling for complaint submission and result uploads
  - Real-time data visualization using Streamlit's chart components

### Backend Framework

#### **Python 3.x**
- **Purpose**: Core programming language for the entire application
- **Why Python**:
  - Extensive libraries for machine learning and data processing
  - Excellent database connectivity
  - Strong ecosystem for web development
- **Key Libraries Used**:
  - `sqlite3`: Database connectivity
  - `pandas`: Data manipulation and CSV processing
  - `numpy`: Numerical computations
  - `pathlib`: File system operations

### Database

#### **SQLite3**
- **Purpose**: Relational database management system
- **Why SQLite**:
  - Lightweight and serverless, perfect for standalone applications
  - ACID-compliant for data integrity
  - No external database server required
  - Excellent for small to medium-scale applications
- **Usage**:
  - Stores user accounts, complaints, results, and communication threads
  - Provides referential integrity through foreign keys
  - Indexed for optimal query performance

### Machine Learning Stack

#### **Scikit-learn**
- **Purpose**: Machine learning library for classification and anomaly detection
- **Usage**:
  - Complaint category classification model
  - Anomaly detection for unusual complaint patterns
  - Model serialization using `joblib`
  - Text vectorization (TF-IDF) for feature extraction

#### **Sentence Transformers (SBERT)**
- **Purpose**: Semantic text embeddings for similarity detection
- **Why SBERT**:
  - State-of-the-art semantic similarity computation
  - Pre-trained models for efficient duplicate detection
  - Generates dense vector representations of complaint text
- **Usage**:
  - Finding similar complaints in historical data
  - Duplicate complaint detection
  - Semantic search functionality

#### **Lifelines**
- **Purpose**: Survival analysis library for SLA prediction
- **Why Lifelines**:
  - Specialized library for time-to-event analysis
  - Cox Proportional Hazards model for predicting resolution times
  - Handles censored data (unresolved complaints)
- **Usage**:
  - Predicting median resolution time for complaints
  - Calculating SLA breach probability
  - Risk level assessment (High/Medium/Low)

#### **NLTK (Natural Language Toolkit)**
- **Purpose**: Natural language processing utilities
- **Usage**:
  - Text preprocessing and cleaning
  - Stopword removal
  - Tokenization for feature extraction

### Data Visualization

#### **Plotly**
- **Purpose**: Interactive data visualization library
- **Why Plotly**:
  - Interactive charts that work seamlessly with Streamlit
  - Professional-quality visualizations
  - Support for various chart types (bar, pie, line, etc.)
- **Usage**:
  - Complaint category distribution charts
  - SLA risk distribution visualizations
  - Timeline analysis of complaints
  - Feature importance plots

### Data Processing

#### **Pandas**
- **Purpose**: Data manipulation and analysis
- **Usage**:
  - CSV file parsing and validation
  - Data cleaning and transformation
  - DataFrame operations for bulk result imports
  - Data export functionality

#### **NumPy**
- **Purpose**: Numerical computing
- **Usage**:
  - Array operations for embeddings
  - Mathematical computations for similarity scores
  - Statistical calculations

### Security and Authentication

#### **SHA-256 Hashing**
- **Purpose**: Password security
- **Implementation**:
  - Passwords are hashed using SHA-256 before storage
  - No plaintext passwords stored in database
  - Secure user authentication mechanism

### File Management

#### **Pathlib**
- **Purpose**: Cross-platform file path handling
- **Usage**:
  - Organizing uploaded files (complaints, messages, resolutions)
  - Model file management
  - Cache directory management

### Model Persistence

#### **Joblib**
- **Purpose**: Efficient serialization of Python objects
- **Usage**:
  - Saving trained ML models (classifier, vectorizer, encoders)
  - Loading models at application startup
  - Faster than pickle for large NumPy arrays

---

## System Architecture

The Secure Result Management System follows a **three-tier architecture**:

### 1. **Presentation Layer (Frontend)**
- Streamlit-based web interface
- Role-based page routing
- Real-time form validation
- Interactive visualizations

### 2. **Application Layer (Backend Logic)**
- Business logic implementation
- ML model integration
- Data processing and validation
- API-like functions for database operations

### 3. **Data Layer (Database)**
- SQLite database for persistent storage
- File system for document storage
- Model cache for performance optimization

### Data Flow Architecture

```
User Input → Streamlit UI → Backend Functions → Database/ML Models → Response → UI Update
```

### Component Interaction

- **Authentication Module**: Validates user credentials and manages sessions
- **Complaint Management Module**: Handles complaint submission, categorization, and tracking
- **Result Management Module**: Manages student results upload and retrieval
- **ML Inference Module**: Provides predictions for categories, SLA, and duplicates
- **Communication Module**: Manages message threads between users
- **Analytics Module**: Generates insights and visualizations

---

## Database Schema

The database consists of **6 main tables** with proper relationships and constraints:

### 1. **users** Table
- **Purpose**: Stores user account information
- **Fields**:
  - `user_id` (PRIMARY KEY, AUTOINCREMENT)
  - `username` (UNIQUE, NOT NULL)
  - `password_hash` (NOT NULL) - SHA-256 hashed password
  - `role` (CHECK constraint: 'student' or 'admin')
  - `created_at` (TIMESTAMP)

### 2. **complaints** Table
- **Purpose**: Stores student complaints with ML predictions
- **Fields**:
  - `complaint_id` (PRIMARY KEY, AUTOINCREMENT)
  - `student_username` (FOREIGN KEY → users.username)
  - `text` (NOT NULL) - Complaint description
  - `predicted_category` - ML-predicted category
  - `confidence` (REAL) - Prediction confidence score
  - `status` (DEFAULT 'Pending') - Complaint status
  - `file_path` - Path to uploaded supporting evidence
  - `course_code` - Related course code
  - `semester` - Related semester
  - `duplicate_reference` - Reference to similar complaint
  - `created_at` (TIMESTAMP)

### 3. **results** Table
- **Purpose**: Stores student academic results
- **Fields**:
  - `result_id` (PRIMARY KEY, AUTOINCREMENT)
  - `student_username` (FOREIGN KEY → users.username)
  - `course_code` (NOT NULL)
  - `course_name`
  - `semester`
  - `marks`
  - `status` (CHECK: 'Pass', 'Fail', 'Backlog', DEFAULT 'Pass')
  - `uploaded_at` (TIMESTAMP)

### 4. **complaint_messages** Table
- **Purpose**: Stores communication thread messages
- **Fields**:
  - `message_id` (PRIMARY KEY, AUTOINCREMENT)
  - `complaint_id` (FOREIGN KEY → complaints.complaint_id)
  - `sender_username` (FOREIGN KEY → users.username)
  - `sender_role` (CHECK: 'student' or 'admin')
  - `message_text`
  - `file_paths` (JSON) - Attached files
  - `created_at` (TIMESTAMP)

### 5. **resolution_updates** Table
- **Purpose**: Stores resolution details when complaints are resolved
- **Fields**:
  - `update_id` (PRIMARY KEY, AUTOINCREMENT)
  - `complaint_id` (FOREIGN KEY → complaints.complaint_id)
  - `admin_username` (FOREIGN KEY → users.username)
  - `note_text` - Resolution description
  - `file_paths` (JSON) - Resolution attachments
  - `created_at` (TIMESTAMP)

### 6. **Indexes**
- `idx_results_student` on `results(student_username)`
- `idx_complaints_student` on `complaints(student_username)`
- `idx_resolution_complaint` on `resolution_updates(complaint_id)`
- `idx_messages_complaint` on `complaint_messages(complaint_id)`

### Relationships
- **One-to-Many**: One user can have multiple complaints, results, and messages
- **One-to-Many**: One complaint can have multiple messages and resolution updates
- **Referential Integrity**: Foreign keys ensure data consistency

---

## Dataset Description

The project utilizes **three main CSV datasets** for machine learning model training and data management:

### 1. **complaints.csv**

This dataset contains historical complaint records used for training the complaint category classification model and duplicate detection system.

| Field Name | Description |
|------------|-------------|
| **Complaint ID** | Unique identifier for each complaint record |
| **Complaint Type** | Categorical classification of complaint (Marks Mismatch, Absentee Error, Missing Grade, Calculation Discrepancy) |
| **Complaint Text** | Full text description of the complaint submitted by the student |
| **Complaint Status** | Current status of the complaint (Pending, In Progress, Resolved, Rejected) |
| **Complaint Resolution Time** | Number of days taken to resolve the complaint |
| **Student ID** | Unique identifier for the student who submitted the complaint |
| **Student Program** | Academic program or course of study of the student |
| **Student Year** | Academic year or semester level of the student |
| **Faculty ID** | Unique identifier for the faculty member handling the complaint |
| **Faculty Department** | Department name where the faculty member belongs |
| **Predicted Complaint Type** | ML model predicted category for the complaint |
| **Predicted Priority** | ML model predicted priority level for the complaint |
| **Duplicate Flag** | Boolean flag indicating if the complaint is a duplicate |
| **SLA Risk Score** | Numerical score indicating the risk of SLA breach |
| **Recommended Action** | Suggested action based on ML model analysis |
| **Anomaly Flag** | Boolean flag indicating if the complaint is an anomaly |
| **Explanation** | Text explanation for anomaly detection or model predictions |

### 2. **resolved_complaints.csv**

This dataset contains resolved complaint records with additional resolution details, used for training the SLA prediction model and duplicate detection system.

| Field Name | Description |
|------------|-------------|
| **Complaint ID** | Unique identifier for each resolved complaint record |
| **Complaint Type** | Categorical classification of the resolved complaint |
| **Complaint Text** | Original text description of the complaint |
| **Complaint Status** | Final status of the complaint (typically "Resolved") |
| **Complaint Resolution Time** | Actual number of days taken to resolve the complaint |
| **Student ID** | Unique identifier for the student who submitted the complaint |
| **Student Program** | Academic program of the student |
| **Student Year** | Academic year or semester level of the student |
| **Faculty ID** | Unique identifier for the faculty member who resolved the complaint |
| **Faculty Department** | Department name of the faculty member |
| **Predicted Complaint Type** | ML model predicted category for the complaint |
| **Predicted Priority** | ML model predicted priority level |
| **Duplicate Flag** | Boolean flag indicating duplicate status |
| **SLA Risk Score** | Numerical score indicating SLA breach risk |
| **Recommended Action** | Suggested action from ML model |
| **Anomaly Flag** | Boolean flag for anomaly detection |
| **Explanation** | Text explanation for model predictions |
| **Resolution Description** | Detailed description of how the complaint was resolved |
| **Faculty Response Time** | Time taken by faculty to respond to the complaint |
| **Student Satisfaction Score** | Satisfaction rating provided by the student after resolution |

### 3. **generated_results.csv**

This dataset is used for bulk uploading student academic results into the system.

| Field Name | Description |
|------------|-------------|
| **student_username** | Username or roll number of the student (must match login username) |
| **course_code** | Unique code identifying the course (e.g., CS101, MATH201) |
| **course_name** | Full name or title of the course |
| **semester** | Academic semester or term when the course was taken |
| **marks** | Marks or grade obtained by the student in the course |
| **status** | Result status indicating Pass, Fail, or Backlog |

### Dataset Usage

- **complaints.csv**: Used for training the complaint category classification model and understanding complaint patterns
- **resolved_complaints.csv**: Used for training the SLA prediction model (Cox Proportional Hazards), duplicate detection (SBERT embeddings), and providing historical resolution context
- **generated_results.csv**: Used for bulk importing student results into the database via the admin upload interface

All datasets are stored in the `secure_result/models/data/` directory and are loaded at application startup for ML model training and inference.

---

## Machine Learning Models

The system incorporates **four sophisticated machine learning models** to provide intelligent automation and insights:

### 1. Complaint Category Classification Model

#### **Purpose**
Automatically categorizes incoming complaints into one of four predefined categories:
- **Marks Mismatch**: Discrepancies between expected and recorded marks
- **Absentee Error**: Issues related to attendance records
- **Missing Grade**: Complaints about missing or unrecorded grades
- **Calculation Discrepancy**: Errors in grade calculations

#### **Technology Stack**
- **Algorithm**: Scikit-learn classifier (Logistic Regression)
- **Feature Extraction**: TF-IDF (Term Frequency-Inverse Document Frequency) vectorization
- **Text Preprocessing**: 
  - Lowercasing
  - URL and email removal
  - Special character removal
  - Stopword removal using NLTK
  - Whitespace normalization

#### **Model Architecture**
1. **Text Cleaning**: Input complaint text is cleaned and normalized
2. **Vectorization**: Cleaned text is converted to TF-IDF feature vectors
3. **Classification**: Pre-trained classifier predicts category and confidence score
4. **Keyword Extraction**: Top 5 keywords contributing to the prediction are identified

#### **Integration**
- Model is loaded at application startup
- Real-time prediction during complaint submission
- Confidence scores stored with each complaint
- Admin can manually override predictions if needed

### 2. Duplicate Complaint Detection Model

#### **Purpose**
Identifies complaints that are semantically similar to previously resolved cases, helping:
- Reduce duplicate work
- Suggest resolution approaches based on similar cases
- Flag potential duplicate submissions

#### **Technology Stack**
- **Algorithm**: Sentence-BERT (SBERT) for semantic embeddings
- **Similarity Metric**: Cosine similarity between complaint embeddings
- **Model**: Pre-trained sentence transformer model stored locally

#### **Model Architecture**
1. **Embedding Generation**: Complaint text is converted to dense vector embeddings using SBERT
2. **Similarity Search**: Cosine similarity computed against cached embeddings of resolved complaints
3. **Ranking**: Top-K similar complaints retrieved and ranked by similarity score
4. **Thresholding**: 
   - Similarity ≥ 0.8: High similarity (potential duplicate)
   - Similarity ≥ 0.6: Moderate similarity (related case)
   - Similarity < 0.6: Low similarity (unique case)

#### **Performance Optimization**
- **Embedding Cache**: Pre-computed embeddings stored in NumPy arrays
- **Cache Validation**: Cache metadata ensures consistency with dataset
- **Lazy Loading**: Embeddings computed only when needed

### 3. SLA (Service Level Agreement) Risk Prediction Model

#### **Purpose**
Predicts the risk of breaching the 7-day SLA for complaint resolution, enabling:
- Proactive resource allocation
- Priority-based complaint handling
- Risk-based workflow management

#### **Technology Stack**
- **Algorithm**: Cox Proportional Hazards Model (Survival Analysis)
- **Library**: Lifelines
- **Features**: 
  - Complaint type (categorical)
  - Faculty department (categorical)
  - One-hot encoded feature vectors

#### **Model Architecture**
1. **Feature Engineering**: Complaint metadata converted to feature vectors
2. **Survival Prediction**: Cox model predicts median resolution time
3. **Breach Probability**: Calculates probability of resolution exceeding 7 days
4. **Risk Classification**:
   - **High Risk**: Breach probability ≥ 60%
   - **Medium Risk**: Breach probability 30-60%
   - **Low Risk**: Breach probability < 30%

#### **Output Metrics**
- **Predicted Median Resolution Time**: Expected days to resolution
- **Breach Probability**: Probability of exceeding 7-day SLA
- **Risk Level**: Categorical classification (High/Medium/Low)

### 4. Anomaly Detection Model

#### **Purpose**
Identifies unusual patterns in complaint data that may indicate:
- Data quality issues
- Unusual complaint characteristics
- Outlier cases requiring special attention

#### **Technology Stack**
- **Algorithm**: Isolation Forest (from Scikit-learn)
- **Features**:
  - Resolution time
  - Student program (encoded)
  - Faculty department (encoded)

#### **Model Architecture**
1. **Feature Encoding**: Categorical features encoded using label encoders
2. **Anomaly Scoring**: Isolation Forest computes anomaly scores
3. **Classification**: Cases with score < threshold marked as anomalies
4. **Explanation**: Provides reasoning for anomaly detection

### Model Training and Deployment

#### **Training Process**
- Models trained on historical complaint data
- Cross-validation for performance evaluation
- Hyperparameter tuning for optimal performance
- Model serialization using Joblib

#### **Model Loading**
- Models loaded at application startup via `model_loader.py`
- Lazy loading for optional models (graceful degradation)
- Error handling for missing model files
- Status monitoring for model availability

#### **Model Updates**
- Models can be retrained with new data
- Version control for model files
- Backward compatibility maintained

---

## User Interface Design

### Design Philosophy

The UI follows a **clean, intuitive, and role-based design** approach:

1. **User-Centric**: Different interfaces for students and admins
2. **Responsive**: Adapts to different screen sizes
3. **Interactive**: Real-time updates and feedback
4. **Accessible**: Clear labels, helpful tooltips, and error messages

### Navigation System

#### **Role-Based Navigation**
- **Student Pages**:
  - Student Dashboard
  - Submit Complaint
  - My Results

- **Admin Pages**:
  - Admin Dashboard
  - View Complaints
  - Upload Results (CSV)
  - Model Insights

#### **Navigation Features**
- Sidebar navigation with icons
- Page titles and headers
- User info display in sidebar
- Logout functionality

### UI Components

#### **Forms**
- **Complaint Submission Form**:
  - Course code selection (auto-populated from student results)
  - Semester selection
  - Text area for complaint description
  - File upload for supporting evidence
  - Real-time ML prediction preview

- **Result Upload Form**:
  - CSV file uploader
  - Data preview table
  - Validation feedback
  - Import statistics

#### **Data Display**
- **Cards View**: Expandable cards for complaints and results
- **Table View**: Sortable, filterable data tables
- **Metrics**: Key performance indicators with visual badges
- **Charts**: Interactive Plotly visualizations

#### **Communication Interface**
- **Message Thread**: Chronological message display
- **Role-Based Styling**: Different colors for student/admin/system messages
- **File Attachments**: Download buttons for attached files
- **Real-Time Updates**: Messages appear immediately after sending

### Visual Feedback

#### **Status Indicators**
- **Complaint Status**: Color-coded badges (Pending/In Progress/Resolved/Rejected)
- **SLA Risk**: Color-coded risk levels (High/Medium/Low)
- **Result Status**: Visual indicators (Pass/Fail/Backlog)

#### **Notifications**
- Success messages with balloons animation
- Error messages with clear descriptions
- Warning messages for potential issues
- Info messages for guidance

### Responsive Design

- **Column Layouts**: Multi-column layouts adapt to content
- **Expandable Sections**: Collapsible sections for detailed views
- **Mobile-Friendly**: Streamlit's responsive components

---

## Backend Implementation

### Database Layer (`db.py`)

#### **Connection Management**
- **Function**: `get_conn()`
- **Purpose**: Creates and returns database connection
- **Features**: Row factory for dictionary-like access

#### **Initialization**
- **Function**: `init_db()`
- **Purpose**: Creates all tables with proper schema
- **Features**: 
  - Handles existing tables gracefully
  - Creates indexes for performance
  - Supports schema migrations

#### **User Management Functions**
- `create_user()`: Creates new user account with hashed password
- `verify_user()`: Validates login credentials
- `get_user_by_username()`: Retrieves user information

#### **Complaint Management Functions**
- `add_complaint()`: Stores new complaint with ML predictions
- `get_complaints_by_student()`: Retrieves student's complaints
- `get_all_complaints()`: Retrieves all complaints (admin)
- `update_complaint_status()`: Updates complaint status
- `update_complaint_category()`: Updates ML-predicted category
- `delete_complaint()`: Removes complaint and related data

#### **Result Management Functions**
- `add_result()`: Adds single result record
- `get_results_by_student()`: Retrieves student's results
- `import_results_from_dataframe()`: Bulk import from CSV
- `fix_student_username_commas()`: Data cleaning utility

#### **Communication Functions**
- `add_complaint_message()`: Stores message in thread
- `get_complaint_messages()`: Retrieves message history
- `add_resolution_update()`: Stores resolution details
- `get_resolution_updates()`: Retrieves resolution information

### Machine Learning Layer (`model_loader.py`)

#### **Model Loading**
- **Function**: `load_model()`
- **Purpose**: Loads all ML models at startup
- **Features**:
  - Error handling for missing models
  - Status tracking for each model
  - Graceful degradation

#### **Text Processing**
- **Function**: `clean_text()`
- **Purpose**: Preprocesses complaint text
- **Steps**:
  1. Lowercasing
  2. URL/email removal
  3. Special character removal
  4. Stopword removal
  5. Whitespace normalization

#### **Prediction Functions**
- `predict_category()`: Classifies complaint category
- `find_similar_complaint()`: Finds similar complaints
- `predict_sla()`: Predicts SLA breach risk
- `detect_anomaly()`: Identifies anomalous patterns

#### **Embedding Management**
- `_load_or_compute_embeddings()`: Manages cached embeddings
- Cache validation against dataset
- Automatic recomputation when needed

#### **Model Status**
- `model_status()`: Returns status of all models
- Useful for debugging and monitoring

### Application Layer (`app.py`)

#### **Session Management**
- **Function**: `require_login()`
- **Purpose**: Checks if user is authenticated
- **Session State**: Stores username and role

#### **Authentication**
- **Function**: `show_login_page()`
- **Features**:
  - Login form with validation
  - Sign-up form with password confirmation
  - Role selection (student/admin)
  - Password strength validation

#### **Navigation Setup**
- **Function**: `main()`
- **Purpose**: Sets up role-based page navigation
- **Features**:
  - Dynamic page list based on role
  - Sidebar navigation
  - Page routing

#### **Error Handling**
- Warning suppression for ML libraries
- Graceful error messages
- Database initialization error handling

### File Management

#### **Upload Directories**
- `uploads/complaints/`: Complaint supporting evidence
- `uploads/complaint_messages/`: Message attachments
- `uploads/resolution/`: Resolution documents

#### **File Naming**
- UUID-based filenames for uniqueness
- Timestamp prefixes for organization
- Safe filename generation

#### **File Validation**
- File type checking
- File size limits (10 MB)
- Secure file storage

---

## Page-by-Page Feature Documentation

### Student Pages

#### **1. Student Dashboard** (`1_Student_Dashboard.py`)

**Purpose**: Central hub for students to view their academic summary and complaint status.

**Key Features**:
1. **Summary Metrics**:
   - Total Results count
   - Passed Courses count
   - Failed Courses count
   - Pending Complaints count

2. **Recent Results Display**:
   - Shows 5 most recent results
   - Expandable cards with course details
   - Status indicators (Pass/Fail/Backlog)
   - Upload timestamp

3. **Recent Complaints Display**:
   - Shows 5 most recent complaints
   - Status indicators with emojis
   - Category display
   - Communication thread integration

4. **Communication Thread**:
   - Message history display
   - System recommendations for similar cases
   - File attachment support
   - Real-time message sending

5. **Resolution Details**:
   - Resolution notes when complaint is resolved
   - Resolution attachments download
   - Admin information

**User Interactions**:
- View detailed complaint information
- Send messages to admins
- Download attached files
- View resolution details

#### **2. Submit Complaint** (`2_Submit_Complaint.py`)

**Purpose**: Allows students to file new complaints with AI-powered assistance.

**Key Features**:
1. **Complaint Form**:
   - Course code selection (auto-populated from student's results)
   - Semester selection dropdown
   - Complaint text area
   - File upload for supporting evidence

2. **Real-Time ML Predictions**:
   - Category prediction preview
   - Confidence score display
   - Predicted resolution time
   - SLA breach probability
   - Top keywords identification

3. **Similar Complaint Detection**:
   - Shows similar resolved cases
   - Similarity score display
   - Previous resolution details
   - Duplicate warning for high similarity

4. **Previous Complaints View**:
   - List of all student's complaints
   - Status tracking
   - Communication thread access
   - Delete functionality

5. **File Management**:
   - Support for images (PNG, JPG, JPEG)
   - Support for documents (PDF, DOC, DOCX)
   - File size validation (10 MB limit)

**User Interactions**:
- Submit new complaints
- View ML predictions before submission
- Review similar cases
- Manage previous complaints
- Upload supporting evidence

#### **3. My Results** (`3_My_Results.py`)

**Purpose**: Comprehensive view of student's academic results.

**Key Features**:
1. **Summary Statistics**:
   - Total Courses count
   - Passed courses with pass rate
   - Failed courses count
   - Backlog count

2. **Filtering Options**:
   - Filter by status (All/Pass/Fail/Backlog)
   - Filter by semester
   - Search by course code or name

3. **Display Modes**:
   - **Cards View**: Expandable cards with course details
   - **Table View**: Sortable data table

4. **Result Details**:
   - Course code and name
   - Semester information
   - Marks obtained
   - Status with visual indicators
   - Upload timestamp

5. **Export Functionality**:
   - Download results as CSV
   - Includes all result fields

**User Interactions**:
- Filter and search results
- Switch between view modes
- Export results to CSV
- View detailed course information

### Admin Pages

#### **4. Admin Dashboard** (`4_Admin_Dashboard.py`)

**Purpose**: Overview dashboard for administrators with analytics and quick actions.

**Key Features**:
1. **Complaint Summary Metrics**:
   - Total Complaints count
   - Pending count
   - In Progress count
   - Resolved count

2. **SLA Risk Analytics**:
   - High Risk SLA Complaints count
   - Mean Predicted Resolution Time
   - Duplicate Complaints count
   - Risk distribution chart (High/Medium/Low)

3. **Visualizations**:
   - Complaint category distribution (pie chart)
   - Complaints over time (bar chart)
   - Duplicate complaints by status (pie chart)

4. **Results Summary**:
   - Passed/Failed/Backlog counts
   - Top courses by result count

5. **Quick Actions**:
   - Recent complaints list (latest 10)
   - Quick status updates
   - Navigation shortcuts

**User Interactions**:
- View complaint statistics
- Monitor SLA risks
- Quick status updates
- Navigate to other admin pages

#### **5. View Complaints** (`5_Admin_View_Complaints.py`)

**Purpose**: Comprehensive complaint management interface for admins.

**Key Features**:
1. **Advanced Filtering**:
   - Filter by status (All/Pending/Resolved/Rejected)
   - Filter by category
   - Filter by SLA risk level
   - Filter by course code
   - Filter by semester
   - Search by student or text
   - Sort options (Newest/Oldest/High Risk/Low Risk)

2. **Display Modes**:
   - **Cards View**: Expandable complaint cards
   - **Table View**: Compact table format

3. **Complaint Details**:
   - Full complaint text
   - Student information
   - Course and semester details
   - ML predictions (category, confidence)
   - Status and SLA risk badge

4. **Duplicate Detection Insights**:
   - Similar complaints display
   - Similarity scores
   - Previous resolution details
   - Recommendations

5. **SLA Prediction Panel**:
   - Risk level (High/Medium/Low)
   - Breach probability percentage
   - Expected resolution time
   - Feature analysis

6. **Communication Thread**:
   - Message history
   - Send messages to students
   - File attachment support
   - System recommendations

7. **Complaint Management**:
   - Update status (Pending/In Progress/Resolved/Rejected)
   - Update category (manual override)
   - Delete complaints
   - Resolution notes (required for resolved complaints)
   - Resolution file uploads

8. **Export Functionality**:
   - Export all complaints as CSV

**User Interactions**:
- Filter and search complaints
- View detailed complaint information
- Update complaint status and category
- Communicate with students
- Add resolution notes
- Export complaint data

#### **6. Upload Results (CSV)** (`6_Admin_Upload_Results.py`)

**Purpose**: Bulk upload student results via CSV files.

**Key Features**:
1. **CSV Upload**:
   - File uploader with CSV validation
   - Data preview table
   - Column validation (required vs optional)

2. **Data Validation**:
   - Required columns: `student_username`, `course_code`
   - Optional columns: `course_name`, `semester`, `marks`, `status`
   - Data type validation
   - Username format cleaning (removes commas)

3. **Data Statistics**:
   - Total records count
   - Unique students count
   - Unique courses count
   - Status distribution

4. **Import Process**:
   - Bulk import to database
   - Error reporting for failed rows
   - Success/error summary
   - User account validation

5. **Manual Entry**:
   - Alternative form for single result entry
   - All fields available
   - Immediate database insertion

6. **Upload Summary**:
   - Total results in database
   - Total students count
   - Total courses count
   - Top courses by result count

**User Interactions**:
- Upload CSV files
- Preview data before import
- Validate data format
- Import results to database
- Manual result entry

#### **7. Model Insights** (`7_Admin_Model_Insights.py`)

**Purpose**: Provides insights into ML model performance and feature importance.

**Key Features**:
1. **SLA Model Feature Importance**:
   - Top 10 most important features
   - Feature importance bar chart
   - Cox coefficients display

2. **Dataset Information**:
   - `complaints.csv` statistics (rows, columns)
   - `resolved_complaints.csv` statistics
   - Column names display

3. **Model Status**:
   - Model loading status
   - Available models list
   - Dataset loading status

4. **Export Functionality**:
   - Export all predictions as CSV
   - Includes complaint ID, student, text, category, confidence, status

**User Interactions**:
- View model feature importance
- Check dataset statistics
- Export prediction data
- Monitor model status

---

## Integration and Testing

### System Integration

#### **Component Integration**
1. **Frontend-Backend Integration**:
   - Streamlit pages call database functions
   - Real-time data updates
   - Session state management

2. **ML Model Integration**:
   - Models loaded at startup
   - Predictions made on-demand
   - Caching for performance

3. **Database Integration**:
   - Connection pooling
   - Transaction management
   - Error handling

#### **Data Flow Integration**
1. **Complaint Submission Flow**:
   - User submits complaint → Text preprocessing → ML prediction → Database storage → UI update

2. **Result Upload Flow**:
   - CSV upload → Validation → Data cleaning → Database insertion → Confirmation

3. **Communication Flow**:
   - Message sent → File upload → Database storage → UI refresh → Display

### Testing Approach

#### **Functional Testing**
1. **Authentication Testing**:
   - Login with valid credentials
   - Login with invalid credentials
   - Sign-up with duplicate username
   - Password validation

2. **Complaint Management Testing**:
   - Submit complaint with valid data
   - Submit complaint with missing fields
   - File upload validation
   - ML prediction accuracy

3. **Result Management Testing**:
   - CSV upload with valid format
   - CSV upload with invalid format
   - Manual result entry
   - Data retrieval

4. **Communication Testing**:
   - Send messages
   - File attachments
   - Message thread display

#### **Performance Testing**
1. **Model Loading**:
   - Startup time
   - Memory usage
   - Model availability

2. **Database Queries**:
   - Query performance
   - Index effectiveness
   - Large dataset handling

3. **File Operations**:
   - Upload speed
   - File size limits
   - Concurrent uploads

#### **Security Testing**
1. **Authentication Security**:
   - Password hashing verification
   - Session management
   - Role-based access control

2. **Input Validation**:
   - SQL injection prevention
   - File upload security
   - XSS prevention

3. **Data Privacy**:
   - Student data isolation
   - Admin access controls

### Error Handling

#### **Graceful Degradation**
- ML models: System works even if models fail to load
- Database: Clear error messages for connection issues
- File uploads: Validation before processing

#### **User Feedback**
- Success messages with clear actions
- Error messages with solutions
- Warning messages for potential issues
- Info messages for guidance

### Deployment Considerations

#### **Environment Setup**
- Python virtual environment
- Required packages installation
- Model files placement
- Database initialization

#### **Configuration**
- Database path configuration
- Model directory paths
- Upload directory paths
- Cache directory management

---

## Conclusion

### Project Achievements

The Secure Result Management System successfully integrates:

1. **Modern Web Technologies**: Streamlit for rapid UI development
2. **Machine Learning**: Four sophisticated ML models for intelligent automation
3. **Robust Database Design**: Well-structured schema with proper relationships
4. **User-Centric Design**: Role-based interfaces for students and admins
5. **Comprehensive Features**: Complaint management, result tracking, and analytics

### Key Strengths

1. **Intelligent Automation**: ML models reduce manual work and improve accuracy
2. **User Experience**: Intuitive interface with real-time feedback
3. **Scalability**: Efficient database design supports growth
4. **Maintainability**: Clean code structure and modular design
5. **Security**: Secure authentication and data isolation

### Future Enhancements

1. **Advanced Analytics**: More detailed reporting and insights
2. **Email Notifications**: Automated notifications for status updates
3. **Mobile App**: Native mobile application
4. **API Development**: RESTful API for external integrations
5. **Multi-language Support**: Internationalization capabilities

### Technical Highlights

- **ML Integration**: Seamless integration of multiple ML models
- **Real-time Predictions**: Instant feedback during complaint submission
- **Semantic Search**: Advanced duplicate detection using SBERT
- **Survival Analysis**: Innovative use of Cox model for SLA prediction
- **Performance Optimization**: Caching and indexing for speed

---

## Appendix

### Diagrams

#### 1. Overall Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (Frontend)                 │
│                         Streamlit UI                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Student    │  │    Admin     │  │   Login/      │        │
│  │   Pages      │  │    Pages     │  │   Signup      │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                  │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                             │
┌───────────────────────────┼─────────────────────────────────────┐
│                    APPLICATION LAYER (Backend)                   │
│                           │                                     │
│  ┌────────────────────────┼────────────────────────┐            │
│  │  ┌──────────────┐     │     ┌──────────────┐   │            │
│  │  │   Database   │     │     │  ML Models   │   │            │
│  │  │   Functions  │◄────┼────►│   Loader     │   │            │
│  │  │  (db.py)     │     │     │(model_loader)│   │            │
│  │  └──────────────┘     │     └──────────────┘   │            │
│  │                       │                          │            │
│  │  ┌──────────────┐     │     ┌──────────────┐   │            │
│  │  │  Session     │     │     │  File        │   │            │
│  │  │  Management  │     │     │  Management  │   │            │
│  │  └──────────────┘     │     └──────────────┘   │            │
│  └────────────────────────┼─────────────────────────┘            │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                             │
┌───────────────────────────┼─────────────────────────────────────┐
│                      DATA LAYER                                   │
│                           │                                     │
│  ┌────────────────────────┼────────────────────────┐            │
│  │  ┌──────────────┐      │     ┌──────────────┐   │            │
│  │  │   SQLite     │      │     │  File        │   │            │
│  │  │   Database   │      │     │  System      │   │            │
│  │  │ (db.sqlite3) │      │     │  (uploads/)  │   │            │
│  │  └──────────────┘      │     └──────────────┘   │            │
│  │                        │                          │            │
│  │  ┌──────────────┐      │     ┌──────────────┐   │            │
│  │  │  ML Model    │      │     │  Cache       │   │            │
│  │  │  Files       │      │     │  Directory   │   │            │
│  │  │  (.pkl)      │      │     │  (embeddings)│   │            │
│  │  └──────────────┘      │     └──────────────┘   │            │
│  └────────────────────────┼─────────────────────────┘            │
└───────────────────────────┴─────────────────────────────────────┘

Data Flow:
User Input → Streamlit UI → Backend Functions → Database/ML Models → Response → UI Update
```

#### 2. Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATABASE SCHEMA                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│       users         │
├─────────────────────┤
│ PK user_id          │
│    username (UNIQUE)│
│    password_hash    │
│    role             │
│    created_at       │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ├──────────────────┬──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│   complaints     │ │   results     │ │complaint_messages│
├──────────────────┤ ├──────────────┤ ├──────────────────┤
│ PK complaint_id  │ │ PK result_id  │ │ PK message_id    │
│ FK student_       │ │ FK student_   │ │ FK complaint_id  │
│    username      │ │    username   │ │ FK sender_       │
│    text          │ │    course_    │ │    username      │
│    predicted_    │ │    code      │ │    sender_role   │
│    category      │ │    course_    │ │    message_text │
│    confidence    │ │    name       │ │    file_paths    │
│    status        │ │    semester   │ │    created_at    │
│    file_path     │ │    marks      │ └──────────────────┘
│    course_code   │ │    status     │
│    semester      │ │    uploaded_  │
│    duplicate_    │ │    at         │
│    reference     │ │              │
│    created_at    │ └──────────────┘
└────────┬─────────┘
         │
         │ 1:N
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌──────────────────┐    ┌──────────────────┐
│resolution_updates│    │complaint_messages│
├──────────────────┤    │  (already shown) │
│ PK update_id     │    └──────────────────┘
│ FK complaint_id  │
│ FK admin_        │
│    username      │
│    note_text     │
│    file_paths    │
│    created_at    │
└──────────────────┘

INDEXES:
- idx_results_student ON results(student_username)
- idx_complaints_student ON complaints(student_username)
- idx_resolution_complaint ON resolution_updates(complaint_id)
- idx_messages_complaint ON complaint_messages(complaint_id)
```

#### 3. ML Model Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              MACHINE LEARNING MODEL PIPELINE                    │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  Complaint Text │
                    │   (User Input)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Text Cleaning   │
                    │  (NLTK, Regex)  │
                    │  - Lowercase     │
                    │  - Remove URLs  │
                    │  - Stopwords    │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────┐      ┌───────────────────┐
    │  Category         │      │  Duplicate        │
    │  Classification   │      │  Detection        │
    │                   │      │                   │
    │  TF-IDF           │      │  SBERT            │
    │  Vectorization    │      │  Embedding        │
    │                   │      │                   │
    │  Scikit-learn     │      │  Cosine           │
    │  Classifier       │      │  Similarity        │
    └─────────┬─────────┘      └─────────┬─────────┘
              │                          │
              ▼                          ▼
    ┌───────────────────┐      ┌───────────────────┐
    │  Category +       │      │  Similar          │
    │  Confidence       │      │  Complaints       │
    │                   │      │  + Scores         │
    └─────────┬─────────┘      └─────────┬─────────┘
              │                          │
              └──────────┬───────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  SLA Risk Prediction   │
            │                        │
            │  Cox Proportional      │
            │  Hazards Model         │
            │  (Lifelines)           │
            │                        │
            │  Features:             │
            │  - Complaint Type      │
            │  - Faculty Department  │
            └───────────┬───────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  Anomaly Detection    │
            │                        │
            │  Isolation Forest      │
            │  (Scikit-learn)        │
            │                        │
            │  Features:             │
            │  - Resolution Time     │
            │  - Program/Dept        │
            └───────────┬───────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  Final Predictions     │
            │                        │
            │  - Category            │
            │  - Similar Cases      │
            │  - SLA Risk           │
            │  - Anomaly Flag       │
            └───────────┬───────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  Database Storage      │
            │  + UI Display          │
            └────────────────────────┘
```

#### 4. User Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER WORKFLOWS                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    STUDENT WORKFLOW                              │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Login/     │
    │   Signup     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   Student    │
    │   Dashboard  │
    └──────┬───────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────────┐
│  View    │  │   Submit     │
│  Results │  │   Complaint  │
└─────────┘  └──────┬───────┘
                    │
                    ▼
            ┌──────────────┐
            │  ML Predictions│
            │  - Category    │
            │  - Similar Cases│
            │  - SLA Risk    │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │  Complaint   │
            │  Submitted   │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │  Communication│
            │  Thread      │
            │  (Messages)  │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │  Resolution  │
            │  (if resolved)│
            └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN WORKFLOW                                │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Login      │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   Admin      │
    │   Dashboard  │
    └──────┬───────┘
           │
    ┌──────┼──────┬──────────────┐
    │      │      │              │
    ▼      ▼      ▼              ▼
┌──────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│ View │ │Upload│ │  Model   │ │  Other   │
│Compl.│ │Results│ │ Insights │ │  Tasks   │
└──┬───┘ └──┬───┘ └──────────┘ └──────────┘
   │        │
   │        ▼
   │   ┌──────────┐
   │   │ CSV      │
   │   │ Upload   │
   │   └────┬─────┘
   │        │
   │        ▼
   │   ┌──────────┐
   │   │ Validate │
   │   │ & Import │
   │   └──────────┘
   │
   ▼
┌──────────────┐
│  Filter &    │
│  Search      │
│  Complaints  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  View ML     │
│  Predictions │
│  - Category  │
│  - SLA Risk  │
│  - Duplicates│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Update      │
│  Status/     │
│  Category    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Communicate │
│  with Student│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Add         │
│  Resolution  │
│  Notes       │
└──────────────┘
```

### Installation Instructions

1. Install Python 3.x
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment
4. Install requirements: `pip install -r requirements.txt`
5. Initialize database: Run application (auto-initialization)
6. Place ML models in `secure_result/models/` directory
7. Run application: `streamlit run secure_result/app.py`

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum
- 500MB disk space for models
- Modern web browser

---

**Report Generated**: 2024
**Project**: Secure Result Management System
**Version**: 1.0


