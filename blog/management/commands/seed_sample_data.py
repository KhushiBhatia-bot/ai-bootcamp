"""
Management command: seed_sample_data
Usage: python manage.py seed_sample_data

Creates sample blog posts with tags to demonstrate the platform features.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta

from blog.models import Post, Tag
from accounts.models import Follow


SAMPLE_POSTS = [
    {
        "title": "Getting Started with Django in 2026",
        "tags": ["python", "django", "web-development", "tutorial"],
        "excerpt": "A comprehensive beginner's guide to building modern web applications with Django 6.1 — from project setup to deployment.",
        "content": """# Getting Started with Django in 2026

Django has evolved dramatically over the years, and in 2026, it remains one of the most powerful and developer-friendly web frameworks available.

## Why Django?

Django follows the **batteries-included** philosophy. Out of the box, you get:

- A powerful **ORM** for database operations
- Built-in **authentication** and authorization
- An automatic **admin panel**
- **Template engine** for rendering HTML
- **Security features** like CSRF protection, XSS prevention, and SQL injection protection

## Setting Up Your First Project

```bash
pip install Django==6.1.1
django-admin startproject myproject
cd myproject
python manage.py runserver
```

## Models & Migrations

Django models map Python classes to database tables:

```python
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
```

Run `python manage.py makemigrations` and `python manage.py migrate` to create the tables.

## What's Next?

In future posts, we'll explore Django REST Framework, async views, and deploying to cloud platforms. Stay tuned!
""",
    },
    {
        "title": "Understanding Machine Learning Pipelines",
        "tags": ["machine-learning", "data-science", "python", "ai"],
        "excerpt": "Breaking down the end-to-end ML pipeline — from data collection to model deployment — with practical Python examples.",
        "content": """# Understanding Machine Learning Pipelines

Building a machine learning model is more than just calling `model.fit()`. A production ML pipeline involves multiple stages, each critical to success.

## The Pipeline Stages

### 1. Data Collection & Ingestion
Gather data from APIs, databases, or streaming sources. Tools like **Apache Kafka** and **Snowflake** are commonly used.

### 2. Data Preprocessing
- Handle missing values
- Feature scaling and normalization
- Encoding categorical variables
- Train/test splitting

### 3. Feature Engineering
This is where domain knowledge shines. Creating meaningful features can improve model performance more than algorithm selection.

### 4. Model Training
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
```

### 5. Evaluation
Use metrics like **accuracy**, **precision**, **recall**, and **F1-score**. Cross-validation helps ensure robustness.

### 6. Deployment
Deploy models as REST APIs using **FastAPI** or **Flask**, or use managed services like **AWS SageMaker**.

> The best model in the world is useless if it never reaches production.
""",
    },
    {
        "title": "Snowflake vs Traditional Databases: When to Use What",
        "tags": ["snowflake", "databases", "cloud", "data-engineering"],
        "excerpt": "A practical comparison of Snowflake's cloud data warehouse against traditional RDBMS — understanding when each shines.",
        "content": """# Snowflake vs Traditional Databases

As data grows exponentially, choosing the right database technology becomes crucial. Let's compare Snowflake with traditional relational databases.

## Traditional RDBMS (PostgreSQL, MySQL)

**Best for:**
- Transactional workloads (OLTP)
- Low-latency reads and writes
- Applications requiring foreign keys and strict ACID compliance

## Snowflake Cloud Data Warehouse

**Best for:**
- Analytical workloads (OLAP)
- Large-scale data aggregation and reporting
- Separating compute from storage
- Handling semi-structured data (JSON, Parquet)

## Key Differences

| Feature | Traditional RDBMS | Snowflake |
|---------|------------------|-----------|
| Scaling | Vertical | Horizontal (auto) |
| Storage | Coupled | Separated |
| Concurrency | Limited | Virtually unlimited |
| Cost Model | Fixed | Pay-per-query |

## Our Experience with Chronicle

This very blog platform uses **Snowflake** as its primary database via `django-snowflake`. It works surprisingly well for a content platform — the separation of compute and storage means we can scale reads independently.

## Conclusion

There's no single "best" database. Use traditional RDBMS for transactional apps, and Snowflake for analytics-heavy workloads.
""",
    },
    {
        "title": "Building REST APIs with FastAPI and Python",
        "tags": ["python", "api", "fastapi", "web-development"],
        "excerpt": "Learn how to build blazingly fast REST APIs with FastAPI — featuring automatic docs, type validation, and async support.",
        "content": """# Building REST APIs with FastAPI

FastAPI has quickly become the go-to framework for building high-performance APIs in Python. Here's why, and how to get started.

## Why FastAPI?

- **Automatic OpenAPI documentation** — Swagger UI out of the box
- **Type hints** for automatic validation
- **Async support** — built on ASGI with Starlette
- **Performance** — on par with Node.js and Go

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, Chronicle!"}

@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    return {"post_id": post_id, "title": "Sample Post"}
```

Run with: `uvicorn main:app --reload`

## Request Validation with Pydantic

```python
from pydantic import BaseModel

class PostCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []

@app.post("/posts/")
async def create_post(post: PostCreate):
    return {"created": post.title}
```

FastAPI automatically validates the request body and returns helpful error messages.

## Database Integration

Pair FastAPI with **SQLAlchemy** or **Tortoise ORM** for database operations. For async workloads, Tortoise ORM is a great choice.
""",
    },
    {
        "title": "The Art of Writing Clean Code",
        "tags": ["programming", "best-practices", "clean-code"],
        "excerpt": "Clean code isn't about being clever — it's about being clear. Principles and practices for writing code that lasts.",
        "content": """# The Art of Writing Clean Code

> "Any fool can write code that a computer can understand. Good programmers write code that humans can understand." — Martin Fowler

## Principles That Matter

### 1. Meaningful Names
```python
# Bad
d = 7

# Good
days_until_deadline = 7
```

### 2. Functions Should Do One Thing
Each function should have a single responsibility. If you find yourself using "and" to describe what a function does, it's doing too much.

### 3. Don't Repeat Yourself (DRY)
Extract common patterns into reusable functions or classes.

### 4. Write Tests
Tests are documentation that never goes out of date. Aim for meaningful test coverage, not 100% line coverage.

### 5. Comments Should Explain *Why*, Not *What*
```python
# Bad: Increment counter by 1
counter += 1

# Good: Retry count tracks failed API calls for circuit breaker pattern
retry_count += 1
```

## The Boy Scout Rule

> "Leave the code cleaner than you found it."

Every time you touch a file, make one small improvement — rename a variable, extract a function, remove dead code.

## Conclusion

Clean code is a practice, not a destination. Start small, be consistent, and your future self will thank you.
""",
    },
    {
        "title": "Introduction to Cloud Computing with AWS",
        "tags": ["cloud", "aws", "devops", "tutorial"],
        "excerpt": "Your first steps into the cloud — understanding AWS core services and how they fit together for modern applications.",
        "content": """# Introduction to Cloud Computing with AWS

Cloud computing has transformed how we build and deploy software. AWS leads the market with hundreds of services, but you only need a few to get started.

## Core Services to Know

### Compute: EC2 & Lambda
- **EC2**: Virtual servers in the cloud
- **Lambda**: Serverless functions — pay only when code runs

### Storage: S3
Amazon S3 provides virtually unlimited object storage. Perfect for static assets, backups, and data lakes.

### Database: RDS & DynamoDB
- **RDS**: Managed relational databases (PostgreSQL, MySQL)
- **DynamoDB**: Serverless NoSQL database

### Networking: VPC
Virtual Private Cloud lets you isolate your resources in a private network.

## Getting Started

1. Create a free-tier AWS account
2. Launch an EC2 instance
3. Deploy a simple web app
4. Set up S3 for static file hosting

## Cost Management Tips

- Use **free tier** services for learning
- Set up **billing alerts**
- Use **spot instances** for non-critical workloads
- Review unused resources monthly

Cloud computing is a journey — start with the basics and build from there!
""",
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample blog posts and tags for demonstration."

    def handle(self, *args, **options):
        # Get or create a user to be the author
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            self.stderr.write(self.style.ERROR("No users found. Create a user first with: python manage.py createsuperuser"))
            return

        self.stdout.write(f"Using author: {user.username}")

        created_count = 0
        for i, post_data in enumerate(SAMPLE_POSTS):
            slug = slugify(post_data["title"])

            # Skip if post already exists
            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(f"  ⏩ Skipped (exists): {post_data['title']}")
                continue

            # Create tags
            tag_objects = []
            for tag_name in post_data["tags"]:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={"slug": slugify(tag_name)}
                )
                tag_objects.append(tag)

            # Create post with staggered dates so they look natural
            post = Post.objects.create(
                title=post_data["title"],
                slug=slug,
                author=user,
                excerpt=post_data["excerpt"],
                content=post_data["content"],
                status=Post.STATUS_PUBLISHED,
                published_at=timezone.now() - timedelta(days=(len(SAMPLE_POSTS) - i) * 2),
            )
            post.tags.set(tag_objects)

            self.stdout.write(self.style.SUCCESS(
                f"  ✅ Created: \"{post.title}\" with tags: {', '.join(post_data['tags'])}"
            ))
            created_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done! Created {created_count} posts."))
        self.stdout.write(f"Total tags in system: {Tag.objects.count()}")
        self.stdout.write(f"Total published posts: {Post.objects.filter(status=Post.STATUS_PUBLISHED).count()}")
