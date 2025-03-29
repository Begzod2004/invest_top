# Top Invest Backend

This is the backend for the Top Invest application, configured for deployment on Timeweb Cloud with SQLite database.

## Version Compatibility

Important version requirements:

- Django 4.2.10 (not 5.x)
- django-jazzmin 2.4.0

Using Django 5.x with the current version of django-jazzmin causes template errors with the `length_is` filter.

## For Frontend Developers

### Authentication API

1. **Login and get token**

   ```http
   POST /api/users/auth/token/
   Content-Type: application/json

   {
     "username": "user",
     "password": "password123"
   }
   ```

   Response:
   ```json
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "user": {
       "id": "1",
       "username": "user",
       "first_name": "User",
       "is_admin": false,
       "permissions": ["can_view_signals", "can_view_reviews"]
     }
   }
   ```

2. **Refresh token**

   ```http
   POST /api/users/auth/token/refresh/
   Content-Type: application/json
   
   {
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
   }
   ```

   Response:
   ```json
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
   }
   ```

3. **Using the token for API requests**

   ```http
   GET /api/users/1/
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

### Permissions and Sidebar API

We've created a special endpoint for fetching user permissions and generating a sidebar menu structure based on those permissions:

```http
GET /api/users/auth/permissions/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

Response:
```json
{
  "permissions": [
    "can_view_signals",
    "can_view_users",
    "can_view_payments"
  ],
  "is_admin": false,
  "menu_items": [
    {
      "id": "dashboard",
      "title": "Dashboard",
      "icon": "dashboard",
      "path": "/dashboard",
      "permissions": []
    },
    {
      "id": "signals",
      "title": "Signallar",
      "icon": "chart-line",
      "path": "/signals",
      "permissions": ["can_view_signals"],
      "children": [
        {
          "id": "create-signal",
          "title": "Yangi signal",
          "path": "/signals/create",
          "permissions": ["can_create_signals"]
        }
      ]
    }
  ],
  "user": {
    "id": 1,
    "username": "user123",
    "full_name": "Firstname Lastname"
  }
}
```

### Implementing Permissions in Frontend

1. **Create AuthContext**

   When building your frontend application, implement an AuthContext provider that fetches and stores user permissions:

   ```javascript
   const AuthContext = createContext();

   export const AuthProvider = ({ children }) => {
     const [user, setUser] = useState(null);
     const [permissions, setPermissions] = useState([]);
     const [menuItems, setMenuItems] = useState([]);
     const [loading, setLoading] = useState(true);
     const [isAdmin, setIsAdmin] = useState(false);

     // Fetch permissions when token is available
     useEffect(() => {
       const fetchPermissions = async () => {
         try {
           const { data } = await api.get('/api/users/auth/permissions/');
           setPermissions(data.permissions);
           setMenuItems(data.menu_items);
           setIsAdmin(data.is_admin);
           setUser(data.user);
         } catch (error) {
           console.error('Error fetching permissions', error);
         } finally {
           setLoading(false);
         }
       };

       fetchPermissions();
     }, []);

     // Check if user has a permission
     const hasPermission = (permission) => {
       if (isAdmin) return true;
       return permissions.includes(permission);
     };

     return (
       <AuthContext.Provider value={{ 
         user, permissions, menuItems, isAdmin, loading, hasPermission 
       }}>
         {children}
       </AuthContext.Provider>
     );
   };
   ```

2. **Conditional Rendering Based on Permissions**

   ```jsx
   // For buttons
   {hasPermission('can_create_signals') && (
     <button onClick={createNewSignal}>Create Signal</button>
   )}

   // For routes
   <Route 
     path="/signals/create" 
     element={hasPermission('can_create_signals') ? <CreateSignal /> : <Navigate to="/" />} 
   />
   ```

3. **Dynamic Sidebar Generation**

   ```jsx
   const SideBar = () => {
     const { menuItems } = useContext(AuthContext);
     
     return (
       <nav className="sidebar">
         <ul>
           {menuItems.map(item => (
             <li key={item.id}>
               <Link to={item.path}>
                 <i className={`fa fa-${item.icon}`}></i>
                 <span>{item.title}</span>
               </Link>
               
               {item.children && (
                 <ul className="submenu">
                   {item.children.map(child => (
                     <li key={child.id}>
                       <Link to={child.path}>{child.title}</Link>
                     </li>
                   ))}
                 </ul>
               )}
             </li>
           ))}
         </ul>
       </nav>
     );
   };
   ```

## Deployment Instructions for Timeweb Cloud

### Prerequisites

- A Timeweb Cloud account
- Docker installed on your local machine (for building the image)

### Steps to Deploy

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd top-invest-1/backend
   ```

2. **Update the .env file**

   - Edit the `.env` file and update the following:
     - `SECRET_KEY`: Set a secure secret key
     - `ALLOWED_HOSTS`: Add your Timeweb Cloud domain
     - `CORS_ALLOWED_ORIGINS`: Add your frontend domain
     - `BOT_TOKEN`: Your Telegram bot token
     - `CHANNEL_ID`: Your Telegram channel ID

3. **Build and push the Docker image**

   ```bash
   docker build -t top-invest-backend .
   ```

4. **Deploy to Timeweb Cloud**

   - Log in to your Timeweb Cloud account
   - Create a new Docker container
   - Select the Docker image you pushed
   - Set the following environment variables:
     - All variables from your `.env` file
   - Map port 8000 to the external port
   - Add persistent volumes for:
     - `/app/db.sqlite3`
     - `/app/media`
     - `/app/payment_screenshots`

5. **Access your application**
   - Your backend will be available at `https://your-domain.timeweb.cloud`
   - Admin panel: `https://your-domain.timeweb.cloud/admin/`
   - API documentation: `https://your-domain.timeweb.cloud/swagger/`

## Local Development

1. **Set up the environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run migrations**

   ```bash
   python manage.py migrate
   ```

3. **Create a superuser**

   ```bash
   python manage.py createsuperuser
   ```

4. **Run the development server**

   ```bash
   python manage.py runserver
   ```

5. **Using Docker Compose**
   ```bash
   docker-compose up --build
   ```

## Project Structure

- `config/`: Django project settings
- `users/`: User management app
- `signals/`: Trading signals app
- `subscriptions/`: Subscription management app
- `payments/`: Payment processing app
- `instruments/`: Trading instruments app
- `reviews/`: User reviews app
- `dashboard/`: Admin dashboard app
- `invest_bot/`: Telegram bot integration
