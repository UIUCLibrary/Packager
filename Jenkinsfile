#!groovy
// @Library("ds-utils@v0.2.0") // Uses library from https://github.com/UIUCLibrary/Jenkins_utils
// import org.ds.*

pipeline {
    agent {
        label "Windows&&DevPi"
    }
    triggers {
        cron('@daily')
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
    }

    parameters {
        // string(name: "PROJECT_NAME", defaultValue: "Packager", description: "Name given to the project")
        booleanParam(name: "BUILD_DOCS", defaultValue: true, description: "Build documentation")
        booleanParam(name: "TEST_UNIT_TESTS", defaultValue: true, description: "Run automated unit tests")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy Tests")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 Tests")
        booleanParam(name: "TEST_DOCTEST", defaultValue: true, description: "Run Doctest on the documentation")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Release Branch Only")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation. Release Branch Only")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    stages {

        stage("Configure Environment") {
            steps {
                bat "${tool 'CPython-3.6'} -m venv venv"
                bat 'venv\\Scripts\\python.exe -m pip install devpi-client'
                bat 'venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                bat 'venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt'
                bat 'venv\\Scripts\\python.exe -m pip install pytest-cov'
                bat 'venv\\Scripts\\python.exe -m pip install pykdu-compress'
                dir("reports/behave"){
                    echo "build reports/behave"
                }
                dir("reports/pytestcoverage"){
                    echo "build reports/pytestcoverage"
                }
                dir("reports/pytest"){
                    echo "build reports/pytest"
                }
            }

        }
        stage('Build') {
            parallel {
                stage("Python Package"){
                    environment {
                        PATH = "${tool 'cmake_3.11.1'};$PATH"
                    }
                    steps {
                        tee('build.log') {
                            bat "venv\\Scripts\\python.exe setup.py build"
                        }
                    }
                    post{
                        always{
                            warnings parserConfigurations: [[parserName: 'Pep8', pattern: 'build.log']]
                            archiveArtifacts artifacts: 'build.log'
                        }
                    }
                }
                stage("Sphinx documentation"){
                    when {
                        equals expected: true, actual: params.BUILD_DOCS
                    }
                    steps {
                        tee('build_sphinx.log') {
                            bat "venv\\Scripts\\python.exe setup.py build_sphinx"
                        }
                    }
                    post{
                        always {
                            warnings parserConfigurations: [[parserName: 'Pep8', pattern: 'build_sphinx.log']]
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                // Multibranch jobs add the slash and add the branch to the job name. I need only the job name
                                def alljob = env.JOB_NAME.tokenize("/") as String[]
                                def project_name = alljob[0]
                                dir('build/docs/') {
                                    zip archive: true, dir: 'html', glob: '', zipFile: "${project_name}-${env.BRANCH_NAME}-docs-html-${env.GIT_COMMIT.substring(0,7)}.zip"
                                    dir("html"){
                                        stash includes: '**', name: "HTML Documentation"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        stage("Test") {
            parallel {
                stage("Run Behave BDD Tests") {
                    when {
                       equals expected: true, actual: params.TEST_UNIT_TESTS
                    }
                    steps {
                        bat "venv\\Scripts\\behave.exe --junit --junit-directory reports/behave"
                    }
                    post {
                        always {
                            junit "reports/behave/*.xml"
                        }
                    }
                }
                stage("Run Pytest Unit Tests"){
                    when {
                       equals expected: true, actual: params.TEST_UNIT_TESTS
                    }
                    environment{
                        junit_filename = "junit-${env.NODE_NAME}-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                    }
                    steps{
                        bat "venv\\Scripts\\py.test.exe --junitxml=reports/pytest/${junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:reports/pytestcoverage/ --cov=uiucprescon/packager"
                    }
                    post {
                        always {
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/pytestcoverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                            junit "reports/pytest/${junit_filename}"
                        }
                    }
                }
                stage("Run Doctest Tests"){
                    when {
                       equals expected: true, actual: params.TEST_DOCTEST
                    }
                    steps {
                        bat "venv\\Scripts\\sphinx-build.exe -b doctest -d build/docs/doctrees docs/source reports/doctest"
                    }
                    post{
                        always {
                            archiveArtifacts artifacts: 'reports/doctest/output.txt'
                        }
                    }
                }
                stage("Run MyPy Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_MYPY
                    }
                    steps{
                        script{
                            try{
                                tee('mypy.log') {
                                    bat "venv\\Scripts\\mypy.exe -p uiucprescon --html-report reports\\mypy\\html\\"
                                }
                            } catch (exc) {
                                echo "MyPy found some warnings"
                            }      
                        }
                    }
                    post {
                        always {
                            warnings parserConfigurations: [[parserName: 'MyPy', pattern: 'mypy.log']], unHealthy: ''
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                        }
                    }
                }
                stage("Run Tox test") {
                    when{
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    agent{
                        label "Windows&&DevPi"
                    }
                    steps {
                        bat "${tool 'CPython-3.6'} -m venv venv"
                        bat 'venv\\Scripts\\python.exe -m pip install tox'
                        bat "venv\\Scripts\\tox.exe"
                    }
                }
                stage("Run Flake8 Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_FLAKE8
                    }
                    steps{
                        script{
                            try{
                                tee('flake8.log') {
                                    bat "venv\\Scripts\\flake8.exe uiucprescon --format=pylint"
                                }
                            } catch (exc) {
                                echo "flake8 found some warnings"
                            }
                        }
                    }
                    post {
                        always {
                            warnings parserConfigurations: [[parserName: 'PyLint', pattern: 'flake8.log']], unHealthy: ''
                        }
                    }
                }
            }
        }

        stage("Package") {

            steps {
                bat "venv\\Scripts\\python.exe setup.py bdist_wheel sdist"
            }
            post {
              success {
                  dir("dist"){
                      archiveArtifacts artifacts: "*.whl", fingerprint: true
                      archiveArtifacts artifacts: "*.tar.gz", fingerprint: true
                }
              }
            }

        }

        stage("Deploy to Devpi Staging") {
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            steps {
                bat "${tool 'Python3.6.3_Win64'} -m devpi use http://devpi.library.illinois.edu"
                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                    bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                    bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                    script {
                        bat "${tool 'Python3.6.3_Win64'} -m devpi upload --from-dir dist"
                        try {
                            bat "${tool 'Python3.6.3_Win64'} -m devpi upload --only-docs"
                        } catch (exc) {
                            echo "Unable to upload to devpi with docs."
                        }
                    }
                }

            }
        }
        stage("Test Devpi packages") {
             when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            parallel {
                stage("Test Source Distribution: .tar.gz") {
                    steps {
                        script {
                            def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                            def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                            node("Windows && DevPi") {
                                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                    bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                    bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                    echo "Testing Source package in devpi"
                                    bat "${tool 'Python3.6.3_Win64'} -m devpi test --index http://devpi.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s tar.gz"
                                }
                            }
                        }
                    }
                }
                stage("Test Source Distribution: .zip") {
                    steps {
                        script {
                            def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                            def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                            node("Windows && DevPi") {
                                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                    bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                    bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                    echo "Testing Source package in devpi"
                                    bat "${tool 'Python3.6.3_Win64'} -m devpi test --index http://devpi.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s zip"
                                }
                            }
                        }
                    }
                }
                stage("Test Built Distribution: .whl") {
                    steps {
                        script {
                            def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --name").trim()
                            def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                            node("Windows") {
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                                bat "venv\\Scripts\\devpi.exe use https://devpi.library.illinois.edu"
                                withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                echo "Testing Whl package in devpi"
                                bat "venv\\Scripts\\devpi.exe test --index https://devpi.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s whl"
                                }
                            }
                        }
                    }
                }
            }
            post {
                success {
                    echo "It Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                        def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                            bat "${tool 'Python3.6.3_Win64'} -m devpi push ${name}==${version} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
                        }

                    }
                }
            }
        }
        stage("Release to DevPi production") {
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                    branch "master"
                }
            }

            steps {
                script {
                    def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                    def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                        bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                        bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                        bat "${tool 'Python3.6.3_Win64'} -m devpi push ${name}==${version} production/release"
                    }
                }
            }
            post{
                success{
                    build job: 'Speedwagon/master', 
                        parameters: [
                            string(name: 'PROJECT_NAME', value: 'Speedwagon'), 
                            booleanParam(name: 'UPDATE_JIRA_EPIC', value: false), 
                            string(name: 'JIRA_ISSUE', value: 'PSR-83'), 
                            booleanParam(name: 'TEST_RUN_PYTEST', value: true), 
                            booleanParam(name: 'TEST_RUN_BEHAVE', value: true), 
                            booleanParam(name: 'TEST_RUN_DOCTEST', value: true), 
                            booleanParam(name: 'TEST_RUN_FLAKE8', value: true), 
                            booleanParam(name: 'TEST_RUN_MYPY', value: true), 
                            booleanParam(name: 'PACKAGE_PYTHON_FORMATS', value: true), 
                            booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE', value: true), 
                            booleanParam(name: 'DEPLOY_DEVPI', value: true), 
                            string(name: 'RELEASE', value: 'None'), 
                            booleanParam(name: 'UPDATE_DOCS', value: false), 
                            string(name: 'URL_SUBFOLDER', value: 'speedwagon')
                        ], 
                        wait: false

                }
            }
        }
        stage("Deploy Online Documentation") {
          when {
            allOf{
              equals expected: true, actual: params.DEPLOY_DOCS
              branch "master"
            }
          }
          steps {
            bat "venv\\Scripts\\python.exe setup.py build_sphinx"
            dir("build/docs/html/"){
              sshPublisher(
                publishers: [
                  sshPublisherDesc(
                    configName: 'apache-ns - lib-dccuser-updater', 
                    sshLabel: [label: 'Linux'], 
                    transfers: [sshTransfer(excludes: '', 
                    execCommand: '', 
                    execTimeout: 120000, 
                    flatten: false, 
                    makeEmptyDirs: false, 
                    noDefaultExcludes: false, 
                    patternSeparator: '[, ]+', 
                    remoteDirectory: "${params.DEPLOY_DOCS_URL_SUBFOLDER}", 
                    remoteDirectorySDF: false, 
                    removePrefix: '', 
                    sourceFiles: '**')], 
                  usePromotionTimestamp: false, 
                  useWorkspaceInPromotion: false, 
                  verbose: true
                  )
                ]
              )
            }
          }
        }
    }
    post {
        cleanup {
            bat "venv\\Scripts\\python.exe setup.py clean --all"
        
            dir('dist') {
                deleteDir()
            }
            dir('build') {
                deleteDir()
            }
            script {
                if (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev"){
                    def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --name").trim()
                    def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                        bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                        bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                        try {
                            bat "venv\\Scripts\\devpi.exe remove -y ${name}==${version}"
                        } catch (Exception ex) {
                            echo "Failed to remove ${name}==${version} from ${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                        }
                        
                    }
                }
            }
        }
    }
}
