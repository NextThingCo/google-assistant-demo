# Setup

To enable access to the Google Assistant API, do the following on your development machine:

1. In the Cloud Platform Console, go to the [Projects page](https://console.cloud.google.com/project?pli=1). Select an existing project or create a new project.

2. Enable the Google Assistant API on the project you selected [at this link](https://console.developers.google.com/apis/api/embeddedassistant.googleapis.com/overview?pli=1). Select your project as mentioned in step 1 and click the “Enable” button.

3. Create an OAuth Client ID with the following steps:
    - [Create the client ID at this link.](https://console.developers.google.com/apis/credentials/oauthclient)
    - You may need to set a product name for the product consent screen. On the OAuth consent screen tab, give the product a name and click Save.
    - Click Other and give the client ID a name.
    - Click Create. A dialog box appears that shows you a client ID and secret. (No need to remember or save this, just close the dialog.)
    - Click ⬇ (at the far right of screen) for the client ID to download the client secret JSON file (client_secret_XXXX.json).

4. Copy the client_secret_XXXX.json file from your development machine to this folder. Alternatively, make a new .json file on your CHIP and paste the data from the file you downloaded into the new one.

5. Open the [Activity Controls page](https://myaccount.google.com/activitycontrols) for the Google account that you want to use with the Assistant. You can use any Google account, it does not need to be your developer account.

Ensure the following toggle switches are enabled (blue):
Web & App Activity
Location History
Device Information
Voice & Audio Activity
