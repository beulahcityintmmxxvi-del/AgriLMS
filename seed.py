# =============================================================
# Agri LMS — Database Seed Script
# =============================================================
# File    : seed.py
# Usage   : python seed.py
# =============================================================

import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.course import Course
from app.models.module import Module
from app.models.material import Material
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.progress import Progress
import random


def now():
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def seed_database():
    """Run the complete database seed."""

    app = create_app('development')

    with app.app_context():

        print('\n🌱 Agri LMS — Database Seeding')
        print('=' * 50)

        # ── Clear existing data ───────────────────────────────
        print('\n⚠️  Clearing existing data...')
        try:
            Progress.query.delete()
            Enrollment.query.delete()
            Assignment.query.delete()
            Material.query.delete()
            Module.query.delete()
            Course.query.delete()
            User.query.delete()
            db.session.commit()
            print('   ✅ All existing data cleared.')
        except Exception as e:
            db.session.rollback()
            print(f'   ❌ Error clearing data: {e}')
            return

        # ── Create Admin ──────────────────────────────────────
        print('\n👤 Creating admin user...')

        admin = User(
            full_name='Platform Administrator',
            email='admin@agrilms.com',
            phone_number='08000000001',
            state='Lagos',
            country='Nigeria',
            role='admin',
            is_active=True,
            date_registered=now() - timedelta(days=120)
        )
        admin.set_password('Admin@12345')
        db.session.add(admin)
        db.session.flush()
        print('   ✅ admin@agrilms.com | Admin@12345')

        # ── Create Learners ───────────────────────────────────
        print('\n👥 Creating learner accounts...')

        learner_data = [
            {
                'full_name':    'Adewale Okafor',
                'email':        'adewale@example.com',
                'phone_number': '08012345678',
                'state':        'Ogun',
                'bio':          'Smallholder cassava and maize farmer.',
                'farming_background':
                    'Farming cassava and maize for 5 years in Ogun State.',
            },
            {
                'full_name':    'Fatima Musa',
                'email':        'fatima@example.com',
                'phone_number': '08098765432',
                'state':        'Kano',
                'bio':          'Poultry and vegetable farmer.',
                'farming_background':
                    'Running a small poultry farm and vegetable garden.',
            },
            {
                'full_name':    'Chukwuemeka Eze',
                'email':        'emeka@example.com',
                'phone_number': '07011223344',
                'state':        'Enugu',
                'bio':          'Yam and cocoyam farmer.',
                'farming_background':
                    'Third-generation yam farmer in Enugu State.',
            },
            {
                'full_name':    'Amina Abdullahi',
                'email':        'amina@example.com',
                'phone_number': '08033445566',
                'state':        'Kaduna',
                'bio':          'Livestock and sorghum farmer.',
                'farming_background':
                    'Mixed farm with cattle and sorghum in Kaduna.',
            },
            {
                'full_name':    'Oluwaseun Adeyemi',
                'email':        'seun@example.com',
                'phone_number': '09055667788',
                'state':        'Osun',
                'bio':          'Cocoa and palm oil farmer.',
                'farming_background':
                    'Growing cocoa and harvesting palm oil in Osun State.',
            },
        ]

        learners = []
        for ld in learner_data:
            learner = User(
                full_name=ld['full_name'],
                email=ld['email'],
                phone_number=ld['phone_number'],
                state=ld['state'],
                country='Nigeria',
                role='learner',
                bio=ld['bio'],
                farming_background=ld['farming_background'],
                is_active=True,
                date_registered=now() - timedelta(
                    days=random.randint(10, 90))
            )
            learner.set_password('Learner@12345')
            db.session.add(learner)
            learners.append(learner)
            print(f'   ✅ {ld["full_name"]} ({ld["email"]})')

        db.session.flush()

        # ── Create Courses ────────────────────────────────────
        print('\n📚 Creating courses...')

        courses_data = [
            {
                'title': 'Introduction to Crop Production',
                'short_description':
                    'Learn the fundamentals of growing major food crops '
                    'including maize, cassava, rice, and yam using '
                    'modern and indigenous methods.',
                'full_description':
                    'This comprehensive course covers all aspects of crop '
                    'production from land preparation to post-harvest '
                    'handling. You will gain practical knowledge of soil '
                    'preparation, seed selection, planting, crop management, '
                    'and harvesting techniques.',
                'category':       'Crop Production',
                'level':          'beginner',
                'duration_weeks': 8,
                'tags':           'maize, cassava, rice, yam, planting',
                'learning_outcomes':
                    'Identify and select the right crop varieties\n'
                    'Prepare land correctly for planting\n'
                    'Apply fertilizers safely and effectively\n'
                    'Monitor crops for pests and diseases\n'
                    'Harvest and store produce correctly',
                'is_featured': True,
            },
            {
                'title': 'Soil Science and Soil Health Management',
                'short_description':
                    'Discover how to assess, improve, and maintain '
                    'soil fertility for maximum crop yield using '
                    'scientific and indigenous soil management methods.',
                'full_description':
                    'Healthy soil is the foundation of productive farming. '
                    'This course teaches you to understand soil types, '
                    'measure soil pH, interpret soil test results, and '
                    'apply amendments using organic and inorganic sources.',
                'category':       'Soil Science',
                'level':          'intermediate',
                'duration_weeks': 6,
                'tags':           'soil, pH, fertility, compost, amendments',
                'learning_outcomes':
                    'Identify the main soil types in Nigeria\n'
                    'Test soil pH accurately using a soil test kit\n'
                    'Interpret soil test results correctly\n'
                    'Apply lime and organic matter for pH correction\n'
                    'Build and manage a compost heap',
                'is_featured': True,
            },
            {
                'title': 'Indigenous Farming Practices and Knowledge',
                'short_description':
                    'Preserve and apply traditional African agricultural '
                    'wisdom including indigenous seed selection, natural '
                    'pest management, intercropping, and seasonal '
                    'farming calendars.',
                'full_description':
                    'This course documents and teaches indigenous farming '
                    'knowledge passed down through generations of African '
                    'farmers. Topics include traditional seed preservation, '
                    'intercropping systems, natural pest control, and '
                    'seasonal planting calendars.',
                'category':       'Indigenous Practices',
                'level':          'beginner',
                'duration_weeks': 10,
                'tags':
                    'indigenous, traditional, seeds, intercropping, calendar',
                'learning_outcomes':
                    'Describe the importance of indigenous knowledge\n'
                    'Apply traditional intercropping systems\n'
                    'Select and preserve indigenous seed varieties\n'
                    'Use natural methods for pest management\n'
                    'Follow traditional seasonal planting calendars',
                'is_featured': False,
            },
        ]

        courses = []
        for cd in courses_data:
            course = Course(
                created_by=admin.id,
                title=cd['title'],
                short_description=cd['short_description'],
                full_description=cd.get('full_description'),
                category=cd['category'],
                level=cd['level'],
                language='English',
                duration_weeks=cd['duration_weeks'],
                tags=cd['tags'],
                learning_outcomes=cd.get('learning_outcomes'),
                passing_score=50.0,
                is_published=True,
                is_featured=cd['is_featured'],
                is_archived=False,
                enrollment_open=True,
                requires_approval=False,
                certificate_available=True,
                date_created=now() - timedelta(days=random.randint(30, 90)),
                date_published=now() - timedelta(days=random.randint(20, 80)),
            )
            course.slug = course.generate_slug()
            db.session.add(course)
            courses.append(course)
            print(f'   ✅ {cd["title"]}')

        db.session.flush()

        # ── Create Modules ────────────────────────────────────
        print('\n📖 Creating modules...')

        modules_data = {
            0: [  # Course 1 — Crop Production
                {
                    'title':        'Introduction and Overview',
                    'description':
                        'Welcome to crop production. This module '
                        'introduces the key concepts and sets the '
                        'foundation for the entire course.',
                    'order_number': 1,
                    'is_last':      False,
                    'duration':     30,
                    'notes':
                        'Key point: Always start with a soil test '
                        'before planting any crop.',
                    'objectives':
                        'Describe the importance of crop production\n'
                        'List the major food crops of Nigeria\n'
                        'Identify key factors affecting crop yield',
                },
                {
                    'title':        'Land Preparation Techniques',
                    'description':
                        'Learn the right way to prepare your land '
                        'for planting using traditional and modern methods.',
                    'order_number': 2,
                    'is_last':      False,
                    'duration':     45,
                    'notes':
                        'Tip: Minimum tillage preserves soil structure '
                        'and reduces erosion on sloped land.',
                    'objectives':
                        'Clear and prepare land safely\n'
                        'Choose between tillage methods\n'
                        'Create ridges and planting beds correctly',
                },
                {
                    'title':        'Seed Selection and Planting',
                    'description':
                        'Choosing the right seed and planting it correctly '
                        'is the most critical step in successful crop production.',
                    'order_number': 3,
                    'is_last':      True,
                    'duration':     60,
                    'notes':
                        'Always plant certified seeds when available. '
                        'Test germination rate before bulk planting.',
                    'objectives':
                        'Select high-quality certified seeds\n'
                        'Calculate correct plant spacing\n'
                        'Apply the correct planting depth',
                },
            ],
            1: [  # Course 2 — Soil Science
                {
                    'title':        'Understanding Soil Types',
                    'description':
                        'Nigeria has many different soil types, each with '
                        'different farming potential. Learn to identify '
                        'and work with your soil type.',
                    'order_number': 1,
                    'is_last':      False,
                    'duration':     40,
                    'notes':
                        'Sandy soils drain fast but hold fewer nutrients. '
                        'Clay soils hold nutrients but can become waterlogged.',
                    'objectives':
                        'Identify sandy, clay, and loam soils by feel\n'
                        'Describe the properties of each soil type\n'
                        'Match crops to suitable soil types',
                },
                {
                    'title':        'Soil pH Testing and Correction',
                    'description':
                        'Soil pH determines which nutrients are available '
                        'to crops. Learn to test and correct pH for '
                        'optimal crop production.',
                    'order_number': 2,
                    'is_last':      True,
                    'duration':     50,
                    'notes':
                        'Most Nigerian crops grow best at pH 6.0–7.0. '
                        'Lime raises pH. Sulphur lowers pH.',
                    'objectives':
                        'Use a soil pH test kit accurately\n'
                        'Interpret pH test results\n'
                        'Calculate and apply lime correctly',
                },
            ],
            2: [  # Course 3 — Indigenous Practices
                {
                    'title':        'Introduction to Indigenous Knowledge',
                    'description':
                        'Explore the rich heritage of African agricultural '
                        'knowledge and why preserving it matters for '
                        'long-term food security.',
                    'order_number': 1,
                    'is_last':      False,
                    'duration':     35,
                    'notes':
                        'Indigenous knowledge has been developed over '
                        'thousands of years of careful observation.',
                    'objectives':
                        'Define indigenous agricultural knowledge\n'
                        'Explain why it must be preserved\n'
                        'Identify examples from your own community',
                },
                {
                    'title':        'Intercropping and Companion Planting',
                    'description':
                        'Traditional intercropping systems like the '
                        'Three Sisters maximize land use, reduce pests, '
                        'and improve soil fertility naturally.',
                    'order_number': 2,
                    'is_last':      False,
                    'duration':     55,
                    'notes':
                        'Legumes in intercropping systems fix nitrogen '
                        'from the air, naturally fertilizing the soil.',
                    'objectives':
                        'Describe traditional intercropping systems\n'
                        'Design a simple intercropping plan\n'
                        'Identify compatible crop combinations',
                },
                {
                    'title':        'Indigenous Seed Preservation',
                    'description':
                        'Learn how traditional farmers select, store, '
                        'and preserve seed varieties across seasons '
                        'and generations.',
                    'order_number': 3,
                    'is_last':      True,
                    'duration':     45,
                    'notes':
                        'Store seeds in a cool, dry place with moisture '
                        'absorbers like ash or dried chilli peppers.',
                    'objectives':
                        'Select the best plants for seed saving\n'
                        'Dry and clean seeds correctly\n'
                        'Store seeds safely for next season',
                },
            ],
        }

        all_modules = []
        for course_idx, module_list in modules_data.items():
            course = courses[course_idx]
            for md in module_list:
                module = Module(
                    course_id=course.id,
                    title=md['title'],
                    description=md['description'],
                    learning_objectives=md.get('objectives'),
                    notes=md.get('notes'),
                    order_number=md['order_number'],
                    is_last_module=md['is_last'],
                    is_published=True,
                    is_free_preview=(md['order_number'] == 1),
                    duration_minutes=md['duration'],
                    date_created=now() - timedelta(
                        days=random.randint(10, 60))
                )
                db.session.add(module)
                all_modules.append((course_idx, module))
                print(
                    f'   ✅ [{course.title[:25]}...] '
                    f'Module {md["order_number"]}: {md["title"]}'
                )

        db.session.flush()

        # ── Create Materials ──────────────────────────────────
        print('\n🎬 Creating sample materials...')

        for course_idx, module in all_modules:
            mat = Material(
                module_id=module.id,
                title=f'{module.title} — Study Guide',
                description=(
                    f'Comprehensive study guide for {module.title}. '
                    f'Contains all key concepts, diagrams, and '
                    f'practice questions for this module.'
                ),
                material_type='pdf',
                file_name=f'study_guide_module_{module.id}.pdf',
                stored_file_name=f'seed_guide_{module.id}.pdf',
                file_extension='pdf',
                file_size_bytes=random.randint(500000, 5000000),
                mime_type='application/pdf',
                order_number=1,
                allow_download=True,
                is_published=True,
                date_uploaded=now() - timedelta(
                    days=random.randint(5, 50))
            )
            db.session.add(mat)

        db.session.flush()
        print(f'   ✅ {len(all_modules)} study guide materials created.')

        # ── Create Assignments ────────────────────────────────
        print('\n📝 Creating assignments...')

        assignments_data = [
            {
                'course_idx':       0,
                'title':            'Assignment 1: Crop Production Plan',
                'description':
                    'Develop a detailed crop production plan for a '
                    '1-hectare farm. Include crop selection, land '
                    'preparation timeline, planting schedule, input '
                    'requirements, and expected yield.',
                'instructions':
                    '1. Choose one major crop (maize, cassava, or rice)\n'
                    '2. Create a month-by-month farming calendar\n'
                    '3. Calculate input costs and expected income\n'
                    '4. Submit as a PDF or typed answer below.',
                'days_until_due':   14,
            },
            {
                'course_idx':       1,
                'title':            'Soil pH Testing Field Report',
                'description':
                    'Conduct a soil pH test on a plot of land near you '
                    'and write a detailed report of your findings with '
                    'recommendations for soil amendment.',
                'instructions':
                    '1. Collect soil samples from at least 3 spots\n'
                    '2. Test each sample using a pH kit or indicator\n'
                    '3. Record all readings carefully\n'
                    '4. Write a 300-500 word report\n'
                    '5. Include your amendment recommendations.',
                'days_until_due':   21,
            },
            {
                'course_idx':       2,
                'title':            'Indigenous Knowledge Documentation',
                'description':
                    'Interview an experienced older farmer in your '
                    'community and document at least 3 traditional '
                    'farming practices they use or used in the past.',
                'instructions':
                    '1. Find and interview an older experienced farmer\n'
                    '2. Document at least 3 traditional practices\n'
                    '3. For each: describe it, how it works, and why used\n'
                    '4. Write 400-600 words — photos are a bonus\n'
                    '5. Reflect on how these compare to modern methods.',
                'days_until_due':   30,
            },
        ]

        all_assignments = []
        for ad in assignments_data:
            due  = now() + timedelta(days=ad['days_until_due'])
            asgn = Assignment(
                course_id=courses[ad['course_idx']].id,
                created_by=admin.id,
                title=ad['title'],
                description=ad['description'],
                instructions=ad['instructions'],
                submission_type='both',
                total_marks=100,
                pass_mark=50,
                weight=1.0,
                due_date=due,
                late_submission_allowed=True,
                late_penalty_percent=10.0,
                allowed_file_types='pdf,docx,doc,png,jpg,jpeg',
                max_file_size_mb=10,
                max_submissions=3,
                is_published=True,
                status='published',
                order_number=1,
                date_created=now() - timedelta(days=5),
                date_published=now() - timedelta(days=5)
            )
            db.session.add(asgn)
            all_assignments.append(asgn)
            print(f'   ✅ {ad["title"]}')

        db.session.flush()

        # ── Create Enrollments ────────────────────────────────
        print('\n🎓 Creating enrollments...')

        enrollment_plan = [
            (0, [0, 1, 2]),   # Adewale → all 3 courses
            (1, [0, 1]),      # Fatima  → courses 1 & 2
            (2, [0, 2]),      # Emeka   → courses 1 & 3
            (3, [1]),         # Amina   → course 2 only
            (4, [2]),         # Seun    → course 3 only
        ]

        all_enrollments = []
        for learner_idx, course_indices in enrollment_plan:
            learner = learners[learner_idx]
            for course_idx in course_indices:
                course = courses[course_idx]
                enroll = Enrollment(
                    user_id=learner.id,           # ← correct
                    course_id=course.id,
                    status='active',
                    is_active=True,
                    progress_percent=0.00,
                    modules_completed=0,
                    is_completed=False,
                    certificate_issued=False,
                    date_enrolled=now() - timedelta(
                        days=random.randint(5, 30)),
                    date_approved=now() - timedelta(
                        days=random.randint(5, 30))
                )
                db.session.add(enroll)
                all_enrollments.append(enroll)
                print(
                    f'   ✅ {learner.full_name[:20]} '
                    f'→ {course.title[:30]}...'
                )

        db.session.flush()

        # ── Simulate Progress for Adewale ─────────────────────
        print('\n📈 Simulating learner progress...')

        adewale = learners[0]
        course1 = courses[0]

        adewale_enroll = Enrollment.query.filter_by(
            user_id=adewale.id,
            course_id=course1.id
        ).first()

        course1_modules = [
            m for ci, m in all_modules if ci == 0
        ]

        if adewale_enroll and course1_modules:
            first_module = course1_modules[0]

            prog = Progress(
                user_id=adewale.id,
                module_id=first_module.id,
                course_id=course1.id,
                is_completed=True,
                date_started=now() - timedelta(days=10),
                date_completed=now() - timedelta(days=8),
                last_accessed=now() - timedelta(days=8),
                access_count=3,
                time_spent_minutes=35
            )
            db.session.add(prog)

            total_mods = len(course1_modules)
            adewale_enroll.modules_completed = 1
            adewale_enroll.progress_percent  = round(
                (1 / total_mods) * 100, 2)
            adewale_enroll.last_accessed_module_id = first_module.id

            print(
                f'   ✅ {adewale.full_name} completed '
                f'Module 1 of {course1.title[:30]}...'
            )

        # ── Commit everything ─────────────────────────────────
        db.session.commit()

        # ── Summary ───────────────────────────────────────────
        print('\n' + '=' * 50)
        print('🎉 DATABASE SEEDING COMPLETE')
        print('=' * 50)
        print(f'\n📊 Summary:')
        print(f'   Users       : {User.query.count()} '
              f'(1 admin + {len(learners)} learners)')
        print(f'   Courses     : {Course.query.count()}')
        print(f'   Modules     : {Module.query.count()}')
        print(f'   Materials   : {Material.query.count()}')
        print(f'   Assignments : {Assignment.query.count()}')
        print(f'   Enrollments : {Enrollment.query.count()}')
        print(f'   Progress    : {Progress.query.count()} records')

        print('\n🔑 Login Credentials:')
        print('   Admin   : admin@agrilms.com   | Admin@12345')
        print('   Learner : adewale@example.com | Learner@12345')
        print('   Learner : fatima@example.com  | Learner@12345')
        print('   Learner : emeka@example.com   | Learner@12345')
        print('   Learner : amina@example.com   | Learner@12345')
        print('   Learner : seun@example.com    | Learner@12345')

        print('\n🌐 Start the platform:')
        print('   flask run')
        print('   Visit: http://localhost:5000')
        print()


if __name__ == '__main__':
    seed_database()