# Agile Quiz Question Bank System --- Windows CI/CD Lab Guide

A start-to-finish practice guide for **VS Code + GitHub + Jenkins (7
stages) + Docker Hub + Kubernetes** on **Windows PowerShell/CMD**.

**Repository:**
https://github.com/shivaranjini569/quiz-question-bank-system\
**Docker Hub:** `shivaranjini569/quiz-question-bank`\
**Project folder:** `D:\Agile-Quiz-Question-Bank`

> This is a practice seven-stage Jenkins pipeline. Follow your
> examiner's exact stages if they differ. The faculty's Kubernetes PDF
> uses GitHub Actions, but the Kubernetes Deployment/Service commands
> are the same. All commands below are Windows PowerShell unless a
> section explicitly says otherwise. No Ubuntu or WSL commands.

## 0. Understand the project

  Version   Feature                   Flask port Docker tag
  --------- ----------------------- ------------ ------------
  v1        Add questions                   5001 `v1`
  v2        Edit/delete questions           5002 `v2`
  v3        View questions                  5003 `v3`

The existing Flask source files load `data/questions.json` relative to
the **project root**. The Dockerfiles below preserve that layout.
**Important:** separate containers have separate copies of this JSON
file. This guide is suitable for a lab demo, but it does **not** make
all three versions share live changes or provide production-safe
persistent storage.

## 1. Prerequisites and verification

Install VS Code, Git for Windows, Python 3.12, Docker Desktop, Jenkins
(Windows installation/service or WAR), and `kubectl`. Sign in to GitHub
and Docker Hub.

1.  Open **Docker Desktop**. Wait until the Docker Engine is running.
2.  In Docker Desktop, enable **Kubernetes** and wait for it to become
    ready.
3.  Open **VS Code → Terminal → New Terminal → PowerShell**.
4.  Run:

``` powershell
git --version
python --version
docker --version
docker info
kubectl version --client
kubectl config current-context
kubectl get nodes
```

**Expected:** `docker info` displays a **Server** section,
`kubectl config current-context` displays `docker-desktop`, and
`kubectl get nodes` shows a node in `Ready` status. **Do not continue
with Docker/Kubernetes steps until these work.**

If `docker` is not recognized on your personal Windows setup,
temporarily add its known location to the current PowerShell terminal:

``` powershell
$env:Path += ";C:\Users\Shivaranjini\AppData\Local\Programs\DockerDesktop\resources\bin"
docker --version
```

This fixes only the command path; it does **not** fix a Docker Desktop
engine that cannot start.

If `kubectl` reports another context, inspect contexts before switching:

``` powershell
kubectl config get-contexts
kubectl config use-context docker-desktop
kubectl get nodes
```

Use the context switch only if `docker-desktop` is actually listed.

## 2. Get the project into VS Code

**Option A --- project already exists locally:**

``` powershell
cd D:\Agile-Quiz-Question-Bank
code .
git status
```

**Option B --- clone into a new folder** (do not overwrite the existing
folder):

``` powershell
cd D:\
git clone https://github.com/shivaranjini569/quiz-question-bank-system.git Quiz-Question-Bank-Lab
cd D:\Quiz-Question-Bank-Lab
code .
```

The public GitHub repository currently contains `v1`, `v2`, `v3`,
`data`, and `.gitignore`. The source files are `v1/app.py`, `v2/app.py`,
`v3/app.py`, with matching `requirements.txt` and `templates` folders.
The Dockerfiles and Kubernetes/Jenkins files in this guide must be added
if absent.

### Target project layout

``` text
Agile-Quiz-Question-Bank/
├── data/
│   └── questions.json
├── v1/
│   ├── app.py
│   ├── requirements.txt
│   ├── questions.json
│   ├── templates/
│   │   └── index.html
│   └── DockerFile
├── v2/
│   ├── app.py
│   ├── requirements.txt
│   ├── questions.json
│   ├── templates/
│   │   └── index.html
│   └── DockerFile
├── v3/
│   ├── app.py
│   ├── requirements.txt
│   ├── questions.json
│   ├── templates/
│   │   └── index.html
│   └── DockerFile
├── tests/
│   └── test_smoke.py
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── Jenkinsfile
├── .dockerignore
├── .gitignore
└── README.md
```

**VS Code file creation:** Right-click the project folder → **New
Folder** / **New File**. Paste each code block into the matching file,
then press **Ctrl+S**. Dockerfiles are named **`DockerFile`** (capital
`F`) in these commands; preserve that exact spelling.

## 3. Test the Flask versions locally

Open three **separate** VS Code PowerShell terminals. From the project
root:

**Terminal 1:**

``` powershell
cd D:\Agile-Quiz-Question-Bank
python -m pip install -r v1/requirements.txt
python v1/app.py
```

Open http://localhost:5001 and add a question.

**Terminal 2:**

``` powershell
cd D:\Agile-Quiz-Question-Bank
python v2/app.py
```

Open http://localhost:5002 and check edit/delete.

**Terminal 3:**

``` powershell
cd D:\Agile-Quiz-Question-Bank
python v3/app.py
```

Open http://localhost:5003 and view the questions.

Stop each server with **Ctrl+C**. All three local Python programs read
the same root `data/questions.json`.

### Create `tests/test_smoke.py`

This smoke test checks that each Flask version can render its home page
without modifying questions.

``` python
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class QuizSmokeTests(unittest.TestCase):
    def test_all_home_pages(self):
        for version in ("v1", "v2", "v3"):
            with self.subTest(version=version):
                path = ROOT / version / "app.py"
                spec = importlib.util.spec_from_file_location(f"quiz_{version}", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                response = module.app.test_client().get("/")
                self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
```

Run from the project root:

``` powershell
python -m unittest discover -s tests -v
```

Expected: `Ran 1 test ... OK`. If a version fails, fix its
source/template/data file before proceeding.

## 4. Create Dockerfiles

**Why these COPY paths matter:** Your Python code uses
`parent.parent / "data" / "questions.json"`. The images must therefore
contain `/app/v1/app.py` and `/app/data/questions.json` (similarly for
v2/v3).

### `v1/DockerFile`

``` dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY v1/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY v1/ /app/v1/
COPY data/ /app/data/
WORKDIR /app/v1
EXPOSE 5001
CMD ["python", "app.py"]
```

### `v2/DockerFile`

``` dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY v2/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY v2/ /app/v2/
COPY data/ /app/data/
WORKDIR /app/v2
EXPOSE 5002
CMD ["python", "app.py"]
```

### `v3/DockerFile`

``` dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY v3/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY v3/ /app/v3/
COPY data/ /app/data/
WORKDIR /app/v3
EXPOSE 5003
CMD ["python", "app.py"]
```

### `.dockerignore` (project root)

``` gitignore
.git/
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
```

**Build from the project root**, not from inside `v1`/`v2`/`v3`, because
the Dockerfiles copy the shared root `data/` folder:

``` powershell
docker build -f v1/DockerFile -t shivaranjini569/quiz-question-bank:v1 .
docker build -f v2/DockerFile -t shivaranjini569/quiz-question-bank:v2 .
docker build -f v3/DockerFile -t shivaranjini569/quiz-question-bank:v3 .
docker images
```

Expected: three image tags `v1`, `v2`, `v3`.

### Run and verify the containers

``` powershell
docker run -d --name quiz-v1 -p 5001:5001 shivaranjini569/quiz-question-bank:v1
docker run -d --name quiz-v2 -p 5002:5002 shivaranjini569/quiz-question-bank:v2
docker run -d --name quiz-v3 -p 5003:5003 shivaranjini569/quiz-question-bank:v3
docker ps
```

Open http://localhost:5001, http://localhost:5002, and
http://localhost:5003.

``` powershell
docker logs quiz-v1
docker logs quiz-v2
docker logs quiz-v3
```

Stop and remove the containers after the demo:

``` powershell
docker stop quiz-v1 quiz-v2 quiz-v3
docker rm quiz-v1 quiz-v2 quiz-v3
```

If a container name already exists, inspect `docker ps -a` before
removing it. Do not delete unrelated containers.

## 5. Push code to GitHub

### `.gitignore`

``` gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
```

In the project root:

``` powershell
git status
git add .
git commit -m "Add Docker, Jenkins, tests and Kubernetes lab files"
git branch -M main
git remote -v
```

If `origin` already points to
`https://github.com/shivaranjini569/quiz-question-bank-system.git`, do
**not** add it again. If it is missing:

``` powershell
git remote add origin https://github.com/shivaranjini569/quiz-question-bank-system.git
```

Push:

``` powershell
git push -u origin main
```

Open https://github.com/shivaranjini569/quiz-question-bank-system and
verify the files. If the remote contains newer work, fetch/pull and
reconcile before pushing; do not force-push.

## 6. Docker Hub login and manual push

Create or verify the **public** Docker Hub repository
`shivaranjini569/quiz-question-bank`.

``` powershell
docker login
docker push shivaranjini569/quiz-question-bank:v1
docker push shivaranjini569/quiz-question-bank:v2
docker push shivaranjini569/quiz-question-bank:v3
```

Confirm all three tags at
https://hub.docker.com/r/shivaranjini569/quiz-question-bank/tags.

If `insufficient_scope` appears, ensure the login is for
`shivaranjini569` and that the account/token has write access to that
repository. If Docker Desktop says it cannot start, fix the Docker
Engine first; repeating `docker login` will not solve it. **Never paste
a token into README or GitHub.**

## 7. Jenkins --- sample seven-stage pipeline

The following is a **sample Jenkins pipeline** for a Windows Jenkins
agent. The stages are:

1.  Checkout
2.  Install Dependencies
3.  Test
4.  Build Images
5.  Docker Hub Login
6.  Push Images
7.  Kubernetes Deploy

**Prerequisites for Jenkins:** Jenkins is running,
Git/Python/Docker/kubectl are available to the Jenkins Windows agent,
Docker Desktop is running, and the agent can access the `docker-desktop`
Kubernetes context. If Jenkins runs as a Windows service under a
different account, it may **not** see your interactive user's Docker
credentials or kubeconfig. Configure the agent under an authorized
Windows account rather than assuming they are shared.

### Add Docker Hub credentials in Jenkins

Open http://localhost:8080 → **Manage Jenkins → Credentials → System →
Global credentials → Add Credentials**.

-   Kind: **Username with password**
-   Username: `shivaranjini569`
-   Password: your Docker Hub **Personal Access Token** with write
    permission
-   ID: `dockerhub-credentials`

Do not store the token in GitHub files.

### Create `Jenkinsfile` at the project root

``` groovy
pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        IMAGE = 'shivaranjini569/quiz-question-bank'
    }

    stages {
        stage('1 - Checkout') {
            steps {
                checkout scm
            }
        }

        stage('2 - Install Dependencies') {
            steps {
                bat 'python --version'
                bat 'python -m pip install -r v1/requirements.txt'
            }
        }

        stage('3 - Test') {
            steps {
                bat 'python -m unittest discover -s tests -v'
            }
        }

        stage('4 - Build Images') {
            steps {
                bat 'docker build -f v1/DockerFile -t %IMAGE%:v1 .'
                bat 'docker build -f v2/DockerFile -t %IMAGE%:v2 .'
                bat 'docker build -f v3/DockerFile -t %IMAGE%:v3 .'
            }
        }

        stage('5 - Docker Hub Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_TOKEN'
                )]) {
                    bat '@echo off\r\n echo %DOCKER_TOKEN% | docker login -u %DOCKER_USER% --password-stdin'
                }
            }
        }

        stage('6 - Push Images') {
            steps {
                bat 'docker push %IMAGE%:v1'
                bat 'docker push %IMAGE%:v2'
                bat 'docker push %IMAGE%:v3'
            }
        }

        stage('7 - Kubernetes Deploy') {
            steps {
                bat 'kubectl apply -f k8s/deployment.yaml'
                bat 'kubectl apply -f k8s/service.yaml'
                bat 'kubectl rollout status deployment/quiz-question-bank --timeout=180s'
                bat 'kubectl get pods'
                bat 'kubectl get services'
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed; check stage results and console output.'
        }
    }
}
```

**Note:** For a production Jenkins setup, prefer a dedicated
credentials-aware Docker login mechanism and a uniquely versioned image
tag. The above is a classroom example. Jenkins may require the
**Credentials Binding** plugin for `withCredentials`.

### Create the Jenkins job

1.  Open http://localhost:8080.
2.  Click **New Item**.
3.  Enter `Quiz-Question-Bank-CICD`.
4.  Select **Pipeline** → OK.
5.  Under **Pipeline**, choose **Pipeline script from SCM**.
6.  SCM: **Git**.
7.  Repository URL:
    `https://github.com/shivaranjini569/quiz-question-bank-system.git`.
8.  Branch specifier: `*/main`.
9.  Script Path: `Jenkinsfile`.
10. Save → **Build Now**.
11. Open **Console Output** and check each of the seven stages.

**Expected:** each stage passes, the three images are visible in Docker
Hub, and Kubernetes resources are created. A red stage must be diagnosed
before claiming success.

## 8. Kubernetes --- faculty-style deployment and service

The faculty guide uses separate YAML files, `kubectl apply`,
`kubectl rollout status`, `kubectl get pods`, and
`kubectl get services`. We adapt those to your v1 image and port
**5001**.

**Important:** Because your app writes to a local JSON file, we use **1
replica** for functional correctness. The faculty's sample uses 2
replicas for a stateless demo. Two quiz Pods without shared persistent
storage can have inconsistent question lists.

### Create `k8s/deployment.yaml`

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quiz-question-bank
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quiz-question-bank
  template:
    metadata:
      labels:
        app: quiz-question-bank
    spec:
      containers:
        - name: quiz-question-bank
          image: shivaranjini569/quiz-question-bank:v1
          imagePullPolicy: Always
          ports:
            - containerPort: 5001
```

### Create `k8s/service.yaml`

``` yaml
apiVersion: v1
kind: Service
metadata:
  name: quiz-question-bank-service
spec:
  type: NodePort
  selector:
    app: quiz-question-bank
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5001
      nodePort: 30081
```

### Deploy from VS Code PowerShell, at project root

``` powershell
kubectl config current-context
kubectl get nodes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/quiz-question-bank --timeout=180s
kubectl get deployments
kubectl get pods
kubectl get services
kubectl get all
```

**Expected:** Deployment `quiz-question-bank` has `1/1` ready, Pod
status is `Running`, and Service has NodePort `30081`.

Open http://localhost:30081.

If NodePort is not reachable, use port forwarding in a separate
PowerShell terminal:

``` powershell
kubectl port-forward service/quiz-question-bank-service 5001:80
```

Keep that terminal open, then visit http://localhost:5001.

### Demonstrate scaling (optional)

``` powershell
kubectl scale deployment quiz-question-bank --replicas=2
kubectl get deployments
kubectl get pods
kubectl scale deployment quiz-question-bank --replicas=1
```

This demonstrates Kubernetes scaling, **not** shared-data correctness.
Restore 1 replica afterward.

### Demonstrate an update (optional)

For a safe classroom update, first publish a new **v1-compatible** image
with a new tag, for example `v1-update`, retaining port 5001 and the
same application structure. Then run:

``` powershell
kubectl set image deployment/quiz-question-bank quiz-question-bank=shivaranjini569/quiz-question-bank:v1-update
kubectl rollout status deployment/quiz-question-bank
kubectl get pods
kubectl rollout history deployment/quiz-question-bank
```

**Do not** switch this deployment directly to the v2 tag without also
changing its port and Service configuration: v2 listens on 5002. In
addition, your v1/v2/v3 are different features, not necessarily
sequential upgrades of the same interface.

### Troubleshooting

``` powershell
kubectl get all
kubectl describe deployment quiz-question-bank
kubectl get pods
kubectl logs deployment/quiz-question-bank
kubectl get events --sort-by=.metadata.creationTimestamp
```

If you need to inspect a specific Pod:

``` powershell
kubectl describe pod YOUR_ACTUAL_POD_NAME
```

Common diagnoses:

  -----------------------------------------------------------------------
  Error                               Meaning / next check
  ----------------------------------- -----------------------------------
  `ImagePullBackOff`                  Check image tag, Docker Hub
                                      repository visibility, and whether
                                      the image was pushed.

  `CrashLoopBackOff`                  Check `kubectl logs`; verify Flask
                                      files and templates.

  `Pending`                           Check `kubectl describe pod` and
                                      cluster resources.

  `connection refused`                Check Docker Desktop Kubernetes,
                                      context, Pods, and Service ports.

  Browser shows no app                Try `kubectl port-forward`; check
                                      Pod readiness and Service selector.
  -----------------------------------------------------------------------

### Clean up only the lab resources

``` powershell
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
```

## 9. Screenshot checklist for the assessment

Take screenshots only after verifying success:

1.  VS Code folder structure with `v1`, `v2`, `v3`, `Jenkinsfile`, and
    `k8s`.
2.  Local Flask app pages on ports 5001, 5002, 5003.
3.  `python -m unittest discover -s tests -v` showing `OK`.
4.  `docker images` and `docker ps` with the quiz images/containers.
5.  GitHub repository with the committed project files.
6.  Jenkins pipeline stage view and successful Console Output.
7.  Docker Hub repository showing tags `v1`, `v2`, `v3`.
8.  `kubectl get nodes` showing `Ready`.
9.  `kubectl get deployments`, `kubectl get pods`,
    `kubectl get services`.
10. Browser displaying the Kubernetes-hosted app.

## 10. Fast revision: commands to remember

``` powershell
# Project
cd D:\Agile-Quiz-Question-Bank

# Local test
python -m unittest discover -s tests -v

# GitHub
git status
git add .
git commit -m "Update lab files"
git push

# Docker
docker info
docker build -f v1/DockerFile -t shivaranjini569/quiz-question-bank:v1 .
docker images
docker login
docker push shivaranjini569/quiz-question-bank:v1

# Kubernetes
kubectl config current-context
kubectl get nodes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/quiz-question-bank
kubectl get pods
kubectl get services
kubectl logs deployment/quiz-question-bank
```

## 11. Important lab reminders

-   **PowerShell commands** belong in the VS Code terminal. **Dockerfile
    directives** such as `FROM`, `COPY`, `EXPOSE`, and `CMD` belong
    **inside Dockerfiles**, not in the terminal.
-   **YAML code** belongs in `.yaml` files, not directly in
    CMD/PowerShell.
-   The Docker **build context** is the final `.` in the `docker build`
    command. It must be the project root for these Dockerfiles.
-   The public GitHub repository does **not** currently contain all
    files shown in this guide. Create and commit them before using
    Jenkins.
-   Jenkins needs a working Windows Docker Engine and Kubernetes access.
    If Docker Desktop cannot start, its Docker/Kubernetes stages cannot
    succeed just by retrying commands.
-   This guide does not make JSON data persistent across Pod
    replacement. A proper shared database or persistent-volume design is
    needed for that.
-   Never run destructive WSL unregister/factory-reset commands as a
    quick fix; they can delete data.
-   Never commit passwords, Docker Hub tokens, or Jenkins secrets.

**End of README.**
