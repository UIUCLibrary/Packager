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
            test_docker_image: "python:3.8",
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

pipeline {
    agent none
    triggers {
       parameterizedCron '@daily % DEPLOY_DEVPI=true; TEST_RUN_TOX=true'
    }
//     options {
//         disableConcurrentBuilds()  //each branch has 1 job running at a time
//     }

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
                    filename 'ci/docker/python/linux/Dockerfile'
                    label 'linux && docker'
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
//                     agent {
//                         dockerfile {
//                             filename 'ci/docker/python/windows/build/msvc/Dockerfile'
//                             label "windows && docker"
//                         }
//                     }
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/Dockerfile'
                            label 'linux && docker'
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
        stage("Test") {
            agent {
                dockerfile {
                    filename 'ci/docker/python/linux/Dockerfile'
                    label 'linux && docker'
                }
            }
//             agent {
//                 dockerfile {
//                     filename 'ci/docker/python/windows/build/msvc/Dockerfile'
//                     label "windows && docker"
//                 }
//             }
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
//                         bat(
//                             label: "Creating logging and report directories",
//                             script: """
//                                 if not exist logs mkdir logs
//                                 if not exist reports\\coverage mkdir reports\\coverage
//                                 if not exist reports\\doctests mkdir reports\\doctests
//                                 if not exist reports\\mypy\\html mkdir reports\\mypy\\html
//                             """
//                         )
                    }
                }
                stage("Running Tests"){
                    parallel {
                        stage("Run PyTest Unit Tests"){
                            steps{
                                sh "coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=reports/pytest/junit-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest"
//                                 bat "coverage run --parallel-mode --source uiucprescon -m pytest --junitxml=reports/pytest/junit-pytest.xml --junit-prefix=${env.NODE_NAME}-pytest "
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
                                sh "python -m sphinx -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log"
//                                 bat "sphinx-build.exe -b doctest -d build/docs/doctrees docs/source reports/doctest -w logs/doctest.log"
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
                                catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                    sh(
                                        script: '''mkdir -p logs
                                                   pylint uiucprescon/packager -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint.txt''',
                                        label: "Running pylint"
                                    )
                                }
                                sh(
                                    script: 'pylint uiucprescon/packager  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint_issues.txt',
                                    label: "Running pylint for sonarqube",
                                    returnStatus: true
                                )
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
                                    sh "flake8 uiucprescon --tee --output-file=logs/flake8.log"
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
                            sh "coverage combine && coverage xml -o reports/coverage.xml && coverage html -d reports/coverage"
//                             bat "coverage combine && coverage xml -o reports\\coverage.xml && coverage html -d reports\\coverage"
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
        stage("Sonarcloud Analysis"){
            agent {
              dockerfile {
                filename 'ci/docker/sonarcloud/Dockerfile'
                label 'linux && docker'
              }
            }
            options{
                lock("uiucprescon.packager-sonarscanner")
            }
            steps{
                checkout scm
                sh "git fetch --all"
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
                    retry(3) {
                        timeout(2) {
                            def sonarqube_result = waitForQualityGate(abortPipeline: false)
                            if (sonarqube_result.status != 'OK') {
                                unstable "SonarQube quality gate: ${sonarqube_result.status}"
                            }
                            def outstandingIssues = get_sonarqube_unresolved_issues(".scannerwork/report-task.txt")
                            writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                        }
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
        stage("Package") {
            agent {
                dockerfile {
                    filename 'ci/docker/python/linux/Dockerfile'
                    label 'linux && docker'
                }
            }
            steps {
                sh "python setup.py bdist_wheel -d dist sdist --format zip -d dist"
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
                        name "PYTHON_VERSION"
                        values(
                            "3.7",
                            "3.8"
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
                        steps{
                            unstash "PYTHON_PACKAGES"
                            bat(
                                label: "Checking Python version",
                                script: "python --version"
                            )
                            script{
                                findFiles(glob: "**/${CONFIGURATIONS[PYTHON_VERSION].package_testing[PYTHON_PACKAGE_TYPE].pkgRegex}").each{
                                    timeout(15){
                                        bat(
                                            script: "tox --installpkg=${WORKSPACE}\\${it} -e py",
                                            label: "Testing ${it}"
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
