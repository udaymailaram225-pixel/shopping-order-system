pipeline {
    agent any

    environment {
        IMAGE_NAME = 'shopping-order-system:v1'
        CONTAINER_NAME = 'shopping-container'
        APP_PORT = '5000'
    }

    stages {
        stage('Checkout Source') {
            steps {
                echo '=== Stage 1: Checking out source code from Git ==='
                checkout scm
            }
        }

        stage('Environment Validation') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            echo "=== Linux/Docker Jenkins Agent Detected ==="
                            python3 --version || echo "Python not found"
                            docker --version || echo "Docker not found"
                        '''
                    } else {
                        bat '''
                            echo "=== Windows Jenkins Agent Detected ==="
                            python --version
                            docker --version
                        '''
                    }
                }
            }
        }

        stage('Install Dependencies & Test') {
            steps {
                script {
                    if (isUnix()) {
                        echo '=== Validating Python in Jenkins Environment ==='
                        sh '''
                            python3 -c "print('Python environment check OK')" || true
                        '''
                    } else {
                        echo '=== Running on Windows agent: Installing requirements & executing Selenium ==='
                        bat '''
                            python -m pip install -r requirements.txt
                            python test_selenium.py --headless
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo '=== Stage 4: Building Docker Image ==='
                    if (isUnix()) {
                        sh "docker build -t ${IMAGE_NAME} ."
                    } else {
                        bat "docker build -t %IMAGE_NAME% ."
                    }
                }
            }
        }

        stage('Deploy Docker Container') {
            steps {
                script {
                    echo '=== Stage 5: Deploying Container on Port 5000 ==='
                    if (isUnix()) {
                        sh """
                            echo "Stopping any existing container named ${CONTAINER_NAME}..."
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true

                            echo "Starting new container ${CONTAINER_NAME}..."
                            docker run -d --name ${CONTAINER_NAME} -p ${APP_PORT}:5000 ${IMAGE_NAME}
                            
                            echo "Verifying running container:"
                            docker ps --filter "name=${CONTAINER_NAME}"
                        """
                    } else {
                        bat """
                            echo Stopping any existing container with name %CONTAINER_NAME%...
                            docker stop %CONTAINER_NAME% 2>nul || ver >nul
                            docker rm %CONTAINER_NAME% 2>nul || ver >nul

                            echo Starting new container %CONTAINER_NAME%...
                            docker run -d --name %CONTAINER_NAME% -p %APP_PORT%:5000 %IMAGE_NAME%
                            
                            echo Verifying running container:
                            docker ps --filter "name=%CONTAINER_NAME%"
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo '======================================================='
            echo ' Pipeline Succeeded: Application deployed successfully! '
            echo ' Access the app at http://localhost:5000               '
            echo '======================================================='
        }
        failure {
            echo '======================================================='
            echo ' Pipeline Failed: Check the Jenkins console output.    '
            echo '======================================================='
        }
        always {
            echo 'Cleaning up workspace artifacts if needed.'
        }
    }
}
