from flask import Flask, request
from kubernetes import client, config
import os
import random

app = Flask(__name__)

def get_deployment_details(deployment_name, namespace):
    config.load_incluster_config() # Loads the in-cluster configuration; use config.load_kube_config() for local development
    apps_v1_api = client.AppsV1Api()

    deployment = apps_v1_api.read_namespaced_deployment(name=deployment_name, namespace=namespace)
    replicas = deployment.status.replicas
    cpu_request = deployment.spec.template.spec.containers[0].resources.requests['cpu']
    mem_request = deployment.spec.template.spec.containers[0].resources.requests['memory']
    labels = deployment.metadata.labels

    return {'replicas': replicas, 'cpu_request': cpu_request, 'mem_request': mem_request, 'labels': labels}

@app.route('/')
def hello_world():
    namespace = os.getenv("NAMESPACE")
    random.seed(hash(namespace))

    # Define correct answers and quiz questions
    correct_answers = {
        'replicas': random.randint(1, 3),
        'cpu_request': random.choice(["250", "300", "350m"]),
        'memory_request': random.choice(["256Mi", "512Mi"]),
        'your_name': os.getenv("YOUR_NAME"),
        'image': os.getenv("IMAGE")
    }

    quiz_questions = [
        ('Set Pod Replica', 'replicas', get_deployment_details()['replicas']),
        ('Set Pod Resource Request (CPU)', 'cpu_request', get_deployment_details()['cpu_request']),
        ('Set Pod Resource Request (Memory)', 'memory_request', get_deployment_details()['memory_request']),
        ('Set Pod Environment Variable: YOUR_NAME', 'your_name', os.getenv("YOUR_NAME")),
        ('Set Pod Environment Variable: IMAGE', 'image', os.getenv("IMAGE")),
    ]

    # Shuffle the questions based on the namespace seed
    random.shuffle(quiz_questions)

    # Get the current question number from the URL
    current_question_number = int(request.args.get('question', 0))

    # Check if the previous answer was correct
    if current_question_number > 0:
        previous_question_key = quiz_questions[current_question_number - 1][1]
        previous_correct_answer = correct_answers[previous_question_key]
        previous_user_answer = quiz_questions[current_question_number - 1][2]
        if previous_correct_answer != previous_user_answer:
            return f'Incorrect answer for {quiz_questions[current_question_number - 1][0]}! Try again.'

    # Show the current question
    current_question, current_question_key, _ = quiz_questions[current_question_number]
    current_correct_answer = correct_answers[current_question_key]
    current_user_answer = request.args.get(current_question_key)
    if current_user_answer is not None and current_correct_answer != current_user_answer:
        return f'Incorrect answer for {current_question}! Try again.'

    # Move to the next question if the current answer is correct
    if current_user_answer is not None:
        current_question_number += 1

    # Return the final result if all questions are answered
    if current_question_number >= len(quiz_questions):
        return 'Congratulations! You have completed the quiz.'

    # Show the next question
    next_question, _, _ = quiz_questions[current_question_number]
    return f'Next question: {next_question}. <a href="/?question={current_question_number}">Click here to continue</a>'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
