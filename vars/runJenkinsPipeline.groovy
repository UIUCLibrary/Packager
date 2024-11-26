// NOTE: this pipeline is too big for normal Jenkins operations. You have to turn on script splitting by entering
//       'org.jenkinsci.plugins.pipeline.modeldefinition.parser.RuntimeASTTransformer.SCRIPT_SPLITTING_TRANSFORMATION=true'
//       into the the Script Console. (No quotes)

library identifier: 'JenkinsPythonHelperLibrary@2024.1.2', retriever: modernSCM(
  [$class: 'GitSCMSource',
   remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git',
   ])


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
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    UV_TOOL_DIR='/tmp/uvtools'
                                    UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                    UV_PYTHON = '3.12'
                                }
                                options {
                                    retry(conditions: [agent()], count: 2)
                                }
                                steps {
                                    sh(
                                        label: "Building docs on ${env.NODE_NAME}",
                                        script: '''python3 -m venv venv
                                                  trap "rm -rf venv" EXIT
                                                  venv/bin/pip install uv
                                                  . ./venv/bin/activate
                                                  mkdir -p logs
                                                  uvx --from sphinx --with-editable . --with-requirements requirements-dev.txt sphinx-build docs/source build/docs/html -d build/docs/.doctrees -v -w logs/build_sphinx.log'''
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
                                            docker{
                                                image 'python'
                                                label 'docker && linux && x86_64' // needed for pysonar-scanner which is x86_64 only as of 0.2.0.520
                                                args '--mount source=python-tmp-uiucpreson-packager,target=/tmp'
                                            }
                                        }
                                        environment{
                                            PIP_CACHE_DIR='/tmp/pipcache'
                                            UV_INDEX_STRATEGY='unsafe-best-match'
                                            UV_TOOL_DIR='/tmp/uvtools'
                                            UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                            UV_CACHE_DIR='/tmp/uvcache'
                                            UV_PYTHON = '3.12'
                                        }
                                        stages{
                                            stage('Configuring Testing Environment'){
                                                steps{
                                                    sh(
                                                        label: 'Create virtual environment',
                                                        script: '''python3 -m venv bootstrap_uv
                                                                   bootstrap_uv/bin/pip install uv
                                                                   bootstrap_uv/bin/uv venv venv
                                                                   . ./venv/bin/activate
                                                                   bootstrap_uv/bin/uv pip install uv
                                                                   rm -rf bootstrap_uv
                                                                   uv pip install -r requirements-dev.txt
                                                                   '''
                                                               )
                                                    sh(
                                                        label: 'Install package in development mode',
                                                        script: '''. ./venv/bin/activate
                                                                   uv pip install -e .
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
                                                            sh '''. ./venv/bin/activate
                                                                  coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=reports/pytest/junit-pytest.xml
                                                               '''
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
                                                            sh '''. ./venv/bin/activate
                                                                  coverage run --parallel-mode --source uiucprescon -m sphinx -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log
                                                               '''
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
                                                                sh '''. ./venv/bin/activate
                                                                      mypy -p uiucprescon --html-report reports/mypy/html/  | tee logs/mypy.log
                                                                   '''
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
                                                                    script: '''. ./venv/bin/activate
                                                                               bandit --format json --output reports/bandit-report.json --recursive uiucprescon || bandit -f html --recursive uiucprescon --output reports/bandit-report.html
                                                                            '''
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
                                                                            script: '''. ./venv/bin/activate
                                                                                       pylint uiucprescon/packager -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"
                                                                                    '''
                                                                        )
                                                                    }
                                                                }
                                                                sh(
                                                                    label: 'Running pylint for sonarqube',
                                                                    returnStatus: true,
                                                                    script: '''. ./venv/bin/activate
                                                                               pylint uiucprescon/packager  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint_issues.txt
                                                                            '''
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
                                                                        script: '''. ./venv/bin/activate
                                                                                   pydocstyle uiucprescon/packager
                                                                                '''
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
                                                                   script: '''. ./venv/bin/activate
                                                                              mkdir -p logs
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
                                                        sh '''. ./venv/bin/activate
                                                              coverage combine && coverage xml -o reports/coverage.xml
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
                                                    script{
                                                        withSonarQubeEnv(installationName:'sonarcloud', credentialsId: params.SONARCLOUD_TOKEN) {
                                                            def sourceInstruction
                                                            if (env.CHANGE_ID){
                                                                sourceInstruction = '-Dsonar.pullrequest.key=$CHANGE_ID -Dsonar.pullrequest.base=$BRANCH_NAME'
                                                            } else{
                                                                sourceInstruction = '-Dsonar.branch.name=$BRANCH_NAME'
                                                            }
                                                            sh(
                                                                label: 'Running Sonar Scanner',
                                                                script: """. ./venv/bin/activate
                                                                            uv tool run pysonar-scanner -Dsonar.projectVersion=$VERSION -Dsonar.buildString=\"$BUILD_TAG\" ${sourceInstruction}
                                                                        """
                                                            )
                                                        }
                                                        timeout(time: 1, unit: 'HOURS') {
                                                            def sonarqube_result = waitForQualityGate(abortPipeline: false)
                                                            if (sonarqube_result.status != 'OK') {
                                                                unstable "SonarQube quality gate: ${sonarqube_result.status}"
                                                            }
                                                            def outstandingIssues = get_sonarqube_unresolved_issues('.scannerwork/report-task.txt')
                                                            writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                                                        }
                                                        milestone label: 'sonarcloud'
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
                                environment{
                                    PIP_CACHE_DIR='/tmp/pipcache'
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    UV_TOOL_DIR='/tmp/uvtools'
                                    UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                }
                                steps{
                                    script{
                                        def envs = []
                                        node('docker && linux'){
                                            docker.image('python').inside('--mount source=python-tmp-uiucpreson-packager,target=/tmp'){
                                                try{
                                                    checkout scm
                                                    sh(script: 'python3 -m venv venv && venv/bin/pip install uv')
                                                    envs = sh(
                                                        label: 'Get tox environments',
                                                        script: './venv/bin/uvx --quiet --with tox-uv tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\n')
                                                } finally{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ]
                                                    )
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
                                                            docker.image('python').inside('--mount source=python-tmp-uiucpreson-packager,target=/tmp'){
                                                                checkout scm
                                                                try{
                                                                    sh( label: 'Running Tox',
                                                                        script: """python3 -m venv venv && venv/bin/pip install uv
                                                                                   . ./venv/bin/activate
                                                                                   uv python install cpython-${version}
                                                                                   uvx -p ${version} --with tox-uv tox run -e ${toxEnv}
                                                                                   rm -rf ./.tox
                                                                                """
                                                                        )
                                                                } catch(e) {
                                                                    sh(script: '''. ./venv/bin/activate
                                                                          uv python list
                                                                          '''
                                                                            )
                                                                    throw e
                                                                } finally{
                                                                    cleanWs(
                                                                        patterns: [
                                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ]
                                                                    )
                                                                }
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
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\pipcache'
                                    UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\uvtools'
                                    UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\uvpython'
                                    UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\uvcache'
                                    VC_RUNTIME_INSTALLER_LOCATION='c:\\msvc_runtime\\'
                                }
                                steps{
                                    script{
                                        def envs = []
                                        node('docker && windows'){
                                            docker.image('python').inside('--mount source=python-tmp-uiucpreson-packager,target=C:\\Users\\ContainerUser\\Documents'){
                                                try{
                                                    checkout scm
                                                    bat(script: 'python -m venv venv && venv\\Scripts\\pip install uv')
                                                    envs = bat(
                                                        label: 'Get tox environments',
                                                        script: '@.\\venv\\Scripts\\uvx --quiet --with tox-uv tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\r\n')
                                                } finally{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && windows'){
                                                            docker.image('python').inside('--mount source=python-tmp-uiucpreson-packager,target=C:\\Users\\ContainerUser\\Documents --mount source=msvc-runtime,target=$VC_RUNTIME_INSTALLER_LOCATION'){
                                                                checkout scm
                                                                try{
                                                                    installMSVCRuntime(env.VC_RUNTIME_INSTALLER_LOCATION)
                                                                    bat(label: 'Install uv',
                                                                        script: 'python -m venv venv && venv\\Scripts\\pip install uv'
                                                                    )
                                                                    retry(3){
                                                                        bat(label: 'Running Tox',
                                                                            script: """call venv\\Scripts\\activate.bat
                                                                                   uv python install cpython-${version}
                                                                                   uvx -p ${version} --with tox-uv tox run -e ${toxEnv}
                                                                                   rmdir /s/q .tox
                                                                                """
                                                                        )
                                                                    }
                                                                } finally{
                                                                    cleanWs(
                                                                        patterns: [
                                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ]
                                                                    )
                                                                }
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
                            UV_INDEX_STRATEGY='unsafe-best-match'
                            UV_CACHE_DIR='/tmp/uvcache'
                        }
                        steps {
                            sh(
                                label: 'Package',
                                script: '''python3 -m venv venv && venv/bin/pip install uv
                                           trap "rm -rf venv" EXIT
                                           . ./venv/bin/activate
                                           uv build
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
                        matrix {
                            axes {
                                axis {
                                    name 'PYTHON_VERSION'
                                    values '3.9', '3.10', '3.11', '3.12', '3.13'
                                }
                                axis {
                                    name 'OS'
                                    values 'linux', 'macos', 'windows'
                                }
                                axis {
                                    name 'ARCHITECTURE'
                                    values 'arm64', 'x86_64'
                                }
                                axis {
                                    name 'PACKAGE_TYPE'
                                    values 'wheel', 'sdist'
                                }
                            }
                            excludes {
                                exclude {
                                    axis {
                                        name 'ARCHITECTURE'
                                        values 'arm64'
                                    }
                                    axis {
                                        name 'OS'
                                        values 'windows'
                                    }
                                }
                            }
                            when{
                                expression{
                                    params.containsKey("INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]
                                }
                            }
                            options {
                                retry(conditions: [agent()], count: 2)
                            }
                            environment{
                                UV_PYTHON="${PYTHON_VERSION}"
                                TOX_ENV="py${PYTHON_VERSION.replace('.', '')}"
                                UV_INDEX_STRATEGY='unsafe-best-match'
                            }
                            stages {
                                stage('Test Package in container') {
                                    when{
                                        expression{['linux', 'windows'].contains(OS)}
                                        beforeAgent true
                                    }
                                    agent {
                                        docker {
                                            image 'python'
                                            label "${OS} && ${ARCHITECTURE} && docker"
                                            args "--mount source=python-tmp-uiucpreson-packager,target=${['windows'].contains(OS) ? 'C:\\Users\\ContainerUser\\Documents': '/tmp'} ${['windows'].contains(OS) ? '--mount source=msvc-runtime,target=c:\\msvc_runtime\\': ''}"
                                        }
                                    }
                                    steps {
                                        unstash 'PYTHON_PACKAGES'
                                        script{
                                            withEnv(
                                                ["TOX_INSTALL_PKG=${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path}"]
                                                ) {
                                                if(isUnix()){
                                                    withEnv([
                                                        'PIP_CACHE_DIR=/tmp/pipcache',
                                                        'UV_TOOL_DIR=/tmp/uvtools',
                                                        'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                                        'UV_CACHE_DIR=/tmp/uvcache'
                                                    ]){
                                                        sh(
                                                            label: 'Testing with tox',
                                                            script: '''python3 -m venv venv
                                                                       . ./venv/bin/activate
                                                                       trap "rm -rf venv" EXIT
                                                                       pip install uv
                                                                       uvx --with tox-uv tox
                                                                       rm -rf .tox
                                                                    '''
                                                        )
                                                    }
                                                } else {
                                                    installMSVCRuntime('c:\\msvc_runtime\\')
                                                    withEnv([
                                                        'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\pipcache',
                                                        'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\uvtools',
                                                        'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\uvpython',
                                                        'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\uvcache'
                                                    ]){
                                                        bat(
                                                            label: 'Install uv',
                                                            script: '''python -m venv venv
                                                                       call venv\\Scripts\\activate.bat
                                                                       pip install uv
                                                                    '''
                                                        )
                                                        script{
                                                            retry(3){
                                                                bat(
                                                                    label: 'Testing with tox',
                                                                    script: '''call venv\\Scripts\\activate.bat
                                                                               uvx --with tox-uv tox
                                                                               rmdir /s/q .tox
                                                                            '''
                                                                )
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    post{
                                        cleanup{
                                            cleanWs(
                                                patterns: [
                                                    [pattern: '.tox/', type: 'INCLUDE'],
                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                    ]
                                            )
                                        }
                                    }
                                }
                                stage('Test Package directly on agent') {
                                    when{
                                        expression{['macos'].contains(OS)}
                                        beforeAgent true
                                    }
                                    agent {
                                        label "${OS} && ${ARCHITECTURE}"
                                    }
                                    steps {
                                        unstash 'PYTHON_PACKAGES'
                                        withEnv(
                                            ["TOX_INSTALL_PKG=${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path}"]
                                            ) {
                                            sh(
                                                label: 'Testing with tox',
                                                script: '''python3 -m venv venv
                                                           trap "rm -rf venv" EXIT
                                                           . ./venv/bin/activate
                                                           pip install uv
                                                           uvx --with tox-uv tox
                                                        '''
                                            )
                                        }
                                    }
                                    post{
                                        cleanup{
                                            cleanWs(
                                                patterns: [
                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
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
            stage('Deploy'){
                parallel {
                    stage('Deploy to pypi') {
                        environment{
                            PIP_CACHE_DIR='/tmp/pipcache'
                            UV_INDEX_STRATEGY='unsafe-best-match'
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
                            withEnv(
                                [
                                    "TWINE_REPOSITORY_URL=${SERVER_URL}",
                                    'UV_INDEX_STRATEGY=unsafe-best-match'
                                ]
                            ){
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
                                                   . ./venv/bin/activate
                                                   pip install uv
                                                   uvx --with-requirements=requirements-dev.txt twine --installpkg upload --disable-progress-bar --non-interactive dist/*
                                                '''
                                    )
                                }
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
