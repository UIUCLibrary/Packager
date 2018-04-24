#!groovy
@Library("ds-utils@v0.2.0") // Uses library from https://github.com/UIUCLibrary/Jenkins_utils
import org.ds.*

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
        string(name: "PROJECT_NAME", defaultValue: "Packager", description: "Name given to the project")
        booleanParam(name: "BUILD_DOCS", defaultValue: true, description: "Build documentation")
        booleanParam(name: "UNIT_TESTS", defaultValue: true, description: "Run automated unit tests")
        booleanParam(name: "ADDITIONAL_TESTS", defaultValue: true, description: "Run additional tests")
        booleanParam(name: "PACKAGE", defaultValue: true, description: "Create a package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        choice(choices: 'None\nRelease_to_devpi_only', description: "Release the build to production. Only available in the Master branch", name: 'RELEASE')
        booleanParam(name: "UPDATE_DOCS", defaultValue: false, description: "Update online documentation")
        string(name: 'URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    stages {

        stage("Configure Environment") {
            steps {
                bat "${tool 'CPython-3.6'} -m venv venv"
                bat 'venv\\Scripts\\python.exe -m pip install devpi-client'
                bat 'venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                bat 'venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt'
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
                stage("Behave") {
                    agent {
                        label 'Windows && DevPi'
                    }
                    when {
                       expression { params.UNIT_TESTS == true }
                    }
                    steps {
                        bat "${tool 'CPython-3.6'} -m venv venv"
                        bat 'venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                        bat 'venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt'
                        bat "venv\\Scripts\\python.exe -m tox -e behave -- --junit --junit-directory reports/behave"
                        junit "reports/behave/*.xml"
                    }
                }
                stage("Pytest"){
                    agent {
                        label 'Windows && DevPi'
                    }
                    when {
                       expression { params.UNIT_TESTS == true }
                    }
                    steps{
                        script {
                            def junit_filename = "junit-${env.NODE_NAME}-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                            bat "${tool 'CPython-3.6'} -m venv venv"
                            bat 'venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                            bat 'venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt'
                            bat "venv\\Scripts\\python.exe -m tox -e pytest -- --junitxml=reports/pytest/${junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:reports/pytestcoverage/ --cov=uiucprescon/packager"
                            junit "reports/pytest/${junit_filename}"
                        }
                        publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/pytestcoverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                    }
                }
                stage("Doctest"){
                    agent {
                        label 'Windows && DevPi'
                    }
                    when {
                       expression { params.ADDITIONAL_TESTS == true }
                    }
                    steps {
                        script{
                            bat "${tool 'CPython-3.6'} -m venv venv"
                            bat 'venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                            bat 'venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt'
                            bat "venv\\Scripts\\tox.exe -e docs"
                        }
                    }
                }
                stage("MyPy") {
                    when {
                        expression { params.ADDITIONAL_TESTS == true }
                        // equals expected: true, actual: params.TEST_RUN_MYPY
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
                stage("Flake8") {
                    when {
                        expression { params.ADDITIONAL_TESTS == true }
                        // equals expected: true, actual: params.TEST_RUN_FLAKE8
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
        stage("Additional tests") {
            when {
                expression { params.ADDITIONAL_TESTS == true }
            }

            steps {
                parallel(
                        "Documentation": {
                            node(label: "Windows&&DevPi") {
                                checkout scm
                                bat "${tool 'Python3.6.3_Win64'} -m tox -e docs"
                                script{
                                    // Multibranch jobs add the slash and add the branch to the job name. I need only the job name
                                    def alljob = env.JOB_NAME.tokenize("/") as String[]
                                    def project_name = alljob[0]
                                    dir('.tox/dist') {
                                        zip archive: true, dir: 'html', glob: '', zipFile: "${project_name}-${env.BRANCH_NAME}-docs-html-${env.GIT_COMMIT.substring(0,6)}.zip"
                                        dir("html"){
                                            stash includes: '**', name: "HTML Documentation"
                                        }
                                        dir("doctest"){
                                            bat "copy output.txt sphinx-doctest-results-${env.GIT_COMMIT.substring(0,6)}.txt"
                                            archiveArtifacts artifacts: "sphinx-doctest-results-${env.GIT_COMMIT.substring(0,6)}.txt", allowEmptyArchive: true
                                        }
                                    }
                                }
                                publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: '.tox/dist/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            }
                        },
                        "MyPy": {
                     
                        node(label: "Windows&&DevPi") {
                            checkout scm
                            bat "call make.bat install-dev"
                            bat "venv\\Scripts\\mypy.exe -p uiucprescon --junit-xml=junit-${env.NODE_NAME}-mypy.xml --html-report reports/mypy_html"

                            junit "junit-${env.NODE_NAME}-mypy.xml"
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy_html', reportFiles: 'index.html', reportName: 'MyPy', reportTitles: ''])
                         }
                    },
                )
            }
        }
        stage("Packaging") {
            when {
                expression { params.PACKAGE == true }
            }

            steps {
                parallel(
                        "Source and Wheel formats": {
                            bat "call make.bat"
                        },
                )
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

        stage("Deploying to Devpi") {
            when {
                expression { params.DEPLOY_DEVPI == true && (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev") }
            }
            steps {
                bat "${tool 'Python3.6.3_Win64'} -m devpi use http://devpy.library.illinois.edu"
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
                expression { params.DEPLOY_DEVPI == true  && (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev")}
            }
            steps {
                parallel(
                        "Source": {
                            script {
                                def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                                def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                                node("Windows&&DevPi") {
                                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                        bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                        bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                        echo "Testing Source package in devpi"
                                        bat "${tool 'Python3.6.3_Win64'} -m devpi test --index http://devpy.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s tar.gz"
                                    }
                                }

                            }
                        },
                        "Wheel": {
                            script {
                                def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                                def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                                node("Windows&&DevPi") {
                                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                                        bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                                        bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                                        echo "Testing Whl package in devpi"
                                        bat " ${tool 'Python3.6.3_Win64'} -m devpi test --index http://devpy.library.illinois.edu/${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${name} -s whl"
                                    }
                                }

                            }
                        }
                )

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
                expression { params.RELEASE != "None" && env.BRANCH_NAME == "master" }
            }

            steps {
                script {
                    if (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev"){
                        def name = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --name").trim()
                        def version = bat(returnStdout: true, script: "@${tool 'Python3.6.3_Win64'} setup.py --version").trim()
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            bat "${tool 'Python3.6.3_Win64'} -m devpi login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            bat "${tool 'Python3.6.3_Win64'} -m devpi use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                            bat "${tool 'Python3.6.3_Win64'} -m devpi push ${name}==${version} production/release"
                        }
                    }

                }
                node("Linux"){
                    updateOnlineDocs url_subdomain: params.URL_SUBFOLDER, stash_name: "HTML Documentation"
                }
            }
        }
        stage("Update online documentation") {
            agent {
                label "Linux"
            }
            when {
              expression {params.UPDATE_DOCS == true }
            }

            steps {
                updateOnlineDocs url_subdomain: params.URL_SUBFOLDER, stash_name: "HTML Documentation"
            }
        }
    }
}
