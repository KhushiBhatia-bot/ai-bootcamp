# Chronicle — Modern Publishing & Blogging Platform

A modern, responsive publishing and blogging platform built with **Django**, **Tailwind CSS**, and backed by **Snowflake Cloud Data Warehouse** as its primary database.

---

## 🌟 Overview

**Chronicle** is designed to deliver a seamless editorial reading experience for visitors while providing authors with a powerful, distraction-free environment to write, manage drafts, and track reader engagement.

Instead of traditional file-based or local relational databases, Chronicle is connected directly to **Snowflake** via `django-snowflake`. All user profiles, blog posts, threaded discussions, likes, and active sessions are persisted directly in an enterprise-grade cloud data warehouse.

---

## 🚀 Key Features

### 📖 Reader Experience & Discovery
- **Open Public Reading**: Anyone can browse the home feed, search articles, read published stories, and view author profile portfolios without needing to log in.
- **Dynamic Search & Filtering**: Instant keyword search and multi-criteria sorting pills (Latest, Most Liked, Most Discussed, and Oldest).
- **Editorial Typography**: Styled with Google Fonts (**Plus Jakarta Sans** and **Newsreader**) and **JetBrains Mono** for formatted code blocks.
- **Rich Markdown Content**: Full Markdown support for headings, bold/italics, blockquotes, lists, tables, and code snippets, rendered into sanitized safe HTML using **Bleach** to prevent XSS vulnerabilities.
- **Reading Estimator**: Real-time calculated reading time badges on each story.

### ✍️ Author & Content Management
- **Creator Dashboard**: Personal workspace showing live engagement metrics (total published stories, drafts in progress, total likes received, and comment counts).
- **Draft Privacy & Author Isolation**: Authors can save works in progress as confidential **Drafts**. Drafts are strictly private and accessible only by the author who wrote them.
- **Ownership Security**: Edit and delete operations are restricted strictly to post owners or administrators. Unauthorized attempts are rejected with `HTTP 403 Forbidden`.
- **Automatic Metadata**: Automatic generation of SEO-friendly URL slugs, publication timestamps, and card preview excerpts.

### 💬 Interactive Engagement
- **Real-Time Likes**: Readers can like/unlike articles with instantaneous counter updates powered by a background asynchronous Fetch API (AJAX) call without page reloads.
- **Threaded Nested Discussions**:
  - Full two-tier threaded conversation tree.
  - Dedicated **Reply** button on every comment that smoothly expands an inline reply form.
  - Auto-prepopulates `@username` handles and organizes replies into clean, indented threads.
  - Highlighted **Author** badges when the post creator participates in the discussion.
  - Author moderation controls to delete comments and replies.

### 🔒 Authentication & Security
- **Cryptographic Password Hashing**: Passwords are never stored in plain text. Django automatically hashes credentials using **PBKDF2 with SHA-256** with thousands of hashing rounds before saving to Snowflake.
- **Session Management**: Secure, cookie-based session tracking stored in Snowflake (`DJANGO_SESSION`).
- **CSRF Protection**: All forms and state-changing actions are secured with Django CSRF tokens.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3, Django 6.1 |
| **Database** | Snowflake Cloud Data Warehouse (via `django-snowflake` engine) |
| **Frontend Styling** | Tailwind CSS (Typography & Forms plugins), Google Fonts |
| **Frontend Interactivity** | Vanilla JavaScript (AJAX likes, mobile menu drawer, inline reply toggles, auto-dismiss alerts) |
| **Content & Security** | Python-Markdown, Bleach (HTML sanitization), PBKDF2/SHA-256 password hashing |
| **Configuration** | `python-dotenv` for secure environment variable management |

---

## 📋 Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.12+** (compatible with Python 3.14)
- **pip** (Python package installer)
- A **Snowflake Account** (with database, schema, and compute warehouse privileges)

---

## ⚙️ Setup & Run Instructions

### 1. Clone & Navigate to Project Directory
```bash
cd /path/to/fun_ai_week1
```

### 2. Activate the Virtual Environment
Activate the existing virtual environment:
```bash
source .venv/bin/activate
```
*(If setting up on a new machine without `.venv`, create one first with `python3 -m venv .venv` and activate it).*

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Snowflake Environment Variables
Create a `.env` file in the root directory (next to `manage.py`):
```bash
touch .env
```

Add your Snowflake connection parameters to `.env`:
```env
SNOWFLAKE_ACCOUNT=YOUR_ACCOUNT_IDENTIFIER
SNOWFLAKE_USER=YOUR_USERNAME
SNOWFLAKE_PASSWORD=YOUR_PASSWORD
SNOWFLAKE_DATABASE=BLOG_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=SYSADMIN
```
> **Note**: Your `.env` file is protected and ignored by `.gitignore` so your credentials remain private.

### 5. Apply Database Migrations
Run Django migrations to build all required tables (`AUTH_USER`, `BLOG_POST`, `BLOG_COMMENT`, etc.) directly inside Snowflake:
```bash
python manage.py migrate
```

### 6. Create an Admin Account
Create a superuser account for platform moderation and admin dashboard access:
```bash
python manage.py createsuperuser
```
Follow the interactive prompt to set your username, email, and password.

### 7. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🗺️ URL Route Reference

| URL Path | View Description | Access Level |
| :--- | :--- | :--- |
| `/` | Public Home Feed (Search & Sort) | Public |
| `/post/<slug>/` | Article Detail & Threaded Discussions | Public |
| `/author/<username>/` | Author Public Portfolio Profile | Public |
| `/dashboard/` | Author Creator Dashboard | Authenticated |
| `/post/new/` | Write New Story (Draft or Publish) | Authenticated |
| `/post/<slug>/edit/` | Edit Story | Post Author Only |
| `/post/<slug>/delete/` | Delete Story | Post Author Only |
| `/post/<slug>/like/` | Toggle Like (AJAX endpoint) | Authenticated |
| `/post/<slug>/comment/` | Submit Comment or Nested Reply | Authenticated |
| `/comment/<id>/delete/` | Delete Comment | Comment/Post Author |
| `/accounts/register/` | Create New Author Account | Public |
| `/accounts/login/` | Sign In | Public |
| `/accounts/logout/` | Sign Out | Authenticated |
| `/accounts/profile/` | Edit Profile Bio & Avatar | Authenticated |
| `/admin/` | Django Administration Portal | Superuser Only |

---

## 📁 Project Structure

```text
fun_ai_week1/
├── .env                         # Snowflake credentials (ignored by git)
├── .gitignore                   # Git ignore configurations
├── manage.py                    # Django management CLI script
├── requirements.txt             # Project dependencies
├── README.md                    # Project documentation
├── blog_platform/               # Core project configuration
│   ├── settings.py              # Snowflake DB, apps, and middleware settings
│   ├── urls.py                  # Root URL router
│   └── wsgi.py                  # WSGI application entrypoint
├── accounts/                    # User authentication & profiles app
│   ├── admin.py                 # Admin integration
│   ├── apps.py                  # App configuration
│   ├── forms.py                 # Register and profile update forms
│   ├── models.py                # Profile model and post_save signal
│   ├── urls.py                  # Account URLs
│   └── views.py                 # Register, login, profile views
├── blog/                        # Blog publishing & engagement app
│   ├── admin.py                 # Post, Comment, and Like admin configuration
│   ├── apps.py                  # App configuration
│   ├── forms.py                 # PostForm and CommentForm
│   ├── models.py                # Post, Comment (self-referential parent), Like
│   ├── urls.py                  # Blog routing
│   └── views.py                 # Feed, detail, CRUD, AJAX like, comments
├── templates/                   # Clean HTML templates (Tailwind CSS)
│   ├── base.html                # Global layout, sticky navbar, flash messages
│   ├── accounts/                # Login, Register, Profile templates
│   └── blog/                    # Home, Post detail, Dashboard, Post form, Delete
└── static/                      # Static client assets
    └── js/
        └── blog.js              # AJAX like toggles, mobile menu, auto-dismiss alerts
```
