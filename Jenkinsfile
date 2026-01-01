pipeline {
  agent any
  environment {
    DJANGO_SETTINGS_MODULE = 'config.settings.base'
    PYTHONUNBUFFERED = '1'
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Install dependencies') {
      steps {
        sh 'python -m pip install --upgrade pip'
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
          python manage.py migrate
          python hrms/apply_triggers.py
          python hrms/apply_views.py
        '''
      }
    }
    stage('Lint') {
      steps {
        sh 'black --check .'
        sh 'ruff check apps utils'
      }
    }
    stage('Test') {
      steps {
        sh 'python manage.py test apps.performance'
      }
    }
    stage('Deploy') {
      steps {
        sh 'bash scripts/deploy.sh'
      }
    }
  }
  post {
    always {
      sh 'docker compose -f ci/docker-compose.yml down --volumes'
    }
  }
}
