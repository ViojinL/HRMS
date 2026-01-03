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
        sh 'docker compose -f ci/docker-compose.yml exec -T web black --check .'
      }
    }
    stage('Security Scan') {
      steps {
        script {
          def webContainer = sh(script: "docker compose -f ci/docker-compose.yml ps -q web", returnStdout: true).trim()
          // Run bandit, don't fail build on issues, just report
          sh "docker compose -f ci/docker-compose.yml exec -T web bandit -r hrms/apps -f json -o bandit_report.json || true"
          sh "docker cp ${webContainer}:/app/bandit_report.json ."
          archiveArtifacts artifacts: 'bandit_report.json', allowEmptyArchive: true
        }
      }
    }
    stage('Test') {
      steps {
        script {
          def webContainer = sh(script: "docker compose -f ci/docker-compose.yml ps -q web", returnStdout: true).trim()
          // Run pytest with coverage and junit xml
          // Return status code to handle failure after copying artifacts
          def exitCode = sh(script: 'docker compose -f ci/docker-compose.yml exec -T web pytest --cov=hrms/apps --cov-report=xml:coverage.xml --junitxml=test-results.xml', returnStatus: true)
          
          // Copy artifacts out of container
          sh "docker cp ${webContainer}:/app/test-results.xml ."
          sh "docker cp ${webContainer}:/app/coverage.xml ."
          
          // publish reports
          junit 'test-results.xml'
          archiveArtifacts artifacts: 'coverage.xml'
          
          if (exitCode != 0) {
            error("Tests failed")
          }
        }
      }
    }
    stage('Deploy') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'vps-deploy-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          // Create a deployment script
          writeFile file: 'deploy.sh', text: '''#!/bin/bash
            set -euo pipefail
            cd /srv/hrms
            git fetch origin
            git reset --hard origin/main
            # Verify env file exists
            if [ ! -f .env.prod ]; then
              echo "Error: .env.prod not found!"
              exit 1
            fi
            docker compose -f docker-compose.prod.yml --env-file .env.prod pull
            docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
            # Wait for DB to be ready
            sleep 10
            docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T web python hrms/manage.py migrate
            docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T web python hrms/apply_triggers.py
            docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T web python hrms/apply_views.py
            docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T web python hrms/manage.py collectstatic --noinput
            docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T web python hrms/manage.py check
          '''
          
          sh """
            set -euo pipefail
            # Copy script to VPS
            scp -o StrictHostKeyChecking=no -i $SSH_KEY -P ${VPS_SSH_PORT} deploy.sh ${VPS_USER}@${VPS_HOST}:/tmp/deploy.sh
            # Execute script
            ssh -o StrictHostKeyChecking=no -i $SSH_KEY -p ${VPS_SSH_PORT} ${VPS_USER}@${VPS_HOST} "chmod +x /tmp/deploy.sh && /tmp/deploy.sh"
            # Health check
            curl -fsSL https://${DOMAIN_NAME}/ # health might redirect to login, just check root for now or health endpoint if no auth required
          """
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
