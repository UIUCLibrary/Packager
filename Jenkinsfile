library identifier: 'JenkinsPythonHelperLibrary@2024.1.2', retriever: modernSCM(
  [$class: 'GitSCMSource',
   remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git',
   ])

// ============================================================================
// Versions of python that are supported
// ----------------------------------------------------------------------------
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9', '3.10', '3.11', '3.12']
SUPPORTED_LINUX_VERSIONS = ['3.8', '3.9', '3.10', '3.11', '3.12']
SUPPORTED_WINDOWS_VERSIONS = ['3.8', '3.9', '3.10', '3.11', '3.12']

def getPypiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['deployment']['indexes']
        }
    }
}

defaultParameterValues = [
    USE_SONARQUBE: false
]



def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: '.scannerwork/report-task.txt'
        def response = httpRequest url : props['serverUrl'] + "/api/issues/search?componentKeys=" + props['projectKey'] + "&resolved=no"
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
    }
}

def testPackages(){

    macTests = [:]
    SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
        def architectures = []
        if(params.INCLUDE_MACOS_X86_64 == true){
            architectures.add('x86_64')
        }
        if(params.INCLUDE_MACOS_ARM == true){
            architectures.add('arm64')
        }
        architectures.each{ processorArchitecture ->
            macTests["Mac - ${processorArchitecture} - Python ${pythonVersion}: sdist"] = {
                testPythonPkg(
                    agent: [
                        label: "mac && python${pythonVersion} && ${processorArchitecture}",
                    ],
                    retries: 3,
                    testSetup: {
                        checkout scm
                        unstash 'PYTHON_PACKAGES'
                    },
                    testCommand: {
                        findFiles(glob: 'dist/*.tar.gz').each{
                            sh(label: 'Running Tox',
                               script: """python${pythonVersion} -m venv venv
                               ./venv/bin/python -m pip install --upgrade pip
                               ./venv/bin/pip install -r requirements/requirements_tox.txt
                               ./venv/bin/tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                            )
                        }

                    },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: 'venv/', type: 'INCLUDE'],
                                        [pattern: '.tox/', type: 'INCLUDE'],
                                    ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                    ]
                )
            }
            macTests["Mac - ${processorArchitecture} - Python ${pythonVersion}: wheel"] = {
                testPythonPkg(
                    agent: [
                        label: "mac && python${pythonVersion} && ${processorArchitecture}",
                    ],
                    retries: 3,
                    testCommand: {
                        unstash 'PYTHON_PACKAGES'
                        findFiles(glob: 'dist/*.whl').each{
                            sh(label: 'Running Tox',
                               script: """python${pythonVersion} -m venv venv
                                          . ./venv/bin/activate
                                          python -m pip install --upgrade pip
                                          pip install -r requirements/requirements_tox.txt
                                          tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                       """
                            )
                        }
                    },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: 'venv/', type: 'INCLUDE'],
                                        [pattern: '.tox/', type: 'INCLUDE'],
                                    ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                        success: {
                             archiveArtifacts artifacts: 'dist/*.whl'
                        }
                    ]
                )
            }
        }
    }
    def linuxTests = [:]
    SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
        def architectures = []
        if(params.INCLUDE_LINUX_ARM == true){
            architectures.add('arm64')
        }
        if(params.INCLUDE_LINUX_X86_64 == true){
            architectures.add('x86_64')
        }
        architectures.each{ processorArchitecture ->
            linuxTests["Linux-${processorArchitecture} - Python ${pythonVersion}: sdist"] = {
                testPythonPkg(
                    agent: [
                        dockerfile: [
                            label: "linux && docker && ${processorArchitecture}",
                            filename: 'ci/docker/python/linux/tox/Dockerfile',
                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                            args: '-v pipcache_packager:/.cache/pip',
                        ]
                    ],
                    retries: 3,
                    testSetup: {
                        checkout scm
                        unstash 'PYTHON_PACKAGES'
                    },
                    testCommand: {
                        findFiles(glob: 'dist/*.tar.gz').each{
                            sh(
                                label: 'Running Tox',
                                script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                )
                        }
                    },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                    ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                    ]
                )
            }
            linuxTests["Linux-${processorArchitecture} - Python ${pythonVersion}: wheel"] = {
                testPythonPkg(
                    agent: [
                        dockerfile: [
                            label: "linux && docker && ${processorArchitecture}",
                            filename: 'ci/docker/python/linux/tox/Dockerfile',
                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                            args: '-v pipcache_packager:/.cache/pip',
                        ]
                    ],
                    retries: 3,
                    testSetup: {
                        checkout scm
                        unstash 'PYTHON_PACKAGES'
                    },
                    testCommand: {
                        findFiles(glob: 'dist/*.whl').each{
                            timeout(5){
                                sh(
                                    label: 'Running Tox',
                                    script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                    )
                            }
                        }
                    },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                    ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                        success: {
                            archiveArtifacts artifacts: 'dist/*.whl'
                        },
                    ]
                )
            }
        }
    }
    def windowsTests = [:]
    if(params.INCLUDE_WINDOWS_X86_64 == true){
        SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
            windowsTests["Windows - Python ${pythonVersion}: sdist"] = {
                testPythonPkg(
                    agent: [
                        dockerfile: [
                            label: 'windows && docker && x86',
                            filename: 'ci/docker/python/windows/tox/Dockerfile',
                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
                            args: '-v pipcache_packager:c:/users/containeradministrator/appdata/local/pip'

                        ]
                    ],
                    retries: 3,
                    testSetup: {
                        checkout scm
                        unstash 'PYTHON_PACKAGES'
                    },
                    testCommand: {
                        findFiles(glob: 'dist/*.tar.gz').each{
                            bat(label: 'Running Tox', script: "tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')} -v")
                        }
                    },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                    [pattern: 'dist/', type: 'INCLUDE'],
                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                    ]
                )
            }
            windowsTests["Windows - Python ${pythonVersion}: wheel"] = {
                testPythonPkg(
                    agent: [
                        dockerfile: [
                            label: 'windows && docker && x86',
                            filename: 'ci/docker/python/windows/tox/Dockerfile',
                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
                            args: '-v pipcache_packager:c:/users/containeradministrator/appdata/local/pip'
                        ]
                    ],
                    retries: 3,
                    testSetup: {
                         checkout scm
                         unstash 'PYTHON_PACKAGES'
                    },
                    testCommand: {
                         findFiles(glob: 'dist/*.whl').each{
                             powershell(label: 'Running Tox', script: "tox --installpkg ${it.path} --workdir \$env:TEMP\\tox  -e py${pythonVersion.replace('.', '')}")
                         }

                    },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                    ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                        success: {
                            archiveArtifacts artifacts: 'dist/*.whl'
                        }
                    ]
                )
            }
        }
    }
    def tests = windowsTests + linuxTests + macTests
    parallel(tests)
}
def startup(){
    parallel(
        [
            failFast: true,
            'Loading Reference Build Information': {
                node(){
                    checkout scm
                    discoverGitReferenceBuild(latestBuildIfNotFound: true)
                }
            },
        ]
    )
}

startup()

pipeline {
    agent none
    parameters {
        booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'USE_SONARQUBE', defaultValue: true, description: 'Send data test data to SonarQube')
        credentials(name: 'SONARCLOUD_TOKEN', credentialType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl', defaultValue: 'sonarcloud_token', required: false)
        booleanParam(name: 'BUILD_PACKAGES', defaultValue: false, description: 'Build Python packages')
        booleanParam(name: 'INCLUDE_MACOS_ARM', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
        booleanParam(name: 'INCLUDE_MACOS_X86_64', defaultValue: false, description: 'Include x86_64 architecture for Mac')
        booleanParam(name: 'INCLUDE_LINUX_ARM', defaultValue: false, description: 'Include ARM architecture for Linux')
        booleanParam(name: 'INCLUDE_LINUX_X86_64', defaultValue: true, description: 'Include x86_64 architecture for Linux')
        booleanParam(name: 'INCLUDE_WINDOWS_X86_64', defaultValue: true, description: 'Include x86_64 architecture for Windows')
        booleanParam(name: 'TEST_PACKAGES', defaultValue: true, description: 'Test packages')
        booleanParam(name: 'DEPLOY_PYPI', defaultValue: false, description: 'Deploy to pypi')
        booleanParam(name: 'DEPLOY_DOCS', defaultValue: false, description: 'Update online documentation. Master branch Only')
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: 'packager', description: 'The directory that the docs should be saved under')
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
                    equals expected: true, actual: params.DEPLOY_DOCS
                }
            }
            stages{
                stage('Build') {
                    parallel {
                        stage('Python Package'){
                            agent {
                                dockerfile {
                                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                                    label 'linux && docker && x86'
                                    additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                }
                            }
                            options {
                                retry(conditions: [agent()], count: 2)
                            }
                            steps {
                                sh 'python setup.py build --build-lib build/lib --build-temp build/temp'
                            }
                            post{
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'build/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE'],
                                            ]
                                    )
                                }
                            }
                        }
                        stage('Sphinx Documentation'){
                            agent {
                                dockerfile {
                                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                                    label 'linux && docker && x86'
                                    additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                }
                            }
                            options {
                                retry(conditions: [agent()], count: 2)
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
                                        def props = readTOML( file: 'pyproject.toml')['project']
                                        def DOC_ZIP_FILENAME = "${props.name}-${props.version}.doc.zip"
                                        zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                        stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                                    }
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'build/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE'],
                                            [pattern: 'uiucprescon.packager.dist-info/', type: 'INCLUDE'],
                                            ]
                                        )
                                }
                            }
                        }
                    }
                }
                stage('Checks'){
                    when{
                        equals expected: true, actual: params.RUN_CHECKS
                    }
                    stages{
                        stage('Code Quality'){
                            stages{
                                stage('Test') {
                                    agent {
                                        dockerfile {
                                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                                            label 'linux && docker && x86'
                                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                                            args '--mount source=sonar-cache-uiucprescon-packager,target=/home/user/.sonar/cache'
                                        }
                                    }
                                    stages{
                                        stage('Configuring Testing Environment'){
                                            steps{
                                                sh(
                                                    label: 'Creating logging and report directories',
                                                    script: """
                                                        mkdir -p logs
                                                        mkdir -p reports/coverage
                                                        mkdir -p reports/doctests
                                                        mkdir -p reports/mypy/html
                                                    """
                                                )
                                            }
                                        }
                                        stage('Running Tests'){
                                            parallel {
                                                stage('Run PyTest Unit Tests'){
                                                    steps{
                                                        sh "coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=reports/pytest/junit-pytest.xml "
                                                    }
                                                    post {
                                                        always {
                                                            junit 'reports/pytest/junit-pytest.xml'
                                                        }
                                                    }
                                                }
                                                stage('Task Scanner'){
                                                    steps{
                                                        recordIssues(tools: [taskScanner(highTags: 'FIXME', includePattern: 'uiucprescon/**/*.py', normalTags: 'TODO')])
                                                    }
                                                }
                                                stage('Run Doctest Tests'){
                                                    steps {
                                                        sh 'coverage run --parallel-mode --source uiucprescon -m sphinx -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log'
                                                    }
                                                    post{
                                                        always {
                                                            archiveArtifacts artifacts: 'reports/doctest/output.txt'
                                                            archiveArtifacts artifacts: 'logs/doctest.log'
                                                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Doctest', pattern: 'logs/doctest.log', id: 'doctest')])
                                                        }

                                                    }
                                                }
                                                stage('Run MyPy Static Analysis') {
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
                                                stage('Run Bandit Static Analysis') {
                                                    steps{
                                                        catchError(buildResult: 'SUCCESS', message: 'Bandit found issues', stageResult: 'UNSTABLE') {
                                                            sh(
                                                                label: 'Running bandit',
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
                                                            archiveArtifacts 'reports/bandit-report.json'
                                                        }
                                                    }
                                                }
                                                stage('Run Pylint Static Analysis') {
                                                    steps{
                                                        withEnv(['PYLINTHOME=.']) {
                                                            catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                                                tee('reports/pylint.txt'){
                                                                    sh(
                                                                        script: 'pylint uiucprescon/packager -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"',
                                                                        label: 'Running pylint'
                                                                    )
                                                                }
                                                            }
                                                            sh(
                                                                script: 'pylint uiucprescon/packager  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint_issues.txt',
                                                                label: 'Running pylint for sonarqube',
                                                                returnStatus: true
                                                            )
                                                        }
                                                    }
                                                    post{
                                                        always{
                                                            archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/pylint.txt'
                                                            recordIssues(skipBlames: true, tools: [pyLint(pattern: 'reports/pylint.txt')])
                                                        }
                                                    }
                                                }
                                                stage('pyDocStyle'){
                                                    steps{
                                                        catchError(buildResult: 'SUCCESS', message: 'Did not pass all pyDocStyle tests', stageResult: 'UNSTABLE') {
                                                            tee('reports/pydocstyle-report.txt'){
                                                                sh(
                                                                    label: 'Run pydocstyle',
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
                                                stage('Run Flake8 Static Analysis') {
                                                    steps{
                                                        catchError(buildResult: 'SUCCESS', message: 'Flake8 found issues', stageResult: 'UNSTABLE') {
                                                            sh(label: 'Running Flake8',
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
                                                    sh 'coverage combine && coverage xml -o reports/coverage.xml'
                                                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                                                }
                                            }
                                        }
                                        stage('Sonarcloud Analysis'){
                                            options{
                                                lock('uiucprescon.packager-sonarscanner')
                                            }
                                            when{
                                                allOf{
                                                    equals expected: true, actual: params.USE_SONARQUBE
                                                    expression{
                                                        try{
                                                            withCredentials([string(credentialsId: params.SONARCLOUD_TOKEN, variable: 'dddd')]) {
                                                                echo 'Found credentials for sonarqube'
                                                            }
                                                        } catch(e){
                                                            return false
                                                        }
                                                        return true
                                                    }
                                                }
                                            }
                                            steps{
                                                script{
                                                    withSonarQubeEnv(installationName:'sonarcloud', credentialsId: params.SONARCLOUD_TOKEN) {
                                                        def props = readTOML( file: 'pyproject.toml')['project']
                                                        if (env.CHANGE_ID){
                                                            sh(
                                                                label: 'Running Sonar Scanner',
                                                                script:"sonar-scanner -Dsonar.projectVersion=${props.version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.CHANGE_TARGET}"
                                                                )
                                                        } else {
                                                            sh(
                                                                label: 'Running Sonar Scanner',
                                                                script: "sonar-scanner -Dsonar.projectVersion=${props.version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.branch.name=${env.BRANCH_NAME}"
                                                                )
                                                        }
                                                    }
                                                    timeout(time: 1, unit: 'HOURS') {
                                                        def sonarqube_result = waitForQualityGate(abortPipeline: false)
                                                        if (sonarqube_result.status != 'OK') {
                                                            unstable "SonarQube quality gate: ${sonarqube_result.status}"
                                                        }
                                                        def outstandingIssues = get_sonarqube_unresolved_issues('.scannerwork/report-task.txt')
                                                        writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                                                    }
                                                }
                                            }
                                            post {
                                                always{
                                                    archiveArtifacts(
                                                        allowEmptyArchive: true,
                                                        artifacts: '.scannerwork/report-task.txt'
                                                    )
                                                    script{
                                                        if(fileExists('reports/sonar-report.json')){
                                                            stash includes: 'reports/sonar-report.json', name: 'SONAR_REPORT'
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
                                                    [pattern: 'dist/', type: 'INCLUDE'],
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
                stage('Run Tox Test') {
                    when{
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    parallel{
                        stage('Linux'){
                            when{
                                expression {return nodesByLabel('linux && docker && x86').size() > 0}
                            }
                            steps{
                                script{
                                    parallel(
                                        getToxTestsParallel(
                                            envNamePrefix: 'Tox Linux',
                                            label: 'linux && docker && x86',
                                            dockerfile: 'ci/docker/python/linux/tox/Dockerfile',
                                            dockerArgs: '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL',
                                            dockerRunArgs: '-v pipcache_packager:/.cache/pip',
                                            retry: 2
                                        )
                                    )
                                }
                            }
                        }
                        stage('Windows'){
                            when{
                                expression {return nodesByLabel('windows && docker && x86').size() > 0}
                            }
                            steps{
                                script{
                                    parallel(
                                        getToxTestsParallel(
                                            envNamePrefix: 'Tox Windows',
                                            label: 'windows && docker && x86',
                                            dockerfile: 'ci/docker/python/windows/tox/Dockerfile',
                                            dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
                                            dockerRunArgs: '-v pipcache_packager:c:/users/containeradministrator/appdata/local/pip',
                                            retry: 2
                                        )
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('Distribution Packaging') {
            when{
                equals expected: true, actual: params.BUILD_PACKAGES
                beforeAgent true
            }
            stages{
                stage('Package') {
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/tox/Dockerfile'
                            label 'linux && docker && x86'
                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    options {
                        retry(2)
                    }
                    steps {
                        sh 'python3 -m build .'
                    }
                    post {
                        always{
                            stash includes: 'dist/*.*', name: 'PYTHON_PACKAGES'
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
                stage('Testing Packages'){
                    when{
                        equals expected: true, actual: params.TEST_PACKAGES
                        beforeAgent true
                    }
                    steps{
                        testPackages()
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
                            additionalBuildArgs '--build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
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
                        pypiUpload(
                            credentialsId: 'jenkins-nexus',
                            repositoryUrl: SERVER_URL,
                            glob: 'dist/*'
                        )
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
                stage('Deploy Online Documentation') {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                    }
                    agent any
                    steps{
                        unstash 'DOCS_ARCHIVE'
                        dir('build/docs/html/'){
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
