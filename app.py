from flask import Flask
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

    return {'replicas': replicas, 'cpu_request': cpu_request, 'mem_request': mem_request}

def get_correct_answers(namespace):
    namespace_value = sum(ord(c) for c in namespace)
    random.seed(namespace_value) # Seeding the random generator with the namespace value
    replicas_choice = random.choice([1, 2, 3, 4, 5])
    cpu_request_choice = random.choice(["250m", "500m"])
    memory_request_choice = random.choice(["512Mi", "768Mi", "1024Mi"])

    return {
        'replicas': replicas_choice,
        'cpu_request': cpu_request_choice,
        'memory_request': memory_request_choice,
    }

@app.route('/')
def main():
    deployment_name = "k8s-deployment-quiz"
    deployment_details = get_deployment_details(deployment_name, namespace)

    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
            namespace = f.read().strip()
    except FileNotFoundError:
        return "Unable to find namespace. Make sure your pod has the necessary permissions."
    
    correct_answers = get_correct_answers(namespace)
    deployment_status = f"""
    Namespace : <span style='color: blue;'>{namespace}</span><br>
    Pod Replica : <span style='color: blue;'>{deployment_details['replicas']}</span><br>
    Pod Resource CPU Request : <span style='color: blue;'>{deployment_details['cpu_request']}</span><br>
    Pod Resource Memory Request : <span style='color: blue;'>{deployment_details['mem_request']}</span><br>
    Environment Variable <b>YOUR_NAME</b> value : <span style='color: blue;'>{os.getenv("YOUR_NAME", "NONE")}</span><br>
    Environment Variable <b>IMAGE_URL</b> value : <span style='color: blue;'>{os.getenv("IMAGE_URL", "NONE")}</span><br>
    """


    quiz_questions = [
        {
            'type': 'fix_choice',
            'question_text': f'1. Set Replica to <span style="color: blue;">{correct_answers["replicas"]}</span>',
            'status': "Pending",
            'key_to_check': 'replicas',
            'correct_answer': correct_answers["replicas"]
        },
        {
            'type': 'fix_choice',
            'question_text': f'2. Set Resource Request (CPU) to <span style="color: blue;">{correct_answers["cpu_request"]}</span>',
            'status': "Pending",
            'key_to_check': 'cpu_request',
            'correct_answer': correct_answers["cpu_request"]
        },
        {
            'type': 'fix_choice',
            'question_text': f'3. Set Resource Request (Memory) to <span style="color: blue;">{correct_answers["memory_request"]}</span>',
            'status': "Pending",
            'key_to_check': 'mem_request',
            'correct_answer': correct_answers["memory_request"]
        },
        {   
            'type': 'free_text',
            'environment_variable': 'YOUR_NAME',
            'question_text': f'4. Set Environment Variable <b>YOUR_NAME</b> to <span style="color: blue;">your name</span>',
            'status': "Pending",
        },
        {   
            'type': 'free_text',
            'environment_variable': 'IMAGE_URL',
            'question_text': f'5. Set Environment Variable <b>IMAGE_URL</b> to <span style="color: blue;">any image you like</span>',
            'status': "Pending",
        }
    ]

    task_status = ""
    for task in quiz_questions:
        if task['type'] == 'fix_choice':
            key_to_check = task['key_to_check']
            if key_to_check and deployment_details[key_to_check] == task['correct_answer']:
                task['status'] = "Correct"
                color = "green"
            else:
                task['status'] = "Incorrect"
                color = "red"

        if task['type'] == 'free_text':
            if os.getenv(task['environment_variable'], "NONE") != "NONE":
                task['status'] = "Correct"
                color = "green"
            else:
                task['status'] = "Incorrect"
                color = "red"
        task_status += f"{task['question_text']} <span style='color: {color}'>({task['status']})</span><br>"
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
            width: 500px;
            margin-bottom: 15px;
        }}
        .task {{
            margin-top: 20px;
            font-weight: bold;
        }}
    </style>
    <img class="image" src="{os.getenv("IMAGE_URL","https://media2.giphy.com/media/xTiIzJSKB4l7xTouE8/giphy.gif")}" alt="Hello There">
    <div class="header">Hello {os.getenv("YOUR_NAME", "there!")}</div>
    <div class="content">
        Let’s play some game!<br>
        We have Kubernetes Deployment here but it doesn’t work properly<br>
        I want you to help me fix this deployment to meet the requirements<br><br>
        <b>Requirement Task</b><br>
        {task_status}
        <br>
        <b>Deployment Status</b><br>
        {deployment_status}
        <br>
        <b>Please make the necessary changes to the Kubernetes deployment and refresh this page to verify.</b>
    </div>
    """

    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
