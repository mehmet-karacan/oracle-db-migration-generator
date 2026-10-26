// Trusted job configuration. Read-only comparison; fixed-recipient Jenkins notification.
pipeline {
  agent { label 'jenkins-2' }
  options {
    disableConcurrentBuilds()
    skipDefaultCheckout(true)
    timeout(time: 120, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '20'))
  }
  parameters {
    choice(name: 'SCHEMA_SCOPE', choices: ['TTBP', 'INNOVA_ODI'], description: 'Varsayılan günlük kapsam TTBP. INNOVA_ODI yalnız manuel istekle seçilir.')
    choice(name: 'RUN_MODE', choices: ['COMPARE', 'ENVIRONMENT_CHECK'], description: 'COMPARE yalnız Git okuma ve Oracle metadata okuması yapar. SQL uygulanmaz.')
    stashedFile(name: 'GENERATOR_RELEASE', description: 'İlk kurulumda SHA ile doğrulanan release ZIP. Sonraki çalışmalarda boş bırakılabilir.')
  }
  environment {
    PYTHONUTF8 = '1'
    PYTHONDONTWRITEBYTECODE = '1'
    GENERATOR_BUILD_STARTED_AT_MS = "${currentBuild.startTimeInMillis}"
    GENERATOR_CONFIG_DIR = ".runtime/scopes/build-${env.BUILD_NUMBER}"
    GENERATOR_PARSER_CACHE_DIR = '.runtime/parser-cache'
    GENERATOR_PREPARED_SOURCE_CACHE_DIR = '.runtime/prepared-source-cache'
    GENERATOR_RELEASE_SHA = '@@RELEASE_SHA@@'
    GENERATOR_RELEASE_DIR = '.runtime/releases/@@RELEASE_SHA@@'
    GENERATOR_RUNTIME_DIR = '.runtime/python/@@RELEASE_SHA@@-r3'
  }
  stages {
    stage('Doğrulanmış Python 3.12 ve Generator') {
      steps {
        sh 'mkdir -p .runtime'
        writeFile(file: '.runtime/jenkins_bootstrap.py', text: '@@BOOTSTRAP_BASE64@@', encoding: 'Base64')
        withFileParameter(name: 'GENERATOR_RELEASE', allowNoFile: true) {
          sh '''#!/bin/sh
set -eu
set +x
if [ -n "${GENERATOR_RELEASE:-}" ]; then
  python3 .runtime/jenkins_bootstrap.py --archive "$GENERATOR_RELEASE" --release "$GENERATOR_RELEASE_DIR" --sha256 "$GENERATOR_RELEASE_SHA" --runtime "$GENERATOR_RUNTIME_DIR"
else
  python3 .runtime/jenkins_bootstrap.py --release "$GENERATOR_RELEASE_DIR" --sha256 "$GENERATOR_RELEASE_SHA" --runtime "$GENERATOR_RUNTIME_DIR"
fi
'''
        }
      }
    }
    stage('Seçili şema kapsamını hazırla') {
      steps {
        writeFile(file: '.runtime/jenkins_scope.py', text: '@@SCOPE_BASE64@@', encoding: 'Base64')
        script { env.GENERATOR_SCHEMA_SCOPE = params.SCHEMA_SCOPE ?: 'TTBP' }
        sh '''#!/bin/sh
set -eu
set +x
"$GENERATOR_RUNTIME_DIR/venv/bin/python" .runtime/jenkins_scope.py --release "$GENERATOR_RELEASE_DIR" --output "$GENERATOR_CONFIG_DIR" --schema "$GENERATOR_SCHEMA_SCOPE"
'''
      }
    }
    stage('Kaynağı sabit SHA ile oku') {
      when { expression { params.RUN_MODE == 'COMPARE' } }
      steps {
        script {
          def settings = readJSON file: "${env.GENERATOR_CONFIG_DIR}/config/job-settings.json"
          dir(".source/build-${env.BUILD_NUMBER}") {
            def revision = checkout([$class: 'GitSCM', branches: [[name: settings.source_ref]],
                userRemoteConfigs: [[url: settings.source_url, credentialsId: '@@SOURCE_CREDENTIAL@@']],
                gitTool: 'jgit', extensions: []])
            env.GENERATOR_SOURCE_SHA = revision.GIT_COMMIT
          }
        }
      }
    }
    stage('Salt okunur karşılaştırma ve rapor') {
      steps {
        script {
          def code
          if (params.RUN_MODE == 'ENVIRONMENT_CHECK') {
            code = sh(returnStatus: true, script: '''#!/bin/sh
set -eu
set +x
"$GENERATOR_RUNTIME_DIR/venv/bin/python" "$GENERATOR_RELEASE_DIR/jenkins_run.py" --release "$GENERATOR_CONFIG_DIR" --mode ENVIRONMENT_CHECK --output "output/runs/build-$BUILD_NUMBER"
''')
          } else {
            withCredentials([usernamePassword(credentialsId: '@@TARGET_CREDENTIAL@@', usernameVariable: 'GENERATOR_INNOVA_ODI_USER', passwordVariable: 'GENERATOR_INNOVA_ODI_PASSWORD'), usernamePassword(credentialsId: '@@SOURCE_METADATA_CREDENTIAL@@', usernameVariable: 'GENERATOR_SOURCE_ODI_USER', passwordVariable: 'GENERATOR_SOURCE_ODI_PASSWORD'), usernamePassword(credentialsId: '@@TTBP_TARGET_CREDENTIAL@@', usernameVariable: 'GENERATOR_TTBP_USER', passwordVariable: 'GENERATOR_TTBP_PASSWORD'), usernamePassword(credentialsId: '@@TTBP_CREDENTIAL@@', usernameVariable: 'GENERATOR_SOURCE_TTBP_USER', passwordVariable: 'GENERATOR_SOURCE_TTBP_PASSWORD')]) {
              code = sh(returnStatus: true, script: '''#!/bin/sh
set -eu
set +x
export GENERATOR_ORACLE_CLIENT_DIR="$(pwd)/$GENERATOR_RELEASE_DIR/instantclient"
export LD_LIBRARY_PATH="$GENERATOR_ORACLE_CLIENT_DIR:${LD_LIBRARY_PATH:-}"
"$GENERATOR_RUNTIME_DIR/venv/bin/python" "$GENERATOR_RELEASE_DIR/jenkins_run.py" --release "$GENERATOR_CONFIG_DIR" --mode COMPARE --source-dir ".source/build-$BUILD_NUMBER" --source-commit "$GENERATOR_SOURCE_SHA" --output "output/runs/build-$BUILD_NUMBER"
''')
            }
          }
          if (code == 10 || code == 20) {
            unstable('Karşılaştırma raporlandı; inceleme/engelli veya UNKNOWN hedef sonuçları var. Hazır SQL dosyaları arşivdedir.')
          } else if (code != 0) {
            error("Generator güvenilir sonuç üretemedi; güvenli hata kodu ${code}.")
          }
        }
      }
    }
  }
  post {
    always {
      archiveArtifacts(artifacts: "output/runs/build-${env.BUILD_NUMBER}/**", excludes: "output/runs/build-${env.BUILD_NUMBER}/observations/**", allowEmptyArchive: true, fingerprint: true)
      script {
        if (fileExists("output/runs/build-${env.BUILD_NUMBER}/index.html")) {
          currentBuild.description = "PROD · ${env.GENERATOR_SCHEMA_SCOPE} · Source/target READ ONLY · SQL uygulanmadı"
        }
        if (params.RUN_MODE == 'COMPARE') {
          def report = "output/runs/build-${env.BUILD_NUMBER}/report-email.jenkins.html"
          emailext(to: '@@NOTIFY_TO@@',
            subject: "SKY | Oracle DB Migration Generator | ${currentBuild.currentResult} | Build #${env.BUILD_NUMBER}",
            mimeType: 'text/html', attachLog: false,
            attachmentsPattern: '',
            body: fileExists(report) ? readFile(report) : "<html><body><h2>PROD · ${env.GENERATOR_SCHEMA_SCOPE} karşılaştırması: ${currentBuild.currentResult}</h2><p>Genel rapor üretilemedi. Source ve target salt okunur; SQL uygulanmadı.</p><p><a href='${env.BUILD_URL}'>Jenkins çalışma kaydı</a></p></body></html>")
        }
      }
    }
  }
}
