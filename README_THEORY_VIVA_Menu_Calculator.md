# Menu-Driven Calculator — Theory Explanation & Viva Preparation

**Practical Question 1 | Five-stage CI/CD pipeline | Python, VS Code, GitHub, GitHub Actions, Docker Hub, Kubernetes**

> **Use this file to understand and explain the lab in your own words.** It is a separate study file; keep the execution instructions in `README.md` and upload this document as `README_THEORY_VIVA.md` to your `pipeline` repository **before Push 1** if you must obey the *exactly two source-code pushes* rule. The explanations describe what the provided workflow is designed to do. Only tell your examiner a stage *succeeded* after you have verified it in your own run.

## 1. What was my practical question?

**Question:** Create a menu-driven calculator in Python. In **Push 1**, implement **addition and subtraction**. In **Push 2**, add **multiplication and division**. Use a **five-stage pipeline**: (1) Source Code, (2) Version Control, (3) Continuous Integration, (4) Build, (5) Deployment. GitHub Actions must automatically check out the code, install packages, test, build and push a Docker image to Docker Hub, then deploy that same version to Kubernetes. Exactly **two source-code pushes** are allowed, and each push needs its own Docker image tag.

### What I built (easy answer)

> “I created a Python Flask menu-driven calculator that runs in a browser. Initially it supports addition and subtraction. I used Git and GitHub to store the code and GitHub Actions to automatically test it. When tests pass, the workflow builds and pushes a Docker image tagged with that Git commit's SHA. It then deploys that exact image to Kubernetes and exposes the application through a Service. In my second push, I added multiplication and division. The second pipeline run builds a different image and updates the Kubernetes deployment.”

**Why a web calculator rather than a terminal-only calculator?** Kubernetes Services expose network applications. A Flask web interface lets the examiner access and demonstrate the calculator in a browser, while the calculation logic is still ordinary Python code. The menu is an HTML dropdown rather than a text-terminal menu.

## 2. Full pipeline flow — what happens after each push?

```text
VS Code (write/modify Python app and tests)
                 |
                 v
       Git commit + git push
                 |
                 v
       GitHub repository: pipeline
                 |
                 v
           GitHub Actions
                 |
     1. SOURCE CODE — checkout/verify app.py
                 |
     2. VERSION CONTROL — identify Git commit SHA
                 |
     3. CONTINUOUS INTEGRATION — install dependencies + pytest
                 |
            tests must pass
                 |
     4. BUILD — Docker build + push to Docker Hub
                 |
          image tag = Git commit SHA
                 |
     5. DEPLOYMENT — kubectl updates Kubernetes Deployment
                 |
        Kubernetes Pods + NodePort Service
                 |
                 v
          Browser: localhost:30080
```

**Key point:** The workflow runs because the `.github/workflows/pipeline.yml` file includes the trigger `on: push` for branch `main`. The stages are ordered with `needs:`. If the tests fail, the Build job does not run; if Build fails, Deployment does not run.

## 3. Explain the exact five stages

| Stage | What it does in my project | Why it matters |
|---|---|---|
| **1. Source Code** | GitHub Actions checks out the latest committed files and verifies `app.py` is present. | Ensures the pipeline has the application source. |
| **2. Version Control** | Uses GitHub's commit information and displays the Git commit SHA. | Connects each build to the exact code version. |
| **3. Continuous Integration** | Checks out code, installs Python 3.12 and packages from `requirements.txt`, then runs `pytest`. | Catches code errors before an image is published. |
| **4. Build** | Runs `docker build`, tags the image with the commit SHA, logs in with GitHub secrets and pushes to Docker Hub. | Packages the tested app into a portable container image. |
| **5. Deployment** | Replaces the image placeholder in `deployment.yaml` with the current SHA-tagged image; runs `kubectl apply`, waits for rollout and checks running Pods and Service. | Makes the tested image available through Kubernetes. |

### Short answer if sir asks: “Why five stages?”

> “They separate coding, tracking changes, testing, packaging, and running the application. Each later stage depends on the earlier stage, so a failed test prevents deployment.”

**CI vs CD:** **CI (Continuous Integration)** automatically checks integrated source changes using builds/tests. **CD (Continuous Delivery/Deployment)** prepares or releases those successful changes; in this lab the workflow automatically applies the Kubernetes deployment, so there is an automated deployment step.

## 4. What each file is for

| File | Purpose |
|---|---|
| `app.py` | Python Flask app; contains `calculate()`, menu choices, `/` route and `/health` route. |
| `templates/index.html` | Browser form: two numbers, operation dropdown, Calculate button, result/error message. |
| `requirements.txt` | Lists Python dependencies: Flask and pytest. |
| `tests/test_app.py` | Automated tests of calculations, menu contents and health endpoint. |
| `Dockerfile` | Instructions to build a Python Docker image that launches the Flask server on port 5000. |
| `.dockerignore` | Excludes unnecessary files from Docker build context. |
| `.gitignore` | Keeps local cache, virtual environment and secrets out of Git commits. |
| `.github/workflows/pipeline.yml` | GitHub Actions workflow defining the five automated jobs. |
| `k8s/deployment.yaml` | Declares the desired Kubernetes Pods, replica count, container image and health/readiness check. |
| `k8s/service.yaml` | Exposes those Pods using a stable Kubernetes Service and NodePort. |
| `README.md` | Step-by-step practical commands and code. |
| `README_THEORY_VIVA.md` | This explanation and viva notes. |

## 5. How the calculator works

1. A user opens the calculator page.
2. The HTML form asks for two numbers and an operation from a dropdown menu.
3. On clicking **Calculate**, the browser submits a `POST` request to `/`.
4. Flask reads the fields with `request.form`; values are converted to `float`.
5. `calculate(a, b, operation)` performs the selected Python operation.
6. Flask passes the result or error to the HTML template, which displays it.

**Push 1:** `OPERATIONS` contains `add` and `subtract`; `calculate()` implements `a + b` and `a - b`.

**Push 2:** `OPERATIONS` additionally contains `multiply` and `divide`; `calculate()` implements `a * b` and `a / b` and rejects a zero divisor with `ZeroDivisionError`. Flask catches that error and displays **“Cannot divide by zero.”**

The same HTML template works for both pushes because it loops over the Python `OPERATIONS` dictionary. Adding the operations to the dictionary changes the dropdown without editing the HTML.

**Test examples:**

| Operation | Inputs | Result |
|---|---|---|
| Add | 10, 5 | 15 |
| Subtract | 10, 5 | 5 |
| Multiply (Push 2) | 10, 5 | 50 |
| Divide (Push 2) | 10, 5 | 2 |
| Divide by zero (Push 2) | 10, 0 | Friendly error message |

### Flask routes

- `/` handles the user interface; `GET` displays the page and `POST` calculates the result.
- `/health` returns `{"status":"healthy"}` with HTTP status 200. Kubernetes uses it to check whether a Pod is ready to receive traffic.
- `app.run(host="0.0.0.0", port=5000)` listens on port 5000 and allows network requests into the container. `0.0.0.0` binds to all interfaces, not a website address.

## 6. How I tested the application

The automated tests use **pytest**.

**Push 1 includes four tests:**

1. Addition returns the expected value.
2. Subtraction returns the expected value.
3. The menu contains Addition and Subtraction, but not Multiplication or Division.
4. `/health` returns a healthy response.

**Push 2 includes seven tests:**

1. Addition still works.
2. Subtraction still works.
3. Multiplication works.
4. Division works.
5. Dividing by zero raises the expected error.
6. The menu shows all four operations.
7. The health endpoint works.

**Why test the old operations again?** To check that adding features did not break existing functionality. This is a form of **regression testing**.

**What is a test client?** Flask's `app.test_client()` sends test requests to the application without starting a separate web server.

**Why does CI run tests before Docker build?** So broken code does not get packaged and deployed.

## 7. Git and exactly two pushes

**Git** tracks file changes locally. A **commit** records a snapshot of changes. **GitHub** stores those commits online. A **push** uploads commits to the remote repository and triggers GitHub Actions.

| Push | Source change | Expected CI result | Image and deployment |
|---|---|---|---|
| **Push 1** | Addition and subtraction only | 4 tests pass | First SHA-tagged image deployed |
| **Push 2** | Add multiplication, division and new tests | 7 tests pass | Different SHA-tagged image deployed |

A **Git commit SHA** is a unique identifier associated with a commit, such as `b7c...` (example only). The workflow uses `${{ github.sha }}` to tag the Docker image with the exact commit that triggered the run. Thus the image for Push 2 has a different tag from Push 1.

**Why not use `latest` for both?** `latest` can point to different images at different times and makes it difficult to prove exactly which version is running. SHA tags allow traceability and controlled updates.

**Important for the two-push rule:** Create the workflow, YAML, README and theory file before Push 1. Do not make a separate Git push just for documentation. Make the only later source-code change for Push 2.

## 8. What Docker does and how the image is built

**Docker** packages the application code, Python runtime and required packages into a **container image**. A **container** is a running instance of that image.

`Dockerfile` line-by-line:

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

| Instruction | Meaning |
|---|---|
| `FROM` | Start with an official lightweight Python 3.12 image. |
| `WORKDIR` | Set `/app` as working folder inside the container. |
| `COPY` | Copy dependencies, Python program and HTML template into the image. |
| `RUN` | Install Python dependencies when building the image. |
| `EXPOSE 5000` | Document the application's internal listening port. |
| `CMD` | Start the Flask application when the container runs. |

**Docker Hub** is an online image registry. GitHub Actions logs into Docker Hub using the secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` and pushes a new image for each commit. The lab repository is `shivaranjini569/menu-calculator`.

**Docker build vs push:** Build creates the image. Push uploads it to Docker Hub. **Docker image vs container:** image is the reusable package; container is a running instance.

## 9. What Kubernetes does

**Kubernetes** manages application containers. In the guide it runs locally using **Docker Desktop Kubernetes**.

- **Pod:** the smallest unit Kubernetes runs; the calculator container runs inside a Pod.
- **Deployment:** describes the desired state, including **2 replicas**, which image to run and update strategy.
- **Replica:** one copy of the application's Pod. With 2 replicas, Kubernetes tries to keep two Pods available.
- **Service:** gives the Pods a stable networking endpoint, even when Pods are replaced.
- **NodePort:** a Service type that exposes a port on the cluster node so the application can be accessed locally.
- **Readiness probe:** regularly checks `/health`; when it succeeds, the Pod is considered ready to serve traffic.
- **Rollout:** Kubernetes updating the Deployment's Pods to a new image version.

### The ports in this lab

```text
Browser: http://localhost:30080
          |
          v
Kubernetes Service NodePort: 30080
          |
          v
Service port: 80
          |
          v
Pod/container port: 5000
          |
          v
Flask calculator
```

`targetPort: 5000` is the port where Flask listens inside the Pod. `port: 80` is the Service's internal port. `nodePort: 30080` is the node's external port used for the demo.

**Why two Pods?** It demonstrates that Kubernetes can maintain multiple application replicas. This small calculator is stateless, so both replicas can independently calculate the same results.

**What happens if a Pod crashes?** The Deployment's controller works to restore the desired number of replicas. Recovery time is not guaranteed to be instantaneous.

## 10. How automatic Kubernetes deployment works in this exact guide

The workflow contains `image: IMAGE_PLACEHOLDER` in `k8s/deployment.yaml`. In the **Deployment** job, the workflow constructs an image name with the current Git commit SHA and replaces the placeholder **in memory** before applying the YAML with `kubectl`.

This ensures that **the deployed image tag matches the image created from that push**. The workflow also compares the deployed image against the expected image and fails if they differ.

For Push 1, the first SHA is deployed. For Push 2, the image reference changes to the new SHA, causing Kubernetes to update the Deployment's Pods. The Service stays the same, so users can visit the same browser URL after the update.

**Why use a Windows self-hosted runner?** A standard GitHub-hosted runner executes on GitHub infrastructure and usually cannot connect to Kubernetes running privately on your Windows laptop. A Windows self-hosted runner runs the workflow on your authorized lab PC where Docker Desktop, Docker Engine and `kubectl` are accessible.

**Security note:** Running a self-hosted runner on a public repo carries risks if untrusted workflows or pull requests are allowed. Use your own trusted coursework and remove/stop the runner after the lab.

## 11. What happens when something fails?

| Problem | What to say or check |
|---|---|
| GitHub Actions test fails | CI stops the dependent Build job, preventing publication of untested code. Read the test output. |
| Docker build fails | Build cannot create an image; deployment should not proceed. Inspect Dockerfile and files. |
| Docker Hub push fails | Check repository name and write-enabled token; Deployment job depends on Build succeeding. |
| `ImagePullBackOff` | Kubernetes cannot pull the named image; verify tag and visibility in Docker Hub. |
| `CrashLoopBackOff` | Container keeps crashing; inspect Pod logs and app startup. |
| `Pending` | Pod is not scheduled/running; inspect Pod events and cluster resources. |
| Browser does not load | Check ready Pods, Service selectors and ports; try port forwarding. |
| New menu not visible | Verify second workflow run, Deployment's SHA tag and rollout; refresh browser. |
| Workflow says waiting for runner | Verify Windows self-hosted runner is online and labels match. |

Useful explanation commands (Windows PowerShell):

```powershell
kubectl get nodes
kubectl get deployments
kubectl get pods
kubectl get services
kubectl rollout status deployment/menu-calculator
kubectl logs deployment/menu-calculator
kubectl get deployment menu-calculator -o jsonpath="{.spec.template.spec.containers[0].image}"
```

## 12. Viva questions and simple answers

**Q1. What is CI/CD?**  
CI automatically tests changes when code is pushed. CD delivers or deploys successful builds to a running environment.

**Q2. Which five stages did you use?**  
Source Code, Version Control, Continuous Integration, Build, and Deployment.

**Q3. What language and framework did you use?**  
Python with the Flask web framework.

**Q4. Why use Flask for a calculator?**  
To provide a browser menu and an HTTP application that Kubernetes can expose through a Service.

**Q5. What was implemented in Push 1?**  
Addition and subtraction only, with tests for both operations, the menu and the health endpoint.

**Q6. What changed in Push 2?**  
I added multiplication and division, handled division by zero, and expanded the tests.

**Q7. How many source-code pushes are allowed?**  
Exactly two. Each push triggers one new GitHub Actions workflow run when pushed to `main`.

**Q8. What is a Git commit?**  
A saved snapshot of tracked project changes.

**Q9. What triggers GitHub Actions?**  
The workflow uses a push event on the `main` branch.

**Q10. Why use `actions/checkout`?**  
It downloads the exact repository revision into the runner's working directory so the workflow can access the files.

**Q11. Why install dependencies in CI?**  
The runner needs Flask and pytest to run the application tests consistently.

**Q12. What is pytest?**  
A Python testing tool that discovers and runs automated test functions.

**Q13. What is the difference between unit testing and regression testing here?**  
Unit tests check individual calculations; running the original tests again after Push 2 checks for regressions.

**Q14. What happens if a test fails?**  
The Build job is blocked because it depends on CI; the new broken version is not deployed by this workflow.

**Q15. What is Docker?**  
A container platform that packages the app, dependencies and runtime into an image.

**Q16. What is Docker Hub?**  
An online registry storing container images, including both versions of this calculator.

**Q17. What is the difference between an image and a container?**  
An image is the package; a container is a running instance of that image.

**Q18. Why is each image tag different?**  
The workflow uses the unique Git commit SHA, so the exact code used for each deployment can be identified.

**Q19. What is Kubernetes?**  
A platform that schedules, runs, updates and maintains containerized applications.

**Q20. What is a Pod?**  
The unit in Kubernetes that holds the calculator container.

**Q21. What is a Deployment?**  
The Kubernetes resource that declares the container image and desired replicas and manages their updates.

**Q22. What is a Service?**  
A stable way to access Pods over the network, even as Pods change.

**Q23. What is NodePort 30080?**  
The node port where the calculator can be opened from the browser as `http://localhost:30080` in this Docker Desktop lab.

**Q24. Why have two replicas?**  
To demonstrate running two copies and Kubernetes maintaining the desired Pod count.

**Q25. What is a readiness probe?**  
An HTTP check to `/health` that indicates when a Pod is ready to serve traffic.

**Q26. What is a rolling update?**  
Kubernetes gradually replaces old Pods with new-version Pods when the Deployment's image changes.

**Q27. Why is the self-hosted runner necessary here?**  
It runs GitHub Actions on the lab PC that can access its local Kubernetes cluster.

**Q28. Why use GitHub Secrets?**  
To pass Docker Hub login credentials to the workflow without writing them into source files.

**Q29. How do you prove that Push 2 is deployed?**  
Show the second green Actions run, second SHA tag in Docker Hub, and the Deployment's image ending with the Push 2 SHA; then demonstrate all four operations in the browser.

**Q30. How is this different from Jenkins?**  
Jenkins is another automation server, but this practical explicitly requires GitHub Actions. GitHub Actions runs the workflow from `.github/workflows/pipeline.yml`.

## 13. One-minute oral presentation (memorize this)

> “My practical question is Menu-Driven Calculator using a Kubernetes CI/CD pipeline. I developed a calculator using Python Flask and displayed the operation menu in a browser. The first version contains addition and subtraction. I stored the code in the GitHub repository named `pipeline`. On my first Git push, GitHub Actions runs five stages: Source Code, Version Control, Continuous Integration, Build and Deployment. In CI, it checks out the code, installs dependencies and runs pytest tests. Only after the tests pass does it build a Docker image and publish it to Docker Hub. The image uses the Git commit SHA as its tag. The Deployment stage then runs on my Windows self-hosted runner, updates Docker Desktop Kubernetes and exposes the calculator with a NodePort Service. For the second push, I added multiplication and division and updated the tests. That push starts a new pipeline run and deploys the new SHA-tagged image. I can verify the update using GitHub Actions, Docker Hub, kubectl and the browser.”

## 14. What to show the examiner, in order

1. **GitHub repository**: `pipeline`, containing source, tests, Dockerfile, Kubernetes YAML and workflow.
2. **GitHub Actions history**: exactly two successful runs (one per push) with five stages each.
3. **CI logs**: Push 1 has four tests; Push 2 has seven tests.
4. **Docker Hub**: two different SHA-tagged images.
5. **Kubernetes terminal**: `kubectl get deployments`, `kubectl get pods`, `kubectl get services` and the deployed image tag.
6. **Browser**: updated calculator with four operations, plus divide-by-zero handling.

**Final reminder:** You can explain the implementation and expected behavior before execution, but claim “two successful deployments” only when both runs, image tags, and Kubernetes rollout have actually been verified.
