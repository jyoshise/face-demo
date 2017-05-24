    def gitCommit() {
        sh "git rev-parse HEAD > GIT_COMMIT"
        def gitCommit = readFile('GIT_COMMIT').trim()
        sh "rm -f GIT_COMMIT"
        return gitCommit
    }

    node {
        // Checkout source code from Git
        stage 'Checkout'
        checkout scm

        // Build Docker image
        stage 'Build'
        sh "docker build -t http://gitlab-test.dcos:50000/junichi/face-demo:${gitCommit()} ."

        // Log in and push image to GitLab
        stage 'Publish'
        withCredentials(
            [[
                $class: 'UsernamePasswordMultiBinding',
                credentialsId: 'gitlab',
                passwordVariable: 'GITLAB_PASSWORD',
                usernameVariable: 'GITLAB_USERNAME'
            ]]
        ) {
            sh "docker login -u ${env.GITLAB_USERNAME} -p ${env.GITLAB_PASSWORD} -e demo@mesosphere.com http://gitlab-test.dcos:50000"
            sh "docker push http://gitlab-test.dcos:50000/junichi/face-demo:${gitCommit()}"
        }


        // Deploy
        stage 'Deploy'

        marathon(
            url: 'http://192.168.65.90:8080',
            forceUpdate: false,
            filename: 'marathon.json',
            appid: 'face',
            docker: "http://gitlab-test.dcos:50000/junichi/face-demo:${gitCommit()}".toString()
        )
    }
