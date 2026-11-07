# Online Shopping and Order Management System

A complete, production-ready DevOps demonstration project built with **Python Flask**, **SQLite**, **Bootstrap 5**, **Docker**, **Jenkins CI/CD**, and **Selenium 4**.

Designed specifically for college DevOps laboratory examinations and technical demonstrations.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture & Modules](#system-architecture--modules)
4. [Project Directory Structure](#project-directory-structure)
5. [Prerequisites & Environment Setup](#prerequisites--environment-setup)
6. [Step-by-Step Installation (Windows PowerShell)](#step-by-step-installation-windows-powershell)
7. [Running the Application](#running-the-application)
8. [Default Seed Credentials](#default-seed-credentials)
9. [Automated Testing with Selenium 4](#automated-testing-with-selenium-4)
10. [Containerization with Docker](#containerization-with-docker)
11. [Jenkins CI/CD Pipeline Configuration](#jenkins-cicd-pipeline-configuration)
12. [Git & GitHub Integration](#git--github-integration)
13. [Troubleshooting & Common Questions](#troubleshooting--common-questions)

---

## 🎯 Project Overview

The **Online Shopping and Order Management System** allows customers to register, browse products, search the catalogue, manage cart items with dynamic stock validation, and place orders. Administrators can access a dedicated dashboard to manage product inventory (add, edit, delete products) and view platform metrics.

### Key Highlights
- **Zero Frontend Bloat**: Clean server-rendered HTML templates with responsive Bootstrap 5 styling.
- **Secure Authentication**: Password hashing with Werkzeug security and role-based access control (RBAC).
- **Persistent Storage**: Lightweight SQLite database with auto-initialization and idempotency.
- **Automated Verification**: End-to-end automated testing suite with 12 Selenium 4 test cases using explicit waits.
- **Windows-Compatible CI/CD**: Declarative Jenkins pipeline configured specifically for Windows agents using batch commands (`bat`).

---

## 🛠 Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+ / Flask | Web server & REST routing |
| **Database** | SQLite 3 | Embedded relational persistence |
| **Frontend** | HTML5, CSS3, Bootstrap 5 | Responsive UI styling |
| **Security** | Werkzeug Security | Password hashing & session management |
| **Testing** | Selenium 4 + Chrome WebDriver | End-to-end automated UI & regression tests |
| **Containerization** | Docker | Linux container deployment |
| **CI/CD Pipeline** | Jenkins (Declarative) | Build, test, containerize, and run stages |
| **Version Control** | Git & GitHub | Source code tracking |

---

## 🧩 System Architecture & Modules

### 1. Customer Capabilities
- **Account Registration & Login**: Validated registration with confirmation password and duplicate email/username checks.
- **Catalogue & Search**: Browse 6+ seeded products with search filters across title and category.
- **Dynamic Cart**: Real-time quantity adjustment, stock ceiling prevention, and item removal.
- **Checkout & Order Placement**: Multi-field delivery address validation and immediate stock reduction.
- **Order History & Details**: Chronological order history with itemized price breakdown.

### 2. Administrator Capabilities
- **Dedicated Admin Dashboard**: Summary statistics (total products, active orders, total customers, revenue).
- **Product Management**: Create, modify, and delete inventory items.
- **Access Protection**: Role decorator `@admin_required` prevents customer tampering with admin routes.

---

## 📁 Project Directory Structure

```
shopping-order-system/
├── app.py                     # Flask backend application & SQLite database setup
├── requirements.txt           # Python dependencies (Flask, Werkzeug, Selenium)
├── Dockerfile                 # Multi-platform Docker container definition
├── Jenkinsfile                # Windows Declarative Jenkins CI/CD pipeline
├── test_selenium.py           # Selenium 4 automated test suite (TC01 - TC12)
├── README.md                  # Comprehensive documentation and lab guide
├── .gitignore                 # Standard exclusions (db, pycache, logs)
└── templates/                 # Jinja2 HTML templates styled with Bootstrap 5
    ├── base.html              # Core navigation layout and flash messages
    ├── index.html             # Product catalogue with live search
    ├── register.html          # Customer registration form
    ├── login.html             # Role-aware login form
    ├── cart.html              # Interactive cart with quantity adjustments
    ├── checkout.html          # Order address & checkout form
    ├── order_confirmation.html# Successful order receipt
    ├── order_history.html     # Customer order list
    ├── order_details.html     # Detailed item breakdown
    ├── admin.html             # Admin statistics & inventory management
    ├── add_product.html       # Add new product form
    └── edit_product.html      # Edit existing product form
```

---

## ⚙ Prerequisites & Environment Setup

Ensure the following tools are installed on your Windows machine:
1. **Python 3.10+**: Available in your system PATH (`python --version`).
2. **Google Chrome**: Standard browser installed.
3. **Git**: Installed for version control (`git --version`).
4. **Docker Desktop** *(Optional for local Docker demo)*: Running on Windows.
5. **Jenkins** *(Optional for CI/CD demo)*: Running on `http://localhost:8080`.

---

## 🚀 Step-by-Step Installation (Windows PowerShell)

Open **PowerShell** and navigate to your project directory:

```powershell
# 1. Navigate to the project directory
cd "d:\programin\uday\DevOps\Online Shopping and Order Management System\shopping-order-system"

# 2. (Recommended) Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install required Python packages
pip install -r requirements.txt
```

---

## 💻 Running the Application

Start the Flask development server:

```powershell
python app.py
```

Output:
```
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

Now open your web browser and visit:  
👉 **`http://localhost:5000`**

The SQLite database (`shopping.db`) is automatically generated and seeded on initial run!

---

## 🔑 Default Seed Credentials

The database comes pre-loaded with these test accounts:

| Role | Username | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full Admin Dashboard & Inventory Management |
| **Customer** | `customer1` | `pass123` | Shopping, Cart, Checkout, Order History |

*(You can also register brand-new customer accounts anytime via `/register`.)*

---

## 🧪 Automated Testing with Selenium 4

The project includes an end-to-end automated test suite in `test_selenium.py`.

### How to Run the Dual-Terminal Demo:

#### **Terminal 1: Start Flask Application**
```powershell
cd "d:\programin\uday\DevOps\Online Shopping and Order Management System\shopping-order-system"
python app.py
```

#### **Terminal 2: Run Selenium Test Suite**
```powershell
cd "d:\programin\uday\DevOps\Online Shopping and Order Management System\shopping-order-system"

# Run tests in headless mode (default background execution)
python test_selenium.py --headless

# OR run with visible Chrome browser window (great for live examination demo!)
python test_selenium.py --no-headless
```

### Covered Test Cases:
- **TC01**: Customer login with valid credentials
- **TC02**: Customer login with invalid credentials & error alert
- **TC03**: Customer registration with fresh unique user
- **TC04**: Product catalogue rendering & seeded products
- **TC05**: Product search filtering by keyword
- **TC06**: Add item to shopping cart & verify badge
- **TC07**: Update cart quantity and subtotal calculation
- **TC08**: Checkout form submission & order confirmation receipt
- **TC09**: Order history listing & detailed order view
- **TC10**: Admin login & new product creation
- **TC11**: Role-based access control (blocking customers from `/admin`)
- **TC12**: Empty cart checkout prevention

---

## 🐳 Containerization with Docker

You can containerize the application to ensure it runs consistently anywhere.

### 1. Build the Docker Image
```powershell
docker build -t shopping-order-system:v1 .
```

### 2. Run the Container
```powershell
docker run -d --name shopping-container -p 5000:5000 shopping-order-system:v1
```

Access the app at: **`http://localhost:5000`**

### 3. Database Persistence with Docker Volumes (Optional)
To persist database changes outside the container lifecycle:
```powershell
docker run -d --name shopping-container -p 5000:5000 -v ${PWD}:/app shopping-order-system:v1
```

### 4. Stop and Remove the Container
```powershell
docker stop shopping-container
docker rm shopping-container
```

---

## 🔄 Jenkins CI/CD Pipeline Configuration

The included `Jenkinsfile` is designed specifically for **Windows Jenkins agents** using Windows Batch (`bat`) commands.

### Pipeline Stages:
1. **Checkout**: Pulls the latest source code from GitHub.
2. **Environment Validation**: Checks Python and Docker availability.
3. **Install Dependencies**: Installs `requirements.txt`.
4. **Automated Testing**: Runs `test_selenium.py` in headless mode.
5. **Docker Build**: Builds image `shopping-order-system:v1`.
6. **Deploy Container**: Stops any conflicting running container on port 5000 and starts `shopping-container`.

### Setting up the Jenkins Job:
1. Open Jenkins (`http://localhost:8080`).
2. Click **New Item** ➔ Choose **Pipeline** ➔ Name it `shopping-order-system`.
3. Under **Pipeline Definition**, select **Pipeline script from SCM**.
4. Choose **Git** and enter your repository URL:  
   `https://github.com/udaymailaram225-pixel/shopping-order-system.git`
5. Set branch to `*/main` and Script Path to `Jenkinsfile`.
6. Click **Save** and then **Build Now**.

---

## 🐙 Git & GitHub Integration

Follow these steps to publish your code to GitHub.

> [!WARNING]
> Ensure you have created the empty repository `shopping-order-system` on your GitHub account before running `git push`.

```powershell
# Step 1: Navigate to the project root
cd "d:\programin\uday\DevOps\Online Shopping and Order Management System\shopping-order-system"

# Step 2: Initialize Git
git init

# Step 3: Stage all project files
git add .

# Step 4: Create initial commit
git commit -m "Initial commit - Shopping Order Management System"

# Step 5: Rename branch to main
git branch -M main

# Step 6: Link your remote GitHub repository
git remote add origin https://github.com/udaymailaram225-pixel/shopping-order-system.git

# Step 7: Push to GitHub (Run when you are ready)
git push -u origin main
```

---

## ❓ Troubleshooting & Common Questions

### 1. `Address already in use` error
If port 5000 is occupied by another process:
```powershell
# Find process using port 5000
netstat -ano | findstr :5000
# Terminate the process by PID
taskkill /F /PID <PID_NUMBER>
```

### 2. Chrome or ChromeDriver version mismatch
Selenium 4 manages drivers automatically via `Selenium Manager`. Make sure you have Google Chrome updated to its standard stable release.

### 3. Docker build fails on Windows
Ensure Docker Desktop is running and switched to **Linux containers** (the default mode for Python-slim images).

---

## 🎓 College Examination Lab Demo Checklist
- [x] Flask backend running on `http://localhost:5000`
- [x] Pre-seeded with 6 products, 1 admin, and 1 customer
- [x] User registration with instant login
- [x] Add to cart, quantity update, stock prevention
- [x] Successful order checkout & order history
- [x] Admin dashboard product management (add/edit/delete)
- [x] 12/12 automated Selenium test cases passing
- [x] Clean Dockerfile with health checks
- [x] Windows-compatible Jenkinsfile pipeline
