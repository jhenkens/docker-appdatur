Docker container that listens for github webhooks, pulls from a github repository, and then runs some scripts and docker-compose.

The intention for this script is to enable a self-hosted stack based on docker-compose and some static configuration. It works best with codercom/code-server mounted to the same directory, so you can manage any conflicts and commit and push manual changes up!
