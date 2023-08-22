from flask import Flask, request, redirect
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

def get_correct_answers(namespace):
    namespace_value = sum(ord(c) for c in namespace)
    replicas_choice = [1, 2, 3][namespace_value % 3]
    cpu_request_choice = ["250", "300", "350m"][namespace_value % 3]
    memory_request_choice = ["256Mi", "512Mi"][namespace_value % 2]
    
    return {
        'replicas': replicas_choice,
        'cpu_request': cpu_request_choice,
        'memory_request': memory_request_choice,
        'your_name': os.getenv("YOUR_NAME"),
        'image': os.getenv("IMAGE")
    }

@app.route('/')
def main():
    deployment_name = "k8s-deployment-quiz"

    # Get namespace
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
            namespace = f.read().strip()
    except FileNotFoundError:
        return "Unable to find namespace. Make sure your pod has the necessary permissions."

    correct_answers = get_correct_answers(namespace)

    # Quiz questions
    quiz_questions = [
        (f'Set Pod Replica to {correct_answers["replicas"]}', 'replicas'),
        (f'Set Pod Resource Request (CPU) to {correct_answers["cpu_request"]}', 'cpu_request'),
        (f'Set Pod Resource Request (Memory) to {correct_answers["memory_request"]}', 'memory_request'),
        (f'Set Pod Environment Variable: YOUR_NAME to {correct_answers["your_name"]}', 'your_name'),
        (f'Set Pod Environment Variable: IMAGE to {correct_answers["image"]}', 'image'),
    ]

    # Shuffle the questions based on the namespace seed
    seed_value = hash(namespace)
    random.seed(seed_value)
    random.shuffle(quiz_questions, random=lambda: seed_value % (10 ** 9) / (10 ** 9))

    # Get the current question number from the URL
    current_question_number = int(request.args.get('question', 0))

    if current_question_number > 0:
        previous_question_key = quiz_questions[current_question_number - 1][1]
        previous_correct_answer = correct_answers[previous_question_key]
        deployment_details = get_deployment_details(deployment_name, namespace)
        previous_user_answer = str(deployment_details[previous_question_key] if previous_question_key in deployment_details else os.getenv(previous_question_key))
        if previous_correct_answer == previous_user_answer:
            return redirect(f"/?question={current_question_number}")
        else:
            return f'Incorrect answer for {quiz_questions[current_question_number - 1][0]}! Try again.'

    # Return the final result if all questions are answered
    if current_question_number >= len(quiz_questions):
        return 'Congratulations! You have completed the quiz.'

    # Show the current question
    deployment_details = get_deployment_details(deployment_name, namespace)
    current_question, current_question_key = quiz_questions[current_question_number]
    current_status = deployment_details[current_question_key] if current_question_key in deployment_details else os.getenv(current_question_key)
    completed_tasks = ""
    for i in range(current_question_number):
        question_text, question_key = quiz_questions[i]
        status = get_deployment_details(deployment_name, namespace)[question_key] if question_key in deployment_details else os.getenv(question_key)
        completed_tasks += f"Task{i + 1}: {question_text} (Success) - Deployment Status: {status}<br>"

        # Constructing the HTML output
    output = f"""
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .header {{
            font-size: 24px;
            font-weight: bold;
        }}
        .content {{
            font-size: 18px;
            line-height: 1.5;
        }}
        .image {{
            width: 100px;
            margin-bottom: 15px;
        }}
        .task {{
            margin-top: 20px;
            font-weight: bold;
        }}
    </style>
    <div class="header">Hello, {os.getenv("YOUR_NAME")}</div>
    <img class="image" src="{os.getenv("IMAGE")}" alt="Hello There">
    <div class="content">
        Let’s play some game!<br>
        We have Kubernetes Deployment here but it doesn’t work properly<br>
        I want you to help me fix this deployment to meet the requirements<br><br>

        Deployment Status<br>
        {completed_tasks}
        {current_question}: {current_status}<br><br>

        <div class="task">Task</div>
        Task{current_question_number + 1}: {current_question} (Pending)<br><br>
    </div>

    Please make the necessary changes to the Kubernetes deployment and refresh this page to verify.
    """

    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
