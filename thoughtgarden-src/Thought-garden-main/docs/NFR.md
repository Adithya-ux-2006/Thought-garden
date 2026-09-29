# Non-Functional Requirements (NFR)

## 1. Performance

**User Story:** As a user, I want the application to respond quickly so I can work efficiently.

**Acceptance Criteria:**
- Page load time < 2 seconds for standard pages
- Note creation with AI analysis < 5 seconds
- Search results returned < 3 seconds
- Knowledge graph loads < 3 seconds for up to 100 notes
- Database queries < 500ms for standard operations

---

## 2. Availability

**User Story:** As a user, I want the application to be available when I need it.

**Acceptance Criteria:**
- Application runs locally without external dependencies
- No downtime during normal usage
- Graceful handling of AI model unavailability
- Data persisted across application restarts

---

## 3. Security

**User Story:** As a user, I want my data to be secure and private.

**Acceptance Criteria:**
- Passwords hashed using Werkzeug (SHA-256)
- Session-based authentication with secure cookies
- CSRF protection on all forms
- User can only access their own notes
- File uploads validated (type, size, content)
- No sensitive data exposed in error messages
- SQL injection prevention via ORM

---

## 4. Reliability

**User Story:** As a user, I want my data to be reliably stored and not lost.

**Acceptance Criteria:**
- Notes saved even if AI processing fails
- Database transactions atomic
- Relationships preserved across sessions
- No data corruption during normal operations
- Backup possible via SQLite file copy

---

## 5. Scalability

**User Story:** As a user, I want the application to handle growing knowledge.

**Acceptance Criteria:**
- Support up to 1,000 notes per user
- Support up to 500 relationships
- Pagination for large lists
- Embeddings cached for performance
- Architecture supports future PostgreSQL migration

---

## 6. Usability

**User Story:** As a user, I want the application to be easy to use.

**Acceptance Criteria:**
- Intuitive navigation
- Clear visual hierarchy
- Responsive design (desktop, tablet, mobile)
- Empty states guide user actions
- Error messages helpful and actionable
- Loading states during AI processing
- Dark mode support

---

## 7. Accessibility

**User Story:** As a user with disabilities, I want to use the application.

**Acceptance Criteria:**
- Semantic HTML structure
- Form labels associated with inputs
- Keyboard navigation support
- Visible focus states
- Sufficient color contrast (WCAG AA)
- Alt text for meaningful images
- ARIA attributes where necessary

---

## 8. Maintainability

**User Story:** As a developer, I want the code to be maintainable.

**Acceptance Criteria:**
- Clean separation of concerns
- Service layer for business logic
- Consistent code style
- Descriptive function/variable names
- Modular architecture
- Minimal dependencies

---

## 9. Data Integrity

**User Story:** As a user, I want my data to be accurate and consistent.

**Acceptance Criteria:**
- Referential integrity enforced via foreign keys
- Unique constraints on email and relationships
- No duplicate relationships
- No self-referential relationships
- Timestamps accurate and consistent

---

## 10. Recoverability

**User Story:** As a user, I want to recover from errors.

**Acceptance Criteria:**
- AI failure doesn't prevent note saving
- Form validation prevents bad data
- Database rollback on errors
- Error logging for debugging
- Graceful degradation when services fail