TRIVIA_TOPICS = {
    "cs": [
        {"question": "What language is based on a snake?", "answer": "Python"},
        {"question": "What language is based on a coffee bean?", "answer": "Java"},
    ],
    "all_topics": [],  # Placeholder; will be populated dynamically if all_topics is selected
}

# Populate "all_topics" with questions from all other topics
for topic, questions in TRIVIA_TOPICS.items():
    if topic != "all_topics":
        TRIVIA_TOPICS["all_topics"].extend(questions)