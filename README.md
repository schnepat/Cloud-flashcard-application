# Cloud-flashcard-application
# Overview

This document describes the scripts and configuration files for deploying and managing a flashcard application using Google App Engine. The application is designed to provide a secure, cloud-based, personal, flashcard tool that uses a number of Google services outlined in the prerequisites section.

# Table of Contents

1.  Prerequisites
2.  Configuration
3.  Deployment
4.  Directory Structure
5.  Usage
6.  Notes
7.  Troubleshooting

# 1. Prerequisites

Before you can deploy this application, you'll need the following:

*   A Google Cloud project: You can create one at the Google Cloud Console.
*   The Google Cloud SDK (gcloud CLI) installed and configured.
*   Specify any other software dependencies, e.g., Python version, Node.js version, Java version, etc.

*   **Google Cloud Services:**  Ensure the following Google Cloud services are enabled for this project. You can enable them via the Google Cloud Console or using the gcloud CLI:

    *   **App Engine:** This application is deployed to Google App Engine. Ensure the App Engine API is enabled for your project. Also, make sure you've selected an App Engine 	location (region) for your project.  As a Platform as a Service, App engine automatically provisions the underlying servers that run the application code, the operating system 	configurations, the runtime environment for languages used (ex Python for this project), load balancing for incoming traffic, scaling, monitoring and logging, as well as a storage 	bucket.
    *   **IAM (Identity and Access Management):**  Enabled by default for most projects. Required for managing permissions and service accounts.  Principle and role permissions will need 	to be granted to allow services to communicate with each other as to users.  
    *   **Cloud Storage (Buckets):**  Although the application is designed around the use of Firestore for storage, Users that upload images for flashcards will have those stored in a 	bucket as Firestore has a small file size limit but is ideal for synchronization, scalability, and flexible schema as defined its NoSQL data model.  
    *   **Firestore:** Make sure the Firestore API is enabled as it is the primary storage for user flashcards.  In instances where users upload an image, the URL for the file (which is in 	the Cloud Storage bucket) will be stored in Firestore. 
    *   **Vertex AI:**  This application utilizes the Vertex AI platform for access to generative AI models to assist users in generating answers to their flashcards.  Ensure the API is 	enabled and proper AIM permissions granted for communications to this service.
    *	**Identity-Aware Proxy (IAP):** To restrict access to this application to specific Google Accounts, IAP is enabled. This service controls access to the website hosting the 	flashcard application and verifies the identity of users.  Users can be added or removed from this service.  


*   **IAM Permissions:** Appropriate IAM permissions to deploy applications to App Engine and access the Google Cloud services you're using.  At a minimum, you'll likely need:

    *   "App Engine Deployer" role to deploy to App Engine.
    *   "Service Account User" role on the App Engine service account (so the deployment process can impersonate the service account).
    *   "Cloud Build Editor" role.
    *   "Storage Object Admin".
    *   "Firestore User".
    *   "Vertex AI User" or "Vertex AI Admin" depending on the operations you are doing.
    *   "IAP-secured Web App User" role to access the application as IAP is enabled.


# 2. Configuration and services

Configuration:
	The flashcard application's behavior is controlled by the following files:


* app.yaml: This file defines the application's runtime environment, instance scaling, handlers, and other core settings.
    	**Important**: Ensure that the `app.yaml` file includes the correct `runtime` (python39)
* .env (Optional): This app uses environmental variables for the storage bucket name as well as the google project id.
* requirements.txt informs app engine on what dependencies to install
*	The directory structure shown in 4. is a basic minimum for the application to run using app engine.


Services:
	These are the configurations for each of the services used in the flashcard application:


**App Engine**
*  In the Google Cloud Console, go to the App Engine page and create an App Engine application within your project.
*  Select a region where you want your app's computing resources to be located. Remember that you can only have one App Engine application per project, and you can't change the location once it's set.
*  Enable the App Engine Admin API and Cloud Build API.
*  Write your application code using your preferred language, libraries, and frameworks (this project uses python with flask.
*   Create an app.yaml file: This configuration file specifies the runtime environment and other settings for your application.
*   Use the gcloud app deploy command to deploy your application to App Engine.
*   After deploying, you can view your application by using the command gcloud app browse or by going to the URL your-project-id.appspot.com . 


**Cloud Storage (Buckets)**
 

*  Access Cloud Storage: In the Google Cloud Console, navigate to Cloud Storage by using the navigation menu or the search bar.
*  Create Bucket: Click the "Create bucket" button.
*  Name Your Bucket: Enter a globally unique name for your bucket.
*  Location Type: Select a location type, either Region, Dual-region, or Multi-region. As the regional option provides the lowest latency and cost, it was used for this project.  Be sure to select a region that best suits the desired location of your backup or data. Choose a region close to you or your users to reduce latency and costs. 
*  Choose a Default Storage Class: Select a storage class, such as Standard, Nearline, Coldline, or Archive, depending on how frequently you'll access the data stored. For backups, consider Nearline (for retention of 30 days or less) or Coldline (for retention of 90 days or more).  This project selected the standard storage
*  Choose How to Control Access to Objects: Select an Access control option. Uniform is recommended for simpler permission management and is used in this project.
*  Click the "Create" button. 
*  Be sure to set permissions to have the users and the application have access to the bucket.


**Firestore**
	- In the Google Cloud Console, navigate to Firestore by using the navigation menu or the search bar.
	- Click on 'create a firestore database'
	- Select Firestore Native under the configuration options, restrictive under the security rules, and multi-region under the location
	- select create database

**Vertex AI**
	- In the Google Cloud Console, navigate to Vertex AI by using the navigation menu or the search bar.
	- select 'enable all recommended AIs' (note that if this doesn't automatically work, you will have to manually find the vertex ai API)

**Identity-Aware Proxy (IAP)**

To grant users access to this web application secured by Identity-Aware Proxy (IAP), you need to add them to the access list with the "IAP-secured Web App User" role. Here's how you  do it:

    	- Go to the Identity-Aware Proxy page in the Google Cloud Console.
    	- Select the project that you want to manage.
    	- Under the "Applications," select the checkbox next to the app engine resource. 
    	- On the right side panel, click "Add Principal".
    	- In the "Add Principal" dialog, enter the email addresses of the users or groups you want to grant access. You can add individual Google Accounts (e.g., user@gmail.com), Google
    	Workspace accounts (e.g., user@example.com ), Google Groups (e.g., admins@googlegroups.com ), service accounts (e.g., server@example.gserviceaccount.com) or even entire Google 	Workspace domains (e.g., example.com).
	- Select the "IAP-secured Web App User" role from the "Roles" dropdown list.
	- Click "Save". 

# 3. Deployment

To deploy the application to App Engine, follow these steps:

1.  **Authenticate with the Google Cloud SDK:**
    ```bash
    gcloud auth login
    ```
2.  **Set the active project:**
    ```bash
    gcloud config set project [Your Project ID]
    ```
    *(Replace \[Your Project ID] with your actual Project ID, which is phrasal-verve-450403-q1)*
3.  **Deploy the application:**
    ```bash
    gcloud app deploy
    ```
    This command will upload your code and configuration to App Engine and start the deployment process.
4.  **Access the application:**
    Once the deployment is complete, you can access your application at `[Your Project ID].appspot.com`.

# 4.  Directory Structure:
	.(root)
	├── app.yaml
	├── main.py
	├── readme.txt
	├── requirements.txt
	├── static
	└── templates
	    └── index.html


# 5.  Usage
	- This application is currently designed for a single user.  The firebase hierarchy and the dependent code will need to be changed to support more users.  
# 6.  Notes
	- There is currently no review session for studying.
# 7.  Troubleshooting
	- Proper IAM permissions
	- The Google Cloud platform is a rapidly changing environment in which services can sometimes be changed.  It is advised to use the Cloud Assist to guide you to proper 	documentation if issues occur during app deployment or app access. 
	- The current library that calls the gemini AI is a preview and may be changed - refer to the newest documentation if there are issues with ai answers. 

