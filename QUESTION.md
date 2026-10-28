Kubernetes CI/CD Pipeline
Six Practical Questions
Instructions for all questions
•
Implement the application in VS Code using Python.
• Use the following five-stage pipeline: (1) Source Code, (2) Version Control, (3) Continuous Integration, (4)
Build, and (5) Deployment.
•
In Continuous Integration, GitHub Actions must check out the code, install dependencies, and run
automated tests.
• After tests pass, build a Docker image and push it to Docker Hub.
• Deploy the image to Kubernetes and expose the application through a Service.
• Make exactly two source-code pushes from VS Code to GitHub. Push 1 must trigger the first deployment;
after modifying the application, Push 2 must trigger a new pipeline run and deploy the updated version.
• Use a unique Docker image tag for each push. The deployment must use the image built from that push.
Practical Questions


1. Menu-Driven Calculator
Develop a Python application with menu options for addition, subtraction, multiplication, and division.
Push 1: Implement addition and subtraction.
Push 2: Add multiplication and division.
