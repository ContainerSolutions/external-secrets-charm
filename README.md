# External Secrets Charm
This Charm deploys the [externalsecrets-operator](https://github.com/ContainerSolutions/externalsecret-operator) operator, which reads information from a third party service like AWS Secrets Manager or AWS SSM and automatically injects the values as Kubernetes Secrets.

For more information, check the docs [here](https://github.com/ContainerSolutions/externalsecret-operator#quick-start).

**This project is only a PoC for the [Canonical Operator Framework](https://github.com/canonical/operator), please do not use it in production.**

## Challenges using the Canonical Operator Framework
This PoC was done in a short period of time, with no previous knowledge on how Juju worked on my side. Even though, I faced some challenges:
- Documentation to develop a Kubernetes Operator was very scarce, most of the information was found on forums or discussing with other people
- Within the Kubernetes community, the Operator concept focuses on developing a Kubernetes aware application to manage Kubernetes objects. So far, I was only able to deploy Pods with the Canonical Framework. This can lead to confusion for developers
- Abstracting Kubernetes objects might not be a good idea, since most of the developers will already know how to interact with them natively
- The juju ecosystem presented some bugs affecting the development cycle, like controllers not being deleted, applications crashing etc

## Setting up a Kubernetes environment 
Using microk8s:
```
microk8s install
microk8s enable storage dns
microk8s config | juju add-k8s mycluster --client
juju bootstrap mycluster --config controller-service-type=loadbalancer --config controller-external-ips="[$(multipass info microk8s-vm | grep IPv4 | awk '{print $2}')]"

microk8s kubectl get pod -A
```

## Deploying the Charm
Make sure to have an accessible Kubernetes cluster registered as a Juju cloud and the Juju CLI ecosystem.

Add a new Juju model:
```
juju add-model eso
```

Build the Charm:
```
charmcraft build 
```

Deploy the Charm:
```
juju deploy ./external-secrets-operator.charm
```

Check the installation:
```
juju status
```

## Quick Start: AWS Secret Manager
Create a secret on AWS Secret Manager:
```
aws secretsmanager create-secret \
  --name=eso-key \
  --secret-string='this string is a secret'
```

Create a Kubernetes Secret to hold the AWS credentials. It will be used by the controller to authenticate to AWS and retrieve the AWS Secret Manager data:
```
cat <<EOF | kubectl apply -f -

apiVersion: v1
kind: Secret
metadata:
  name: credentials-awssm
  labels:
    type: asm 
type: Opaque
stringData:
  credentials.json: |-
    {
      "accessKeyID": "",
      "secretAccessKey": ""
    }
EOF
```

Create a `SecretStore`, it represents the AWS provider within the controller:
```
cat <<EOF | kubectl apply -f -

apiVersion: store.externalsecret-operator.container-solutions.com/v1alpha1
kind: SecretStore
metadata:
  name: secretstore-awssm
spec:
  controller: staging
  store:
    type: asm
    auth: 
      secretRef: 
        name: credentials-awssm
    parameters:
      region: eu-central-1
 
EOF
```

Now, create an `ExternalSecret`. It will fetch the data from AWS SM and create a Kubernetes `Secret`.
```
cat <<EOF | kubectl apply -f -

apiVersion: secrets.externalsecret-operator.container-solutions.com/v1alpha1
kind: ExternalSecret
metadata:
  name: externalsecret-sample
spec:
  storeRef: 
    name: secretstore-awssm
  data:
    - key: eso-key
      version: latest

EOF
```

A Secret named `externalsecret-sample` will be created with the content from the AWS Secret Manager key created before.