# Practical Question 1 — Menu-Driven Calculator

**Five-stage Kubernetes CI/CD pipeline | Windows PowerShell | Exactly two GitHub source-code pushes**

**Question:** Develop a Python menu-driven calculator with addition, subtraction, multiplication and division. **Push 1:** addition and subtraction only. **Push 2:** add multiplication and division. Each push must run GitHub Actions tests, build/push a uniquely tagged Docker image and automatically deploy that exact image to Kubernetes.

> **Important lab design:** This uses a small **Flask web calculator** with a menu (dropdown) so it can be exposed through a Kubernetes Service and tested in a browser. The pipeline uses a **Windows self-hosted GitHub Actions runner on the same lab PC as Docker Desktop Kubernetes**. GitHub-hosted runners cannot normally deploy to your local cluster. **Do not use Jenkins for this question:** the examiner explicitly requires GitHub Actions.
>
> **Exactly two `git push` commands appear in this guide.** Do not push the README or workflow separately. Prepare all Push 1 files before the first push, then modify the application and tests for Push 2.

## Stage overview

| Stage | What happens |
|---|---|
| 1. Source Code | Create Flask calculator, tests, Dockerfile, Kubernetes YAML and workflow in VS Code |
| 2. Version Control | Push code to the GitHub repository named `pipeline` |
| 3. Continuous Integration | GitHub Actions checks out code, installs dependencies and runs pytest |
| 4. Build | After tests pass, build and push Docker image tagged with the **commit SHA** |
| 5. Deployment | Same workflow deploys **that SHA-tagged image** to Docker Desktop Kubernetes |

---

## 0. Before starting: verify Windows tools

Open **Docker Desktop**. Wait for the Docker Engine to start. Enable **Kubernetes** in Docker Desktop and wait for the node to be ready. Open **VS Code → Terminal → New Terminal → PowerShell** and run **one at a time**:

```powershell
git --version
python --version
docker --version
docker info
kubectl version --client
kubectl config current-context
kubectl get nodes
```

**Expected:** `docker info` includes a `Server` section; `kubectl config current-context` is `docker-desktop`; `kubectl get nodes` shows `Ready`. **Stop and fix Docker Desktop/Kubernetes if either is not working.** The GitHub Actions runner must use the same Windows account with access to Docker Desktop and the Kubernetes configuration.

If your context is not correct, inspect it first:

```powershell
kubectl config get-contexts
kubectl config use-context docker-desktop
kubectl get nodes
```

Only use the context-switch command if `docker-desktop` is listed. If `docker` is not recognized but Docker Desktop is installed in your known local path, this changes PATH for the current PowerShell session only:

```powershell
$env:Path += ";C:\Users\Shivaranjini\AppData\Local\Programs\DockerDesktop\resources\bin"
docker --version
```

**Do not continue if the Docker Engine is still failing to start.** A PATH change cannot fix a stopped Engine.

## 1. Create GitHub repository `pipeline`

1. Open https://github.com/new and sign in as `shivaranjini569` (or replace the username everywhere if using another account).
2. Repository name: **`pipeline`**.
3. Select **Public** for this classroom exercise. Do **not** initialize with a README, `.gitignore`, or license.
4. Click **Create repository**. Your expected URL is `https://github.com/shivaranjini569/pipeline`.
5. **Do not push anything yet.**

## 2. Create project folder and files in VS Code (Push 1)

**WHERE:** VS Code PowerShell terminal.

```powershell
cd D:\
mkdir pipeline
cd D:\pipeline
code .
mkdir templates
mkdir tests
mkdir k8s
mkdir .github
mkdir .github\workflows
```

If `D:\pipeline` already exists, open that folder instead of recreating it. In the VS Code Explorer, create the following **exact filenames**:

```text
D:\pipeline\
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── templates\
│   └── index.html
├── tests\
│   └── test_app.py
├── k8s\
│   ├── deployment.yaml
│   └── service.yaml
├── .github\
│   └── workflows\
│       └── pipeline.yml
└── README.md
```

**Important:** Put the entire contents of this guide in `README.md` if you want the instructions in GitHub. Do this **before Push 1**. Do not commit a separate README update between Push 1 and Push 2.

### File A — `app.py` (PUSH 1 VERSION: addition and subtraction only)

**WHERE:** VS Code Explorer → root folder → `app.py`. Paste and save (`Ctrl+S`).

```python
from flask import Flask, render_template, request

app = Flask(__name__)

OPERATIONS = {
    "add": "Addition",
    "subtract": "Subtraction",
}


def calculate(a, b, operation):
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    raise ValueError("Invalid operation")


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None
    if request.method == "POST":
        try:
            a = float(request.form.get("a", ""))
            b = float(request.form.get("b", ""))
            operation = request.form.get("operation", "")
            result = calculate(a, b, operation)
        except (ValueError, TypeError):
            error = "Enter valid numbers and select an available operation."
    return render_template(
        "index.html", operations=OPERATIONS, result=result, error=error
    )


@app.get("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### File B — `templates/index.html` (works for both pushes; do not modify for Push 2)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Menu-Driven Calculator</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 480px; margin: 70px auto; padding: 20px; }
    input, select, button { display: block; width: 100%; box-sizing: border-box; padding: 10px; margin: 12px 0; }
    button { background: #184d8c; color: white; border: 0; cursor: pointer; }
    .result { font-weight: bold; color: #166534; }
    .error { color: #b91c1c; }
  </style>
</head>
<body>
  <h1>Menu-Driven Calculator</h1>
  <form method="post">
    <label>First number</label>
    <input type="number" step="any" name="a" required>
    <label>Second number</label>
    <input type="number" step="any" name="b" required>
    <label>Choose operation</label>
    <select name="operation" required>
      {% for key, label in operations.items() %}
      <option value="{{ key }}">{{ label }}</option>
      {% endfor %}
    </select>
    <button type="submit">Calculate</button>
  </form>
  {% if result is not none %}<p class="result">Result: {{ result }}</p>{% endif %}
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
</body>
</html>
```

### File C — `requirements.txt`

```text
Flask==3.1.1
pytest>=8,<10
```

### File D — `tests/test_app.py` (PUSH 1 TESTS)

```python
import pytest
from app import app, calculate


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_addition():
    assert calculate(10, 5, "add") == 15


def test_subtraction():
    assert calculate(10, 5, "subtract") == 5


def test_menu_shows_only_push1_operations(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Addition" in response.data
    assert b"Subtraction" in response.data
    assert b"Multiplication" not in response.data
    assert b"Division" not in response.data


def test_health(client):
    assert client.get("/health").json == {"status": "healthy"}
```

### File E — `Dockerfile` (root folder, capital D; no extension)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates/ templates/
EXPOSE 5000
CMD ["python", "app.py"]
```

### File F — `.dockerignore`

```text
.git/
.github/
.venv/
__pycache__/
.pytest_cache/
tests/
k8s/
*.pyc
```

### File G — `.gitignore`

```text
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
```

### File H — `k8s/deployment.yaml`

The workflow will replace the literal placeholder `IMAGE_PLACEHOLDER` with the exact Docker image tag created by that push. **Do not replace it manually.**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: menu-calculator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: menu-calculator
  template:
    metadata:
      labels:
        app: menu-calculator
    spec:
      containers:
        - name: calculator
          image: IMAGE_PLACEHOLDER
          imagePullPolicy: Always
          ports:
            - containerPort: 5000
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 3
            periodSeconds: 5
```

### File I — `k8s/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: menu-calculator-service
spec:
  type: NodePort
  selector:
    app: menu-calculator
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
```

### File J — `.github/workflows/pipeline.yml` (the required five-stage GitHub Actions pipeline)

**WHERE:** VS Code → `.github` → `workflows` → `pipeline.yml`.

The five jobs are named after the examiner's five stages. All five jobs run on the **self-hosted Windows runner**. Every image tag uses `${{ github.sha }}`, so Push 1 and Push 2 produce different image tags. **The Deploy job waits for the Build job to succeed.**

```yaml
name: Calculator Five-Stage CI-CD

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  source_code:
    name: "1 - Source Code"
    runs-on: [self-hosted, Windows, X64]
    steps:
      - name: Checkout source
        uses: actions/checkout@v4
      - name: Verify application file
        shell: powershell
        run: |
          if (!(Test-Path app.py)) { throw "app.py is missing" }
          Write-Host "Source code present"

  version_control:
    name: "2 - Version Control"
    needs: source_code
    runs-on: [self-hosted, Windows, X64]
    steps:
      - name: Checkout committed version
        uses: actions/checkout@v4
      - name: Display commit ID
        shell: powershell
        run: |
          git rev-parse HEAD
          Write-Host "Commit: $env:GITHUB_SHA"

  continuous_integration:
    name: "3 - Continuous Integration"
    needs: version_control
    runs-on: [self-hosted, Windows, X64]
    steps:
      - name: Checkout source
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        shell: powershell
        run: python -m pip install -r requirements.txt
      - name: Run automated tests
        shell: powershell
        run: python -m pytest -v

  build:
    name: "4 - Build"
    needs: continuous_integration
    runs-on: [self-hosted, Windows, X64]
    steps:
      - name: Checkout source
        uses: actions/checkout@v4
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - name: Build image with unique commit tag
        shell: powershell
        run: |
          $image = "shivaranjini569/menu-calculator:$env:GITHUB_SHA"
          docker build -t $image .
          if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
          docker push $image
          if ($LASTEXITCODE -ne 0) { throw "Docker push failed" }
          Write-Host "Published $image"

  deployment:
    name: "5 - Deployment"
    needs: build
    runs-on: [self-hosted, Windows, X64]
    steps:
      - name: Checkout Kubernetes manifests
        uses: actions/checkout@v4
      - name: Deploy this push's image to Kubernetes
        shell: powershell
        run: |
          kubectl config use-context docker-desktop
          if ($LASTEXITCODE -ne 0) { throw "Docker Desktop context missing" }
          $image = "shivaranjini569/menu-calculator:$env:GITHUB_SHA"
          $manifest = (Get-Content 'k8s/deployment.yaml' -Raw).Replace('IMAGE_PLACEHOLDER', $image)
          $manifest | kubectl apply -f -
          if ($LASTEXITCODE -ne 0) { throw "Deployment apply failed" }
          kubectl apply -f k8s/service.yaml
          if ($LASTEXITCODE -ne 0) { throw "Service apply failed" }
          kubectl rollout status deployment/menu-calculator --timeout=180s
          if ($LASTEXITCODE -ne 0) { throw "Rollout failed" }
          kubectl get deployments
          kubectl get pods
          kubectl get services
          $deployed = kubectl get deployment menu-calculator -o jsonpath='{.spec.template.spec.containers[0].image}'
          if ($deployed -ne $image) { throw "Wrong deployed image: $deployed" }
          Write-Host "Verified deployed image: $deployed"
```

**Docker Hub image repository:** `shivaranjini569/menu-calculator` (create it in the next section). If your Docker Hub username differs, replace the image name in the **two workflow places** above before Push 1.

## 3. Configure Docker Hub and GitHub secrets BEFORE Push 1

### Docker Hub

1. Open https://hub.docker.com and sign in.
2. Create a **public** repository named **`menu-calculator`** under username `shivaranjini569`.
3. Create a Docker Hub **Personal Access Token** with **Read/Write** permissions at https://app.docker.com/settings/personal-access-tokens.
4. Copy the token somewhere secure for the next step. **Do not paste it into project files or screenshots.**

### GitHub repository secrets

In `https://github.com/shivaranjini569/pipeline`, open **Settings → Secrets and variables → Actions → New repository secret**. Add **both**:

| Secret name | Secret value |
|---|---|
| `DOCKERHUB_USERNAME` | `shivaranjini569` |
| `DOCKERHUB_TOKEN` | Your Docker Hub Personal Access Token |

**Do not put the token in `pipeline.yml`, README, Git commits, or terminal commands.**

## 4. Configure the Windows self-hosted GitHub Actions runner BEFORE Push 1

**Why:** GitHub Actions must automatically deploy to **your laptop's** Kubernetes cluster. The runner must execute on the Windows computer where Docker Desktop and `kubectl` work.

1. On GitHub, open the `pipeline` repository.
2. Open **Settings → Actions → Runners → New self-hosted runner**.
3. Select **Windows** and **x64**.
4. GitHub will display current **Download** and **Configure** commands and a short-lived registration token. **Copy and run those exact commands from GitHub** in a **new PowerShell terminal**, in a dedicated folder such as `C:\actions-runner`. Do not use an old or invented registration token.
5. Follow the runner configuration prompts. Use the default labels so it matches `[self-hosted, Windows, X64]`.
6. Start the runner **interactively** with `./run.cmd` (in PowerShell: `.\run.cmd`). **Keep that terminal open** during both pushes and pipeline runs.
7. Verify GitHub **Settings → Actions → Runners** shows the runner as **Idle / Online**.

**Before starting the runner**, from that same Windows account check:

```powershell
docker info
kubectl config current-context
kubectl get nodes
```

**Expected:** Docker Engine working, context `docker-desktop`, node `Ready`. If GitHub Actions says **Waiting for a runner**, check the runner terminal and GitHub's Runners page. A self-hosted runner on a public repository executes repository workflows on your PC; use it only for your own trusted coursework, avoid untrusted pull requests, and stop/remove it when the lab is over.

> **Important:** If your instructor forbids self-hosted runners, you cannot claim that GitHub-hosted Actions automatically deployed to your private local Docker Desktop cluster. Ask for an accessible Kubernetes cluster or an approved deployment runner instead. A manual `kubectl apply` would not satisfy the question's automatic-deployment wording.

## 5. Local check BEFORE Push 1 (no Git push yet)

**WHERE:** VS Code PowerShell in `D:\pipeline`.

```powershell
cd D:\pipeline
python -m pip install -r requirements.txt
python -m pytest -v
```

**Expected:** 4 tests pass.

Start Flask:

```powershell
python app.py
```

Open http://localhost:5000. The dropdown must show **Addition** and **Subtraction only**. Test `10 + 5 = 15`, `10 - 5 = 5`. Open http://localhost:5000/health; expected `{"status":"healthy"}`. Press **Ctrl+C** to stop the server.

Optional local Docker check (requires Docker Desktop running):

```powershell
docker build -t menu-calculator:local .
docker run --rm -d --name calculator-local -p 5000:5000 menu-calculator:local
docker ps
```

Open http://localhost:5000. Then stop:

```powershell
docker stop calculator-local
```

If port 5000 is occupied, stop the local Flask server before running Docker.

## 6. PUSH 1 — first and only initial GitHub push

**Checkpoint BEFORE running:** GitHub repo exists; Docker Hub repo exists; GitHub secrets are configured; Windows runner is **Online**; Docker Desktop Kubernetes is **Ready**; all Push 1 files are saved, including README.

**WHERE:** VS Code PowerShell, `D:\pipeline`.

```powershell
cd D:\pipeline
git init
git add .
git commit -m "Push 1: calculator addition and subtraction"
git branch -M main
git remote add origin https://github.com/shivaranjini569/pipeline.git
git push -u origin main
```

**This is source-code push 1 of exactly 2.** Do **not** run another push until the Push 2 section. If Git asks for sign-in, use GitHub's browser authentication. If `origin` already exists, inspect `git remote -v` rather than adding it twice.

### Verify Push 1 pipeline and first deployment

1. GitHub → `pipeline` → **Actions** → open **Calculator Five-Stage CI-CD**.
2. Verify **all five jobs are green**: Source Code, Version Control, Continuous Integration, Build, Deployment.
3. Docker Hub → `shivaranjini569/menu-calculator` → **Tags**. Confirm a tag that looks like a long Git commit SHA.
4. VS Code PowerShell:

```powershell
kubectl get deployments
kubectl get pods
kubectl get services
kubectl rollout status deployment/menu-calculator
kubectl get deployment menu-calculator -o jsonpath="{.spec.template.spec.containers[0].image}"
```

**Expected:** `menu-calculator` has **2/2** ready replicas; Pods are `Running`; Service has NodePort `30080`; deployed image ends in the Push 1 commit SHA.

Open **http://localhost:30080** and demonstrate **addition and subtraction only**.

If NodePort doesn't work on your setup, use a separate terminal:

```powershell
kubectl port-forward service/menu-calculator-service 5000:80
```

Keep it open and visit http://localhost:5000. Stop forwarding with **Ctrl+C** after testing.

**SCREENSHOTS FOR PUSH 1:** GitHub Actions five green jobs, Docker Hub SHA tag, `kubectl get pods`, browser showing only Addition/Subtraction.

## 7. Modify code for PUSH 2 (do not change workflow)

**Requirement:** Add multiplication and division. The same GitHub Actions workflow must trigger a **new run**, publish a **new SHA tag**, and update the Kubernetes Deployment to that new tag.

### Replace the entire `app.py` with this PUSH 2 version

```python
from flask import Flask, render_template, request

app = Flask(__name__)

OPERATIONS = {
    "add": "Addition",
    "subtract": "Subtraction",
    "multiply": "Multiplication",
    "divide": "Division",
}


def calculate(a, b, operation):
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
    raise ValueError("Invalid operation")


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None
    if request.method == "POST":
        try:
            a = float(request.form.get("a", ""))
            b = float(request.form.get("b", ""))
            operation = request.form.get("operation", "")
            result = calculate(a, b, operation)
        except (ValueError, TypeError):
            error = "Enter valid numbers and select an available operation."
        except ZeroDivisionError:
            error = "Cannot divide by zero."
    return render_template(
        "index.html", operations=OPERATIONS, result=result, error=error
    )


@app.get("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### Replace the entire `tests/test_app.py` with these PUSH 2 tests

```python
import pytest
from app import app, calculate


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_addition():
    assert calculate(10, 5, "add") == 15


def test_subtraction():
    assert calculate(10, 5, "subtract") == 5


def test_multiplication():
    assert calculate(10, 5, "multiply") == 50


def test_division():
    assert calculate(10, 5, "divide") == 2


def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        calculate(10, 0, "divide")


def test_menu_shows_all_four_operations(client):
    response = client.get("/")
    assert response.status_code == 200
    for label in (b"Addition", b"Subtraction", b"Multiplication", b"Division"):
        assert label in response.data


def test_health(client):
    assert client.get("/health").json == {"status": "healthy"}
```

**Do not change** `templates/index.html`, `Dockerfile`, Kubernetes YAML or GitHub Actions workflow. The HTML menu automatically reads the new `OPERATIONS` dictionary.

### Test Push 2 locally before pushing

```powershell
cd D:\pipeline
python -m pytest -v
```

**Expected:** 7 tests pass. If tests fail, fix files **before** Push 2. Optionally run `python app.py`, test the four options at http://localhost:5000, then stop with Ctrl+C.

## 8. PUSH 2 — second and FINAL source-code push

**WHERE:** VS Code PowerShell in `D:\pipeline`.

```powershell
cd D:\pipeline
git status
git add app.py tests/test_app.py
git commit -m "Push 2: add multiplication and division"
git push origin main
```

**This is source-code push 2 of exactly 2. DO NOT PUSH AGAIN.**

### Verify Push 2 pipeline and updated deployment

1. GitHub → `pipeline` → **Actions**. A **new** workflow run must appear. Wait for **all five stages to pass**.
2. Docker Hub → `menu-calculator` → **Tags**. There must be **two different commit SHA tags** (one per push).
3. VS Code PowerShell:

```powershell
kubectl rollout status deployment/menu-calculator
kubectl get deployments
kubectl get pods
kubectl get services
kubectl get deployment menu-calculator -o jsonpath="{.spec.template.spec.containers[0].image}"
kubectl rollout history deployment/menu-calculator
```

**Expected:** two ready Pods; deployed image now ends with the **Push 2 SHA**, which differs from Push 1. Open **http://localhost:30080** and verify all four operations:

- `10 + 5 = 15`
- `10 - 5 = 5`
- `10 × 5 = 50`
- `10 ÷ 5 = 2`
- `10 ÷ 0` shows **Cannot divide by zero.**

If necessary, use `kubectl port-forward service/menu-calculator-service 5000:80` and open http://localhost:5000.

**SCREENSHOTS FOR PUSH 2:** second green GitHub Actions run, both Docker Hub SHA tags, new deployed SHA, two running Pods, updated browser menu with four operations.

## 9. Troubleshooting — only if a step fails

| Symptom | What to do |
|---|---|
| `docker info` fails | Start/fix Docker Desktop Engine first. |
| `kubectl get nodes` fails | Enable Docker Desktop Kubernetes, verify context `docker-desktop`, wait for `Ready`. |
| Workflow waits for runner | Keep `C:\actions-runner\run.cmd` running and verify the runner is **Online** with matching Windows/x64 labels. |
| GitHub Actions CI is red | Expand failed **Run automated tests** step; fix Python/test files before the next allowed push. |
| Docker push denied | Check `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, repository name and token write permission. |
| `ImagePullBackOff` | Check Docker Hub public visibility and exact SHA image tag. |
| `CrashLoopBackOff` | Inspect Pod logs and Dockerfile/app startup. |
| NodePort browser fails | Check Pods, Service, endpoints; use port forwarding. |
| Push 2 still shows old version | Verify Actions Deployment job succeeded and Deployment image is the new SHA; refresh browser. |

**Commands:**

```powershell
kubectl get all
kubectl describe deployment menu-calculator
kubectl get pods
kubectl logs deployment/menu-calculator
kubectl get endpoints menu-calculator-service
kubectl get events --sort-by=.metadata.creationTimestamp
```

**If the first workflow fails:** debug and fix the setup **without extra Git pushes** when possible (runner, credentials, Docker Engine, cluster). If committed code itself is broken, the exact-two-push rule becomes difficult to satisfy; catch problems using the local tests **before Push 1**. Avoid pretending a failed deployment succeeded.

## 10. Final lab checklist

- [ ] Repository is named **`pipeline`**.
- [ ] Exactly **two** source-code pushes from VS Code (`git push` only in Steps 6 and 8).
- [ ] Push 1 contains **addition and subtraction only**.
- [ ] Push 2 adds **multiplication and division**, including divide-by-zero handling.
- [ ] Each push triggers **five GitHub Actions jobs** in the required order.
- [ ] CI checks out code, installs dependencies and runs automated tests.
- [ ] Build runs **only after tests pass**.
- [ ] Docker Hub contains **two unique SHA-tagged images**.
- [ ] Each successful run automatically deploys **its own SHA-tagged image**.
- [ ] Kubernetes Deployment shows **2/2 ready Pods** and a Service.
- [ ] Browser shows the correct Push 1 and Push 2 calculator menus.
- [ ] Screenshots demonstrate both successful runs and updated deployment.

**After the assessment:** stop the self-hosted runner (Ctrl+C in its terminal). If no longer needed, remove it from GitHub **Settings → Actions → Runners** and follow GitHub's removal instructions. Kubernetes cleanup (only if permitted): `kubectl delete -f k8s/service.yaml` and `kubectl delete deployment menu-calculator`.
