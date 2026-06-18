[Leapp](https://www.leapp.cloud/) is a utility that makes it easier to manage AWS SSO authentication sessions. Using it is optional, but recommended. The desktop app is free, and is all that is needed.

Below are the steps for configuring Leapp.

#### 1. Gather Account Information

First you need to gather some information. Log in to the AWS console and look in the top right corner to grab the following:

- Account ID, e.g. `1768-1584-4596` (replace `<account-id>` in the following steps, WITHOUT dashes, e.g. `176815844596`)
- Federated User, e.g. `aws-innovationlabs-houston-admin/ryan.henderson@slalom.com` (replace `<role-name>` in the following steps with the PREFIX only -- the part before the `/`, e.g. `aws-innovationlabs-houston-admin`)
- Azure App ID, e.g. `6d489cb4-c180-451d-bc45-fdcfe934255e` for Slalom Dev or `724f34aa-ee19-43f1-b7a2-fb3c51abc3a2` for Slalom Prod

#### 2. Configure Leapp

Then in Leapp, configure an AWS Session with the following parameters:

- Named profile: `<you choose, but this is what you will need to put in AWS_PROFILE in your .env file>`
- Aws Region: `us-east-1`
- Role ARN: `arn:aws:iam::<account-id>:role/<role-name>`
- SAML 2.0 Url: `https://launcher.myapps.microsoft.com/api/signin/<azure-app-id>?tenantId=9ca75128-a244-4596-877b-f24828e476e2`
- Identity Provider: `arn:aws:iam::<account-id>:saml-provider/slalomazure`
