// NOTE: this pipeline is too big for normal Jenkins operations. You have to turn on script splitting by entering
//       'org.jenkinsci.plugins.pipeline.modeldefinition.parser.RuntimeASTTransformer.SCRIPT_SPLITTING_TRANSFORMATION=true'
//       into the the Script Console. (No quotes)


def getPypiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['deployment']['indexes']
        }
    }
}


def installMSVCRuntime(cacheLocation){
    def cachedFile = "${cacheLocation}\\vc_redist.x64.exe".replaceAll(/\\\\+/, '\\\\')
    withEnv(
        [
            "CACHED_FILE=${cachedFile}",
            "RUNTIME_DOWNLOAD_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe"
        ]
    ){
        lock("${cachedFile}-${env.NODE_NAME}"){
            powershell(
                label: 'Ensuring vc_redist runtime installer is available',
                script: '''if ([System.IO.File]::Exists("$Env:CACHED_FILE"))
                           {
                                Write-Host 'Found installer'
                            } else {
                                Write-Host 'No installer found'
                                Write-Host 'Downloading runtime'
                                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;Invoke-WebRequest "$Env:RUNTIME_DOWNLOAD_URL" -OutFile "$Env:CACHED_FILE"
                           }
                        '''
            )
        }
        powershell(label: 'Install VC Runtime', script: 'Start-Process -filepath "$Env:CACHED_FILE" -ArgumentList "/install", "/passive", "/norestart" -Passthru | Wait-Process;')
    }
}

def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: '.scannerwork/report-task.txt'
        def response = httpRequest url : props['serverUrl'] + "/api/issues/search?componentKeys=" + props['projectKey'] + "&resolved=no"
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
    }
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
def call(){
    library(
        identifier: 'JenkinsPythonHelperLibrary@2024.12.0',
        retriever: modernSCM(
            [
                $class: 'GitSCMSource',
                remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git'
            ]
        )
    )
    pipeline {
        agent none
        parameters {
            booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
            booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
            booleanParam(name: 'USE_SONARQUBE', defaultValue: true, description: 'Send data test data to SonarQube')
            credentials(name: 'SONARCLOUD_TOKEN', credentialType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl', defaultValue: 'sonarcloud_token', required: false)
            booleanParam(name: 'BUILD_PACKAGES', defaultValue: false, description: 'Build Python packages')
            booleanParam(name: 'INCLUDE_MACOS-ARM64', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
            booleanParam(name: 'INCLUDE_MACOS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Mac')
            booleanParam(name: 'INCLUDE_LINUX-ARM64', defaultValue: false, description: 'Include ARM architecture for Linux')
            booleanParam(name: 'INCLUDE_LINUX-X86_64', defaultValue: true, description: 'Include x86_64 architecture for Linux')
            booleanParam(name: 'INCLUDE_WINDOWS-X86_64', defaultValue: true, description: 'Include x86_64 architecture for Windows')
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
                        stages {
                            stage('Sphinx Documentation'){
                                agent {
                                    docker{
                                        image 'python'
                                        label 'docker && linux && x86_64' // needed for pysonar-scanner which is x86_64 only as of 0.2.0.520
                                        args '--mount source=python-tmp-uiucpreson-packager,target=/tmp'
                                    }
                                }
                                environment{
                                    PIP_CACHE_DIR='/tmp/pipcache'
                                    UV_TOOL_DIR='/tmp/uvtools'
                                    UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                    UV_PYTHON = '3.12'
                                    UV_FROZEN = '1'
                                }
                                options {
                                    retry(conditions: [agent()], count: 2)
                                }
                                steps {
                                    sh(
                                        label: "Building docs on ${env.NODE_NAME}",
                                        script: '''python3 -m venv venv
                                                   trap "rm -rf venv" EXIT
                                                   venv/bin/pip install --disable-pip-version-check uv
                                                   mkdir -p logs
                                                   ./venv/bin/uv run --group docs --no-dev sphinx-build docs/source build/docs/html -d build/docs/.doctrees -v -w logs/build_sphinx.log
                                                '''
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
                                        sh 'git clean -dfx'
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
                                            docker{
                                                image 'python'
                                                label 'docker && linux && x86_64' // needed for pysonar-scanner which is x86_64 only as of 0.2.0.520
                                                args '--mount source=python-tmp-uiucpreson-packager,target=/tmp'
                                            }
                                        }
                                        environment{
                                            PIP_CACHE_DIR='/tmp/pipcache'
                                            UV_TOOL_DIR='/tmp/uvtools'
                                            UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                            UV_CACHE_DIR='/tmp/uvcache'
                                            UV_PYTHON = '3.12'
                                            UV_FROZEN = '1'
                                        }
                                        stages{
                                            stage('Configuring Testing Environment'){
                                                steps{
                                                    sh(
                                                        label: 'Create virtual environment',
                                                        script: '''python3 -m venv bootstrap_uv
                                                                   bootstrap_uv/bin/pip install --disable-pip-version-check uv
                                                                   bootstrap_uv/bin/uv sync --group=ci --extra=kdu
                                                                   bootstrap_uv/bin/uv pip install uv --target .venv
                                                                   rm -rf bootstrap_uv
                                                                   '''
                                                               )
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
                                                            sh '.venv/bin/uv run coverage run --parallel-mode --source src -m pytest --junitxml=reports/pytest/junit-pytest.xml'
                                                        }
                                                        post {
                                                            always {
                                                                junit 'reports/pytest/junit-pytest.xml'
                                                            }
                                                        }
                                                    }
                                                    stage('Task Scanner'){
                                                        steps{
                                                            recordIssues(tools: [taskScanner(highTags: 'FIXME', includePattern: 'src/**/*.py', normalTags: 'TODO')])
                                                        }
                                                    }
                                                    stage('Run Doctest Tests'){
                                                        steps {
                                                            sh '.venv/bin/uv run coverage run --parallel-mode --source src -m sphinx -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log'
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
                                                                sh '.venv/bin/uv run mypy -p uiucprescon.packager --html-report reports/mypy/html/  | tee logs/mypy.log'
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
                                                                    script: '.venv/bin/uv run bandit --format json --output reports/bandit-report.json --recursive src || .venv/bin/uv run bandit -f html --recursive src --output reports/bandit-report.html'
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
                                                                            label: 'Running pylint',
                                                                            script: '.venv/bin/uv run pylint src -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"'
                                                                        )
                                                                    }
                                                                }
                                                                sh(
                                                                    label: 'Running pylint for sonarqube',
                                                                    returnStatus: true,
                                                                    script: '.venv/bin/uv run pylint src  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint_issues.txt'
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
                                                                        script: '.venv/bin/uv run pydocstyle src'
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
                                                                              .venv/bin/uv run flake8 src --tee --output-file=logs/flake8.log
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
                                                        sh '''.venv/bin/uv run coverage combine
                                                              .venv/bin/uv run coverage xml -o reports/coverage.xml
                                                           '''
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
                                                environment{
                                                    VERSION="${readTOML( file: 'pyproject.toml')['project'].version}"
                                                    SONAR_USER_HOME='/tmp/sonar'
                                                }
                                                steps{
                                                    milestone ordinal: 1, label: 'sonarcloud'
                                                    script{
                                                        withSonarQubeEnv(installationName:'sonarcloud', credentialsId: params.SONARCLOUD_TOKEN) {
                                                            def sourceInstruction
                                                            if (env.CHANGE_ID){
                                                                sourceInstruction = '-Dsonar.pullrequest.key=$CHANGE_ID -Dsonar.pullrequest.base=$BRANCH_NAME'
                                                            } else{
                                                                sourceInstruction = '-Dsonar.branch.name=$BRANCH_NAME'
                                                            }
                                                            withCredentials([string(credentialsId: params.SONARCLOUD_TOKEN, variable: 'token')]) {
                                                                sh(
                                                                    label: 'Running Sonar Scanner',
                                                                    script: " .venv/bin/uv run pysonar -t \$token -Dsonar.projectVersion=$VERSION -Dsonar.buildString=\"$BUILD_TAG\" ${sourceInstruction}"
                                                                )
                                                            }
                                                        }
                                                        script{
                                                            timeout(time: 1, unit: 'HOURS') {
                                                                def sonarqubeResult = waitForQualityGate(abortPipeline: false, credentialsId: params.SONARCLOUD_TOKEN)
                                                                if (sonarqubeResult.status != 'OK') {
                                                                   unstable "SonarQube quality gate: ${sonarqubeResult.status}"
                                                               }
                                                               if(env.BRANCH_IS_PRIMARY){
                                                                   writeJSON file: 'reports/sonar-report.json', json: get_sonarqube_unresolved_issues('.sonar/report-task.txt')
                                                                   recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                                                               }
                                                            }
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
                                                sh 'git clean -dfx'
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
                                environment{
                                    PIP_CACHE_DIR='/tmp/pipcache'
                                    UV_TOOL_DIR='/tmp/uvtools'
                                    UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                }
                                steps{
                                    script{
                                        def envs = []
                                        node('docker && linux'){
                                            checkout scm
                                            docker.image('python').inside('--mount source=python-tmp-uiucpreson-packager,target=/tmp'){
                                                try{
                                                    sh(script: 'python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv')
                                                    envs = sh(
                                                        label: 'Get tox environments',
                                                        script: './venv/bin/uv run --quiet --only-group tox --with tox-uv --isolated tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\n')
                                                } finally{
                                                    sh 'git clean -dfx'
                                                }
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && linux'){
                                                            try{
                                                                checkout scm
                                                                docker.image('python').inside('--mount source=python-tmp-uiucpreson-packager,target=/tmp'){
                                                                    try{
                                                                        sh( label: 'Running Tox',
                                                                            script: """python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                                                                       ./venv/bin/uv python install cpython-${version}
                                                                                       ./venv/bin/uv run --only-group tox --with tox-uv --isolated tox run -e ${toxEnv} --runner uv-venv-lock-runner -vvv
                                                                                       rm -rf ./.tox
                                                                                    """
                                                                            )
                                                                    } catch(e) {
                                                                        sh(script: './venv/bin/uv python list')
                                                                        throw e
                                                                    }
                                                                }
                                                            } finally{
                                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        )
                                    }
                                }
                            }
                            stage('Windows'){
                                when{
                                    expression {return nodesByLabel('windows && docker && x86').size() > 0}
                                }
                                environment{
                                    PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\pipcache'
                                    UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvtools'
                                    UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvpython'
                                    UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
                                    VC_RUNTIME_INSTALLER_LOCATION='c:\\msvc_runtime'
                                }
                                steps{
                                    script{
                                        def envs = []
                                        node('docker && windows'){
                                            checkout scm
                                            try{
                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                    .inside("\
                                                        --mount type=volume,source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR} \
                                                        --mount type=volume,source=pipcache,target=${env.PIP_CACHE_DIR} \
                                                        --mount type=volume,source=uv_cache_dir,target=${env.UV_CACHE_DIR}\
                                                        "
                                                    ){
                                                    bat(script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv')
                                                    envs = bat(
                                                        label: 'Get tox environments',
                                                        script: '@.\\venv\\Scripts\\uv run --quiet --only-group tox --with tox-uv --isolated tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\r\n')
                                                }
                                            } finally{
                                                bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && windows'){
                                                            checkout scm
                                                            try{
                                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                                    .inside("\
                                                                        --mount type=volume,source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR} \
                                                                        --mount type=volume,source=msvc-runtime,target=${env.VC_RUNTIME_INSTALLER_LOCATION} \
                                                                        --mount type=volume,source=pipcache,target=${env.PIP_CACHE_DIR} \
                                                                        --mount type=volume,source=uv_cache_dir,target=${env.UV_CACHE_DIR}\
                                                                        "
                                                                    ){
                                                                    installMSVCRuntime(env.VC_RUNTIME_INSTALLER_LOCATION)
                                                                    retry(3){
                                                                        try{
                                                                            bat(label: 'Install uv',
                                                                                script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv'
                                                                            )
                                                                            bat(label: 'Running Tox',
                                                                                script: """venv\\Scripts\\uv python install cpython-${version}
                                                                                           venv\\Scripts\\uv run --only-group tox --with tox-uv --isolated tox run -e ${toxEnv} --runner uv-venv-lock-runner
                                                                                           rmdir /s/q .tox
                                                                                        """
                                                                            )
                                                                        } catch(e){
                                                                            cleanWs(
                                                                                deleteDirs: true,
                                                                                patterns: [
                                                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                                                    [pattern: '.tox/', type: 'INCLUDE'],
                                                                                ]
                                                                            )
                                                                            throw e
                                                                        }
                                                                    }
                                                                }
                                                            } finally{
                                                                bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            }

                                                        }
                                                    }
                                                ]
                                            }
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
                            docker{
                                image 'python'
                                label 'linux && docker'
                                args '--mount source=python-tmp-uiucpreson-packager,target=/tmp'
                              }
                        }
                        options{
                            timeout(5)
                        }
                        environment{
                            PIP_CACHE_DIR='/tmp/pipcache'
                            UV_CACHE_DIR='/tmp/uvcache'
                        }
                        steps {
                            sh(
                                label: 'Package',
                                script: '''python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                           trap "rm -rf venv" EXIT
                                           ./venv/bin/uv build
                                        '''
                            )
                        }
                        post {
                            always{
                                stash includes: 'dist/*.*', name: 'PYTHON_PACKAGES'
                            }
                            success {
                                archiveArtifacts artifacts: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', fingerprint: true
                            }
                            cleanup{
                                sh 'git clean -dfx'
                            }
                        }
                    }
                    stage('Testing Packages'){
                        when{
                            equals expected: true, actual: params.TEST_PACKAGES
                        }
                        steps{
                            customMatrix(
                                axes: [
                                    [
                                        name: 'PYTHON_VERSION',
                                        values: ['3.10', '3.11', '3.12','3.13']
                                    ],
                                    [
                                        name: 'OS',
                                        values: ['linux','macos','windows']
                                    ],
                                    [
                                        name: 'ARCHITECTURE',
                                        values: ['x86_64', 'arm64']
                                    ],
                                    [
                                        name: 'PACKAGE_TYPE',
                                        values: ['wheel', 'sdist'],
                                    ]
                                ],
                                excludes: [
                                    [
                                        [
                                            name: 'OS',
                                            values: 'windows'
                                        ],
                                        [
                                            name: 'ARCHITECTURE',
                                            values: 'arm64',
                                        ]
                                    ]
                                ],
                                when: {entry -> "INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase() && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]},
                                stages: [
                                    { entry ->
                                        stage('Test Package') {
                                            node("${entry.OS} && ${entry.ARCHITECTURE} ${['linux', 'windows'].contains(entry.OS) ? '&& docker': ''}"){
                                                timeout(60){
                                                    try{
                                                        checkout scm
                                                        unstash 'PYTHON_PACKAGES'
                                                        if(['linux', 'windows'].contains(entry.OS) && params.containsKey("INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]){
                                                            docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                                .inside(
                                                                    isUnix() ?
                                                                        '--mount source=python-tmp-uiucpreson-packager,target=/tmp'
                                                                    :
                                                                        "\
                                                                            --mount type=volume,source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython \
                                                                            --mount type=volume,source=msvc-runtime,target=c:\\msvc_runtime \
                                                                            --mount type=volume,source=pipcache,target=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache \
                                                                            --mount type=volume,source=uv_cache_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache \
                                                                        "
                                                                ){
                                                                 if(isUnix()){
                                                                    withEnv([
                                                                        'PIP_CACHE_DIR=/tmp/pipcache',
                                                                        'UV_TOOL_DIR=/tmp/uvtools',
                                                                        'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                                                        'UV_CACHE_DIR=/tmp/uvcache',
                                                                    ]){
                                                                         sh(
                                                                            label: 'Testing with tox',
                                                                            script: """python3 -m venv venv
                                                                                       ./venv/bin/pip install --disable-pip-version-check uv
                                                                                       ./venv/bin/uv python install cpython-${entry.PYTHON_VERSION}
                                                                                       ./venv/bin/uv run --only-group tox --with tox-uv --isolated tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                    """
                                                                        )
                                                                    }
                                                                 } else {
                                                                    withEnv([
                                                                        'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                                                                        'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvtools',
                                                                        'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                                                                        'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                                                                    ]){
                                                                        installMSVCRuntime('c:\\msvc_runtime\\')
                                                                        bat(
                                                                            label: 'Testing with tox',
                                                                            script: """python -m venv venv
                                                                                       .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                       .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                                       .\\venv\\Scripts\\uv run --only-group tox --with tox-uv --isolated tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                    """
                                                                        )
                                                                    }
                                                                 }
                                                            }
                                                        } else {
                                                            if(isUnix()){
                                                                sh(
                                                                    label: 'Testing with tox',
                                                                    script: """python3 -m venv venv
                                                                               ./venv/bin/pip install --disable-pip-version-check uv
                                                                               ./venv/bin/uv run --only-group tox --with tox-uv --isolated tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                            """
                                                                )
                                                            } else {
                                                                bat(
                                                                    label: 'Testing with tox',
                                                                    script: """python -m venv venv
                                                                               .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                               .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                               .\\venv\\Scripts\\uv run --only-group tox --with tox-uv --isolated tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                            """
                                                                )
                                                            }
                                                        }
                                                    } finally{
                                                        if(isUnix()){
                                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        } else {
                                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                ]
                            )
                        }
                    }
                }
            }
            stage('Deploy'){
                parallel {
                    stage('Deploy to pypi') {
                        environment{
                            PIP_CACHE_DIR='/tmp/pipcache'
                            UV_TOOL_DIR='/tmp/uvtools'
                            UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                            UV_CACHE_DIR='/tmp/uvcache'
                        }
                        agent {
                            docker{
                                image 'python'
                                label 'docker && linux'
                                args '--mount source=python-tmp-uiucpreson-packager,target=/tmp'
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
                            withEnv(["TWINE_REPOSITORY_URL=${SERVER_URL}",]){
                                withCredentials(
                                    [
                                        usernamePassword(
                                            credentialsId: 'jenkins-nexus',
                                            passwordVariable: 'TWINE_PASSWORD',
                                            usernameVariable: 'TWINE_USERNAME'
                                        )
                                    ]
                                ){
                                    sh(
                                        label: 'Uploading to pypi',
                                        script: '''python3 -m venv venv
                                                   trap "rm -rf venv" EXIT
                                                   ./venv/bin/pip install --disable-pip-version-check uv
                                                   ./venv/bin/uv run --only-group release twine --installpkg upload --disable-progress-bar --non-interactive dist/*
                                                '''
                                    )
                                }
                            }
                        }
                        post{
                            cleanup{
                                sh 'git clean -dfx'
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
}
