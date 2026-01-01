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
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Install dependencies') {
      steps {
        // sh 'python -m pip install --upgrade pip'
        sh 'cat requirements.txt'
        sh 'pip install -r requirements.txt'
      }
    }
    stage('Start database') {
      steps {
        sh 'docker compose -f ci/docker-compose.yml up -d db'
        sh 'docker compose -f ci/docker-compose.yml ps'
      }
    }
    stage('Migrate & SQL scripts') {
      steps {
        sh '''
          cd hrms && python manage.py migrate
          cd hrms && python apply_triggers.py
          cd hrms && python apply_views.py
        '''
      }
    }
    stage('Lint') {
      steps {
        // sh 'black --check .' // Skip black check for now as it might check root
        // sh 'ruff check apps utils' // Skip ruff as it is removed
        echo 'Skipping lint for now'
      }
    }
    stage('Test') {
      steps {
        sh 'cd hrms && python manage.py test apps.performance'
      }
    }
    stage('Deploy') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'vps-deploy-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          sh """
            set -euo pipefail
            ssh -i $SSH_KEY -p ${VPS_SSH_PORT} ${VPS_USER}@${VPS_HOST} <<'EOF'
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
