# Hamari Awaz - University Complaint Management System

A comprehensive, production-ready web application for managing university complaints and feedback with role-based access control, real-time notifications, and analytics.

## 🚀 Features

### Core Functionality
- **Role-Based Access Control**: Student, Staff, Department Head, Vice Chancellor, and Admin roles
- **Complaint Management**: Submit, track, assign, escalate, and resolve complaints
- **Feedback System**: Collect and respond to student feedback with voting capabilities
- **Real-time Notifications**: Email and in-app notifications for all stakeholders
- **Analytics & Reporting**: Comprehensive dashboards with charts and export functionality
- **File Management**: Secure file uploads and downloads for complaints
- **Audit Trail**: Complete history tracking for all actions

### User Roles & Permissions

#### 🎓 Student
- Self-registration and login
- Submit complaints and feedback
- Track complaint status and history
- Receive notifications and responses
- View personal analytics

#### 👨‍💼 Staff
- View assigned complaints
- Add comments and request additional information
- Update complaint status and progress
- Forward complaints to higher authorities

#### 🏢 Department Head
- View all department complaints
- Assign complaints to staff members
- Escalate complaints to Vice Chancellor
- Access department-level analytics

#### 🎯 Vice Chancellor
- University-wide complaint visibility
- Final authority for complaint resolution
- Access to system-wide analytics
- Bulk notification capabilities

#### ⚙️ Admin
- Complete system control
- User and role management
- System configuration and settings
- Advanced analytics and reporting

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 5.0.7
- **API**: Django REST Framework 3.15.2
- **Database**: MySQL
- **Authentication**: JWT (Simple JWT)
- **File Storage**: Django file handling
- **Email**: Django email backend

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: Chakra UI
- **State Management**: Zustand
- **Forms**: React Hook Form + Yup validation
- **HTTP Client**: Axios
- **Charts**: Chart.js with react-chartjs-2
- **Icons**: React Icons

### Development Tools
- **Package Manager**: npm/pip
- **Code Quality**: ESLint, Prettier
- **Version Control**: Git

## 📁 Project Structure

```
hamariawaz/
├── backend/                    # Django backend
│   ├── hamariawaz/            # Main project settings
│   ├── accounts/              # User management & authentication
│   ├── complaints/            # Complaint management
│   ├── feedback/              # Feedback system
│   ├── notifications/         # Notification system
│   ├── analytics/             # Analytics & reporting
│   ├── static/                # Static files
│   ├── media/                 # User uploads
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/              # App router pages
│   │   ├── components/       # Reusable components
│   │   ├── store/            # Zustand stores
│   │   ├── services/         # API services
│   │   ├── lib/              # Utilities
│   │   └── providers/        # Context providers
│   ├── public/               # Static assets
│   └── package.json          # Node dependencies
├── docker-compose.yml        # Development environment
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hamariawaz/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Update backend/hamariawaz/settings.py with your MySQL credentials
   # Default configuration:
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'hamariawaz',
           'USER': 'root',
           'PASSWORD': 'password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   # Create .env.local file
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

### Using Docker (Alternative)

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

## 📱 Application URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **Admin Panel**: http://localhost:8000/admin

## 🔐 Default Credentials

After running the setup, you can create test users:

### Admin User
- Email: admin@hamariawaz.com
- Password: (set during superuser creation)

### Test Student
- Register through the frontend at `/register`

## 📊 API Documentation

### Authentication Endpoints
- `POST /api/v1/accounts/auth/login/` - User login
- `POST /api/v1/accounts/auth/register/` - Student registration
- `POST /api/v1/accounts/auth/refresh/` - Refresh access token
- `POST /api/v1/accounts/auth/logout/` - User logout

### Complaint Endpoints
- `GET /api/v1/complaints/` - List complaints
- `POST /api/v1/complaints/` - Create complaint
- `GET /api/v1/complaints/{id}/` - Get complaint details
- `PATCH /api/v1/complaints/{id}/` - Update complaint
- `POST /api/v1/complaints/{id}/comments/` - Add comment

### User Management (Admin only)
- `GET /api/v1/accounts/users/` - List users
- `POST /api/v1/accounts/users/` - Create user
- `GET /api/v1/accounts/users/{id}/` - Get user details
- `PATCH /api/v1/accounts/users/{id}/` - Update user

## 🎨 UI Components

The application uses Chakra UI with a custom theme:

### Color Scheme
- **Primary**: Blue (#2196f3)
- **Secondary**: Green (#4caf50)
- **Accent**: Pink (#e91e63)

### Key Components
- **Dashboard Cards**: Statistics and quick actions
- **Data Tables**: Sortable and filterable lists
- **Forms**: Validated forms with error handling
- **Modals**: For confirmations and detailed views
- **Charts**: Interactive analytics visualizations

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:password@localhost:3306/hamariawaz
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Hamari Awaz
```

## 📈 Analytics Features

### Student Analytics
- Personal complaint statistics
- Response time tracking
- Satisfaction ratings

### Authority Analytics
- Department-wise complaint distribution
- Resolution time trends
- Workload distribution
- Performance metrics

### System Analytics
- User activity monitoring
- System performance metrics
- Export capabilities (CSV, PDF)

## 🔔 Notification System

### Notification Types
- **Email**: For important updates
- **In-app**: Real-time notifications
- **SMS**: For urgent matters (configurable)

### Notification Triggers
- New complaint submitted
- Complaint status updated
- Comment added
- Complaint assigned
- Complaint escalated
- Feedback received

## 🚀 Deployment

### Production Checklist

#### Backend
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up email backend
- [ ] Configure static file serving
- [ ] Set up SSL certificates
- [ ] Configure CORS settings

#### Frontend
- [ ] Build production bundle: `npm run build`
- [ ] Configure environment variables
- [ ] Set up CDN for static assets
- [ ] Configure domain and SSL

### Recommended Deployment Stack
- **Backend**: Django + Gunicorn + Nginx
- **Frontend**: Next.js + Vercel/Netlify
- **Database**: MySQL/PostgreSQL
- **File Storage**: AWS S3/CloudFlare R2
- **Email**: SendGrid/AWS SES

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Email: support@hamariawaz.com
- Documentation: [Wiki](https://github.com/your-repo/hamariawaz/wiki)

## 🎯 Roadmap

### Phase 1 (Current)
- [x] Basic complaint management
- [x] User authentication and roles
- [x] Basic dashboard and analytics
- [x] Email notifications

### Phase 2 (Upcoming)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics with ML insights
- [ ] Integration with university systems
- [ ] Multi-language support
- [ ] Advanced reporting features

### Phase 3 (Future)
- [ ] AI-powered complaint categorization
- [ ] Chatbot for common queries
- [ ] Integration with social media
- [ ] Advanced workflow automation

---

**Built with ❤️ for better university communication**

