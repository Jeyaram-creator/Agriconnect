# 🌾 AgriConnect – Farmer Partnership and Sales System

## 📌 Project Overview

AgriConnect is a web-based application developed to connect farmers and customers through an online agricultural marketplace. It provides a centralized platform for managing agricultural products, farmer partnerships, customer orders, and sales activities.

The system has three main users: Admin, Farmer, and Customer. Each user has separate functionalities to manage their activities efficiently.

## 🎯 Objectives

- To provide an online platform for agricultural product sales.
- To help farmers manage their products digitally.
- To support partnerships between farmers.
- To allow customers to browse and purchase agricultural products.
- To simplify order and sales management.
- To maintain application information using a centralized database.

## 🚀 Main Features

### 👨‍💼 Admin Module
- Admin Login
- User Management
- Product Monitoring
- Order Monitoring
- Manage User Status

### 🌱 Farmer Module
- Farmer Registration and Login
- Farmer Dashboard
- Add, Edit, and Delete Products
- View Product Details
- View Customer Orders
- Farmer-to-Farmer Partnership Requests
- Accept or Reject Partnership Requests

### 🛒 Customer Module
- Customer Registration and Login
- Customer Dashboard
- Browse Agricultural Products
- Search Products
- View Product Details
- Add Products to Cart
- Checkout and Place Orders
- View Order History

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| HTML | Web Page Structure |
| CSS | User Interface Design |
| JavaScript | Client-Side Interactivity |
| Python | Backend Programming |
| Flask | Web Application Framework |
| MySQL | Database Management |
| VS Code | Code Editor |

## 🗄️ Database Tables

The application uses MySQL to store and manage information.

Main database tables:

1. Users
2. Farmers
3. Customers
4. Products
5. Partnerships
6. Orders
7. Order Items
8. Sales (if implemented)

## ⚙️ Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/AgriConnect.git
```

### Step 2: Open the Project Folder

```bash
cd AgriConnect
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### Step 5: Install Required Packages

```bash
pip install -r requirements.txt
```

### Step 6: Configure MySQL Database

- Open MySQL Workbench or your MySQL client.
- Create the required database.
- Import or execute your project SQL table definitions.
- Configure the database connection in your application.
- Add your own database credentials securely.

### Step 7: Run the Application

```bash
python app.py
```

Open the application in your browser using the local address displayed by Flask, usually:

```text
http://127.0.0.1:5000/
```

## 🔄 Application Workflow

```text
User Login
    ↓
Credential Verification
    ↓
Role Identification
    ↓
Role-Based Dashboard
    ↓
Admin / Farmer / Customer Activities
    ↓
MySQL Database
```

## 🔮 Future Enhancements

- Online Payment Gateway Integration
- Mobile Application Development
- Order and Delivery Tracking
- SMS and Email Notifications
- Product Rating and Review System
- AI-Based Crop and Price Prediction
- Advanced Sales Reports and Data Visualization

## 👨‍💻 Project Information

**Project Name:** AgriConnect – Farmer Partnership and Sales System

**Project Type:** Web-Based Application

**Frontend:** HTML, CSS, JavaScript

**Backend:** Python Flask

**Database:** MySQL

**Code Editor:** Visual Studio Code

## 📄 License

This project is developed for academic and learning purposes.

---

**AgriConnect – Connecting Farmers, Empowering Agriculture! 🌾**
