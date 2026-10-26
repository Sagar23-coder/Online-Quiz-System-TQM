"""
QuizFlow CLI Utilities: Admin Account Provisioning and Demo Seeding.
"""
import argparse
import getpass
import sys

from app.core.security import get_password_hash
from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.user import User, UserRole


def create_admin():
    parser = argparse.ArgumentParser(description="Create or bootstrap an administrator account.")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--name", help="Administrator full name")
    parser.add_argument("--password", help="Administrator password (omit to prompt securely)")
    args = parser.parse_args(sys.argv[2:])

    email = args.email or input("Enter administrator email: ").strip()
    name = args.name or input("Enter administrator full name: ").strip()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter administrator password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)

    if len(password) < 6:
        print("Error: Password must be at least 6 characters.")
        sys.exit(1)

    db = SessionLocal()
    try:
        init_db(db)
        existing = db.query(User).filter(User.email == email.lower()).first()
        if existing:
            existing.role = UserRole.ADMIN.value
            existing.full_name = name
            existing.hashed_password = get_password_hash(password)
            db.commit()
            print(f"Successfully updated user '{email}' to administrator.")
        else:
            admin_user = User(
                email=email.lower(),
                full_name=name,
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            print(f"Administrator account '{email}' created successfully.")
    finally:
        db.close()


def seed_demo():
    """Seed clean, realistic demo quizzes and questions for evaluation."""
    db = SessionLocal()
    try:
        init_db(db)
        admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if not admin:
            print("Please create an administrator account first using: python -m app.cli create-admin")
            sys.exit(1)

        # Check if demo quiz already exists
        demo_title = "Python & Web Architecture Fundamentals"
        existing_quiz = db.query(Quiz).filter(Quiz.title == demo_title).first()
        if existing_quiz:
            print("Demo quiz already exists in database.")
            return

        demo_quiz = Quiz(
            title=demo_title,
            description="Assess your foundational understanding of Python data structures, HTTP protocols, and REST API design.",
            duration_minutes=15,
            passing_percentage=60,
            total_marks=5,
            is_published=True,
            join_code="QF-DEMO",
            is_public=True,
            release_results_immediately=True,
            results_released=True,
            created_by_id=admin.id,
        )
        db.add(demo_quiz)
        db.flush()

        questions_data = [
            {
                "question_text": "Which HTTP status code is most appropriate for a resource created successfully via a POST request?",
                "option_a": "200 OK",
                "option_b": "201 Created",
                "option_c": "204 No Content",
                "option_d": "202 Accepted",
                "correct_option": "B",
                "marks": 1,
                "explanation": "HTTP 201 indicates that the request has succeeded and led to the creation of a new resource.",
                "order_index": 1,
            },
            {
                "question_text": "In Python, which built-in data type is immutable and hashable, making it suitable as a dictionary key?",
                "option_a": "list",
                "option_b": "dict",
                "option_c": "tuple",
                "option_d": "set",
                "correct_option": "C",
                "marks": 1,
                "explanation": "Tuples containing only immutable elements are themselves immutable and hashable.",
                "order_index": 2,
            },
            {
                "question_text": "What is the primary role of an ASGI server such as Uvicorn in modern Python web applications?",
                "option_a": "Managing relational database schema migrations",
                "option_b": "Providing an asynchronous interface between the web server and Python async web frameworks",
                "option_c": "Encrypting JWT tokens in the browser local storage",
                "option_d": "Compiling TypeScript into optimized bytecode",
                "correct_option": "B",
                "marks": 1,
                "explanation": "ASGI (Asynchronous Server Gateway Interface) allows async frameworks like FastAPI to handle concurrent connections efficiently.",
                "order_index": 3,
            },
            {
                "question_text": "Which algorithm is officially recommended by OWASP as the primary standard for password hashing?",
                "option_a": "MD5",
                "option_b": "SHA-1",
                "option_c": "Argon2id",
                "option_d": "Base64",
                "correct_option": "C",
                "marks": 1,
                "explanation": "Argon2id won the Password Hashing Competition and provides memory-hard protection against GPU-based cracking attacks.",
                "order_index": 4,
            },
            {
                "question_text": "What does ACID stand for in the context of relational database management systems?",
                "option_a": "Atomicity, Consistency, Isolation, Durability",
                "option_b": "Authentication, Cryptography, Integrity, Decryption",
                "option_c": "Asynchronous, Concurrent, Isolated, Distributed",
                "option_d": "Array, Collection, Index, Directory",
                "correct_option": "A",
                "marks": 1,
                "explanation": "ACID properties guarantee reliable transaction processing in database systems.",
                "order_index": 5,
            },
        ]

        for q in questions_data:
            question = Question(quiz_id=demo_quiz.id, **q)
            db.add(question)

        db.commit()
        print(f"Demo quiz '{demo_title}' with 5 questions seeded and published successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m app.cli create-admin [--email EMAIL] [--name NAME] [--password PASS]")
        print("  python -m app.cli seed-demo")
        sys.exit(1)

    command = sys.argv[1]
    if command == "create-admin":
        create_admin()
    elif command == "seed-demo":
        seed_demo()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
