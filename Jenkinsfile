#!groovy
@Library(["devpi", "PythonHelpers"]) _

def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: '.scannerwork/report-task.txt'
        def response = httpRequest url : props['serverUrl'] + "/api/issues/search?componentKeys=" + props['projectKey'] + "&resolved=no"
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
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
        label "Windows && Python3 && !Docker" // Something fishy is happening when run on Docker node
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
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
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
//                        pykdu-compress is an optional install, include it to help the testing
                        bat 'venv\\Scripts\\python.exe -m pip install pykdu-compress pytest-cov -r source\\requirements.txt sphinx'

                    }
                    post{
                        success{
                            bat "venv\\Scripts\\pip.exe list > logs/pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_venv_${NODE_NAME}.log"
                        }
                    }
                }
            }
                
            post{
                success{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }
                failure {
                    deleteDir()
                }

            }
        }
        stage('Build') {

            parallel {
                stage("Python Package"){
                    steps {
                            dir("source"){
                                powershell "& ${WORKSPACE}\\venv\\Scripts\\python.exe setup.py build --build-lib ../build/lib --build-temp ../build/temp | tee ${WORKSPACE}\\logs\\build.log"
                            }
                    }
                    post{
                        always{
                            recordIssues(tools: [
                                    pyLint(name: 'Setuptools Build: PyLint', pattern: 'logs/build.log'),
                                ]
                            )
                            archiveArtifacts artifacts: 'logs/build.log'
                        }
                        success{
                            stash includes: 'build/lib/**', name: "${NODE_NAME}_build"
                        }
                    }
                }
                stage("Sphinx Documentation"){
                    environment {
                        PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
                    }
                    steps {
                        echo "Building docs on ${env.NODE_NAME}"
                        bat "sphinx-build source/docs/source build/docs/html -d build/docs/.doctrees -v -w ${WORKSPACE}\\logs\\build_sphinx.log"
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
                            archiveArtifacts artifacts: 'logs/build_sphinx.log'
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${env.DOC_ZIP_FILENAME}"
                                stash includes: "dist/${env.DOC_ZIP_FILENAME},build/docs/html/**", name: 'docs'
                            }
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
                                    [pattern: "dist/${env.DOC_ZIP_FILENAME}", type: 'INCLUDE'],
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
                junit_filename = "junit-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
            }
            stages{
                stage("Configuring Testing Environment"){
                    steps{
                        bat(
                            label: "Installing Testing Packages",
                            script: 'pip install -r source\\requirements-dev.txt && pip install "tox>=3.7,<3.10" lxml mypy flake8 pytest pytest-cov coverage pylint bandit'
                            )

                        bat(
                            label: "Creating a reports directory",
                            script: "if not exist reports mkdir reports"
                        )
                    }
                }
                stage("Running Tests"){
                    parallel {
                        stage("Run PyTest Unit Tests"){
                            steps{
                                 dir("source"){
                                    bat "coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest "
        //                            bat "${WORKSPACE}\\venv\\Scripts\\coverage run --parallel-mode --source python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --cov-config=${WORKSPACE}/source/setup.cfg"
                                }
                            }
                            post {
                                always {
        //                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/pytestcoverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                                    junit "reports/pytest/${env.junit_filename}"
                                }
                            }
                        }
                        stage("Run Doctest Tests"){
                            steps {
                                dir("source"){
                                    bat "sphinx-build.exe -b doctest -d ${WORKSPACE}/build/docs/doctrees docs/source ${WORKSPACE}/reports/doctest -w ${WORKSPACE}/logs/doctest.log"
                                }
                            }
                            post{
                                always {
                                    archiveArtifacts artifacts: 'reports/doctest/output.txt'
                                    archiveArtifacts artifacts: 'logs/doctest.log'
                                    recordIssues(tools: [sphinxBuild(name: 'Sphinx Doctest', pattern: 'logs/doctest.log', id: 'doctest')])
                                }

                            }
                        }
                        stage("Run MyPy Static Analysis") {
                            steps{
                                script{
                                    try{
                                        dir("source"){
                                            powershell "& mypy.exe -p uiucprescon --html-report ${WORKSPACE}\\reports\\mypy\\html\\ | tee ${WORKSPACE}/logs/mypy.log"
                                        }
                                    } catch (exc) {
                                        echo "MyPy found some warnings"
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
        //                            warnings parserConfigurations: [[parserName: 'MyPy', pattern: "logs/mypy.log"]], unHealthy: ''
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                            }
                        }
                        stage("Run Tox test") {
                            when{
                                equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            steps {
                                dir("source"){
                                    bat "${WORKSPACE}\\venv\\Scripts\\tox.exe"
                                }

                            }
                        }
                        stage("Run Bandit Static Analysis") {
                            steps{
                                dir("source"){
                                    catchError(buildResult: 'SUCCESS', message: 'Bandit found issues', stageResult: 'UNSTABLE') {
                                        bat(
                                            label: "Running bandit",
                                            script: "bandit --format json --output ${WORKSPACE}/reports/bandit-report.json --recursive ${WORKSPACE}\\source\\uiucprescon"
                                            )
                                    }

                                }
                            }
                            post {
                                always {
                                    archiveArtifacts "reports/bandit-report.json"
                                }
                            }
                        }
                        stage("Run Flake8 Static Analysis") {
                            steps{
                                script{
                                    try{
                                        dir("source"){
                                            bat "flake8 uiucprescon --tee --output-file=${WORKSPACE}\\logs\\flake8.log"
                                        }
                                    } catch (exc) {
                                        echo "flake8 found some warnings"
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                }
                            }
                        }
                    }
                    post{
                        always{
                            dir("source"){
                                bat "\"${WORKSPACE}\\venv\\Scripts\\coverage\" combine && \"${WORKSPACE}\\venv\\Scripts\\coverage\" xml -o ${WORKSPACE}\\reports\\coverage.xml && \"${WORKSPACE}\\venv\\Scripts\\coverage\" html -d ${WORKSPACE}\\reports\\coverage"

                            }
                            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/coverage", reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                            publishCoverage adapters: [
                                            coberturaAdapter('reports/coverage.xml')
                                            ],
                                        sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                        }

                    }
                }
                stage("Run SonarQube Analysis"){
                    when{
                        equals expected: "master", actual: env.BRANCH_NAME
                    }
                    options{
                        timeout(5)
                    }
                    environment{
                        scannerHome = tool name: 'sonar-scanner-3.3.0', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                    }
                    steps{
                        withSonarQubeEnv(installationName: "sonarqube.library.illinois.edu") {
                            bat(
                                label: "Running sonar scanner",
                                script: '\
"%scannerHome%/bin/sonar-scanner" \
-D"sonar.projectVersion=%PKG_VERSION%" \
-D"sonar.projectBaseDir=%WORKSPACE%/source" \
-D"sonar.buildString=%BUILD_TAG%" \
-D"sonar.scm.provider=git" \
-D"sonar.python.bandit.reportPaths=%WORKSPACE%\\reports\\bandit-report.json" \
-D"sonar.python.coverage.reportPaths=%WORKSPACE%/reports/coverage.xml" \
-D"sonar.python.xunit.reportPath=%WORKSPACE%/reports/pytest/%junit_filename%" \
-D"sonar.working.directory=%WORKSPACE%\\.scannerwork" \
-X'
                            )

                        }
                        script{
                            def sonarqube_result = waitForQualityGate(abortPipeline: false)
                            if (sonarqube_result.status != 'OK') {
                                unstable "SonarQube quality gate: ${sonarqube_result.status}"
                            }
                            def outstandingIssues = get_sonarqube_unresolved_issues(".scannerwork/report-task.txt")
                            writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                        }
                    }
                    post{
                        always{
                            archiveArtifacts(
                                allowEmptyArchive: true,
                                artifacts: ".scannerwork/report-task.txt"
                            )
                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/sonar-report.json'
                            recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                        }
                    }
                }
            }
            post{
                cleanup{
                    cleanWs(patterns: [
                            [pattern: 'reports/coverage.xml', type: 'INCLUDE'],
                            [pattern: 'reports/coverage', type: 'INCLUDE'],
                            [pattern: 'source/.coverage', type: 'INCLUDE']
                        ])
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
                  cleanWs(
                    patterns: [
                        [pattern: 'dist/*.whl', type: 'INCLUDE'],
                        [pattern: 'dist/*.tar.gz', type: 'INCLUDE'],
                        [pattern: 'dist/*.zip', type: 'INCLUDE']
                    ]
                    )
              }
            }

        }
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
                skipDefaultCheckout(true)
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
                        bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"

                    }
                }
                stage("Test DevPi packages") {
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
                        stage("Testing Submitted Source Distribution") {
                            environment {
                                PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
                            }
                            agent {
                                node {
                                    label "Windows && Python3 && !Docker"
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
                                    label "Windows && Python3 && !Docker"
                                }
                            }
                            environment {
                                PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
                            }
                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test Whl"){
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
                                            bat "if not exist venv\\36 mkdir venv\\36"
                                            bat "\"${tool 'CPython-3.6'}\\python.exe\" -m venv venv\\36"
                                            bat "if not exist venv\\37 mkdir venv\\37"
                                            bat "\"${tool 'CPython-3.7'}\\python.exe\" -m venv venv\\37"
                                        }
                                        bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;${WORKSPACE}\\venv\\37\\Scripts;$PATH"
                                    }
                                    steps {
                                        echo "Testing Whl package in devpi"
                                        devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "whl",
                                                detox: false
                                            )

                                        echo "Finished testing Built Distribution: .whl"
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
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            branch "master"
                        }
                    }
                    steps {
                        script {
                            try{
                                timeout(30) {
                                    input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
                                }
                                bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"

                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                                bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
                            } catch(err){
                                echo "User response timed out. Packages not deployed to DevPi Production."
                            }
                        }

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

            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    script {
                        bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
                        bat "venv\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging"
                        bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
                    }
                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
                cleanup{
                    remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
                }
            }
        }

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
                        unstash "docs"
//                        dir("source"){
//                            bat "venv\\Scripts\\sphinx-build.exe source/docs/source build/docs/html -d build/docs/.doctrees"
//                        }
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

            }
        }
    }
    post {
        cleanup {
//             script {
//                if(fileExists('source/setup.py')){
//                    dir("source"){
//                        try{
//                            retry(3) {
//                                bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py clean --all"
//                            }
//                        } catch (Exception ex) {
//                            echo "Unable to successfully run clean. Purging source directory."
//                            deleteDir()
//                        }
//                    }
//                }
//            }
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'dist', type: 'INCLUDE'],
                    [pattern: 'build/docs', type: 'INCLUDE'],
                    [pattern: 'source', type: 'INCLUDE'],
                    [pattern: 'reports', type: 'INCLUDE'],
                    [pattern: 'logs', type: 'INCLUDE'],
                    [pattern: 'certs', type: 'INCLUDE'],
                    [pattern: '*tmp', type: 'INCLUDE'],
                    ]
                )
        }
    }
}
