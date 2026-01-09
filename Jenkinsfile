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
    POSTGRES_HOST = 'db'
    POSTGRES_DB = 'hrms'
    POSTGRES_USER = 'postgres'
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Start database') {
      steps {
        sh 'docker compose -f ci/docker-compose.yml down --volumes --remove-orphans || true'
        sh 'docker compose -f ci/docker-compose.yml up -d --remove-orphans db web'
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
         sh 'docker compose -f ci/docker-compose.yml exec -T web python -m playwright install --with-deps chromium'
      }
    }
    stage('Migrate & SQL scripts') {
      steps {
        sh '''
          docker compose -f ci/docker-compose.yml exec -T web python hrms/manage.py migrate
          docker compose -f ci/docker-compose.yml exec -T web python hrms/apply_triggers.py
          docker compose -f ci/docker-compose.yml exec -T web python hrms/apply_views.py
          docker compose -f ci/docker-compose.yml exec -T web python hrms/init_data.py
        '''
      }
    }
    stage('Lint & Format') {
      steps {
        sh 'docker compose -f ci/docker-compose.yml exec -T web black .'
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
          // Execute tests and generate HTML report with all static assets embedded
          def webContainer = sh(script: "docker compose -f ci/docker-compose.yml ps -q web", returnStdout: true).trim()
          
          // 1. Run Unit/Integration tests (ignore e2e folder)
          def exitCode = sh(script: 'docker compose -f ci/docker-compose.yml exec -T web pytest --ignore=hrms/tests/e2e --cov=hrms/apps --cov-report=xml:coverage.xml --cov-report=html:htmlcov --junitxml=test-results.xml --html=report.html --self-contained-html -c pytest.ini', returnStatus: true)
          
          // 2. Run E2E tests specifically
          def e2eExitCode = sh(script: 'docker compose -f ci/docker-compose.yml exec -T web env PLAYWRIGHT_HEADLESS=true PLAYWRIGHT_SLOW_MO=0 pytest hrms/tests/e2e -m e2e --e2e --junitxml=e2e-results.xml --html=e2e-report.html --self-contained-html -c pytest.ini', returnStatus: true)
          
          sh "docker cp ${webContainer}:/app/test-results.xml ."
          sh "docker cp ${webContainer}:/app/report.html ."
          sh "docker cp ${webContainer}:/app/coverage.xml ."
          sh "docker cp ${webContainer}:/app/htmlcov ."
          sh "docker cp ${webContainer}:/app/e2e-results.xml ."
          sh "docker cp ${webContainer}:/app/e2e-report.html ."
          
          junit 'test-results.xml'
          junit 'e2e-results.xml'
          archiveArtifacts artifacts: 'report.html,coverage.xml,htmlcov/**', allowEmptyArchive: true
          archiveArtifacts artifacts: 'e2e-report.html', allowEmptyArchive: true

          try {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'report.html',
                reportName: 'Unit Test Report',
                reportTitles: 'HRMS Test Details'
            ])
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Code Coverage Report',
                reportTitles: 'HRMS Coverage Details'
            ])
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'e2e-report.html',
                reportName: 'E2E Test Report',
                reportTitles: 'HRMS E2E Details'
            ])
          } catch (Throwable e) {
            echo "Notice: High-level visual reports unavailable. Check 'Build Artifacts'."
          }

          if (exitCode != 0 || e2eExitCode != 0) {
            echo "Warning: Some tests failed!"
            currentBuild.result = 'UNSTABLE'
          } else {
            echo "Success! All tests passed."
            currentBuild.result = 'SUCCESS'
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
          
          // Use single-quoted Groovy string to avoid interpolating secrets in Groovy; shell expands env vars.
          sh '''
            set -euo pipefail
            # Copy script to VPS
            scp -o StrictHostKeyChecking=no -i $SSH_KEY -P $VPS_SSH_PORT deploy.sh $VPS_USER@$VPS_HOST:/tmp/deploy.sh
            # Execute script
            ssh -o StrictHostKeyChecking=no -i $SSH_KEY -p $VPS_SSH_PORT $VPS_USER@$VPS_HOST "chmod +x /tmp/deploy.sh && /tmp/deploy.sh"
            # Health check (may redirect to login)
            curl -fsSL https://$DOMAIN_NAME/
          '''
        }
      }
    }
  }
  post {
    always {
      sh 'docker compose -f ci/docker-compose.yml down --volumes --remove-orphans'
    }
  }
}
