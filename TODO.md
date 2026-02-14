# TODO: Comprehensive Role-Based Access Control (RBAC) Implementation

## Phase 1: Database Schema & Authentication (COMPLETED)
- [x] Create users table with password hashing
- [x] Create user_sessions table for session management
- [x] Create audit_logs table for activity tracking
- [x] Create system_settings table for configuration
- [x] Create prediction_history table for quota tracking
- [x] Implement password hashing with SHA-256
- [x] Create initial admin user in database
- [x] Update LoginDialog with enhanced authentication
- [x] Implement prediction quota checking for Standard Users
- [x] Implement audit logging for login/logout/predictions/reports
- [x] Implement session management
- [x] Save prediction history to database
- [x] Save generated reports to database

## Phase 2: User Management (Admin Only)
- [ ] Create UserManagementDialog class
- [ ] Implement add user functionality
- [ ] Implement edit user functionality
- [ ] Implement delete user functionality
- [ ] Implement user search/filter
- [ ] Add user activation/deactivation

## Phase 3: Profile Management (All Users)
- [ ] Create ProfileDialog class
- [ ] Implement change password functionality
- [ ] Implement update profile information
- [ ] Display user's prediction history
- [ ] Add password strength validation

## Phase 4: Dataset Upload Feature
- [ ] Create DatasetUploadDialog class
- [ ] Implement CSV file selection
- [ ] Add data validation and preview
- [ ] Implement role-based upload permissions
- [ ] Add upload to database functionality

## Phase 5: Prediction Quota System (COMPLETED)
- [x] Implement prediction tracking per user
- [x] Add quota limits for Standard Users (10/day)
- [x] Display remaining predictions
- [x] Prevent predictions when quota exceeded
- [x] Reset quotas daily

## Phase 6: Report Access Control (PARTIALLY COMPLETED)
- [x] Save generated reports to database
- [ ] Create ReportsViewerDialog for all reports (Admin/Analyst)
- [ ] Implement view own reports (All users)
- [x] Add user attribution to reports
- [ ] Filter reports by user/date

## Phase 7: Audit Logging System (PARTIALLY COMPLETED)
- [ ] Create AuditLogViewer class
- [x] Log user login/logout events
- [x] Log prediction activities
- [x] Log report generation
- [ ] Log user management actions
- [ ] Log dataset uploads
- [ ] Add filtering by date/user/action

## Phase 8: System Settings (Admin Only)
- [ ] Create SystemSettingsDialog class
- [ ] Configure prediction quotas
- [ ] Set session timeout
- [ ] Configure data retention
- [ ] Email notification settings

## Phase 9: UI Enhancements
- [ ] Add menu bar with role-based items
- [ ] Add status bar (user, role, session time)
- [ ] Add prediction quota indicator
- [ ] Update main window layout
- [ ] Add logout functionality

## Phase 10: Testing & Documentation
- [ ] Test all user roles
- [ ] Test user management
- [ ] Test prediction quotas
- [ ] Test report access controls
- [ ] Test audit logging
- [ ] Security testing
- [ ] Create user documentation

## Completed Tasks (Previous Features)
- [x] Analyze track.py file and understand structure
- [x] Confirm user requirements: Add anticipated date/times to predictions
- [x] Update run_prediction method to include anticipated times
- [x] Update plot_predicted_crimes method to display anticipated times
- [x] Add "Generate Anticipated Crimes Report" button
- [x] Implement generate_anticipated_report method
- [x] Test the application to ensure changes work correctly
- [x] Verify PDF generation and map updates
- [x] Implement basic login dialog with user roles
- [x] Add basic role-based access control for Guest role
- [x] Fix main execution to pass role to ZRPPredictionApp
