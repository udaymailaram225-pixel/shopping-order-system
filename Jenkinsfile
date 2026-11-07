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

        stage('Install Dependencies') {
            steps {
                echo '=== Stage 2: Installing Python dependencies on Windows Agent ==='
                bat '''
                    python --version
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Automated Tests') {
            steps {
                echo '=== Stage 3: Running Automated Selenium 4 Test Suite in Headless Chrome ==='
                // Note: The Jenkins agent requires Python and Google Chrome installed.
                // The test suite executes in headless mode so no display server is required.
                bat '''
                    python -c "import app; print('App syntax check passed successfully.')"
                    python test_selenium.py --headless
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '=== Stage 4: Building Docker Image ==='
                bat '''
                    docker --version
                    docker build -t %IMAGE_NAME% .
                '''
            }
        }

        stage('Deploy Docker Container') {
            steps {
                echo '=== Stage 5: Deploying Container on Port 5000 ==='
                bat '''
                    echo Stopping any existing container with name %CONTAINER_NAME%...
                    docker stop %CONTAINER_NAME% 2>nul || ver >nul
                    docker rm %CONTAINER_NAME% 2>nul || ver >nul

                    echo Starting new container %CONTAINER_NAME%...
                    docker run -d --name %CONTAINER_NAME% -p %APP_PORT%:5000 %IMAGE_NAME%
                    
                    echo Verifying running container:
                    docker ps --filter "name=%CONTAINER_NAME%"
                '''
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
