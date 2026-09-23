import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Note, Tag, Relationship
from app.services.similarity_service import update_relationships_for_note

app = create_app()

with app.app_context():
    db.create_all()
    
    if User.query.first():
        print("Database already seeded. Skipping.")
        sys.exit(0)
    
    user = User(name="Demo User", email="demo@thoughtgarden.app")
    user.set_password("demo1234")
    db.session.add(user)
    db.session.flush()
    
    tags_data = [
        "Machine Learning", "Neural Networks", "Deep Learning", "NLP",
        "Computer Vision", "Data Science", "AI", "Research",
        "Cybersecurity", "Network Security", "Intrusion Detection",
        "Software Engineering", "Agile", "Testing",
        "Operating Systems", "CPU Scheduling", "Process Management", "Deadlocks"
    ]
    
    tags = {}
    for tag_name in tags_data:
        tag = Tag(name=tag_name)
        db.session.add(tag)
        tags[tag_name] = tag
    
    db.session.flush()
    
    notes_data = [
        {
            "title": "Machine Learning Fundamentals",
            "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves. The process begins with observations or data, such as examples, direct experience, or instruction, to look for patterns in data and make better decisions in the future.",
            "category": "AI",
            "tags": ["Machine Learning", "AI", "Research"],
            "is_pinned": True,
            # Backdated so the demo garden can actually show a 'tree' stage
            # (growth_service.py needs both age AND connections - this note
            # is the AI cluster's hub, so it reliably ends up well-connected
            # after relationship discovery below). Doesn't touch the scoring
            # logic itself, just gives one note a realistic age to combine
            # with real connections.
            "days_old": 20
        },
        {
            "title": "Neural Networks Explained",
            "content": "Neural networks are computing systems inspired by biological neural networks that constitute animal brains. They consist of layers of interconnected nodes or neurons that process information using connectionist approaches. Neural networks can learn and model nonlinear relationships and complex patterns in data. They are the foundation of deep learning and have revolutionized fields like computer vision and natural language processing.",
            "category": "AI",
            "tags": ["Neural Networks", "Deep Learning", "AI"]
        },
        {
            "title": "Deep Learning and Representation Learning",
            "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to progressively extract higher-level features from raw input. It has achieved remarkable success in image recognition, speech recognition, and natural language processing. Deep learning models can automatically learn hierarchical representations of data, making them powerful for complex tasks.",
            "category": "AI",
            "tags": ["Deep Learning", "Neural Networks", "Machine Learning"]
        },
        {
            "title": "Natural Language Processing Techniques",
            "content": "Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language. It focuses on how to program computers to process and analyze large amounts of natural language data. Modern NLP uses deep learning models like transformers to understand and generate human language.",
            "category": "AI",
            "tags": ["NLP", "Deep Learning", "AI"]
        },
        {
            "title": "Computer Vision Applications",
            "content": "Computer vision is an interdisciplinary scientific field that deals with how computers can gain high-level understanding from digital images or videos. From the perspective of engineering, it seeks to understand and automate tasks that the human visual system can do. Computer vision tasks include methods for acquiring, processing, analyzing, and understanding digital images.",
            "category": "AI",
            "tags": ["Computer Vision", "Deep Learning", "AI"]
        },
        {
            "title": "Data Science and Analytics",
            "content": "Data science is an interdisciplinary field that uses scientific methods, processes, algorithms, and systems to extract knowledge and insights from structured and unstructured data. It combines aspects of statistics, mathematics, programming, and domain expertise to analyze and interpret complex data. Data science is essential for making data-driven decisions in modern organizations.",
            "category": "AI",
            "tags": ["Data Science", "Machine Learning", "AI"]
        },
        {
            "title": "Intrusion Detection Systems",
            "content": "Intrusion detection systems (IDS) are devices or software applications that monitor a network or systems for malicious activity or policy violations. They are a key part of network security infrastructure. IDS can detect various types of attacks including port scanning, denial of service attacks, and malware infections. Modern IDS use machine learning algorithms to improve detection accuracy.",
            "category": "Cybersecurity",
            "tags": ["Intrusion Detection", "Cybersecurity", "Network Security"]
        },
        {
            "title": "Network Security Fundamentals",
            "content": "Network security involves policies, practices, and devices designed to protect the integrity, confidentiality, and availability of computer networks and data. It includes both hardware and software technologies. Effective network security targets a variety of threats and stops them from entering or spreading on a network. Common measures include firewalls, encryption, and access controls.",
            "category": "Cybersecurity",
            "tags": ["Network Security", "Cybersecurity", "Intrusion Detection"]
        },
        {
            "title": "Adaptive Threat Detection",
            "content": "Adaptive threat detection is an approach to cybersecurity that uses artificial intelligence and machine learning to identify and respond to evolving threats. It continuously learns from network traffic and user behavior to detect anomalies and potential security breaches. This approach is particularly effective against advanced persistent threats and zero-day attacks.",
            "category": "Cybersecurity",
            "tags": ["Cybersecurity", "Machine Learning", "Network Security"]
        },
        {
            "title": "Agile Software Development",
            "content": "Agile software development is an approach to software development under which requirements and solutions evolve through the collaborative effort of self-organizing and cross-functional teams. It promotes adaptive planning, evolutionary development, early delivery, and continuous improvement. Agile encourages rapid and flexible response to change.",
            "category": "Software Engineering",
            "tags": ["Agile", "Software Engineering"]
        },
        {
            "title": "Software Requirements Engineering",
            "content": "Software requirements engineering is the process of determining, analyzing, documenting, validating, and managing the needs and requirements of software systems. It involves elicitation, analysis, specification, and verification of requirements. Good requirements engineering is crucial for successful software projects as it ensures the final product meets user needs.",
            "category": "Software Engineering",
            "tags": ["Software Engineering", "Agile"]
        },
        {
            "title": "Software Testing Strategies",
            "content": "Software testing is an investigation conducted to provide stakeholders with information about the quality of the product or service under test. Testing strategies include unit testing, integration testing, system testing, and acceptance testing. Modern approaches also include test-driven development (TDD) and behavior-driven development (BDD).",
            "category": "Software Engineering",
            "tags": ["Testing", "Software Engineering"]
        },
        {
            "title": "CPU Scheduling Algorithms",
            "content": "CPU scheduling is the process of selecting a process from the ready queue and allocating the CPU to it. Various scheduling algorithms exist including First-Come-First-Served (FCFS), Shortest Job Next (SJN), Round Robin (RR), and Priority Scheduling. The choice of algorithm affects system performance, response time, and throughput.",
            "category": "Operating Systems",
            "tags": ["CPU Scheduling", "Operating Systems", "Process Management"]
        },
        {
            "title": "Process Management in Operating Systems",
            "content": "Process management in operating systems involves managing processes from creation to termination. It includes process scheduling, synchronization, and communication. An operating system manages multiple processes simultaneously, ensuring they share resources efficiently and don't interfere with each other. Key concepts include process states, context switching, and inter-process communication.",
            "category": "Operating Systems",
            "tags": ["Process Management", "Operating Systems", "CPU Scheduling"]
        },
        {
            "title": "Deadlock Prevention and Avoidance",
            "content": "A deadlock is a situation where two or more processes are unable to proceed because each is waiting for a resource held by another. Deadlock prevention involves designing systems to eliminate one of the four necessary conditions: mutual exclusion, hold and wait, no preemption, and circular wait. Deadlock avoidance uses algorithms like Banker's algorithm to dynamically check resource allocation.",
            "category": "Operating Systems",
            "tags": ["Deadlocks", "Operating Systems", "Process Management"]
        },
        {
            "title": "Research Idea: Adaptive Cybersecurity Systems",
            "content": "This research explores the development of adaptive cybersecurity systems that use machine learning to continuously improve threat detection. The system would analyze network patterns, user behavior, and threat intelligence to dynamically adjust security policies. This approach could significantly reduce response time to new threats and improve overall security posture.",
            "category": "Research",
            "tags": ["Research", "Cybersecurity", "Machine Learning", "AI"],
            "is_pinned": True
        },
        {
            "title": "Paper Notes: Transformer Architecture",
            "content": "Notes from research on Transformer architecture: Transformers use self-attention mechanisms to process input sequences in parallel, unlike RNNs which process sequentially. The key innovation is the multi-head attention mechanism which allows the model to focus on different parts of the input simultaneously. Transformers have become the foundation for models like BERT, GPT, and T5, achieving state-of-the-art results in NLP tasks.",
            "category": "Research",
            "tags": ["Research", "NLP", "Deep Learning", "Neural Networks"]
        }
    ]
    
    for note_data in notes_data:
        note = Note(
            user_id=user.id,
            title=note_data["title"],
            content=note_data["content"],
            category=note_data.get("category"),
            source_type="manual",
            is_pinned=note_data.get("is_pinned", False)
        )
        if "days_old" in note_data:
            # Note.created_at otherwise defaults to utcnow() at insert time
            # (see app/models.py) - explicitly setting it here is what lets
            # a demo note be old enough to reach the 'tree' growth stage.
            note.created_at = datetime.utcnow() - timedelta(days=note_data["days_old"])
        db.session.add(note)
        db.session.flush()
        
        for tag_name in note_data.get("tags", []):
            if tag_name in tags:
                note.tags.append(tags[tag_name])
    
    db.session.commit()
    
    print("Seed data created. Discovering relationships automatically...")
    
    notes = Note.query.filter_by(user_id=user.id).all()
    
    for note in notes:
        try:
            update_relationships_for_note(note)
        except Exception as e:
            print(f"Warning: Could not update relationships for note {note.id}: {e}")
    
    db.session.commit()
    
    rel_count = Relationship.query.count()
    print(f"\nSeeding complete!")
    print(f"  - {len(notes_data)} notes created")
    print(f"  - {rel_count} relationships discovered")
    print(f"\nLogin with:")
    print(f"  Email: demo@thoughtgarden.app")
    print(f"  Password: demo1234")
