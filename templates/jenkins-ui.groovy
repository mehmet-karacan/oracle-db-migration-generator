// Ayrı manuel UI işi. Mevcut 08:00 karşılaştırma işine uygulanmaz.
// Placeholder'lar kurulum belgesine göre yönetici tarafından doldurulur.
pipeline {
  agent { label '@@UI_AGENT_LABEL@@' }
  options {
    skipDefaultCheckout(true)
    buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '20'))
    timeout(time: 250, unit: 'MINUTES')
  }
  parameters { string(name: 'RUN_ID', defaultValue: '', description: 'API tarafından oluşturulan çalışma kimliği') }
  environment {
    ODMG_UI_STATE_ROOT = '@@PROTECTED_SHARED_STATE_PATH@@'
    ODMG_UI_PYTHON = '@@UI_VENV_PYTHON_PATH@@'
    ODMG_UI_RELEASE = '@@IMMUTABLE_RELEASE_PATH@@'
    ODMG_ORACLE_CLIENT_DIR = '@@ORACLE_CLIENT_PATH@@'
  }
  stages {
    stage('Salt okunur UI karşılaştırması') {
      steps {
        script {
          if (!(params.RUN_ID ==~ /[0-9a-f]{32}/)) { error('Geçersiz çalışma kimliği') }
          env.ODMG_RUN_ID = params.RUN_ID
          withCredentials([string(credentialsId: '@@UI_VAULT_KEY_CREDENTIAL_ID@@', variable: 'ODMG_UI_VAULT_KEY')]) {
            def code = sh(returnStatus: true, script: '''#!/bin/sh
set -eu
set +x
"$ODMG_UI_PYTHON" -m oracle_db_migration_generator.control.worker --root "$ODMG_UI_STATE_ROOT" --run "$ODMG_RUN_ID"
''')
            sh '''#!/bin/sh
set -eu
set +x
"$ODMG_UI_PYTHON" "$ODMG_UI_RELEASE/tools/ui_jenkins_archive.py" --root "$ODMG_UI_STATE_ROOT" --run "$ODMG_RUN_ID" --output "output/runs/build-$BUILD_NUMBER" --build-number "$BUILD_NUMBER" --build-url "$BUILD_URL" --job-url "$JOB_URL"
'''
            if (code == 10) { unstable('Kısmi karşılaştırma: inceleme/engeller korunuyor') }
            else if (code != 0) { currentBuild.result = 'FAILURE' }
          }
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts(artifacts: "output/runs/build-${env.BUILD_NUMBER}/**", allowEmptyArchive: true, fingerprint: true)
      script {
        if (fileExists(".local/ui-notify-build-${env.BUILD_NUMBER}.json")) {
          def notification = readJSON file: ".local/ui-notify-build-${env.BUILD_NUMBER}.json"
          if (notification.enabled && notification.to == 'mkaracan@innova.com.tr') {
            emailext(to: 'mkaracan@innova.com.tr',
              subject: "SKY | Oracle DB Migration Generator | ${currentBuild.currentResult} | UI #${env.BUILD_NUMBER}",
              mimeType: 'text/html', attachLog: false, attachmentsPattern: '',
              body: readFile("output/runs/build-${env.BUILD_NUMBER}/report-email.jenkins.html"))
          }
        }
      }
    }
  }
}
