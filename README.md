# E-Voting System

A secure and transparent online voting system built with Django and React. This system allows organizations to conduct elections efficiently while ensuring the integrity and security of the voting process.

## Features

- **User Authentication**: Secure registration and login system with email verification
- **Election Management**: Create, edit, and manage elections with different statuses (draft, published, active, completed, cancelled)
- **Role-Based Access Control**: Different user roles including voters, election managers, and administrators
- **Voting Interface**: Intuitive interface for casting votes
- **Real-time Results**: View election results in real-time with visualizations
- **Audit Trail**: Comprehensive logging of all election activities
- **Responsive Design**: Works on desktop and mobile devices

## User Roles and Permissions

### 1. Super Admin
- Full access to all system features
- Can manage all elections and users
- Can assign election managers

### 2. Election Manager
- Can create and manage elections
- Can add/remove candidates
- Can verify voter eligibility
- Can view and export election results

### 3. Voter
- Can view active elections
- Can cast votes in active elections
- Can view election results after voting

### 4. Candidate
- Can be nominated for positions
- Can view their own candidacy details
- Can view election results after voting ends

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL 12+ (or SQLite for development)
- Redis (for background tasks)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/vincent8494/evotesystem.git
   cd evotesystem
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

7. **Start the development servers**
   In one terminal (backend):
   ```bash
   python manage.py runserver
   ```
   
   In another terminal (frontend):
   ```bash
   cd frontend
   npm start
   ```

8. **Access the application**
   - Frontend: http://localhost:3000
   - Admin: http://localhost:8000/admin

## Project Structure

```
.
├── accounts/                 # User authentication and profile management
├── api/                      # REST API endpoints
├── config/                   # Django project settings
├── frontend/                 # React frontend application
├── voting/                   # Core voting application
│   ├── management/           # Custom management commands
│   ├── migrations/           # Database migrations
│   ├── templates/            # Django templates
│   ├── templatetags/         # Custom template tags
│   ├── views/                # View classes
│   ├── admin.py              # Admin configuration
│   ├── apps.py               # App configuration
│   ├── forms.py              # Form definitions
│   ├── models.py             # Database models
│   ├── urls.py               # URL routing
│   └── views.py              # View functions
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── manage.py                 # Django management script
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## Security Considerations

- All passwords are hashed using PBKDF2 with SHA-256
- CSRF protection enabled
- XSS protection headers
- Rate limiting on authentication endpoints
- Secure session management
- Audit logging for sensitive operations

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please contact the project maintainers:
- [Vincent](mailto:vincent@example.com)

## Acknowledgments

- Django Team for the amazing web framework
- React Team for the frontend library
- All contributors who have helped improve this project
