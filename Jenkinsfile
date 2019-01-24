#!groovy
@Library(["devpi", "PythonHelpers"]) _

//  TODO: Replace WARNINGS commands with reportIssues

def remove_files(artifacts){
    script{
        def files = findFiles glob: "${artifacts}"
        files.each { file_name ->
            bat "del ${file_name}"
        }
    }
}


def remove_from_devpi(devpiExecutable, pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
    script {
                try {
                    bat "${devpiExecutable} login ${devpiUsername} --password ${devpiPassword}"
                    bat "${devpiExecutable} use ${devpiIndex}"
                    bat "${devpiExecutable} remove -y ${pkgName}==${pkgVersion}"
                } catch (Exception ex) {
                    echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
            }

    }
}

pipeline {
    agent {
        label "Windows && Python3"
    }
    triggers {
        cron('@daily')
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
        timeout(60)
        checkoutToSubdirectory("source")
        preserveStashes()
    }
    environment {
        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
        PKG_NAME = pythonPackageName(toolName: "CPython-3.6")
        PKG_VERSION = pythonPackageVersion(toolName: "CPython-3.6")
        DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
        DEVPI = credentials("DS_devpi")
    }

    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
        booleanParam(name: "BUILD_DOCS", defaultValue: true, description: "Build documentation")
        booleanParam(name: "TEST_UNIT_TESTS", defaultValue: true, description: "Run automated unit tests")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy Tests")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 Tests")
        booleanParam(name: "TEST_DOCTEST", defaultValue: true, description: "Run Doctest on the documentation")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Master branch Only")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation. Master branch Only")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Configure Environment") {
            stages{
                stage("Purge all existing data in workspace"){
                    when{
                        equals expected: true, actual: params.FRESH_WORKSPACE
                    }
                    steps{
                        deleteDir()
                        dir("source"){
                            checkout scm
                        }
                    }
                }
//                stage("Cleanup"){
//                    steps {
//                        dir("logs"){
//                            deleteDir()
//                            bat "dir > nul"
//                        }
//                        dir("build"){
//                            deleteDir()
//                            echo "Cleaned out build directory"
//                            bat "dir > nul"
//                        }
//                        dir("dist"){
//                            deleteDir()
//                            echo "Cleaned out dist directory"
//                            bat "dir > nul"
//                        }
//
//                        dir("reports"){
//                            deleteDir()
//                            echo "Cleaned out reports directory"
//                            bat "dir > nul"
//                        }
//                        dir("certs"){
//                            deleteDir()
//                            echo "Cleaned out certs directory"
//                            bat "dir > nul"
//                        }
//                    }
//                    post{
//                        failure {
//                            deleteDir()
//                        }
//                    }
//                }
                stage("Installing Required System Level Dependencies"){
                    steps{
                        lock("system_python_${NODE_NAME}"){
                            bat "python -m pip install pip --upgrade --quiet && python -m pip install --upgrade pipenv --quiet"
                        }



                    }
                    post{
                        always{
                            bat "(if not exist logs mkdir logs) && python -m pip list > logs/pippackages_system_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }
                        failure {
                            deleteDir()
                        }
                    }

                }
            
                stage("Creating Virtualenv for Building"){
                    steps {
                        bat "python -m venv venv"

                        script {
                            try {
                                bat "venv\\Scripts\\python.exe -m pip install -U pip --quiet"
                            }
                            catch (exc) {
                                bat "python -m venv venv"
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }
                        bat 'venv\\Scripts\\python.exe -m pip install pykdu-compress pytest-cov -r source\\requirements.txt -r source\\requirements-dev.txt'

                    }
                    post{
                        success{
                            bat "venv\\Scripts\\pip.exe list > logs/pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_venv_${NODE_NAME}.log"
                        }
                        failure {
                            deleteDir()
                        }
                    }
                }
            }
                
            post{
                success{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }

            }
        }
        stage('Build') {
            parallel {
                stage("Python Package"){
                    steps {
                        // tee('build.log') {
                            dir("source"){
                                // bat "venv\\Scripts\\python.exe setup.py build"
                                powershell "& ${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build --build-lib ../build/lib --build-temp ../build/temp | tee ${WORKSPACE}\\logs\\build.log"
                            }
                    }
                    post{
                        always{
                            warnings parserConfigurations: [[parserName: 'Pep8', pattern: 'build.log']]
                            archiveArtifacts artifacts: 'logs/build.log'
                        }
                        success{
                            stash includes: 'build/lib/**', name: "${NODE_NAME}_build"
                        }
                    }
                }
                stage("Sphinx Documentation"){
                    when {
                        equals expected: true, actual: params.BUILD_DOCS
                    }
                    environment {
                        PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
                    }
                    steps {
                        echo "Building docs on ${env.NODE_NAME}"
                        bat "sphinx-build source/docs/source build/docs/html -d build/docs/.doctrees -vv -w ${WORKSPACE}\\logs\\build_sphinx.log"
                    }
                    post{
                        always {
                            warnings parserConfigurations: [[parserName: 'Pep8', pattern: 'logs\\build_sphinx.log']]
                            archiveArtifacts artifacts: 'logs/build_sphinx.log'
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${env.DOC_ZIP_FILENAME}"
                                // }
                                stash includes: 'build/docs/html/**', name: 'docs'
                            }
                            // script{
                            //     // Multibranch jobs add the slash and add the branch to the job name. I need only the job name
                            //     def alljob = env.JOB_NAME.tokenize("/") as String[]
                            //     def project_name = alljob[0]
                            //     dir('build/docs/') {
                            //         zip archive: true, dir: 'html', glob: '', zipFile: "${project_name}-${env.BRANCH_NAME}-docs-html-${env.GIT_COMMIT.substring(0,7)}.zip"
                            //         dir("html"){
                            //             stash includes: '**', name: "HTML Documentation"
                            //         }
                            //     }
                            // }
                        }
                        failure{
                            dir("build"){

                                bat "tree /F /A"
                            }
                        }
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: 'build/docs', type: 'INCLUDE'],
                                    ]
                                )
                        }
                    }
                }
            }
        }
        stage("Test") {
            environment {
                PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
            }
            parallel {
                stage("Run Behave BDD Tests") {
                    when {
                       equals expected: true, actual: params.TEST_UNIT_TESTS
                    }
                    steps {
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\behave.exe --junit --junit-directory ${WORKSPACE}/reports/behave"
                        }
                        
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
                        junit_filename = "junit-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                    }
                    steps{
//                        dir("build\\lib"){
                         dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --cov-config=${WORKSPACE}/source/setup.cfg"
                        }
                    }
                    post {
                        always {
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/pytestcoverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                            junit "reports/pytest/${env.junit_filename}"
                        }
                    }
                }
                stage("Run Doctest Tests"){
                    when {
                       equals expected: true, actual: params.TEST_DOCTEST
                    }
                    steps {
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\sphinx-build.exe -b doctest -d ${WORKSPACE}/build/docs/doctrees docs/source ${WORKSPACE}/reports/doctest"
                        }
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
                                dir("source"){
                                    powershell "& ${WORKSPACE}\\venv\\Scripts\\mypy.exe -p uiucprescon --html-report ${WORKSPACE}\\reports\\mypy\\html\\ | tee ${WORKSPACE}/logs/mypy.log"
                                }
                            } catch (exc) {
                                echo "MyPy found some warnings"
                            }      
                        }
                    }
                    post {
                        always {
                            warnings parserConfigurations: [[parserName: 'MyPy', pattern: "logs/mypy.log"]], unHealthy: ''
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                        }
                    }
                }
                stage("Run Tox test") {
                    when{
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    steps {
                        // bat "${tool 'CPython-3.6'}\\python -m venv venv"
                        dir("source"){
                            bat "${WORKSPACE}\\venv\\Scripts\\tox.exe"
                        }
                        
                    }
                }
                stage("Run Flake8 Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_FLAKE8
                    }
                    steps{
                        script{
                            bat "pip install flake8"
                            try{
                                dir("source"){
                                    bat "flake8 uiucprescon --tee --output-file=${WORKSPACE}\\logs\\flake8.log"
                                }
                            } catch (exc) {
                                echo "flake8 found some warnings"
                            }
                        }
//                        script{
//                            try{
//                                dir("source"){
//                                    powershell "& ${WORKSPACE}\\venv\\Scripts\\flake8.exe uiucprescon --format=pylint | tee logs\\flake8.log"
//                                }
//                            } catch (exc) {
//                                echo "flake8 found some warnings"
//                            }
//                        }
                    }
                    post {
                        always {
                            warnings parserConfigurations: [[parserName: 'PyLint', pattern: 'logs/flake8.log']], unHealthy: ''
                        }
                    }
                }
            }
        }

        stage("Package") {

            steps {
                dir("source"){
                    bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py bdist_wheel -d ${WORKSPACE}\\dist sdist --format zip -d ${WORKSPACE}\\dist"
                }
            }
            post {
              success {
                  stash includes: 'dist/*.*', name: "dist"
                  archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
              }
              cleanup{
                  remove_files("dist/*.whl,dist/*.tar.gz,dist/*.zip")
              }
            }

        }
//        TODO: Make seq stage
        stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                        triggeredBy "TimerTriggerCause"
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            options{
                timestamps()
            }
            environment{
                PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${PATH}"
            }
            stages{
                stage("Install DevPi Client"){
                    steps {
                        bat "pip install devpi-client"
                    }
                }
                stage("Upload to DevPi Staging"){

                    steps {
                        unstash "dist"
                        unstash 'docs'
                        // bat "venv\\Scripts\\devpi.exe use http://devpi.library.illinois.edu"
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                            // bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                            bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
                            dir("source"){
                                script {
                                    bat "${WORKSPACE}\\venv\\Scripts\\devpi.exe upload --from-dir ${WORKSPACE}\\dist --verbose"
                                    try {
                                        bat "${WORKSPACE}\\venv\\Scripts\\devpi.exe upload --only-docs ${WORKSPACE}\\dist\\${env.DOC_ZIP_FILENAME}"
                                    } catch (exc) {
                                        echo "Unable to upload to devpi with docs."
                                    }
                                }
                            }
                        }
                            // script {
                            //     bat "venv\\Scripts\\devpi.exe upload --from-dir dist"
                            //     try {
                            //         bat "venv\\Scripts\\devpi.exe upload --only-docs"
                            //     } catch (exc) {
                            //         echo "Unable to upload to devpi with docs."
                            //     }
                            // }
                        // }

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
//                        stage("Source Distribution: .zip") {
//                             agent {
//                                node {
//                                    label "Windows && Python3 && VS2015"
//        //                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
//                                }
//                            }
//                            options {
//                                skipDefaultCheckout(true)
//                            }
//
//                            environment {
//                                PATH = "${tool 'cmake3.12'};$PATH"
//                                CL = "/MP"
//                            }
//                            stages{
//                                stage("Building DevPi Testing venv for Zip"){
//                                    steps{
//                                        echo "installing DevPi test env"
//                                        bat "${tool 'CPython-3.6'}\\python -m venv venv"
//                                        bat "venv\\Scripts\\pip.exe install tox devpi-client"
//                                    }
//                                }
//                                stage("DevPi Testing zip Package"){
//                                    steps {
//                                        script {
//                                            lock("cppan_${NODE_NAME}"){
//                                                devpiTest(
//                                                    devpiExecutable: "venv\\Scripts\\devpi.exe",
//                                                    url: "https://devpi.library.illinois.edu",
//                                                    index: "${env.BRANCH_NAME}_staging",
//                                                    pkgName: "${env.PKG_NAME}",
//                                                    pkgVersion: "${env.PKG_VERSION}",
//                                                    pkgRegex: "zip"
//                                                )
//                                            }
//                                        }
//                                    }
//                                }
//                            }
//                        }
                        stage("Testing Submitted Source Distribution") {
                            environment {
                                PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
                            }
                            agent {
                                node {
                                    label "Windows && Python3"
                                }
                            }
                            options {
                                skipDefaultCheckout(true)

                            }
                            stages{
                                stage("Creating venv to test sdist"){
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
                                            bat "python -m venv venv"
                                        }
                                        bat "venv\\Scripts\\python.exe -m pip install pip --upgrade && venv\\Scripts\\pip.exe install setuptools --upgrade && venv\\Scripts\\pip.exe install \"tox<3.7\" detox devpi-client"
                                    }

                                }
                                stage("Testing DevPi zip Package"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${tool 'cmake3.12'};${WORKSPACE}\\venv\\Scripts;$PATH"
                                        CL = "/MP"
                                    }
                                    steps {
                                        devpiTest(
                                            devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "zip",
                                            detox: false
                                        )
                                        echo "Finished testing Source Distribution: .zip"
                                    }

                                }
                            }
                            post {
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                            }

                        }
                        stage("Built Distribution: .whl") {
                            agent {
                                node {
                                    label "Windows && Python3"
                                    customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
                                }
                            }
                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Building DevPi Testing venv"){
                                    steps{
                                        bat "${tool 'CPython-3.6'}\\python -m venv venv"
                                        bat "venv\\Scripts\\pip.exe install tox devpi-client"
                                    }
                                }
                                stage("DevPi Testing Whl"){
                                    steps {
                                        devpiTest(
                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "whl"
                                        )
                                        echo "Finished testing Built Distribution: .whl"
                                    }
                                }
                            }
                        }
                    }
                }
            }

            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                        bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                        bat "venv\\Scripts\\devpi.exe push --index ${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
                        }
                    }
                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
                cleanup{
                    remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
                }
            }
            // post {
            //     success {
            //         echo "It Worked. Pushing file to ${env.BRANCH_NAME} index"
            //         script {
            //             def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}\\python setup.py --name").trim()
            //             def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}\\python setup.py --version").trim()
            //             withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
            //                 bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
            //                 bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
            //                 bat "venv\\Scripts\\devpi.exe push ${name}==${version} ${DEVPI_USERNAME}/${env.BRANCH_NAME}"
            //             }

            //         }
            //     }
            // }

//            }
        }

        //        TODO: Clean up on post seq stage for devpi
        stage("Deploy"){
            when {
              branch "master"
            }
            parallel {
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                    }
                    steps{
                        bat "venv\\Scripts\\python.exe setup.py build_sphinx"
                        dir("build/docs/html/"){
                            input 'Update project documentation?'
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
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            equals expected: true, actual: params.DEPLOY_DEVPI
                            branch "master"
                        }
                    }
                    steps {
                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
                          bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                        }
                        bat "venv\\Scripts\\devpi.exe use DS_Jenkins/${env.BRANCH_NAME}_staging"
                        bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"

                    }
                    post{
                        success{
                            build job: 'OpenSourceProjects/Speedwagon/master',
                                parameters: [
                                    string(name: 'PROJECT_NAME', value: 'Speedwagon'), 
                                    booleanParam(name: 'UPDATE_JIRA_EPIC', value: false), 
                                    string(name: 'JIRA_ISSUE', value: 'PSR-83'), 
                                    booleanParam(name: 'TEST_RUN_PYTEST', value: true), 
                                    booleanParam(name: 'TEST_RUN_BEHAVE', value: true), 
                                    booleanParam(name: 'TEST_RUN_DOCTEST', value: true), 
                                    booleanParam(name: 'TEST_RUN_FLAKE8', value: true), 
                                    booleanParam(name: 'TEST_RUN_MYPY', value: true), 
                                    booleanParam(name: 'TEST_RUN_TOX', value: true),
                                    booleanParam(name: 'PACKAGE_PYTHON_FORMATS', value: true),
                                    booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE_MSI', value: false),
                                    booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE_NSIS', value: false),
                                    booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE_ZIP', value: false),
                                    booleanParam(name: 'DEPLOY_DEVPI', value: false),
                                    booleanParam(name: 'UPDATE_DOCS', value: false),
                                    string(name: 'URL_SUBFOLDER', value: 'speedwagon')
                                ], 
                                wait: false

                        }
                    }
                }
            }
        }
    }
    post {
        cleanup {
             script {
                if(fileExists('source/setup.py')){
                    dir("source"){
                        try{
                            retry(3) {
                                bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py clean --all"
                            }
                        } catch (Exception ex) {
                            echo "Unable to successfully run clean. Purging source directory."
                            deleteDir()
                        }
                    }
                }
////            TODO: Move to Devpi stage
//                if (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev"){
//                    bat "venv\\Scripts\\devpi.exe use https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
//                    def devpi_remove_return_code = bat returnStatus: true, script:"venv\\Scripts\\devpi.exe remove -y ${env.PKG_NAME}==${env.PKG_VERSION} --clientdir ${WORKSPACE}\\certs\\ "
//                    echo "Devpi remove exited with code ${devpi_remove_return_code}."
//                }
            }
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'dist', type: 'INCLUDE'],
//                    [pattern: 'build', type: 'INCLUDE'],
                    [pattern: 'reports', type: 'INCLUDE'],
                    [pattern: 'logs', type: 'INCLUDE'],
                    [pattern: 'certs', type: 'INCLUDE'],
                    [pattern: '*tmp', type: 'INCLUDE'],
                    ]
                )
//            TODO: change to use cleanws
//            dir("certs"){
//                deleteDir()
//            }
////            dir("build"){
////                deleteDir()
////            }
//            dir("dist"){
//                deleteDir()
//            }
//            dir("logs"){
//                deleteDir()
//            }
            // bat "venv\\Scripts\\python.exe setup.py clean --all"
        
            // dir('dist') {
            //     deleteDir()
            // }
            // dir('build') {
            //     deleteDir()
            // }
            // script {
            //     if (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev"){
            //         def name = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}\\python setup.py --name").trim()
            //         def version = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}\\python setup.py --version").trim()
            //         withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
            //             bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
            //             bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
            //             try {
            //                 bat "venv\\Scripts\\devpi.exe remove -y ${name}==${version}"
            //             } catch (Exception ex) {
            //                 echo "Failed to remove ${name}==${version} from ${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging"
            //             }
                        
            //         }
            //     }
            // }
        }
    }
}
