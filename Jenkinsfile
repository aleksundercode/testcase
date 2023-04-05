pipeline {
    agent {
        label 'agent'
    }

    environment {
        CHART_PATH = 'pytest'
        CHART_REPO_URL = 'https://aleksundercode.github.io/testcase/'
        PACKAGE_PATH = 'helm-package'
        DOCKER_IMAGE = 'pytest'
    }
    
    stages {
        stage('git checkout') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('docker build') {
        steps {
            sh """
                export DOCKER_TLS_VERIFY="1"
                export DOCKER_HOST="tcp://192.168.49.2:2376"
                export DOCKER_CERT_PATH="/root/.minikube/certs"
                export MINIKUBE_ACTIVE_DOCKERD="minikube"
                docker build -t ${DOCKER_IMAGE} .
            """
        }
        }
        
        stage('helm check') {
            steps {
                sh 'helm lint ${CHART_PATH}'
            }
        }
    
        stage('package chart') {
            steps {
                sh 'mkdir -p ${PACKAGE_PATH}'
                sh 'helm package ${CHART_PATH} -d ${PACKAGE_PATH}'
            }
        }
    
        stage('push chart to repo') {
            steps {
                sh 'helm repo add helm-repo ${CHART_REPO_URL}'
                sh 'helm repo update'
                
                withCredentials([sshUserPrivateKey(credentialsId: 'privatekey', keyFileVariable: 'SSH_KEY')]) {
                    sh '''
                        git config --global user.email "you@example.com"
                        git config --global user.name "Your Name"
                        git add -A
                        git commit -m "Helm update"
                        ssh-agent bash -c 'ssh-add ${SSH_KEY}
                        git push origin HEAD:master'
                    '''
                }
            }
        }

        stage('install to minikube') {
            steps {
                sh '''
                    export DOCKER_TLS_VERIFY="1"
                    export DOCKER_HOST="tcp://192.168.49.2:2376"
                    export DOCKER_CERT_PATH="/root/.minikube/certs"
                    export MINIKUBE_ACTIVE_DOCKERD="minikube"
                    export KUBECONFIG="/root/.kube/config"
                    docker ps
                    helm upgrade --install pytest-release ${CHART_PATH}
                '''
            }
        }
    }
}

