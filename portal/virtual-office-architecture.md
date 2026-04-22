# Virtual Office Platform Architecture

## Main Components
- **App**: Handles authentication, login/signup, and routes to the main layout after login.
- **MainLayout**: Provides sidebar navigation and renders the selected department/module page.
- **Sidebar**: Navigation for all modules (Dashboard, Admin, HR, Payroll, PR, Virtual Office).
- **Dashboard**: Personalized landing page for each user.
- **AdminUserManagement**: Admin tools for user/role management and onboarding.
- **HRManagement**: Employee directory, onboarding, leave, reviews.
- **PayrollFinance**: Payslips, tax, expenses, finance dashboard.
- **PRCommunications**: News, announcements, chat, calendar/events.
- **VirtualOffice**: Real-time presence, collaboration, groups.

## Routing
- Managed by `page` state in `MainLayout`.
- Add new modules by creating a new component and adding a button in `Sidebar`.

## Extensibility
- Future modules (Recruitment, Asset Tracking, etc.) can be added as new components and sidebar entries.

## Styling
- All components use existing Tailwind CSS and custom styles for visual consistency.

## Data
- Firebase is used for authentication and data storage.
- Extend Firestore structure for new modules as needed.
