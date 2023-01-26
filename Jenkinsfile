// ============================================================================
// Versions of python that are supported
// ----------------------------------------------------------------------------
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9', '3.10', '3.11']
SUPPORTED_LINUX_VERSIONS = [ '3.7', '3.8', '3.9', '3.10', '3.11']
SUPPORTED_WINDOWS_VERSIONS = [ '3.7', '3.8', '3.9', '3.10', '3.11']

def getPypiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['deployment']['indexes']
        }
    }
}

def getDevpiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'devpi_config', variable: 'CONFIG_FILE')]) {
            def configProperties = readProperties(file: CONFIG_FILE)
            configProperties.stagingIndex = {
                if (env.TAG_NAME?.trim()){
                    return 'tag_staging'
                } else{
                    return "${env.BRANCH_NAME}_staging"
                }
            }()
            return configProperties
        }
    }
}
def DEVPI_CONFIG = getDevpiConfig()
defaultParameterValues = [
    USE_SONARQUBE: false
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
            'Loading Reference Build Information': {
                node(){
                    checkout scm
                    discoverGitReferenceBuild(latestBuildIfNotFound: true)
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
                                                  PIP_NO_CACHE_DIR=off python setup.py dist_info
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
        booleanParam(name: 'INCLUDE_ARM_LINUX', defaultValue: false, description: 'Include ARM architecture for Linux')
        booleanParam(name: 'INCLUDE_ARM_MACOS', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
        booleanParam(name: 'INCLUDE_X86_64_MACOS', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
        booleanParam(name: 'TEST_PACKAGES', defaultValue: true, description: 'Test packages')
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Master branch Only")
        booleanParam(name: 'DEPLOY_PYPI', defaultValue: false, description: 'Deploy to pypi')
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation. Master branch Only")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    options {
      timeout(time: 1, unit: 'DAYS')
    }
    stages {
        stage('Building and Testing'){
            when{
                anyOf{
                    equals expected: true, actual: params.RUN_CHECKS
                    equals expected: true, actual: params.TEST_RUN_TOX
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    equals expected: true, actual: params.DEPLOY_DOCS
                }
            }
            stages{
                stage('Build') {
                    parallel {
                        stage("Python Package"){
                            agent {
                                dockerfile {
                                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                                    label 'linux && docker && x86'
                                    additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
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
                                    label 'linux && docker && x86'
                                    additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
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
                                            label 'linux && docker && x86'
                                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                            args '--mount source=sonar-cache-uiucprescon-packager,target=/home/user/.sonar/cache'
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
                                                        }
                                                    }
                                                }
                                                stage('Task Scanner'){
                                                    steps{
                                                        recordIssues(tools: [taskScanner(highTags: 'FIXME', includePattern: 'uiucprescon/**/*.py', normalTags: 'TODO')])
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
                                                        }
                                                    }
                                                }
                                                stage("Run Pylint Static Analysis") {
                                                    steps{
                                                        withEnv(['PYLINTHOME=.']) {
                                                            catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                                                tee('reports/pylint.txt'){
                                                                    sh(
                                                                        script: 'pylint uiucprescon/packager -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"',
                                                                        label: "Running pylint"
                                                                    )
                                                                }
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
                                                            archiveArtifacts allowEmptyArchive: true, artifacts: "reports/pylint.txt"
                                                            recordIssues(skipBlames: true, tools: [pyLint(pattern: 'reports/pylint.txt')])
                                                        }
                                                    }
                                                }
                                                stage("pyDocStyle"){
                                                    steps{
                                                        catchError(buildResult: 'SUCCESS', message: 'Did not pass all pyDocStyle tests', stageResult: 'UNSTABLE') {
                                                            tee('reports/pydocstyle-report.txt'){
                                                                sh(
                                                                    label: "Run pydocstyle",
                                                                    script: 'pydocstyle uiucprescon/packager'
                                                                )
                                                            }
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
                                                }
                                            }
                                        }
                                        stage("Sonarcloud Analysis"){
                                            options{
                                                lock("uiucprescon.packager-sonarscanner")
                                            }
                                            when{
                                                equals expected: true, actual: params.USE_SONARQUBE
                                                beforeOptions true
                                            }
                                            steps{
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
                                    post{
                                        cleanup{
                                            cleanWs(patterns: [
                                                    [pattern: 'reports/coverage.xml', type: 'INCLUDE'],
                                                    [pattern: 'reports/coverage', type: 'INCLUDE'],
                                                    [pattern: "dist/", type: 'INCLUDE'],
                                                    [pattern: 'build/', type: 'INCLUDE'],
                                                    [pattern: '.pytest_cache/', type: 'INCLUDE'],
                                                    [pattern: '.mypy_cache/', type: 'INCLUDE'],
                                                    [pattern: '.tox/', type: 'INCLUDE'],
                                                    [pattern: 'uiucprescon.packager.egg-info/', type: 'INCLUDE'],
                                                    [pattern: 'reports/', type: 'INCLUDE'],
                                                    [pattern: 'logs/', type: 'INCLUDE']
                                                ])
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
                            def tox = fileLoader.fromGit(
                                'tox',
                                'https://github.com/UIUCLibrary/jenkins_helper_scripts.git',
                                '4',
                                null,
                                ''
                            )
                            def windowsJobs = [:]
                            def linuxJobs = [:]
                            script{
                                parallel(
                                    'Linux': {
                                        linuxJobs = tox.getToxTestsParallel(
                                                envNamePrefix: 'Tox Linux',
                                                label: 'linux && docker && x86',
                                                dockerfile: 'ci/docker/python/linux/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                            )
                                    },
                                    'Windows': {
                                        windowsJobs = tox.getToxTestsParallel(
                                                envNamePrefix: 'Tox Windows',
                                                label: 'windows && docker && x86',
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
                            label 'linux && docker && x86'
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
                                def architectures = []
                                if(params.INCLUDE_X86_64_MACOS == true){
                                    architectures.add('x86_64')
                                }
                                if(params.INCLUDE_ARM_MACOS == true){
                                    architectures.add("m1")
                                }
                                architectures.each{ processorArchitecture ->
                                    macTests["Mac - ${processorArchitecture} - Python ${pythonVersion}: sdist"] = {
                                        packages.testPkg(
                                                agent: [
                                                    label: "mac && python${pythonVersion} && ${processorArchitecture}",
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
                                                                   venv/bin/pip install -r requirements/requirements_tox.txt
                                                                   '''
                                                    )
                                                },
                                                testTeardown: {
                                                    sh 'rm -r venv/'
                                                },
                                                onFailure: {
                                                    sh(label: 'Getting installed packages',
                                                       script:
                                                        '''. ./venv/bin/activate
                                                            pip list
                                                        '''
                                                        )
                                                },

                                            )
                                    }
                                    macTests["Mac - ${processorArchitecture} - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg(
                                                agent: [
                                                    label: "mac && python${pythonVersion} && ${processorArchitecture}",
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
                                                                   venv/bin/pip install -r requirements/requirements_tox.txt
                                                                   '''
                                                    )
                                                },
                                                onFailure: {
                                                    sh(label: 'Getting installed packages',
                                                       script:
                                                        '''. ./venv/bin/activate
                                                            pip list
                                                        '''
                                                        )
                                                },
                                                testTeardown: {
                                                    sh 'rm -r venv/'
                                                }

                                            )
                                    }
                                }
                            }
                            def linuxTests = [:]
                            SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
                                def architectures = ['x86']
                                if(params.INCLUDE_ARM_LINUX == true){
                                    architectures.add("arm")
                                }
                                architectures.each{ processorArchitecture ->
                                    linuxTests["Linux - Python ${pythonVersion}-${processorArchitecture}: sdist"] = {
                                        packages.testPkg(
                                            agent: [
                                                dockerfile: [
                                                    label: "linux && docker && ${processorArchitecture}",
                                                    filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                                ]
                                            ],
                                            retryTimes: 3,
                                            glob: 'dist/*.tar.gz',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion,
                                            onFailure: {
                                                sh(script:'pip list')
                                            },
                                        )
                                    }
                                    linuxTests["Linux - Python ${pythonVersion}-${processorArchitecture}: wheel"] = {
                                        packages.testPkg(
                                            agent: [
                                                dockerfile: [
                                                    label: "linux && docker && ${processorArchitecture}",
                                                    filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                                ]
                                            ],
                                            retryTimes: 3,
                                            glob: 'dist/*.whl',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion,
                                            onFailure: {
                                                sh(script:'pip list')
                                            },
                                        )
                                    }
                                }
                            }
                            def windowsTests = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                windowsTests["Windows - Python ${pythonVersion}: sdist"] = {
                                        packages.testPkg(
                                            agent: [
                                                dockerfile: [
                                                    label: 'windows && docker && x86',
                                                    filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                                ]
                                            ],
                                            retryTimes: 3,
                                            glob: 'dist/*.tar.gz,dist/*.zip',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion,
                                            onFailure: {
                                                bat(script:'pip list')
                                            },
                                        )
                                    }
                                windowsTests["Windows - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg(
                                            agent: [
                                                dockerfile: [
                                                    label: 'windows && docker && x86',
                                                    filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                                ]
                                            ],
                                            retryTimes: 3,
                                            glob: 'dist/*.whl',
                                            stash: 'PYTHON_PACKAGES',
                                            pythonVersion: pythonVersion,
                                            onFailure: {
                                                bat(script:'pip list')
                                            },
                                        )
                                    }
                            }
                            def tests = windowsTests + linuxTests + macTests
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
                            filename 'ci/docker/python/linux/tox/Dockerfile'
                            label 'linux && docker && devpi-access'
                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                          }
                    }
                    options{
                        retry(3)
                    }
                    steps {
                        unstash 'DOCS_ARCHIVE'
                        unstash 'PYTHON_PACKAGES'
                        script{
                            def devpi = load('ci/jenkins/scripts/devpi.groovy')
                            devpi.upload(
                                    server: DEVPI_CONFIG.server,
                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                    index: DEVPI_CONFIG.stagingIndex,
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
                                def architectures = []
                                if(params.INCLUDE_X86_64_MACOS == true){
                                    architectures.add('x86_64')
                                }
                                if(params.INCLUDE_ARM_MACOS == true){
                                    architectures.add("m1")
                                }
                                architectures.each{ processorArchitecture ->
                                    macPackages["Test Python ${pythonVersion}: wheel Mac ${processorArchitecture}"] = {
                                        withEnv(['PATH+EXTRA=./venv/bin']) {
                                            devpi.testDevpiPackage(
                                                agent: [
                                                    label: "mac && python${pythonVersion} && ${processorArchitecture} && devpi-access"
                                                ],
                                                devpi: [
                                                    index: DEVPI_CONFIG.stagingIndex,
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
                                                        checkout scm
                                                        sh(
                                                            label:'Installing Devpi client',
                                                            script: '''python3 -m venv venv
                                                                       . ./venv/bin/activate
                                                                       python -m pip install pip --upgrade
                                                                       python -m pip install devpi_client -r requirements/requirements_tox.txt
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
                                    macPackages["Test Python ${pythonVersion}: sdist Mac ${processorArchitecture}"] = {
                                        withEnv(['PATH+EXTRA=./venv/bin']) {
                                            devpi.testDevpiPackage(
                                                agent: [
                                                    label: "mac && python${pythonVersion} && ${processorArchitecture} && devpi-access"
                                                ],
                                                devpi: [
                                                    index: DEVPI_CONFIG.stagingIndex,
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
                                                                       . ./venv/bin/activate
                                                                       python -m pip install pip --upgrade
                                                                       python -m pip install devpi_client -r requirements/requirements_tox.txt
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
                                                label: 'windows && docker && x86 && devpi-access'
                                            ]
                                        ],
                                        retryTimes: 3,
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
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
                                                label: 'windows && docker && x86'
                                            ]
                                        ],
                                        retryTimes: 3,
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
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
                                                label: 'linux && docker && x86 && devpi-access'
                                            ]
                                        ],
                                        retryTimes: 3,
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
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
                                                label: 'linux && docker && x86 && devpi-access'
                                            ]
                                        ],
                                        retryTimes: 3,
                                        devpi: [
                                            index: DEVPI_CONFIG.stagingIndex,
                                            server: DEVPI_CONFIG.server,
                                            credentialsId: DEVPI_CONFIG.credentialsId,
                                        ],
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
                            label 'linux && docker && devpi-access'
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
                                indexSource: DEVPI_CONFIG.stagingIndex,
                                indexDestination: 'production/release',
                                credentialsId: DEVPI_CONFIG.credentialsId
                            )
                        }
                    }
                }
            }
            post{
                success{
                    node('linux && docker && devpi-access') {
                        checkout scm
                        script{
                            if (!env.TAG_NAME?.trim()){
                                docker.build("uiucpresconpackager:devpi",'-f ./ci/docker/python/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                    def devpi = load('ci/jenkins/scripts/devpi.groovy')
                                    devpi.pushPackageToIndex(
                                        pkgName: props.Name,
                                        pkgVersion: props.Version,
                                        server: DEVPI_CONFIG.server,
                                        indexSource: DEVPI_CONFIG.stagingIndex,
                                        indexDestination: "DS_Jenkins/${env.BRANCH_NAME}",
                                        credentialsId: DEVPI_CONFIG.credentialsId
                                    )
                                }
                            }
                        }
                    }
                }
                cleanup{
                    node('linux && docker && devpi-access') {
                       script{
                            checkout scm
                            docker.build("uiucpresconpackager:devpi",'-f ci/docker/python/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                def devpi = load('ci/jenkins/scripts/devpi.groovy')
                                devpi.removePackage(
                                    pkgName: props.Name,
                                    pkgVersion: props.Version,
                                    index: DEVPI_CONFIG.stagingIndex,
                                    server: DEVPI_CONFIG.server,
                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                )
                            }
                       }
                    }
                }
            }
        }
        stage('Deploy'){
            parallel {
                stage('Deploy to pypi') {
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '-build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    when{
                        allOf{
                            equals expected: true, actual: params.BUILD_PACKAGES
                            equals expected: true, actual: params.DEPLOY_PYPI
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        retry(3)
                    }
                    input {
                        message 'Upload to pypi server?'
                        parameters {
                            choice(
                                choices: getPypiConfig(),
                                description: 'Url to the pypi index to upload python packages.',
                                name: 'SERVER_URL'
                            )
                        }
                    }
                    steps{
                        unstash 'PYTHON_PACKAGES'
                        script{
                            def pypi = fileLoader.fromGit(
                                    'pypi',
                                    'https://github.com/UIUCLibrary/jenkins_helper_scripts.git',
                                    '2',
                                    null,
                                    ''
                                )
                            pypi.pypiUpload(
                                credentialsId: 'jenkins-nexus',
                                repositoryUrl: SERVER_URL,
                                glob: 'dist/*'
                                )
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE']
                                    ]
                            )
                        }
                    }
                }
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                    }
                    agent any
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
                                        remoteDirectory: params.DEPLOY_DOCS_URL_SUBFOLDER,
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
