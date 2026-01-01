pipeline {
  agent any
  environment {
    DJANGO_SETTINGS_MODULE = 'config.settings.base'
    PYTHONUNBUFFERED = '1'
    VPS_HOST = '198.12.74.104'
    VPS_USER = 'deploy'
    VPS_SSH_PORT = '20189'
    DEPLOY_DIR = '/srv/hrms'
    DOMAIN_NAME = 'hrms.kohinbox.top'
    PIP_BREAK_SYSTEM_PACKAGES = '1'
    POSTGRES_HOST = '172.17.0.1'
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Start database') {
      steps {
        sh 'docker compose -f ci/docker-compose.yml up -d db web'
        sh 'docker compose -f ci/docker-compose.yml ps'
      }
    }
    stage('Install dependencies') {
      steps {
         script {
           // Copy code into container because volume mount fails in DIND
           def webContainer = sh(script: "docker compose -f ci/docker-compose.yml ps -q web", returnStdout: true).trim()
           sh "docker cp . ${webContainer}:/app"
         }
         sh 'docker compose -f ci/docker-compose.yml exec -T web pip install -r requirements.txt'
      }
    }
    stage('Migrate & SQL scripts') {
      steps {
        sh '''
          docker compose -f ci/docker-compose.yml exec -T web python hrms/manage.py migrate
          docker compose -f ci/docker-compose.yml exec -T web python hrms/apply_triggers.py
          docker compose -f ci/docker-compose.yml exec -T web python hrms/apply_views.py
        '''
      }
    }
    stage('Lint') {
      steps {
        echo 'Skipping lint'
      }
    }
    stage('Test') {
      steps {
        sh 'docker compose -f ci/docker-compose.yml exec -T web python hrms/manage.py test apps.performance'
      }
    }
    stage('Deploy') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'vps-deploy-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          sh """
            set -euo pipefail
            ssh -o StrictHostKeyChecking=no -i $SSH_KEY -p ${VPS_SSH_PORT} ${VPS_USER}@${VPS_HOST} <<'EOF'
              cd ${DEPLOY_DIR}
              git fetch origin
              git reset --hard origin/main
              docker compose -f docker-compose.prod.yml pull
              docker compose -f docker-compose.prod.yml up -d --build
              docker compose -f docker-compose.prod.yml exec web python manage.py migrate
              docker compose -f docker-compose.prod.yml exec web python apply_triggers.py
              docker compose -f docker-compose.prod.yml exec web python apply_views.py
              docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
              docker compose -f docker-compose.prod.yml exec web python manage.py check
            EOF
          """
          sh "curl -fsSL https://${DOMAIN_NAME}/health/"
        }
      }
    }
  }
  post {
    always {
      sh 'docker compose -f ci/docker-compose.yml down --volumes'
    }
  }
}
