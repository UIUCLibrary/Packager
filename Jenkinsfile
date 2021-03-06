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
def getDevPiStagingIndex(){

    if (env.TAG_NAME?.trim()){
        return "tag_staging"
    } else{
        return "${env.BRANCH_NAME}_staging"
    }
}
pipeline {
    agent none
    parameters {
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "RUN_CHECKS", defaultValue: true, description: "Run checks on code")
        booleanParam(name: "USE_SONARQUBE", defaultValue: true, description: "Send data test data to SonarQube")
        booleanParam(name: "BUILD_PACKAGES", defaultValue: false, description: "Build Python packages")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Master branch Only")
        booleanParam(name: "DEPLOY_ADD_TAG", defaultValue: false, description: "Tag commit to current version")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation. Master branch Only")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "packager", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
            agent {
                dockerfile {
                    filename 'ci/docker/python/linux/Dockerfile'
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
                            filename 'ci/docker/python/linux/Dockerfile'
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
                            filename 'ci/docker/python/linux/Dockerfile'
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
        stage("Checks"){
            when{
                equals expected: true, actual: params.RUN_CHECKS
            }
            stages{
                stage("Test") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/Dockerfile'
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
                                stage("Run Tox test") {
                                    when{
                                        equals expected: true, actual: params.TEST_RUN_TOX
                                    }
                                    steps {
                                        sh "tox -e py"

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
                            filename 'ci/docker/python/linux/Dockerfile'
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
                                unstash "DIST-INFO"
                                def props = readProperties(interpolate: true, file: "uiucprescon.packager.dist-info/METADATA")
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
                            filename 'ci/docker/python/linux/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    steps {
                        sh "python -m pep517.build ."
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
                stage('Testing all Package') {
                    matrix{
                        agent none
                        axes{
                            axis {
                                name "PLATFORM"
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                            axis {
                                name "PYTHON_VERSION"
                                values(
                                    "3.7",
                                    "3.8"
                                )
                            }
                        }
                        stages{
                            stage("Testing Wheel Package"){
                                agent {
                                    dockerfile {
                                        filename "ci/docker/python/${PLATFORM}/Dockerfile"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image[PLATFORM]} --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL"
                                    }
                                }
                                steps{
                                    unstash "PYTHON_PACKAGES"
                                    script{
                                        findFiles(glob: "**/*.whl").each{
                                            cleanWs(
                                                deleteDirs: true,
                                                disableDeferredWipeout: true,
                                                patterns: [
                                                    [pattern: '.git/', type: 'EXCLUDE'],
                                                    [pattern: 'tests/', type: 'EXCLUDE'],
                                                    [pattern: 'dist/', type: 'EXCLUDE'],
                                                    [pattern: 'tox.ini', type: 'EXCLUDE']
                                                ]
                                            )
                                            timeout(15){
                                                if(isUnix()){
                                                    sh(label: "Testing ${it}",
                                                        script: """python --version
                                                                   tox --installpkg=${it.path} -e py -vv
                                                                   """
                                                    )
                                                } else {
                                                    bat(label: "Testing ${it}",
                                                        script: """python --version
                                                                   tox --installpkg=${it.path} -e py -vv
                                                                   """
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }
                                post{
                                    cleanup{
                                        cleanWs(
                                            notFailBuild: true,
                                            deleteDirs: true,
                                            patterns: [
                                                [pattern: 'dist/', type: 'INCLUDE'],
                                                [pattern: '**/__pycache__', type: 'INCLUDE'],
                                                [pattern: 'build/', type: 'INCLUDE'],
                                                [pattern: '.tox/', type: 'INCLUDE'],
                                                ]
                                        )
                                    }
                                }
                            }
                            stage("Testing sdist Package"){
                                agent {
                                    dockerfile {
                                        filename "ci/docker/python/${PLATFORM}/Dockerfile"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image[PLATFORM]} --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL"
                                    }
                                }
                                steps{
                                    unstash "PYTHON_PACKAGES"
                                    script{
                                        findFiles(glob: "dist/*.tar.gz,dist/*.zip").each{
                                            cleanWs(
                                                deleteDirs: true,
                                                disableDeferredWipeout: true,
                                                patterns: [
                                                    [pattern: '.git/', type: 'EXCLUDE'],
                                                    [pattern: 'tests/', type: 'EXCLUDE'],
                                                    [pattern: 'dist/', type: 'EXCLUDE'],
                                                    [pattern: 'tox.ini', type: 'EXCLUDE']
                                                ]
                                            )
                                            timeout(15){
                                                if(isUnix()){
                                                    sh(label: "Testing ${it}",
                                                        script: """python --version
                                                                   tox --installpkg=${it.path} -e py -vv
                                                                   """
                                                    )
                                                } else {
                                                    bat(label: "Testing ${it}",
                                                        script: """python --version
                                                                   tox --installpkg=${it.path} -e py -vv
                                                                   """
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }
                                post{
                                    cleanup{
                                        cleanWs(
                                            notFailBuild: true,
                                            deleteDirs: true,
                                            patterns: [
                                                [pattern: 'dist/', type: 'INCLUDE'],
                                                [pattern: 'build/', type: 'INCLUDE'],
                                                [pattern: '**/__pycache__', type: 'INCLUDE'],
                                                [pattern: '.tox/', type: 'INCLUDE'],
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
                        script{
                            def devpiStagingIndex = getDevPiStagingIndex()
                            sh(label: "Uploading to DevPi Staging",
                               script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                          devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                          devpi use /${env.DEVPI_USR}/${devpiStagingIndex} --clientdir ./devpi
                                          devpi upload --from-dir dist --clientdir ./devpi
                                          """
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
                    matrix {
                        axes {
                            axis {
                                name "PLATFORM"
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                            axis {
                                name 'FORMAT'
                                values 'zip', "whl"
                            }
                            axis {
                                name 'PYTHON_VERSION'
                                values '3.8', "3.7"
                            }
                        }
                        agent {
                          dockerfile {
                            filename "ci/docker/python/${PLATFORM}/Dockerfile"
                            additionalBuildArgs "--build-arg PYTHON_DOCKER_IMAGE_BASE=${CONFIGURATIONS[PYTHON_VERSION].test_docker_image[PLATFORM]} --build-arg PIP_INDEX_URL --build-arg PIP_EXTRA_INDEX_URL"
                            label "${PLATFORM} && docker"
                          }
                        }
                        stages{
                            stage("Testing DevPi Package"){
                                steps{
                                    script{
                                        unstash "DIST-INFO"
                                        def props = readProperties interpolate: true, file: 'uiucprescon.packager.dist-info/METADATA'
                                        def devpiStagingIndex = getDevPiStagingIndex()
                                        timeout(10){
                                            if(isUnix()){
                                                sh(
                                                    label: "Testing ${FORMAT} package stored on DevPi with Python version ${PYTHON_VERSION}",
                                                    script: """devpi use https://devpi.library.illinois.edu --clientdir certs
                                                               devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir certs
                                                               devpi use ${devpiStagingIndex} --clientdir certs
                                                               devpi test --index ${devpiStagingIndex} ${props.Name}==${props.Version} -s ${FORMAT} --clientdir certs -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v
                                                               """
                                                )
                                            }else{
                                                bat(
                                                    label: "Testing ${FORMAT} package stored on DevPi with Python version ${PYTHON_VERSION}",
                                                    script: """devpi use https://devpi.library.illinois.edu --clientdir certs\\
                                                               devpi login %DEVPI_USR% --password %DEVPI_PSW% --clientdir certs\\
                                                               devpi use ${devpiStagingIndex} --clientdir certs\\
                                                               devpi test --index ${devpiStagingIndex} ${props.Name}==${props.Version} -s ${FORMAT} --clientdir certs\\ -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v
                                                               """
                                                )
                                            }
                                        }
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
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    input {
                        message 'Release to DevPi Production?'
                    }
                    steps {
                        unstash "DIST-INFO"
                        script{
                            def props = readProperties interpolate: true, file: "uiucprescon.packager.dist-info/METADATA"
                            def devpiStagingIndex = getDevPiStagingIndex()
                            sh(label: "Pushing to production index",
                               script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                          devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                          devpi push --index DS_Jenkins/${devpiStagingIndex} ${props.Name}==${props.Version} production/release --clientdir ./devpi
                                       """
                            )
                        }
                    }
                }
            }
            post{
                success{
                    node('linux && docker') {
                       script{
                           if (!env.TAG_NAME?.trim()){
                                def devpiStagingIndex = getDevPiStagingIndex()
                                def devpiIndex = "${env.BRANCH_NAME}"

                                docker.build("uiucpresconpackager:devpi",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                    unstash "DIST-INFO"
                                    def props = readProperties interpolate: true, file: 'uiucprescon.packager.dist-info/METADATA'
                                    sh(
                                        label: "Connecting to DevPi Server",
                                        script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                                    )
                                    sh(
                                        label: "Selecting to DevPi index",
                                        script: "devpi use /DS_Jenkins/${devpiStagingIndex} --clientdir ${WORKSPACE}/devpi"
                                    )
                                    sh(
                                        label: "Pushing package to DevPi index",
                                        script:  "devpi push ${props.Name}==${props.Version} DS_Jenkins/${devpiIndex} --clientdir ${WORKSPACE}/devpi"
                                    )
                                }
                            }
                       }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            def devpiStagingIndex = getDevPiStagingIndex()
                            docker.build("uiucpresconpackager:devpi",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: 'uiucprescon.packager.dist-info/METADATA'
                                sh(
                                    label: "Removing package to DevPi index",
                                    script: """devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi
                                               devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi
                                               devpi use /DS_Jenkins/${devpiStagingIndex} --clientdir ${WORKSPACE}/devpi
                                               devpi remove -y ${props.Name}==${props.Version} --clientdir ${WORKSPACE}/devpi
                                               """
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
        stage("Deploy"){
            parallel {
                stage("Tagging git Commit"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PIP_EXTRA_INDEX_URL'
                        }
                    }
                    when{
                        allOf{
                            equals expected: true, actual: params.DEPLOY_ADD_TAG
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        timeout(time: 1, unit: 'DAYS')
                        retry(3)
                    }
                    input {
                          message 'Add a version tag to git commit?'
                          parameters {
                                credentials credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl', defaultValue: 'github.com', description: '', name: 'gitCreds', required: true
                          }
                    }
                    steps{
                        unstash "DIST-INFO"
                        script{
                            def props = readProperties interpolate: true, file: "uiucprescon.packager.dist-info/METADATA"
                            def commitTag = input message: 'git commit', parameters: [string(defaultValue: "v${props.Version}", description: 'Version to use a a git tag', name: 'Tag', trim: false)]
                            withCredentials([usernamePassword(credentialsId: gitCreds, passwordVariable: 'password', usernameVariable: 'username')]) {
                                sh(label: "Tagging ${commitTag}",
                                   script: """git config --local credential.helper "!f() { echo username=\\$username; echo password=\\$password; }; f"
                                              git tag -a ${commitTag} -m 'Tagged by Jenkins'
                                              git push origin --tags
                                   """
                                )
                            }
                        }
                    }
                    post{
                        cleanup{
                            deleteDir()
                        }
                    }
                }
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
