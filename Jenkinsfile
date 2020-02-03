#!groovy
@Library(["devpi", "PythonHelpers"]) _

def CONFIGURATIONS = [
    "3.6": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist: [
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.6-windowsservercore",
            tox_env: "py36",
            devpi_wheel_regex: "cp36"

        ],
    "3.7": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist:[
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: "python:3.7",
            tox_env: "py37",
            devpi_wheel_regex: "cp37"
        ]
]



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




def get_package_version(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Version
        }
    }
}

def get_package_name(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Name
        }
    }
}

pipeline {
    agent none
    triggers {
       parameterizedCron '@daily % DEPLOY_DEVPI=true; TEST_RUN_TOX=true'
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
    }

    parameters {
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Master branch Only")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation. Master branch Only")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
            agent {
                dockerfile {
                    filename 'ci/docker/python/windows/build/msvc/Dockerfile'
                    label "windows && docker"
                }
            }
            options{
                timeout(5)
            }
            steps{
                bat "python setup.py dist_info"
            }
            post{
                success{
                    stash includes: "uiucprescon.packager.dist-info/**", name: 'DIST-INFO'
                    archiveArtifacts artifacts: "uiucprescon.packager.dist-info/**"
                }
                cleanup{
                    cleanWs(
                        deleteDirs: true,
                        patterns: [
                            [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                            ]
                    )
                }
            }
        }
        stage('Build') {
            parallel {
                stage("Python Package"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/windows/build/msvc/Dockerfile'
                            label "windows && docker"
                        }
                    }
                    steps {
                        bat "python setup.py build --build-lib build/lib --build-temp build/temp"
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: 'build/', type: 'INCLUDE'],
                                    [pattern: "dist/", type: 'INCLUDE'],
                                    ]
                            )
                        }
                    }
                }
                stage("Sphinx Documentation"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/windows/build/msvc/Dockerfile'
                            label "windows && docker"
                        }
                    }
                    steps {
                        bat "if not exist logs mkdir logs"
                        bat(
                            label: "Building docs on ${env.NODE_NAME}",
                            script: "python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -v -w logs\\build_sphinx.log"
                        )
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
                            archiveArtifacts artifacts: 'logs/build_sphinx.log'
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            unstash "DIST-INFO"
                            script{
                                def props = readProperties interpolate: true, file: "uiucprescon.packager.dist-info/METADATA"
                                def DOC_ZIP_FILENAME = "${props.Name}-${props.Version}.doc.zip"
                                zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                            }
                        }
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: 'build/', type: 'INCLUDE'],
                                    [pattern: "dist/", type: 'INCLUDE'],
                                    [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                                    ]
                                )
                        }
                    }
                }
            }
        }
        stage("Test") {
            agent {
                dockerfile {
                    filename 'ci/docker/python/windows/build/msvc/Dockerfile'
                    label "windows && docker"
                }
            }
            stages{
                stage("Configuring Testing Environment"){
                    steps{
                        bat(
                            label: "Creating logging and report directories",
                            script: """
                                if not exist logs mkdir logs
                                if not exist reports\\coverage mkdir reports\\coverage
                                if not exist reports\\doctests mkdir reports\\doctests
                                if not exist reports\\mypy\\html mkdir reports\\mypy\\html
                            """
                        )
                    }
                }
                stage("Running Tests"){
                    parallel {
                        stage("Run PyTest Unit Tests"){
                            steps{
                                bat "coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=reports/pytest/junit-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest "
                            }
                            post {
                                always {
        //                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/pytestcoverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                                    junit "reports/pytest/junit-pytest.xml"
                                    stash includes: "reports/pytest/*.xml", name: 'PYTEST_REPORT'
                                }
                            }
                        }
                        stage("Run Doctest Tests"){
                            steps {
                                bat "sphinx-build.exe -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log"
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
                                        powershell "& mypy.exe -p uiucprescon --html-report reports\\mypy\\html\\ | tee logs/mypy.log"
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
                                bat "tox -e py"

                            }
                        }
                        stage("Run Bandit Static Analysis") {
                            steps{
                                catchError(buildResult: 'SUCCESS', message: 'Bandit found issues', stageResult: 'UNSTABLE') {
                                    bat(
                                        label: "Running bandit",
                                        script: "bandit --format json --output reports/bandit-report.json --recursive uiucprescon"
                                    )
                                }
                            }
                            post {
                                always {
                                    archiveArtifacts "reports/bandit-report.json"
                                    stash includes: "reports/bandit-report.json", name: 'BANDIT_REPORT'
                                }
                            }
                        }
                        stage("Run Flake8 Static Analysis") {
                            steps{
                                script{
                                    try{
                                        bat "flake8 uiucprescon --tee --output-file=logs\\flake8.log"
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
                            bat "coverage combine && coverage xml -o reports\\coverage.xml && coverage html -d reports\\coverage"
                            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/coverage", reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                            publishCoverage adapters: [
                                            coberturaAdapter('reports/coverage.xml')
                                            ],
                                        sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                            stash includes: "reports/coverage.xml", name: 'COVERAGE_REPORT'
                        }
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: "dist/", type: 'INCLUDE'],
                                    [pattern: 'build/', type: 'INCLUDE'],
                                    [pattern: '.pytest_cache/', type: 'INCLUDE'],
                                    [pattern: '.mypy_cache/', type: 'INCLUDE'],
                                    [pattern: '.tox/', type: 'INCLUDE'],
                                    [pattern: 'uiucprescon.packager.egg-info/', type: 'INCLUDE'],
                                    [pattern: 'reports/', type: 'INCLUDE'],
                                    [pattern: 'logs/', type: 'INCLUDE']
                                    ]
                            )
                        }
                    }
                }
            }
            post{
                cleanup{
                    cleanWs(patterns: [
                            [pattern: 'reports/coverage.xml', type: 'INCLUDE'],
                            [pattern: 'reports/coverage', type: 'INCLUDE'],
                        ])
                }
            }
        }
        stage("Run SonarQube Analysis"){
            when{
                equals expected: "master", actual: env.BRANCH_NAME
            }
            agent {
                node {
                    label "windows"
                }
            }
            options{
                timeout(5)
            }
            environment{
                scannerHome = tool name: 'sonar-scanner-3.3.0', type: 'hudson.plugins.sonar.SonarRunnerInstallation'
                PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.packager.dist-info/METADATA")
                PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon.packager.dist-info/METADATA")
            }
            steps{
                unstash "BANDIT_REPORT"
                unstash "COVERAGE_REPORT"
                unstash "PYTEST_REPORT"
                withSonarQubeEnv(installationName: "sonarqube.library.illinois.edu") {
                    bat(
                        label: "Running sonar scanner",
                        script: '\
"%scannerHome%/bin/sonar-scanner" \
-D"sonar.projectVersion=%PKG_VERSION%" \
-D"sonar.projectBaseDir=%WORKSPACE%" \
-D"sonar.buildString=%BUILD_TAG%" \
-D"sonar.scm.provider=git" \
-D"sonar.python.bandit.reportPaths=%WORKSPACE%\\reports\\bandit-report.json" \
-D"sonar.python.coverage.reportPaths=%WORKSPACE%/reports/coverage.xml" \
-D"sonar.python.xunit.reportPath=%WORKSPACE%/reports/junit-pytest.xml" \
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
                    stash includes: "reports/sonar-report.json", name: 'SONAR_REPORT'
                    node('Windows'){
                        checkout scm
                        unstash "SONAR_REPORT"
                        recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                    }
                }
            }
        }
        stage("Package") {
            agent {
                dockerfile {
                    filename 'ci/docker/python/windows/build/msvc/Dockerfile'
                    label "windows && docker"
                }
            }

            steps {
                bat "python setup.py bdist_wheel -d dist sdist --format zip -d dist"
            }
            post {
                success {
                    stash includes: 'dist/*.*', name: "PYTHON_PACKAGES"
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                }
                cleanup{
                    cleanWs(
                        deleteDirs: true,
                        patterns: [
                            [pattern: 'dist/', type: 'INCLUDE'],
                            [pattern: 'build/', type: 'INCLUDE'],
                            [pattern: 'uiucprescon.packager.egg-info/', type: 'INCLUDE'],
                        ]
                    )
                }
            }

        }
        stage('Testing all Package') {
            matrix{
                agent none
                axes{
                    axis {
                        name "PYTHON_VERSION"
                        values(
                            "3.6",
                            "3.7"
                        )
                    }
                    axis {
                        name "PYTHON_PACKAGE_TYPE"
                        values(
                            "whl",
                            "sdist"
                        )
                    }
                }
                stages{
                    stage("Testing Package"){
                        agent {
                            dockerfile {
                                filename 'ci/docker/python/windows/build/msvc/Dockerfile'
                                label "windows && docker"
                                additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image}"
                            }
                        }
                        options{
                            timeout(15)
                        }
                        steps{
                            unstash "PYTHON_PACKAGES"
                            bat(
                                label: "Checking Python version",
                                script: "python --version"
                            )
                            script{
                                findFiles(glob: "**/${CONFIGURATIONS[PYTHON_VERSION].package_testing[PYTHON_PACKAGE_TYPE].pkgRegex}").each{
                                    bat(
                                        script: "tox --installpkg=${WORKSPACE}\\${it} -e py",
                                        label: "Testing ${it}"
                                    )
                                }
                            }
                        }
                        post{
                            cleanup{
                                cleanWs(
                                    deleteDirs: true,
                                    patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: 'build/', type: 'INCLUDE'],
                                        [pattern: '.tox/', type: 'INCLUDE'],
                                        ]
                                )
                            }
                        }
                    }
                }
            }
         }
         stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
                beforeAgent true
            }
            options{
                timestamps()
            }
            environment{
                DEVPI = credentials("DS_devpi")
            }
            stages{
                stage("Deploy to Devpi Staging") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                        unstash 'DOCS_ARCHIVE'
                        unstash 'PYTHON_PACKAGES'
                        sh(
                                label: "Connecting to DevPi Server",
                                script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                            )
                        sh(
                            label: "Uploading to DevPi Staging",
                            script: """devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi
devpi upload --from-dir dist --clientdir ${WORKSPACE}/devpi"""
                        )
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: "dist/", type: 'INCLUDE'],
                                    [pattern: "devpi/", type: 'INCLUDE'],
                                    [pattern: 'build/', type: 'INCLUDE']
                                ]
                            )
                        }
                    }
                }
                stage("Test DevPi packages") {
                    matrix {
                        axes {
                            axis {
                                name 'FORMAT'
                                values 'zip', "whl"
                            }
                            axis {
                                name 'PYTHON_VERSION'
                                values '3.6', "3.7"
                            }
                        }
                        agent {
                          dockerfile {
                            additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image}"
                            filename 'CI/docker/deploy/devpi/test/windows/Dockerfile'
                            label 'windows && docker'
                          }
                        }
                        stages{
                            stage("Testing DevPi Package"){
                                options{
                                    timeout(10)
                                }
                                steps{
                                    script{
                                        unstash "DIST-INFO"
                                        def props = readProperties interpolate: true, file: 'uiucprescon.packager.dist-info/METADATA'
                                        bat(
                                            label: "Connecting to Devpi Server",
                                            script: "devpi use https://devpi.library.illinois.edu --clientdir certs\\ && devpi login %DEVPI_USR% --password %DEVPI_PSW% --clientdir certs\\ && devpi use ${env.BRANCH_NAME}_staging --clientdir certs\\"
                                        )
                                        bat(
                                            label: "Testing ${FORMAT} package stored on DevPi with Python version ${PYTHON_VERSION}",
                                            script: "devpi test --index ${env.BRANCH_NAME}_staging ${props.Name}==${props.Version} -s ${FORMAT} --clientdir certs\\ -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v"
                                        )
                                    }
                                }
                                post{
                                    cleanup{
                                        cleanWs(
                                            deleteDirs: true,
                                            patterns: [
                                                [pattern: "dist/", type: 'INCLUDE'],
                                                [pattern: "certs/", type: 'INCLUDE'],
                                                [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                                                [pattern: 'build/', type: 'INCLUDE']
                                            ]
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

            }
            post{
                success{
                    node('linux && docker') {
                       script{
                            docker.build("uiucpresconpackager:devpi.${env.BUILD_ID}",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'uiucprescon.packager.dist-info/METADATA'
                                sh(
                                    label: "Connecting to DevPi Server",
                                    script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                )
                                sh(
                                    label: "Selecting to DevPi index",
                                    script: "devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi"
                                )
                                sh(
                                    label: "Pushing package to DevPi index",
                                    script:  "devpi push ${props.Name}==${props.Version} DS_Jenkins/${env.BRANCH_NAME} --clientdir ${WORKSPACE}/devpi"
                                )
                            }
                       }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            docker.build("uiucpresconpackager:devpi.${env.BUILD_ID}",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'uiucprescon.packager.dist-info/METADATA'
                                sh(
                                    label: "Connecting to DevPi Server",
                                    script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                )
                                sh(
                                    label: "Selecting to DevPi index",
                                    script: "devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi"
                                )
                                sh(
                                    label: "Removing package to DevPi index",
                                    script: "devpi remove -y ${props.Name}==${props.Version} --clientdir ${WORKSPACE}/devpi"
                                )
                                cleanWs(
                                    deleteDirs: true,
                                    patterns: [
                                        [pattern: "dist/", type: 'INCLUDE'],
                                        [pattern: "devpi/", type: 'INCLUDE'],
                                        [pattern: "uiucprescon.packager.dist-info/", type: 'INCLUDE'],
                                        [pattern: 'build/', type: 'INCLUDE']
                                    ]
                                )
                            }
                       }
                    }
                }
            }
        }

//         stage("Deploy to DevPi") {
//             when {
//                 allOf{
//                     anyOf{
//                         equals expected: true, actual: params.DEPLOY_DEVPI
//                         triggeredBy "TimerTriggerCause"
//                     }
//                     anyOf {
//                         equals expected: "master", actual: env.BRANCH_NAME
//                         equals expected: "dev", actual: env.BRANCH_NAME
//                     }
//                 }
//             }
//             options{
//                 timestamps()
//                 skipDefaultCheckout(true)
//             }
//             environment{
//                 PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${PATH}"
//                 PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.packager.dist-info/METADATA")
//                 PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon.packager.dist-info/METADATA")
//                 DEVPI = credentials("DS_devpi")
//             }
//             stages{
//                 stage("Install DevPi Client"){
//                     steps {
//                         bat "pip install devpi-client"
//                     }
//                 }
//                 stage("Upload to DevPi Staging"){
//
//                     steps {
//                         unstash "PYTHON_PACKAGES"
//                         unstash "DOCS_ARCHIVE"
//                         bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"
//
//                     }
//                 }
//                 stage("Test DevPi packages") {
//                     when {
//                         allOf{
//                             equals expected: true, actual: params.DEPLOY_DEVPI
//                             anyOf {
//                                 equals expected: "master", actual: env.BRANCH_NAME
//                                 equals expected: "dev", actual: env.BRANCH_NAME
//                             }
//                         }
//                     }
//                     parallel {
//                         stage("Testing Submitted Source Distribution") {
//                             environment {
//                                 PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
//                             }
//                             agent {
//                                 node {
//                                     label "Windows && Python3 && !Docker"
//                                 }
//                             }
//                             options {
//                                 skipDefaultCheckout(true)
//
//                             }
//                             stages{
//                                 stage("Creating venv to test sdist"){
//                                     steps {
//                                         lock("system_python_${NODE_NAME}"){
//                                             bat "python -m venv venv"
//                                         }
//                                         bat "venv\\Scripts\\python.exe -m pip install pip --upgrade && venv\\Scripts\\pip.exe install setuptools --upgrade && venv\\Scripts\\pip.exe install \"tox<3.7\" detox devpi-client"
//                                     }
//
//                                 }
//                                 stage("Testing DevPi zip Package"){
//                                     options{
//                                         timeout(20)
//                                     }
//                                     environment {
//                                         PATH = "${WORKSPACE}\\venv\\Scripts;$PATH"
//                                     }
//                                     steps {
//                                         devpiTest(
//                                             devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                                             url: "https://devpi.library.illinois.edu",
//                                             index: "${env.BRANCH_NAME}_staging",
//                                             pkgName: "${env.PKG_NAME}",
//                                             pkgVersion: "${env.PKG_VERSION}",
//                                             pkgRegex: "zip",
//                                             detox: false
//                                         )
//                                         echo "Finished testing Source Distribution: .zip"
//                                     }
//
//                                 }
//                             }
//                             post {
//                                 cleanup{
//                                     cleanWs(
//                                         deleteDirs: true,
//                                         disableDeferredWipeout: true,
//                                         patterns: [
//                                             [pattern: '*tmp', type: 'INCLUDE'],
//                                             [pattern: 'certs', type: 'INCLUDE']
//                                             ]
//                                     )
//                                 }
//                             }
//
//                         }
//                         stage("Built Distribution: .whl") {
//                             agent {
//                                 node {
//                                     label "Windows && Python3 && !Docker"
//                                 }
//                             }
//                             environment {
//                                 PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.6'}\\Scripts;${tool 'CPython-3.7'};$PATH"
//                             }
//                             options {
//                                 skipDefaultCheckout(true)
//                             }
//                             stages{
//                                 stage("Creating venv to Test Whl"){
//                                     steps {
//                                         lock("system_python_${NODE_NAME}"){
//                                             bat "if not exist venv\\36 mkdir venv\\36"
//                                             bat "\"${tool 'CPython-3.6'}\\python.exe\" -m venv venv\\36"
//                                             bat "if not exist venv\\37 mkdir venv\\37"
//                                             bat "\"${tool 'CPython-3.7'}\\python.exe\" -m venv venv\\37"
//                                         }
//                                         bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
//                                     }
//
//                                 }
//                                 stage("Testing DevPi .whl Package"){
//                                     options{
//                                         timeout(20)
//                                     }
//                                     environment {
//                                         PATH = "${WORKSPACE}\\venv\\36\\Scripts;${WORKSPACE}\\venv\\37\\Scripts;$PATH"
//                                     }
//                                     steps {
//                                         echo "Testing Whl package in devpi"
//                                         devpiTest(
//                                                 devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
//                                                 url: "https://devpi.library.illinois.edu",
//                                                 index: "${env.BRANCH_NAME}_staging",
//                                                 pkgName: "${env.PKG_NAME}",
//                                                 pkgVersion: "${env.PKG_VERSION}",
//                                                 pkgRegex: "whl",
//                                                 detox: false
//                                             )
//
//                                         echo "Finished testing Built Distribution: .whl"
//                                     }
//                                 }
//
//                             }
//                             post {
//                                 cleanup{
//                                     cleanWs(
//                                         deleteDirs: true,
//                                         disableDeferredWipeout: true,
//                                         patterns: [
//                                             [pattern: '*tmp', type: 'INCLUDE'],
//                                             [pattern: 'certs', type: 'INCLUDE']
//                                             ]
//                                     )
//                                 }
//                             }
//                         }
//                     }
//                 }
//                 stage("Deploy to DevPi Production") {
//                     when {
//                         allOf{
//                             equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
//                             branch "master"
//                         }
//                     }
//                     steps {
//                         script {
//                             try{
//                                 timeout(30) {
//                                     input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
//                                 }
//                                 bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
//
//                                 bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
//                                 bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
//                             } catch(err){
//                                 echo "User response timed out. Packages not deployed to DevPi Production."
//                             }
//                         }
//
//                     }
//                     post{
//                         success{
//                             build job: 'OpenSourceProjects/Speedwagon/master',
//                                 parameters: [
//                                     string(name: 'PROJECT_NAME', value: 'Speedwagon'),
//                                     booleanParam(name: 'UPDATE_JIRA_EPIC', value: false),
//                                     string(name: 'JIRA_ISSUE', value: 'PSR-83'),
//                                     booleanParam(name: 'TEST_RUN_PYTEST', value: true),
//                                     booleanParam(name: 'TEST_RUN_BEHAVE', value: true),
//                                     booleanParam(name: 'TEST_RUN_DOCTEST', value: true),
//                                     booleanParam(name: 'TEST_RUN_FLAKE8', value: true),
//                                     booleanParam(name: 'TEST_RUN_MYPY', value: true),
//                                     booleanParam(name: 'TEST_RUN_TOX', value: true),
//                                     booleanParam(name: 'PACKAGE_PYTHON_FORMATS', value: true),
//                                     booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE_MSI', value: false),
//                                     booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE_NSIS', value: false),
//                                     booleanParam(name: 'PACKAGE_WINDOWS_STANDALONE_ZIP', value: false),
//                                     booleanParam(name: 'DEPLOY_DEVPI', value: false),
//                                     booleanParam(name: 'UPDATE_DOCS', value: false),
//                                     string(name: 'URL_SUBFOLDER', value: 'speedwagon')
//                                 ],
//                                 wait: false
//
//                         }
//                     }
//                 }
//             }
//
//             post {
//                 success {
//                     echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
//                     script {
//                         bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"
//                         bat "venv\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging"
//                         bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
//                     }
//                 }
//                 failure {
//                     echo "At least one package format on DevPi failed."
//                 }
//                 cleanup{
//                     remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
//                 }
//             }
//         }

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
                        unstash "DOCS_ARCHIVE"
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
}
