# Sans Mercantile Virtual Office Platform

This platform transforms the original Admin Portal into a full-fledged virtual office for remote work, with dedicated modules for:

- **Admin User Management**: Create users, assign roles, approve onboarding
- **HR Management**: Onboarding, directory, profiles, leave, reviews
- **Payroll & Finance**: Payslips, tax, expenses, finance dashboard
- **PR & Communications**: News feed, announcements, chat, calendar/events
- **Virtual Office**: Real-time presence, collaboration spaces, groups

## Navigation
- Use the sidebar to access each department/module.
- All new features use the existing design and CSS for visual continuity.

## Extensibility
- Add new modules (e.g., Recruitment, Asset Tracking) by creating new components and adding them to the sidebar and routing logic in `index.html`.

## Development Notes
- All logic and UI are in `portal/index.html` as React components (Babel in-browser JSX).
- Firebase is used for authentication and data storage.
- Tailwind CSS and custom styles are used for a modern, consistent look.
