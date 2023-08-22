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
def main():
    deployment_name = "k8s-deployment-quiz"

    # Get namespace
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
            namespace = f.read().strip()
    except FileNotFoundError:
        return "Unable to find namespace. Make sure your pod has the necessary permissions."

    # Use namespace as a seed for randomization
    random.seed(hash(namespace))

    # Define correct answers
    correct_answers = {
        'replicas': random.choice([1, 2, 3]),
        'cpu_request': random.choice(["250", "300", "350m"]),
        'memory_request': random.choice(["256Mi", "512Mi"]), # Change to match 'memory_request'
        'your_name': os.getenv("YOUR_NAME"),
        'image': os.getenv("IMAGE")
    }

    # Quiz questions
    quiz_questions = [
        (f'Set Pod Replica to {correct_answers["replicas"]}', 'replicas'),
        (f'Set Pod Resource Request (CPU) to {correct_answers["cpu_request"]}', 'cpu_request'),
        (f'Set Pod Resource Request (Memory) to {correct_answers["memory_request"]}', 'memory_request'),
        (f'Set Pod Environment Variable: YOUR_NAME to {correct_answers["your_name"]}', 'your_name'),
        (f'Set Pod Environment Variable: IMAGE to {correct_answers["image"]}', 'image'),
    ]

    # Shuffle the questions based on the namespace seed
    random.shuffle(quiz_questions)

    # Get the current question number from the URL
    current_question_number = int(request.args.get('question', 0))

    # Check if the previous answer was correct
    if current_question_number > 0:
        previous_question_key = quiz_questions[current_question_number - 1][1]
        previous_correct_answer = correct_answers[previous_question_key]
        deployment_details = get_deployment_details(deployment_name, namespace)
        previous_user_answer = str(deployment_details[previous_question_key] if previous_question_key in deployment_details else os.getenv(previous_question_key))
        if previous_correct_answer != previous_user_answer:
            return f'Incorrect answer for {quiz_questions[current_question_number - 1][0]}! Try again.'

    # Return the final result if all questions are answered
    if current_question_number >= len(quiz_questions):
        return 'Congratulations! You have completed the quiz.'

    # Show the current question
    current_question, current_question_key = quiz_questions[current_question_number]
    deployment_details = get_deployment_details(deployment_name, namespace)
    current_status = deployment_details[current_question_key] if current_question_key in deployment_details else os.getenv(current_question_key)

    # Constructing the HTML output
    output = f"""
    Hello, {os.getenv("YOUR_NAME")}
    <img src="{os.getenv("IMAGE")}" alt="Hello There">

    Let’s play some game!
    We have Kubernetes Deployment here but it doesn’t work properly
    I want you to help me fix this deployment to meet the requirements 

    Deployment Status
    {current_question}: {current_status}

    Task
    Task{current_question_number + 1}: {current_question} (Pending)
    
    Please make the necessary changes to the Kubernetes deployment and refresh this page to verify.
    """

    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
