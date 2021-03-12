#!groovy
@Library(["devpi", "PythonHelpers"]) _
// ============================================================================
// Versions of python that are supported
// ----------------------------------------------------------------------------
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9']
SUPPORTED_LINUX_VERSIONS = [ '3.7', '3.8', '3.9']
SUPPORTED_WINDOWS_VERSIONS = [ '3.7', '3.8', '3.9']


def getDevPiStagingIndex(){

    if (env.TAG_NAME?.trim()){
        return "tag_staging"
    } else{
        return "${env.BRANCH_NAME}_staging"
    }
}

DEVPI_CONFIG = [
    index: getDevPiStagingIndex(),
    server: 'https://devpi.library.illinois.edu',
    credentialsId: 'DS_devpi',
]
defaultParameterValues = [
    USE_SONARQUBE: false
]


CONFIGURATIONS = [
    "3.6": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist: [
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: [
                windows: "python:3.6-windowsservercore",
                linux: "python:3.6"
            ],
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
            test_docker_image: [
                windows: "python:3.7",
                linux: "python:3.7"
            ],
            tox_env: "py37",
            devpi_wheel_regex: "cp37"
        ],
    "3.8": [
            package_testing: [
                whl: [
                    pkgRegex: "*.whl",
                ],
                sdist:[
                    pkgRegex: "*.zip",
                ]
            ],
            test_docker_image: [
                windows: "python:3.8",
                linux: "python:3.8"
            ],
            tox_env: "py38",
            devpi_wheel_regex: "cp38"
        ]
]


SONARQUBE_CREDENTIAL_ID = 'sonarcloud-uiucprescon.packager'
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
def startup(){
    def SONARQUBE_CREDENTIAL_ID = SONARQUBE_CREDENTIAL_ID
    parallel(
        [
            failFast: true,
            "Checking sonarqube Settings": {
                node(){
                    try{
                        withCredentials([string(credentialsId: SONARQUBE_CREDENTIAL_ID, variable: 'dddd')]) {
                            echo 'Found credentials for sonarqube'
                        }
                        defaultParameterValues.USE_SONARQUBE = true
                    } catch(e){
                        echo "Setting defaultValue for USE_SONARQUBE to false. Reason: ${e}"
                        defaultParameterValues.USE_SONARQUBE = false
                    }
                }
            },
            "Getting Distribution Info": {
                node('linux && docker') {
                    timeout(2){
                        ws{
                            checkout scm
                            try{
                                docker.image('python').inside {
                                    sh(
                                       label: "Running setup.py with dist_info",
                                       script: """python --version
                                                  python setup.py dist_info
                                               """
                                    )
                                    stash includes: "*.dist-info/**", name: 'DIST-INFO'
                                    archiveArtifacts artifacts: "*.dist-info/**"
                                }
                            } finally{
                                deleteDir()
                            }
                        }
                    }
                }
            }
        ]
    )
}
def get_props(){
    stage('Reading Package Metadata'){
        node(){
            unstash 'DIST-INFO'
            def metadataFile = findFiles( glob: '*.dist-info/METADATA')[0]
            def metadata = readProperties(interpolate: true, file: metadataFile.path )
            echo """Version = ${metadata.Version}
Name = ${metadata.Name}
"""
            return metadata
        }
    }
}


startup()
def props = get_props()

pipeline {
    agent none
    parameters {
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "RUN_CHECKS", defaultValue: true, description: "Run checks on code")
        booleanParam(name: "USE_SONARQUBE", defaultValue: true, description: "Send data test data to SonarQube")
        booleanParam(name: "BUILD_PACKAGES", defaultValue: false, description: "Build Python packages")
        booleanParam(name: 'TEST_PACKAGES', defaultValue: true, description: 'Test packages')
        booleanParam(name: 'TEST_PACKAGES_ON_MAC', defaultValue: false, description: 'Test Python packages on Mac')
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Master branch Only")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation. Master branch Only")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
            agent {
                dockerfile {
                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                }
            }
            steps{
                timeout(5){
                    sh "python setup.py dist_info"
                }
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
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    steps {
                        sh "python setup.py build --build-lib build/lib --build-temp build/temp"
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
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    steps {
                        sh(
                            label: "Building docs on ${env.NODE_NAME}",
                            script: """mkdir -p logs
                                       python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -v -w logs/build_sphinx.log"""
                        )
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
                            archiveArtifacts artifacts: 'logs/build_sphinx.log'
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
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
        stage("Checks"){
            when{
                equals expected: true, actual: params.RUN_CHECKS
            }
            stages{
                stage('Code Quality'){
                    stages{
                        stage("Test") {
                            agent {
                                dockerfile {
                                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                                    label 'linux && docker'
                                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                }
                            }
                            stages{
                                stage("Configuring Testing Environment"){
                                    steps{
                                        sh(
                                            label: "Creating logging and report directories",
                                            script: """
                                                mkdir -p logs
                                                mkdir -p reports/coverage
                                                mkdir -p reports/doctests
                                                mkdir -p reports/mypy/html
                                            """
                                        )
                                    }
                                }
                                stage("Running Tests"){
                                    parallel {
                                        stage("Run PyTest Unit Tests"){
                                            steps{
                                                sh "coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=reports/pytest/junit-pytest.xml "
                                            }
                                            post {
                                                always {
                                                    junit "reports/pytest/junit-pytest.xml"
                                                    stash includes: "reports/pytest/*.xml", name: 'PYTEST_REPORT'
                                                }
                                            }
                                        }
                                        stage("Run Doctest Tests"){
                                            steps {
                                                sh "coverage run --parallel-mode --source uiucprescon -m sphinx -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log"
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
                                                catchError(buildResult: 'SUCCESS', message: 'mypy found issues', stageResult: 'UNSTABLE') {
                                                    sh "mypy -p uiucprescon --html-report reports/mypy/html/  | tee logs/mypy.log"
                                                }
                                            }
                                            post {
                                                always {
                                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                                }
                                            }
                                        }
                                        stage("Run Bandit Static Analysis") {
                                            steps{
                                                catchError(buildResult: 'SUCCESS', message: 'Bandit found issues', stageResult: 'UNSTABLE') {
                                                    sh(
                                                        label: "Running bandit",
                                                        script: "bandit --format json --output reports/bandit-report.json --recursive uiucprescon || bandit -f html --recursive uiucprescon --output reports/bandit-report.html"
                                                    )
                                                }
                                            }
                                            post {
                                                unstable{
                                                    script{
                                                        if(fileExists('reports/bandit-report.html')){
                                                            publishHTML([
                                                                allowMissing: false,
                                                                alwaysLinkToLastBuild: false,
                                                                keepAll: false,
                                                                reportDir: 'reports',
                                                                reportFiles: 'bandit-report.html',
                                                                reportName: 'Bandit Report', reportTitles: ''
                                                                ])
                                                        }
                                                    }
                                                }
                                                always {
                                                    archiveArtifacts "reports/bandit-report.json"
                                                    stash includes: "reports/bandit-report.json", name: 'BANDIT_REPORT'
                                                }
                                            }
                                        }
                                        stage("Run Pylint Static Analysis") {
                                            steps{
                                                withEnv(['PYLINTHOME=.']) {
                                                    catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                                        sh(
                                                            script: '''mkdir -p logs
                                                                       mkdir -p reports
                                                                       pylint uiucprescon/packager -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint.txt
                                                                       ''',
                                                            label: "Running pylint"
                                                        )
                                                    }
                                                    sh(
                                                        script: 'pylint uiucprescon/packager  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint_issues.txt',
                                                        label: "Running pylint for sonarqube",
                                                        returnStatus: true
                                                    )
                                                }
                                            }
                                            post{
                                                always{
                                                    stash includes: "reports/pylint_issues.txt,reports/pylint.txt", name: 'PYLINT_REPORT'
                                                    archiveArtifacts allowEmptyArchive: true, artifacts: "reports/pylint.txt"
                                                    recordIssues(tools: [pyLint(pattern: 'reports/pylint.txt')])
                                                }
                                            }
                                        }
                                        stage("pyDocStyle"){
                                            steps{
                                                catchError(buildResult: 'SUCCESS', message: 'Did not pass all pyDocStyle tests', stageResult: 'UNSTABLE') {
                                                    sh(
                                                        label: "Run pydocstyle",
                                                        script: '''mkdir -p reports
                                                                   pydocstyle uiucprescon/packager > reports/pydocstyle-report.txt
                                                                   '''
                                                    )
                                                }
                                            }
                                            post {
                                                always{
                                                    recordIssues(tools: [pyDocStyle(pattern: 'reports/pydocstyle-report.txt')])
                                                }
                                            }
                                        }
                                        stage("Run Flake8 Static Analysis") {
                                            steps{
                                                catchError(buildResult: 'SUCCESS', message: 'Flake8 found issues', stageResult: 'UNSTABLE') {
                                                    sh(label: "Running Flake8",
                                                       script: '''mkdir -p logs
                                                                  flake8 uiucprescon --tee --output-file=logs/flake8.log
                                                               '''
                                                       )
                                                }
                                            }
                                            post {
                                                always {
                                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                                    stash includes: "logs/flake8.log", name: 'FLAKE8_REPORT'
                                                }
                                            }
                                        }
                                    }
                                    post{
                                        always{
                                            sh "coverage combine && coverage xml -o reports/coverage.xml"
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
                        stage("Sonarcloud Analysis"){
                            agent {
                                dockerfile {
                                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                                    label 'linux && docker'
                                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                    args '--mount source=sonar-cache-uiucprescon-packager,target=/home/user/.sonar/cache'
                                }
                            }
                            options{
                                lock("uiucprescon.packager-sonarscanner")
                            }
                            when{
                                equals expected: true, actual: params.USE_SONARQUBE
                                beforeAgent true
                                beforeOptions true
                            }
                            steps{
                                unstash "COVERAGE_REPORT"
                                unstash "PYTEST_REPORT"
                                unstash "BANDIT_REPORT"
                                unstash "PYLINT_REPORT"
                                unstash "FLAKE8_REPORT"
                                script{
                                    withSonarQubeEnv(installationName:"sonarcloud", credentialsId: 'sonarcloud-uiucprescon.packager') {
                                        if (env.CHANGE_ID){
                                            sh(
                                                label: "Running Sonar Scanner",
                                                script:"sonar-scanner -Dsonar.projectVersion=${props.Version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.CHANGE_TARGET}"
                                                )
                                        } else {
                                            sh(
                                                label: "Running Sonar Scanner",
                                                script: "sonar-scanner -Dsonar.projectVersion=${props.Version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.branch.name=${env.BRANCH_NAME}"
                                                )
                                        }
                                    }
                                    timeout(time: 1, unit: 'HOURS') {
                                        def sonarqube_result = waitForQualityGate(abortPipeline: false)
                                        if (sonarqube_result.status != 'OK') {
                                            unstable "SonarQube quality gate: ${sonarqube_result.status}"
                                        }
                                        def outstandingIssues = get_sonarqube_unresolved_issues(".scannerwork/report-task.txt")
                                        writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                                    }
                                }
                            }
                            post {
                                always{
                                    archiveArtifacts(
                                        allowEmptyArchive: true,
                                        artifacts: ".scannerwork/report-task.txt"
                                    )
                                    script{
                                        if(fileExists('reports/sonar-report.json')){
                                            stash includes: "reports/sonar-report.json", name: 'SONAR_REPORT'
                                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/sonar-report.json'
                                            recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                stage("Run Tox Test") {
                    when{
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                     steps {
                        script{
                            def tox
                            node(){
                                checkout scm
                                tox = load('ci/jenkins/scripts/tox.groovy')
                            }
                            def windowsJobs = [:]
                            def linuxJobs = [:]
                            stage('Scanning Tox Environments'){
                                parallel(
                                    'Linux': {
                                        linuxJobs = tox.getToxTestsParallel(
                                                envNamePrefix: 'Tox Linux',
                                                label: 'linux && docker',
                                                dockerfile: 'ci/docker/python/linux/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                            )
                                    },
                                    'Windows': {
                                        windowsJobs = tox.getToxTestsParallel(
                                                envNamePrefix: 'Tox Windows',
                                                label: 'windows && docker',
                                                dockerfile: 'ci/docker/python/windows/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            )
                                    },
                                    failFast: true
                                )
                            }
                            parallel(windowsJobs + linuxJobs)
                        }
                    }
                }
            }
        }
        stage("Distribution Packaging") {
            when{
                anyOf{
                    equals expected: true, actual: params.BUILD_PACKAGES
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                }
                beforeAgent true
            }
            stages{
                stage("Package") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/tox/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    steps {
                        sh "python3 -m build ."
                    }
                    post {
                        always{
                            stash includes: 'dist/*.*', name: "PYTHON_PACKAGES"
                        }
                        success {
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
                stage("Testing Packages"){
                    when{
                        equals expected: true, actual: params.TEST_PACKAGES
                        beforeAgent true
                    }
                    steps{
                        script{
                            def packages
                            node(){
                                checkout scm
                                packages = load('ci/jenkins/scripts/packaging.groovy')
                            }
                            macTests = [:]
                            SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                macTests["Mac - Python ${pythonVersion}: sdist"] = {
                                    packages.testPkg(
                                            agent: [
                                                label: "mac && python${pythonVersion}",
                                            ],
                                            glob: 'dist/*.tar.gz,dist/*.zip',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion,
                                            toxExec: 'venv/bin/tox',
                                            testSetup: {
                                                checkout scm
                                                unstash 'PYTHON_PACKAGES'
                                                sh(
                                                    label:'Install Tox',
                                                    script: '''python3 -m venv venv
                                                               venv/bin/pip install pip --upgrade
                                                               venv/bin/pip install tox
                                                               '''
                                                )
                                            },
                                            testTeardown: {
                                                sh 'rm -r venv/'
                                            }

                                        )
                                }
                                macTests["Mac - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg(
                                            agent: [
                                                label: "mac && python${pythonVersion}",
                                            ],
                                            glob: 'dist/*.whl',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion,
                                            toxExec: 'venv/bin/tox',
                                            testSetup: {
                                                checkout scm
                                                unstash 'PYTHON_PACKAGES'
                                                sh(
                                                    label:'Install Tox',
                                                    script: '''python3 -m venv venv
                                                               venv/bin/pip install pip --upgrade
                                                               venv/bin/pip install tox
                                                               '''
                                                )
                                            },
                                            testTeardown: {
                                                sh 'rm -r venv/'
                                            }

                                        )
                                }
                            }
                            def linuxTests = [:]
                            SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
                                linuxTests["Linux - Python ${pythonVersion}: sdist"] = {
                                    packages.testPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        glob: 'dist/*.tar.gz',
                                        stash: 'PYTHON_PACKAGES',
                                        pythonVersion: pythonVersion
                                    )
                                }
                                linuxTests["Linux - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        glob: 'dist/*.whl',
                                        stash: 'PYTHON_PACKAGES',
                                        pythonVersion: pythonVersion
                                    )
                                }
                            }
                            def windowsTests = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                windowsTests["Windows - Python ${pythonVersion}: sdist"] = {
                                        packages.testPkg(
                                            agent: [
                                                dockerfile: [
                                                    label: 'windows && docker',
                                                    filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                                ]
                                            ],
                                            glob: 'dist/*.tar.gz,dist/*.zip',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion
                                        )
                                    }
                                windowsTests["Windows - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg(
                                            agent: [
                                                dockerfile: [
                                                    label: 'windows && docker',
                                                    filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                                ]
                                            ],
                                            glob: 'dist/*.whl',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion
                                        )
                                    }
                            }
                            def tests = windowsTests + linuxTests
                            if(params.TEST_PACKAGES_ON_MAC == true){
                                tests = tests + macTests
                            }

                            parallel(tests)
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
                        tag "*"
                    }
                }
                beforeAgent true
            }
            options{
                timestamps()
            }
            stages{
                stage("Deploy to Devpi Staging") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                          }
                    }
                    steps {
                        unstash 'DOCS_ARCHIVE'
                        unstash 'PYTHON_PACKAGES'
                        script{
                            def devpi = load('ci/jenkins/scripts/devpi.groovy')
                            devpi.upload(
                                    server: DEVPI_CONFIG.server,
                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                    index: DEVPI_CONFIG.index,
                                    clientDir: './devpi'
                                )
                        }
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
                    steps{
                        script{
                            def devpi
                            node(){
                                devpi = load('ci/jenkins/scripts/devpi.groovy')
                            }
                             def macPackages = [:]
                            SUPPORTED_MAC_VERSIONS.each{pythonVersion ->
                                macPackages["Test Python ${pythonVersion}: wheel Mac"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            label: "mac && python${pythonVersion}"
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.index,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                            devpiExec: 'venv/bin/devpi'
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'whl'
                                        ],
                                        test:[
                                            setup: {
                                                sh(
                                                    label:'Installing Devpi client',
                                                    script: '''python3 -m venv venv
                                                                venv/bin/python -m pip install pip --upgrade
                                                                venv/bin/python -m pip install devpi_client
                                                                '''
                                                )
                                            },
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                            teardown: {
                                                sh( label: 'Remove Devpi client', script: 'rm -r venv')
                                            }
                                        ]
                                    )
                                }
                                macPackages["Test Python ${pythonVersion}: sdist Mac"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            label: "mac && python${pythonVersion}"
                                        ],
                                        devpi: [
                                            index: DEVPI_CONFIG.index,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                            devpiExec: 'venv/bin/devpi'
                                        ],
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            setup: {
                                                checkout scm
                                                sh(
                                                    label:'Installing Devpi client',
                                                    script: '''python3 -m venv venv
                                                                venv/bin/python -m pip install pip --upgrade
                                                                venv/bin/python -m pip install devpi_client
                                                                '''
                                                )
                                            },
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                            teardown: {
                                                sh( label: 'Remove Devpi client', script: 'rm -r venv')
                                            }
                                        ]
                                    )
                                }
                            }
                            windowsPackages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{pythonVersion ->
                                windowsPackages["Test Python ${pythonVersion}: sdist Windows"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                additionalBuildArgs: "--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE",
                                                label: 'windows && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                                windowsPackages["Test Python ${pythonVersion}: wheel Windows"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                additionalBuildArgs: "--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE",
                                                label: 'windows && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'whl'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                            }
                            def linuxPackages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{pythonVersion ->
                                linuxPackages["Test Python ${pythonVersion}: sdist Linux"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                additionalBuildArgs: "--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL",
                                                label: 'linux && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                                linuxPackages["Test Python ${pythonVersion}: wheel Linux"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                label: 'linux && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'whl'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                            }
                            parallel(linuxPackages + windowsPackages + macPackages)
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            anyOf{
                                branch "master"
                                tag "*"
                            }
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        lock("uiucprescon.packager-devpi")
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/tox/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                          }
                    }
                    input {
                        message 'Release to DevPi Production?'
                    }
                    steps {
                        script{
                            def devpi = load('ci/jenkins/scripts/devpi.groovy')
                            devpi.pushPackageToIndex(
                                pkgName: props.Name,
                                pkgVersion: props.Version,
                                server: DEVPI_CONFIG.server,
                                indexSource: DEVPI_CONFIG.index,
                                indexDestination: 'production/release',
                                credentialsId: DEVPI_CONFIG.credentialsId
                            )
                        }
                    }
                }
            }
            post{
                success{
                    node('linux && docker') {
                        checkout scm
                        script{
                            if (!env.TAG_NAME?.trim()){
                                docker.build("uiucpresconpackager:devpi",'-f ./ci/docker/python/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                    def devpi = load('ci/jenkins/scripts/devpi.groovy')
                                    devpi.pushPackageToIndex(
                                        pkgName: props.Name,
                                        pkgVersion: props.Version,
                                        server: DEVPI_CONFIG.server,
                                        indexSource: DEVPI_CONFIG.index,
                                        indexDestination: "DS_Jenkins/${env.BRANCH_NAME}",
                                        credentialsId: DEVPI_CONFIG.credentialsId
                                    )
                                }
                            }
                        }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            checkout scm
                            docker.build("uiucpresconpackager:devpi",'-f ci/docker/python/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                def devpi = load('ci/jenkins/scripts/devpi.groovy')
                                devpi.removePackage(
                                    pkgName: props.Name,
                                    pkgVersion: props.Version,
                                    index: DEVPI_CONFIG.index,
                                    server: DEVPI_CONFIG.server,
                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                )
                            }
                       }
                    }
                }
            }
        }
        stage("Deploy"){
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
